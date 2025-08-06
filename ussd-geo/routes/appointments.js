const express = require('express');
const router = express.Router();
const {
  createAppointment,
  getPatientAppointments,
  getAppointmentDetails,
  updateAppointmentStatus,
  cancelAppointment,
  rescheduleAppointment
} = require('../services/appointmentService');

// Create new appointment
router.post('/', async (req, res) => {
  try {
    const appointmentData = req.body;
    
    // Validate required fields
    const requiredFields = ['patient_id', 'doctor_id', 'appointment_date', 'appointment_time', 'appointment_type'];
    const missingFields = requiredFields.filter(field => !appointmentData[field]);
    
    if (missingFields.length > 0) {
      return res.status(400).json({
        success: false,
        error: 'Missing required fields',
        missing_fields: missingFields
      });
    }
    
    const appointment = await createAppointment(req.db, appointmentData);
    
    res.status(201).json({
      success: true,
      data: appointment,
      message: 'Appointment created successfully'
    });
    
  } catch (error) {
    console.error('Error creating appointment:', error);
    res.status(500).json({
      success: false,
      error: 'Failed to create appointment',
      message: error.message
    });
  }
});

// Get patient appointments
router.get('/patient/:patientId', async (req, res) => {
  try {
    const patientId = req.params.patientId;
    const { include_history = false } = req.query;
    
    const appointments = await getPatientAppointments(
      req.db, 
      patientId, 
      include_history === 'true'
    );
    
    res.json({
      success: true,
      data: appointments,
      count: appointments.length,
      patient_id: patientId
    });
    
  } catch (error) {
    console.error('Error getting patient appointments:', error);
    res.status(500).json({
      success: false,
      error: 'Failed to retrieve patient appointments'
    });
  }
});

// Get appointment details
router.get('/:id', async (req, res) => {
  try {
    const appointmentId = req.params.id;
    const appointment = await getAppointmentDetails(req.db, appointmentId);
    
    if (!appointment) {
      return res.status(404).json({
        success: false,
        error: 'Appointment not found'
      });
    }
    
    res.json({
      success: true,
      data: appointment
    });
    
  } catch (error) {
    console.error('Error getting appointment details:', error);
    res.status(500).json({
      success: false,
      error: 'Failed to retrieve appointment details'
    });
  }
});

// Update appointment status
router.patch('/:id/status', async (req, res) => {
  try {
    const appointmentId = req.params.id;
    const { status, notes } = req.body;
    
    if (!status) {
      return res.status(400).json({
        success: false,
        error: 'Status is required'
      });
    }
    
    const validStatuses = ['confirmed', 'in_progress', 'completed', 'cancelled', 'no_show'];
    if (!validStatuses.includes(status)) {
      return res.status(400).json({
        success: false,
        error: 'Invalid status',
        valid_statuses: validStatuses
      });
    }
    
    const appointment = await updateAppointmentStatus(req.db, appointmentId, status, notes);
    
    if (!appointment) {
      return res.status(404).json({
        success: false,
        error: 'Appointment not found'
      });
    }
    
    res.json({
      success: true,
      data: appointment,
      message: 'Appointment status updated successfully'
    });
    
  } catch (error) {
    console.error('Error updating appointment status:', error);
    res.status(500).json({
      success: false,
      error: 'Failed to update appointment status'
    });
  }
});

// Cancel appointment
router.patch('/:id/cancel', async (req, res) => {
  try {
    const appointmentId = req.params.id;
    const { reason } = req.body;
    
    const appointment = await cancelAppointment(req.db, appointmentId, reason);
    
    res.json({
      success: true,
      data: appointment,
      message: 'Appointment cancelled successfully'
    });
    
  } catch (error) {
    console.error('Error cancelling appointment:', error);
    res.status(500).json({
      success: false,
      error: 'Failed to cancel appointment',
      message: error.message
    });
  }
});

