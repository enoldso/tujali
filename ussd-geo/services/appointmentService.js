/**
 * Appointment service for managing appointment bookings
 */

/**
 * Create a new appointment
 */
async function createAppointment(db, appointmentData) {
  try {
    const {
      patient_id,
      doctor_id,
      appointment_date,
      appointment_time,
      appointment_type,
      status = 'confirmed',
      source = 'ussd_geo',
      notes = null
    } = appointmentData;

    const query = `
      INSERT INTO appointments (
        patient_id,
        provider_id,
        appointment_date,
        appointment_time,
        appointment_type,
        status,
        source,
        notes,
        created_at,
        updated_at
      ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, NOW(), NOW())
      RETURNING *
    `;

    const values = [
      patient_id,
      doctor_id,
      appointment_date,
      appointment_time,
      appointment_type,
      status,
      source,
      notes
    ];

    const result = await db.query(query, values);
    
    if (result.rows.length > 0) {
      // Log the appointment creation
      console.log(`Appointment created: ID ${result.rows[0].id} for patient ${patient_id} with doctor ${doctor_id}`);
      
      // Send confirmation SMS (if SMS service is available)
      await sendAppointmentConfirmation(db, result.rows[0]);
      
      return result.rows[0];
    }
    
    throw new Error('Failed to create appointment');
    
  } catch (error) {
    console.error('Error creating appointment:', error);
    throw error;
  }
}

/**
 * Get patient appointments
 */
async function getPatientAppointments(db, patientId, includeHistory = false) {
  try {
    let query = `
      SELECT 
        a.id,
        a.appointment_date,
        a.appointment_time,
        a.appointment_type,
        a.status,
        a.notes,
        a.created_at,
        p.full_name as doctor_name,
        p.specialization,
        p.phone_number as doctor_phone,
        p.location as doctor_location,
        p.hospital,
        p.consultation_fee
      FROM appointments a
      JOIN providers p ON a.provider_id = p.id
      WHERE a.patient_id = $1
    `;
    
    if (!includeHistory) {
      query += ` AND a.appointment_date >= CURRENT_DATE AND a.status NOT IN ('cancelled', 'completed')`;
    }
    
    query += ` ORDER BY a.appointment_date DESC, a.appointment_time DESC`;
    
    const result = await db.query(query, [patientId]);
    return result.rows;
    
  } catch (error) {
    console.error('Error getting patient appointments:', error);
    throw error;
  }
}

/**
 * Get appointment details
 */
async function getAppointmentDetails(db, appointmentId) {
  try {
    const query = `
      SELECT 
        a.*,
        p.full_name as doctor_name,
        p.specialization,
        p.phone_number as doctor_phone,
        p.location as doctor_location,
        p.hospital,
        p.consultation_fee,
        pt.name as patient_name,
        pt.phone_number as patient_phone
      FROM appointments a
      JOIN providers p ON a.provider_id = p.id
      JOIN patients pt ON a.patient_id = pt.id
      WHERE a.id = $1
    `;
    
    const result = await db.query(query, [appointmentId]);
    
    if (result.rows.length === 0) {
      return null;
    }
    
    return result.rows[0];
    
  } catch (error) {
    console.error('Error getting appointment details:', error);
    throw error;
  }
}

/**
 * Update appointment status
 */
async function updateAppointmentStatus(db, appointmentId, status, notes = null) {
  try {
    const query = `
      UPDATE appointments 
      SET status = $1, notes = COALESCE($2, notes), updated_at = NOW()
      WHERE id = $3
      RETURNING *
    `;
    
    const result = await db.query(query, [status, notes, appointmentId]);
    
    if (result.rows.length > 0) {
      // Send status update notification
      await sendStatusUpdateNotification(db, result.rows[0]);
      return result.rows[0];
    }
    
    return null;
    
  } catch (error) {
    console.error('Error updating appointment status:', error);
    throw error;
  }
}

/**
 * Cancel appointment
 */
async function cancelAppointment(db, appointmentId, reason = null) {
  try {
    const appointment = await getAppointmentDetails(db, appointmentId);
    
    if (!appointment) {
      throw new Error('Appointment not found');
    }
    
    if (appointment.status === 'cancelled') {
      throw new Error('Appointment is already cancelled');
    }
    
    const notes = reason ? `Cancelled: ${reason}` : 'Cancelled by patient';
    
    const result = await updateAppointmentStatus(db, appointmentId, 'cancelled', notes);
    
    // Send cancellation notification
    await sendCancellationNotification(db, result);
    
    return result;
    
  } catch (error) {
    console.error('Error cancelling appointment:', error);
    throw error;
  }
}

/**
 * Reschedule appointment
 */
