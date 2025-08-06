/**
 * Doctor service for managing doctor data and availability
 */

/**
 * Get doctor details by ID
 */
async function getDoctorDetails(db, doctorId) {
  try {
    const query = `
      SELECT 
        p.id,
        p.full_name as name,
        p.specialization,
        p.phone_number,
        p.location,
        p.years_experience,
        p.consultation_fee,
        p.latitude,
        p.longitude,
        p.hospital,
        p.languages,
        p.rating,
        p.available_days,
        p.available_hours,
        p.email,
        p.license_number,
        p.active,
        p.created_at
      FROM providers p
      WHERE p.id = $1 AND p.role = 'provider' AND p.active = true
    `;
    
    const result = await db.query(query, [doctorId]);
    
    if (result.rows.length === 0) {
      return null;
    }
    
    return result.rows[0];
    
  } catch (error) {
    console.error('Error getting doctor details:', error);
    throw error;
  }
}

/**
 * Get doctor availability for booking
 */
async function getDoctorAvailability(db, doctorId, days = 7) {
  try {
    // First get doctor's general availability
    const doctorQuery = `
      SELECT available_days, available_hours, consultation_fee
      FROM providers 
      WHERE id = $1 AND active = true
    `;
    
    const doctorResult = await db.query(doctorQuery, [doctorId]);
    
    if (doctorResult.rows.length === 0) {
      return [];
    }
    
    const doctor = doctorResult.rows[0];
    
    // Get existing appointments to check conflicts
    const appointmentQuery = `
      SELECT appointment_date, appointment_time, status
      FROM appointments 
      WHERE provider_id = $1 
        AND appointment_date >= CURRENT_DATE 
        AND appointment_date <= CURRENT_DATE + INTERVAL '${days} days'
        AND status NOT IN ('cancelled', 'completed')
      ORDER BY appointment_date, appointment_time
    `;
    
    const appointmentResult = await db.query(appointmentQuery, [doctorId]);
    const bookedSlots = appointmentResult.rows;
    
    // Generate available time slots
    const availableSlots = generateAvailableSlots(doctor, bookedSlots, days);
    
    return availableSlots;
    
  } catch (error) {
    console.error('Error getting doctor availability:', error);
    // Return sample availability for testing
    return getSampleAvailability(days);
  }
}

/**
 * Generate available time slots based on doctor's schedule
 */
function generateAvailableSlots(doctor, bookedSlots, days) {
  const slots = [];
  const today = new Date();
  
  // Default working hours if not specified
  const workingHours = doctor.available_hours || '09:00-17:00';
  const workingDays = doctor.available_days || 'Monday,Tuesday,Wednesday,Thursday,Friday';
  
  const [startTime, endTime] = workingHours.split('-');
  const availableDays = workingDays.split(',').map(day => day.trim().toLowerCase());
  
  // Days of the week
  const dayNames = ['sunday', 'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday'];
  
  for (let i = 1; i <= days; i++) {
    const date = new Date(today);
    date.setDate(today.getDate() + i);
    
    const dayName = dayNames[date.getDay()];
    
    // Check if doctor works on this day
    if (!availableDays.includes(dayName)) {
      continue;
    }
    
    // Generate time slots for this day
    const dateStr = date.toISOString().split('T')[0];
    const timeSlots = generateTimeSlots(startTime, endTime);
    
    timeSlots.forEach(time => {
      // Check if this slot is already booked
      const isBooked = bookedSlots.some(slot => 
        slot.appointment_date.toISOString().split('T')[0] === dateStr && 
        slot.appointment_time === time
      );
      
      if (!isBooked) {
        slots.push({
          date: formatDate(date),
          time: time,
          available: true,
          doctor_id: doctor.id
        });
      }
    });
  }
  
  return slots.slice(0, 20); // Limit to 20 slots
}

/**
 * Generate time slots between start and end time
 */
function generateTimeSlots(startTime, endTime, intervalMinutes = 60) {
  const slots = [];
  const [startHour, startMin] = startTime.split(':').map(Number);
  const [endHour, endMin] = endTime.split(':').map(Number);
  
  let currentHour = startHour;
  let currentMin = startMin;
  
  while (currentHour < endHour || (currentHour === endHour && currentMin < endMin)) {
    const timeStr = `${currentHour.toString().padStart(2, '0')}:${currentMin.toString().padStart(2, '0')}`;
    slots.push(timeStr);
    
    currentMin += intervalMinutes;
    if (currentMin >= 60) {
      currentHour += Math.floor(currentMin / 60);
      currentMin = currentMin % 60;
    }
  }
  
  return slots;
}

/**
 * Format date for display
 */
function formatDate(date) {
  const options = { 
    weekday: 'short', 
    month: 'short', 
    day: 'numeric' 
  };
  return date.toLocaleDateString('en-US', options);
}

/**
 * Sample availability for testing
 */
function getSampleAvailability(days = 7) {
  const slots = [];
  const today = new Date();
  
  const times = ['09:00', '10:00', '11:00', '14:00', '15:00', '16:00'];
  
  for (let i = 1; i <= Math.min(days, 5); i++) {
    const date = new Date(today);
    date.setDate(today.getDate() + i);
    
    // Skip weekends
    if (date.getDay() === 0 || date.getDay() === 6) {
      continue;
    }
    
    // Add 2-3 available slots per day
    const availableTimes = times.slice(0, Math.floor(Math.random() * 3) + 2);
    
    availableTimes.forEach(time => {
      slots.push({
        date: formatDate(date),
        time: time,
        available: true
      });
    });
  }
  
  return slots;
}

/**
 * Get doctors by specialization
 */
async function getDoctorsBySpecialization(db, specialization, location = null, limit = 10) {
  try {
    let query = `
      SELECT 
        p.id,
        p.full_name as name,
        p.specialization,
        p.phone_number,
        p.location,
        p.years_experience,
        p.consultation_fee,
        p.hospital,
        p.rating
      FROM providers p
      WHERE p.role = 'provider' 
        AND p.active = true
        AND LOWER(p.specialization) LIKE LOWER($1)
    `;
    
    const params = [`%${specialization}%`];
    
    if (location) {
      query += ` AND LOWER(p.location) LIKE LOWER($2)`;
      params.push(`%${location}%`);
    }
    
    query += ` ORDER BY p.rating DESC, p.years_experience DESC LIMIT $${params.length + 1}`;
    params.push(limit);
    
    const result = await db.query(query, params);
    return result.rows;
    
  } catch (error) {
    console.error('Error getting doctors by specialization:', error);
    throw error;
  }
}

/**
 * Search doctors by name or hospital
 */
async function searchDoctors(db, searchTerm, limit = 10) {
  try {
    const query = `
      SELECT 
        p.id,
        p.full_name as name,
        p.specialization,
        p.phone_number,
        p.location,
        p.years_experience,
        p.consultation_fee,
        p.hospital,
        p.rating
      FROM providers p
      WHERE p.role = 'provider' 
        AND p.active = true
        AND (
          LOWER(p.full_name) LIKE LOWER($1) OR
          LOWER(p.hospital) LIKE LOWER($1) OR
          LOWER(p.specialization) LIKE LOWER($1)
        )
      ORDER BY p.rating DESC, p.years_experience DESC 
      LIMIT $2
    `;
    
    const result = await db.query(query, [`%${searchTerm}%`, limit]);
    return result.rows;
    
  } catch (error) {
    console.error('Error searching doctors:', error);
    throw error;
  }
}

module.exports = {
  getDoctorDetails,
  getDoctorAvailability,
  getDoctorsBySpecialization,
  searchDoctors
};