// Reschedule appointment
router.patch('/:id/reschedule', async (req, res) => {
  try {
    const appointmentId = req.params.id;
    const { new_date, new_time } = req.body;
    
    if (!new_date || !new_time) {
      return res.status(400).json({
        success: false,
        error: 'New date and time are required'
      });
    }
    
    const appointment = await rescheduleAppointment(req.db, appointmentId, new_date, new_time);
    
    res.json({
      success: true,
      data: appointment,
      message: 'Appointment rescheduled successfully'
    });
    
  } catch (error) {
    console.error('Error rescheduling appointment:', error);
    res.status(500).json({
      success: false,
      error: 'Failed to reschedule appointment',
      message: error.message
    });
  }
});

// Get appointments by date range
router.get('/date-range/:startDate/:endDate', async (req, res) => {
  try {
    const { startDate, endDate } = req.params;
    const { doctor_id, patient_id, status } = req.query;
    
    let query = `
      SELECT 
        a.*,
        p.full_name as doctor_name,
        p.specialization,
        pt.name as patient_name,
        pt.phone_number as patient_phone
      FROM appointments a
      JOIN providers p ON a.provider_id = p.id
      JOIN patients pt ON a.patient_id = pt.id
      WHERE a.appointment_date >= $1 AND a.appointment_date <= $2
    `;
    
    const params = [startDate, endDate];
    
    if (doctor_id) {
      query += ` AND a.provider_id = $${params.length + 1}`;
      params.push(doctor_id);
    }
    
    if (patient_id) {
      query += ` AND a.patient_id = $${params.length + 1}`;
      params.push(patient_id);
    }
    
    if (status) {
      query += ` AND a.status = $${params.length + 1}`;
      params.push(status);
    }
    
    query += ` ORDER BY a.appointment_date, a.appointment_time`;
    
    const result = await req.db.query(query, params);
    
    res.json({
      success: true,
      data: result.rows,
      count: result.rows.length,
      date_range: { start: startDate, end: endDate }
    });
    
  } catch (error) {
    console.error('Error getting appointments by date range:', error);
    res.status(500).json({
      success: false,
      error: 'Failed to retrieve appointments'
    });
  }
});

// Get appointment statistics
router.get('/stats/summary', async (req, res) => {
  try {
    const { start_date, end_date } = req.query;
    
    let dateFilter = '';
    const params = [];
    
    if (start_date && end_date) {
      dateFilter = 'WHERE a.appointment_date >= $1 AND a.appointment_date <= $2';
      params.push(start_date, end_date);
    }
    
    const query = `
      SELECT 
        COUNT(*) as total_appointments,
        COUNT(CASE WHEN a.status = 'confirmed' THEN 1 END) as confirmed,
        COUNT(CASE WHEN a.status = 'completed' THEN 1 END) as completed,
        COUNT(CASE WHEN a.status = 'cancelled' THEN 1 END) as cancelled,
        COUNT(CASE WHEN a.status = 'no_show' THEN 1 END) as no_show,
        COUNT(CASE WHEN a.appointment_type = 'physical' THEN 1 END) as physical_visits,
        COUNT(CASE WHEN a.appointment_type = 'teleconsult' THEN 1 END) as teleconsultations,
        COUNT(CASE WHEN a.source = 'ussd_geo' THEN 1 END) as ussd_bookings,
        AVG(CASE WHEN p.consultation_fee IS NOT NULL THEN p.consultation_fee END) as avg_consultation_fee
      FROM appointments a
      LEFT JOIN providers p ON a.provider_id = p.id
      ${dateFilter}
    `;
    
    const result = await req.db.query(query, params);
    
    res.json({
      success: true,
      data: result.rows[0],
      date_range: start_date && end_date ? { start: start_date, end: end_date } : null
    });
    
  } catch (error) {
    console.error('Error getting appointment statistics:', error);
    res.status(500).json({
      success: false,
      error: 'Failed to retrieve appointment statistics'
    });
  }
});

module.exports = router;