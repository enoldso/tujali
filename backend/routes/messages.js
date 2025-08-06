const express = require('express');
const router = express.Router();
const { check, validationResult } = require('express-validator');
const authMiddleware = require('../middleware/auth');
const { models } = require('../models');

/**
 * @route   GET /api/messages/conversations
 * @desc    Get all conversations for a provider
 * @access  Private
 */
router.get('/conversations', authMiddleware, async (req, res) => {
  try {
    const providerId = req.query.provider_id;
    
    if (!providerId) {
      return res.status(400).json({ message: 'Provider ID is required' });
    }
    
    const conversations = models.Message.get_conversations(providerId);
    res.json(conversations);
  } catch (err) {
    console.error('Error fetching conversations:', err);
    res.status(500).json({ message: 'Server error' });
  }
});

/**
 * @route   GET /api/messages/:patientId
 * @desc    Get conversation with a specific patient
 * @access  Private
 */
router.get('/:patientId', authMiddleware, async (req, res) => {
  try {
    const providerId = req.query.provider_id;
    const patientId = req.params.patientId;
    
    if (!providerId) {
      return res.status(400).json({ message: 'Provider ID is required' });
    }
    
    const messages = models.Message.get_conversation(providerId, patientId);
    
    // Mark messages as read
    models.Message.mark_as_read(patientId, providerId);
    
    res.json(messages);
  } catch (err) {
    console.error('Error fetching messages:', err);
    res.status(500).json({ message: 'Server error' });
  }
});

/**
 * @route   POST /api/messages
 * @desc    Send a message to a patient
 * @access  Private
 */
router.post('/', [
  authMiddleware,
  check('provider_id', 'Provider ID is required').not().isEmpty(),
  check('patient_id', 'Patient ID is required').not().isEmpty(),
  check('content', 'Message content is required').not().isEmpty()
], async (req, res) => {
  // Validate request
  const errors = validationResult(req);
  if (!errors.isEmpty()) {
    return res.status(400).json({ errors: errors.array() });
  }
  
  try {
    const { provider_id, patient_id, content } = req.body;
    
    // Check if provider and patient exist
    const provider = models.Provider.get_by_id(provider_id);
    const patient = models.Patient.get_by_id(patient_id);
    
    if (!provider) {
      return res.status(404).json({ message: 'Provider not found' });
    }
    
    if (!patient) {
      return res.status(404).json({ message: 'Patient not found' });
    }
    
    // In a real implementation, this would use Message.create
    // For demo, we'll create a mock message
    const newMessageId = Date.now().toString();
    const newMessage = {
      id: newMessageId,
      provider_id,
      patient_id,
      content,
      sender_type: 'provider',
      is_read: false,
      created_at: new Date().toISOString()
    };
    
    // In a real implementation, we would save this to the database
    // For demo, let's just return the message as if it was saved
    
    res.status(201).json(newMessage);
  } catch (err) {
    console.error('Error sending message:', err);
    res.status(500).json({ message: 'Server error' });
  }
});

/**
 * @route   GET /api/messages/unread/count
 * @desc    Get count of unread messages for a provider
 * @access  Private
 */
router.get('/unread/count', authMiddleware, async (req, res) => {
  try {
    const providerId = req.query.provider_id;
    
    if (!providerId) {
      return res.status(400).json({ message: 'Provider ID is required' });
    }
    
    const unreadCount = models.Message.get_unread_count(providerId);
    res.json({ count: unreadCount });
  } catch (err) {
    console.error('Error fetching unread count:', err);
    res.status(500).json({ message: 'Server error' });
  }
});

/**
 * @route   GET /api/messages/recent
 * @desc    Get recent messages for a provider
 * @access  Private
 */
router.get('/recent', authMiddleware, async (req, res) => {
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