async function rescheduleAppointment(db, appointmentId, newDate, newTime) {
  try {
    const appointment = await getAppointmentDetails(db, appointmentId);
    
    if (!appointment) {
      throw new Error('Appointment not found');
    }
    
    if (appointment.status === 'cancelled' || appointment.status === 'completed') {
      throw new Error('Cannot reschedule a cancelled or completed appointment');
    }
    
    // Check if new slot is available
    const doctorAvailability = await require('./doctorService').getDoctorAvailability(db, appointment.provider_id);
    const isSlotAvailable = doctorAvailability.some(slot => 
      slot.date === newDate && slot.time === newTime
    );
    
    if (!isSlotAvailable) {
      throw new Error('Selected time slot is not available');
    }
    
    const query = `
      UPDATE appointments 
      SET 
        appointment_date = $1, 
        appointment_time = $2, 
        status = 'rescheduled',
        notes = COALESCE(notes || ' | ', '') || 'Rescheduled from ' || appointment_date || ' ' || appointment_time,
        updated_at = NOW()
      WHERE id = $3
      RETURNING *
    `;
    
    const result = await db.query(query, [newDate, newTime, appointmentId]);
    
    if (result.rows.length > 0) {
      // Send reschedule notification
      await sendRescheduleNotification(db, result.rows[0]);
      return result.rows[0];
    }
    
    return null;
    
  } catch (error) {
    console.error('Error rescheduling appointment:', error);
    throw error;
  }
}

/**
 * Get doctor's appointments for a specific date
 */
async function getDoctorAppointments(db, doctorId, date) {
  try {
    const query = `
      SELECT 
        a.*,
        pt.name as patient_name,
        pt.phone_number as patient_phone,
        pt.age,
        pt.gender
      FROM appointments a
      JOIN patients pt ON a.patient_id = pt.id
      WHERE a.provider_id = $1 
        AND a.appointment_date = $2
        AND a.status NOT IN ('cancelled')
      ORDER BY a.appointment_time
    `;
    
    const result = await db.query(query, [doctorId, date]);
    return result.rows;
    
  } catch (error) {
    console.error('Error getting doctor appointments:', error);
    throw error;
  }
}

/**
 * Send appointment confirmation (placeholder for SMS integration)
 */
async function sendAppointmentConfirmation(db, appointment) {
  try {
    // This would integrate with SMS service (Twilio, Africa's Talking, etc.)
    console.log(`Appointment confirmation: ${appointment.id}`);
    
    // Log the notification
    const logQuery = `
      INSERT INTO notifications (
        type,
        recipient_id,
        recipient_type,
        title,
        message,
        status,
        created_at
      ) VALUES ($1, $2, $3, $4, $5, $6, NOW())
    `;
    
    await db.query(logQuery, [
      'appointment_confirmation',
      appointment.patient_id,
      'patient',
      'Appointment Confirmed',
      `Your appointment has been confirmed for ${appointment.appointment_date} at ${appointment.appointment_time}`,
      'sent'
    ]);
    
  } catch (error) {
    console.error('Error sending appointment confirmation:', error);
  }
}

/**
 * Send status update notification
 */
async function sendStatusUpdateNotification(db, appointment) {
  try {
    console.log(`Appointment status updated: ${appointment.id} - ${appointment.status}`);
    
    // Log the notification
    const logQuery = `
      INSERT INTO notifications (
        type,
        recipient_id,
        recipient_type,
        title,
        message,
        status,
        created_at
      ) VALUES ($1, $2, $3, $4, $5, $6, NOW())
    `;
    
    await db.query(logQuery, [
      'appointment_status_update',
      appointment.patient_id,
      'patient',
      'Appointment Status Update',
      `Your appointment status has been updated to: ${appointment.status}`,
      'sent'
    ]);
    
  } catch (error) {
    console.error('Error sending status update notification:', error);
  }
}

/**
 * Send cancellation notification
 */
async function sendCancellationNotification(db, appointment) {
  try {
    console.log(`Appointment cancelled: ${appointment.id}`);
    
    // Log the notification
    const logQuery = `
      INSERT INTO notifications (
        type,
        recipient_id,
        recipient_type,
        title,
        message,
        status,
        created_at
      ) VALUES ($1, $2, $3, $4, $5, $6, NOW())
    `;
    
    await db.query(logQuery, [
      'appointment_cancellation',
      appointment.patient_id,
      'patient',
      'Appointment Cancelled',
      `Your appointment for ${appointment.appointment_date} at ${appointment.appointment_time} has been cancelled`,
      'sent'
    ]);
    
  } catch (error) {
    console.error('Error sending cancellation notification:', error);
  }
}

/**
 * Send reschedule notification
 */
async function sendRescheduleNotification(db, appointment) {
  try {
    console.log(`Appointment rescheduled: ${appointment.id}`);
    
    // Log the notification
    const logQuery = `
      INSERT INTO notifications (
        type,
        recipient_id,
        recipient_type,
        title,
        message,
        status,
        created_at
      ) VALUES ($1, $2, $3, $4, $5, $6, NOW())
    `;
    
    await db.query(logQuery, [
      'appointment_reschedule',
      appointment.patient_id,
      'patient',
      'Appointment Rescheduled',
      `Your appointment has been rescheduled to ${appointment.appointment_date} at ${appointment.appointment_time}`,
      'sent'
    ]);
    
  } catch (error) {
    console.error('Error sending reschedule notification:', error);
  }
}

module.exports = {
  createAppointment,
  getPatientAppointments,
  getAppointmentDetails,
  updateAppointmentStatus,
  cancelAppointment,
  rescheduleAppointment,
  getDoctorAppointments
};