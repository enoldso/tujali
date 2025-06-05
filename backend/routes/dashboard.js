const express = require('express');
const router = express.Router();
const authMiddleware = require('../middleware/auth');
const { models } = require('../models');

/**
 * @route   GET /api/dashboard/stats
 * @desc    Get dashboard statistics
 * @access  Private
 */
router.get('/stats', authMiddleware, async (req, res) => {
  try {
    const providerId = req.query.provider_id;
    
    if (!providerId) {
      return res.status(400).json({ message: 'Provider ID is required' });
    }
    
    // Get statistics
    const totalPatients = models.Patient.get_count();
    const pendingAppointments = models.Appointment.get_count_by_status(providerId, 'pending');
    const unreadMessages = models.Message.get_unread_count(providerId);
    
    const stats = {
      totalPatients,
      pendingAppointments,
      unreadMessages
    };
    
    res.json(stats);
  } catch (err) {
    console.error('Error fetching dashboard stats:', err);
    res.status(500).json({ message: 'Server error' });
  }
});

/**
 * @route   GET /api/dashboard/recent-patients
 * @desc    Get recent patients
 * @access  Private
 */
router.get('/recent-patients', authMiddleware, async (req, res) => {
  try {
    const patients = models.Patient.get_recent(5);
    res.json(patients);
  } catch (err) {
    console.error('Error fetching recent patients:', err);
    res.status(500).json({ message: 'Server error' });
  }
});

/**
 * @route   GET /api/dashboard/recent-appointments
 * @desc    Get recent appointments
 * @access  Private
 */
router.get('/recent-appointments', authMiddleware, async (req, res) => {
  try {
    const providerId = req.query.provider_id;
    
    if (!providerId) {
      return res.status(400).json({ message: 'Provider ID is required' });
    }
    
    const appointments = models.Appointment.get_recent_by_provider(providerId, 5);
    
    // Enhance appointments with patient names
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
 * @route   GET /api/dashboard/recent-messages
 * @desc    Get recent messages
 * @access  Private
 */
router.get('/recent-messages', authMiddleware, async (req, res) => {
  try {
    const providerId = req.query.provider_id;
    
    if (!providerId) {
      return res.status(400).json({ message: 'Provider ID is required' });
    }
    
    const messages = models.Message.get_recent_by_provider(providerId, 5);
    
    // Enhance messages with patient names
    const enhancedMessages = messages.map(message => {
      const patient = models.Patient.get_by_id(message.patient_id);
      return {
        ...message,
        patient_name: patient ? patient.name : 'Unknown Patient'
      };
    });
    
    res.json(enhancedMessages);
  } catch (err) {
    console.error('Error fetching recent messages:', err);
    res.status(500).json({ message: 'Server error' });
  }
});

module.exports = router;