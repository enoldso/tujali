const express = require('express');
const router = express.Router();
const { check, validationResult } = require('express-validator');
const authMiddleware = require('../middleware/auth');
const { models } = require('../models');

/**
 * @route   GET /api/health-info
 * @desc    Get all health information
 * @access  Private
 */
router.get('/', authMiddleware, async (req, res) => {
  try {
    const healthInfo = models.HealthInfo.get_all();
    res.json(healthInfo);
  } catch (err) {
    console.error('Error fetching health information:', err);
    res.status(500).json({ message: 'Server error' });
  }
});

/**
 * @route   GET /api/health-info/:language
 * @desc    Get health information by language
 * @access  Private
 */
router.get('/:language', authMiddleware, async (req, res) => {
  try {
    const language = req.params.language;
    
    if (!language) {
      return res.status(400).json({ message: 'Language is required' });
    }
    
    const healthInfo = models.HealthInfo.get_by_language(language);
    res.json(healthInfo);
  } catch (err) {
    console.error('Error fetching health information by language:', err);
    res.status(500).json({ message: 'Server error' });
  }
});

/**
 * @route   POST /api/health-info
 * @desc    Create new health information
 * @access  Private
 */
router.post('/', [
  authMiddleware,
  check('title', 'Title is required').not().isEmpty(),
  check('content', 'Content is required').not().isEmpty(),
  check('language', 'Language is required').isIn(['en', 'sw'])
], async (req, res) => {
  // Validate request
  const errors = validationResult(req);
  if (!errors.isEmpty()) {
    return res.status(400).json({ errors: errors.array() });
  }
  
  try {
    const { title, content, language } = req.body;
    
    // In a real implementation, this would use HealthInfo.create
    // For demo, we'll create a mock health info
    const newHealthInfoId = Date.now().toString();
    const newHealthInfo = {
      id: newHealthInfoId,
      title,
      content,
      language,
      created_at: new Date().toISOString()
    };
    
    // In a real implementation, we would save this to the database
    // For demo, let's just return the health info as if it was saved
    
    res.status(201).json(newHealthInfo);
  } catch (err) {
    console.error('Error creating health information:', err);
    res.status(500).json({ message: 'Server error' });
  }
});

module.exports = router;