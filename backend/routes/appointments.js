const express = require('express');
const router = express.Router();
const { check, validationResult } = require('express-validator');
const authMiddleware = require('../middleware/auth');
const { models } = require('../models');

/**
 * @route   GET /api/appointments
 * @desc    Get all appointments for a provider
 * @access  Private
 */
router.get('/', authMiddleware, async (req, res) => {
  try {
    const providerId = req.query.provider_id;
    
    if (!providerId) {
      return res.status(400).json({ message: 'Provider ID is required' });
    }
    
    const appointments = models.Appointment.get_by_provider(providerId);
    
    // Enhance appointment data with patient names
    const enhancedAppointments = appointments.map(appointment => {
      const patient = models.Patient.get_by_id(appointment.patient_id);
      return {
        ...appointment,
        patient_name: patient ? patient.name : 'Unknown Patient'
      };
    });
    
    res.json(enhancedAppointments);
  } catch (err) {
    console.error('Error fetching appointments:', err);
    res.status(500).json({ message: 'Server error' });
  }
});

/**
 * @route   GET /api/appointments/recent
 * @desc    Get recent appointments for a provider
 * @access  Private
 */
router.get('/recent', authMiddleware, async (req, res) => {
  try {
    const providerId = req.query.provider_id;
    
    if (!providerId) {
      return res.status(400).json({ message: 'Provider ID is required' });
    }
    
    const appointments = models.Appointment.get_recent_by_provider(providerId, 5);
    
    // Enhance appointment data with patient names
    const enhancedAppointments = appointments.map(appointment => {
      const patient = models.Patient.get_by_id(appointment.patient_id);
      return {
        ...appointment,
        patient_name: patient ? patient.name : 'Unknown Patient'
      };
    });
    
    res.json(enhancedAppointments);
  } catch (err) {
    console.error('Error fetching recent appointments:', err);
    res.status(500).json({ message: 'Server error' });
  }
});

/**
 * @route   GET /api/appointments/:id
 * @desc    Get appointment by ID
 * @access  Private
 */
router.get('/:id', authMiddleware, async (req, res) => {
  try {
    const appointment = models.Appointment.get_by_id(req.params.id);
    
    if (!appointment) {
      return res.status(404).json({ message: 'Appointment not found' });
    }
    
    // Enhance appointment with patient and provider info
    const patient = models.Patient.get_by_id(appointment.patient_id);
    const provider = models.Provider.get_by_id(appointment.provider_id);
    
    const enhancedAppointment = {
      ...appointment,
      patient_name: patient ? patient.name : 'Unknown Patient',
      provider_name: provider ? provider.name : 'Unknown Provider'
    };
    
    res.json(enhancedAppointment);
  } catch (err) {
    console.error('Error fetching appointment:', err);
    res.status(500).json({ message: 'Server error' });
  }
});

/**
 * @route   PUT /api/appointments/:id/status
 * @desc    Update appointment status
 * @access  Private
 */
router.put('/:id/status', [
  authMiddleware,
  check('status', 'Status is required').not().isEmpty(),
  check('status', 'Invalid status').isIn(['pending', 'confirmed', 'completed', 'cancelled'])
], async (req, res) => {
  // Validate request
  const errors = validationResult(req);
  if (!errors.isEmpty()) {
    return res.status(400).json({ errors: errors.array() });
  }
  
  try {
    const { status } = req.body;
    const appointmentId = req.params.id;
    
    const appointment = models.Appointment.get_by_id(appointmentId);
    
    if (!appointment) {
      return res.status(404).json({ message: 'Appointment not found' });
    }
    
    const success = models.Appointment.update_status(appointmentId, status);
    
    if (!success) {
      return res.status(400).json({ message: 'Failed to update appointment status' });
    }
    
    // Get the updated appointment
    const updatedAppointment = models.Appointment.get_by_id(appointmentId);
    
    res.json(updatedAppointment);
  } catch (err) {
    console.error('Error updating appointment status:', err);
    res.status(500).json({ message: 'Server error' });
  }
});

module.exports = router;