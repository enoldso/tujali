const express = require('express');
const router = express.Router();
const { handleUSSDFlow } = require('../services/ussdHandler');
const { logUSSDSession } = require('../services/logger');

// Main USSD endpoint
router.post('/', async (req, res) => {
  try {
    const { sessionId, serviceCode, phoneNumber, text } = req.body;
    
    // Log the incoming USSD request
    await logUSSDSession(req.db, {
      session_id: sessionId,
      phone_number: phoneNumber,
      service_code: serviceCode,
      input_text: text,
      timestamp: new Date()
    });

    // Process USSD flow
    const response = await handleUSSDFlow(req.db, {
      sessionId,
      serviceCode,
      phoneNumber,
      text
    });

    // Log the response
    await logUSSDSession(req.db, {
      session_id: sessionId,
      phone_number: phoneNumber,
      service_code: serviceCode,
      response_text: response,
      timestamp: new Date()
    });

    res.set('Content-Type', 'text/plain');
    res.send(response);

  } catch (error) {
    console.error('USSD Error:', error);
    res.set('Content-Type', 'text/plain');
    res.send('END Sorry, we encountered an error. Please try again later.');
  }
});

// USSD callback endpoint for Africa's Talking
router.post('/callback', async (req, res) => {
  try {
    const { sessionId, serviceCode, phoneNumber, text } = req.body;
    
    const response = await handleUSSDFlow(req.db, {
      sessionId,
      serviceCode,
      phoneNumber,
      text
    });

    res.set('Content-Type', 'text/plain');
    res.send(response);

  } catch (error) {
    console.error('USSD Callback Error:', error);
    res.set('Content-Type', 'text/plain');
    res.send('END Service temporarily unavailable. Please try again.');
  }
});

module.exports = router;