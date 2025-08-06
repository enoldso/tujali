const express = require('express');
const router = express.Router();
const { findNearestDoctors, parseLocation, calculateDistance } = require('../services/geoService');
const { logGeoSearch } = require('../services/logger');

// Find nearest doctors by location
router.post('/doctors/nearby', async (req, res) => {
  try {
    const { location, phone_number, limit = 10 } = req.body;
    
    if (!location) {
      return res.status(400).json({
        success: false,
        error: 'Location is required'
      });
    }
    
    const doctors = await findNearestDoctors(req.db, location, parseInt(limit));
    
    // Log the search
    await logGeoSearch(req.db, {
      phone_number: phone_number || 'unknown',
      location_input: location,
      results_count: doctors.length,
      search_timestamp: new Date()
    });
    
    res.json({
      success: true,
      data: doctors,
      count: doctors.length,
      location: location
    });
  } catch (error) {
    console.error('Error finding nearby doctors:', error);
    res.status(500).json({
      success: false,
      error: 'Failed to find nearby doctors'
    });
  }
});

// Parse location coordinates
router.post('/location/parse', async (req, res) => {
  try {
    const { location } = req.body;
    
    if (!location) {
      return res.status(400).json({
        success: false,
        error: 'Location is required'
      });
    }
    
    const coordinates = parseLocation(location);
    
    res.json({
      success: true,
      data: coordinates,
      input: location
    });
  } catch (error) {
    console.error('Error parsing location:', error);
    res.status(500).json({
      success: false,
      error: 'Failed to parse location'
    });
  }
});

// Calculate distance between two points
router.post('/distance/calculate', async (req, res) => {
  try {
    const { from_lat, from_lng, to_lat, to_lng } = req.body;
    
    if (!from_lat || !from_lng || !to_lat || !to_lng) {
      return res.status(400).json({
        success: false,
        error: 'All coordinates (from_lat, from_lng, to_lat, to_lng) are required'
      });
    }
    
    const distance = calculateDistance(
      parseFloat(from_lat),
      parseFloat(from_lng),
      parseFloat(to_lat),
      parseFloat(to_lng)
    );
    
    res.json({
      success: true,
      data: {
        distance: distance,
        unit: 'km',
        from: { lat: from_lat, lng: from_lng },
        to: { lat: to_lat, lng: to_lng }
      }
    });
  } catch (error) {
    console.error('Error calculating distance:', error);
    res.status(500).json({
      success: false,
      error: 'Failed to calculate distance'
    });
  }
});

// Get supported locations
router.get('/locations/supported', (req, res) => {
  try {
    const supportedLocations = {
      major_cities: [
        'Nairobi', 'Mombasa', 'Kisumu', 'Nakuru', 'Eldoret',
        'Meru', 'Kikuyu', 'Malindi', 'Garissa', 'Kitale',
        'Thika', 'Machakos', 'Kericho', 'Nyeri', 'Embu'
      ],
      landmarks: [
        'CBD', 'City Center', 'Downtown', 'Westgate', 'Karen',
        'Westlands', 'Kasarani', 'Kondele', 'Nyalenda', 'Stadium',
        'Pipeline', 'Langas', 'Moi University'
      ],
      formats: [
        'City name (e.g., "Nairobi")',
        'City with area (e.g., "Nairobi, Westlands")',
        'Landmark (e.g., "Near Westgate Mall")',
        'GPS coordinates (e.g., "-1.286389, 36.817223")'
      ]
    };
    
    res.json({
      success: true,
      data: supportedLocations
    });
  } catch (error) {
    console.error('Error getting supported locations:', error);
    res.status(500).json({
      success: false,
      error: 'Failed to retrieve supported locations'
    });
  }
});

module.exports = router;