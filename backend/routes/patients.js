const express = require('express');
const router = express.Router();
const authMiddleware = require('../middleware/auth');
const { models } = require('../models');

/**
 * @route   GET /api/patients
 * @desc    Get all patients
 * @access  Private
 */
router.get('/', authMiddleware, async (req, res) => {
  try {
    const patients = models.Patient.get_all();
    res.json(patients);
  } catch (err) {
    console.error('Error fetching patients:', err);
    res.status(500).json({ message: 'Server error' });
  }
});

/**
 * @route   GET /api/patients/recent
 * @desc    Get recent patients
 * @access  Private
 */
router.get('/recent', authMiddleware, async (req, res) => {
  try {
    const patients = models.Patient.get_recent(5);
    res.json(patients);
  } catch (err) {
    console.error('Error fetching recent patients:', err);
    res.status(500).json({ message: 'Server error' });
  }
});

/**
 * @route   GET /api/patients/:id
 * @desc    Get patient by ID
 * @access  Private
 */
router.get('/:id', authMiddleware, async (req, res) => {
  try {
    const patient = models.Patient.get_by_id(req.params.id);
    
    if (!patient) {
      return res.status(404).json({ message: 'Patient not found' });
    }
    
    res.json(patient);
  } catch (err) {
    console.error('Error fetching patient:', err);
    res.status(500).json({ message: 'Server error' });
  }
});

/**
 * @route   GET /api/patients/:id/appointments
 * @desc    Get appointments for a patient
 * @access  Private
 */
router.get('/:id/appointments', authMiddleware, async (req, res) => {
  try {
    const appointments = models.Appointment.get_by_patient(req.params.id);
    
    // Enhance appointment data with provider names
    const enhancedAppointments = appointments.map(appointment => {
      const provider = models.Provider.get_by_id(appointment.provider_id);
      return {
        ...appointment,
        provider_name: provider ? provider.name : 'Unknown Provider'
      };
    });
    
    res.json(enhancedAppointments);
  } catch (err) {
    console.error('Error fetching patient appointments:', err);
    res.status(500).json({ message: 'Server error' });
  }
});

module.exports = router;