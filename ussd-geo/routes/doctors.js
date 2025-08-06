const express = require('express');
const router = express.Router();
const { 
  getDoctorDetails, 
  getDoctorAvailability, 
  getDoctorsBySpecialization,
  searchDoctors 
} = require('../services/doctorService');

// Get all doctors
router.get('/', async (req, res) => {
  try {
    const { specialization, location, limit = 20 } = req.query;
    
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
        p.rating,
        p.languages
      FROM providers p
      WHERE p.role = 'provider' AND p.active = true
    `;
    
    const params = [];
    
    if (specialization) {
      query += ` AND LOWER(p.specialization) LIKE LOWER($${params.length + 1})`;
      params.push(`%${specialization}%`);
    }
    
    if (location) {
      query += ` AND LOWER(p.location) LIKE LOWER($${params.length + 1})`;
      params.push(`%${location}%`);
    }
    
    query += ` ORDER BY p.rating DESC, p.years_experience DESC LIMIT $${params.length + 1}`;
    params.push(parseInt(limit));
    
    const result = await req.db.query(query, params);
    
    res.json({
      success: true,
      data: result.rows,
      count: result.rows.length
    });
    
  } catch (error) {
    console.error('Error getting doctors:', error);
    res.status(500).json({
      success: false,
      error: 'Failed to retrieve doctors'
    });
  }
});

// Get doctor by ID
router.get('/:id', async (req, res) => {
  try {
    const doctorId = req.params.id;
    const doctor = await getDoctorDetails(req.db, doctorId);
    
    if (!doctor) {
      return res.status(404).json({
        success: false,
        error: 'Doctor not found'
      });
    }
    
    res.json({
      success: true,
      data: doctor
    });
    
  } catch (error) {
    console.error('Error getting doctor details:', error);
    res.status(500).json({
      success: false,
      error: 'Failed to retrieve doctor details'
    });
  }
});

// Get doctor availability
router.get('/:id/availability', async (req, res) => {
  try {
    const doctorId = req.params.id;
    const { days = 7 } = req.query;
    
    const availability = await getDoctorAvailability(req.db, doctorId, parseInt(days));
    
    res.json({
      success: true,
      data: availability,
      doctor_id: doctorId,
      days: parseInt(days)
    });
    
  } catch (error) {
    console.error('Error getting doctor availability:', error);
    res.status(500).json({
      success: false,
      error: 'Failed to retrieve doctor availability'
    });
  }
});

// Find doctors near location
router.get('/near/:location', async (req, res) => {
  try {
    const location = req.params.location;
    const { limit = 10 } = req.query;
    
    const { findNearestDoctors } = require('../services/geoService');
    const doctors = await findNearestDoctors(req.db, location, parseInt(limit));
    
    res.json({
      success: true,
      data: doctors,
      count: doctors.length,
      location: location
    });
    
  } catch (error) {
    console.error('Error finding doctors near location:', error);
    res.status(500).json({
      success: false,
      error: 'Failed to find doctors near location'
    });
  }
});

// Get doctors by specialization
router.get('/specialization/:specialization', async (req, res) => {
  try {
    const specialization = req.params.specialization;
    const { location, limit = 10 } = req.query;
    
    const doctors = await getDoctorsBySpecialization(
      req.db, 
      specialization, 
      location, 
      parseInt(limit)
    );
    
    res.json({
      success: true,
      data: doctors,
      count: doctors.length,
      specialization: specialization,
      location: location || null
    });
    
  } catch (error) {
    console.error('Error getting doctors by specialization:', error);
    res.status(500).json({
      success: false,
      error: 'Failed to retrieve doctors by specialization'
    });
  }
});

// Search doctors
router.get('/search/:term', async (req, res) => {
  try {
    const searchTerm = req.params.term;
    const { limit = 10 } = req.query;
    
    const doctors = await searchDoctors(req.db, searchTerm, parseInt(limit));
    
    res.json({
      success: true,
      data: doctors,
      count: doctors.length,
      search_term: searchTerm
    });
    
  } catch (error) {
    console.error('Error searching doctors:', error);
    res.status(500).json({
      success: false,
      error: 'Failed to search doctors'
    });
  }
});

// Get doctor's appointments for a specific date
router.get('/:id/appointments/:date', async (req, res) => {
  try {
    const doctorId = req.params.id;
    const date = req.params.date;
    
    const { getDoctorAppointments } = require('../services/appointmentService');
    const appointments = await getDoctorAppointments(req.db, doctorId, date);
    
    res.json({
      success: true,
      data: appointments,
      count: appointments.length,
      doctor_id: doctorId,
      date: date
    });
    
  } catch (error) {
    console.error('Error getting doctor appointments:', error);
    res.status(500).json({
      success: false,
      error: 'Failed to retrieve doctor appointments'
    });
  }
});

// Get available specializations
router.get('/meta/specializations', async (req, res) => {
  try {
    const query = `
      SELECT DISTINCT specialization, COUNT(*) as doctor_count
      FROM providers 
      WHERE role = 'provider' AND active = true
      GROUP BY specialization
      ORDER BY doctor_count DESC, specialization ASC
    `;
    
    const result = await req.db.query(query);
    
    res.json({
      success: true,
      data: result.rows
    });
    
  } catch (error) {
    console.error('Error getting specializations:', error);
    res.status(500).json({
      success: false,
      error: 'Failed to retrieve specializations'
    });
  }
});

// Get available locations
router.get('/meta/locations', async (req, res) => {
  try {
    const query = `
      SELECT DISTINCT location, COUNT(*) as doctor_count
      FROM providers 
      WHERE role = 'provider' AND active = true AND location IS NOT NULL
      GROUP BY location
      ORDER BY doctor_count DESC, location ASC
    `;
    
    const result = await req.db.query(query);
    
    res.json({
      success: true,
      data: result.rows
    });
    
  } catch (error) {
    console.error('Error getting locations:', error);
    res.status(500).json({
      success: false,
      error: 'Failed to retrieve locations'
    });
  }
});

module.exports = router;