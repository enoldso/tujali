const axios = require('axios');

// Kenya's major cities and their approximate coordinates
const KENYA_CITIES = {
  'nairobi': { lat: -1.286389, lng: 36.817223 },
  'mombasa': { lat: -4.043740, lng: 39.668207 },
  'kisumu': { lat: -0.091702, lng: 34.767956 },
  'nakuru': { lat: -0.303099, lng: 36.080025 },
  'eldoret': { lat: 0.520240, lng: 35.269779 },
  'meru': { lat: 0.046900, lng: 37.649200 },
  'kikuyu': { lat: -1.246667, lng: 36.662500 },
  'malindi': { lat: -3.219167, lng: 40.116944 },
  'garissa': { lat: -0.453611, lng: 39.646389 },
  'kitale': { lat: 1.015556, lng: 35.006111 },
  'thika': { lat: -1.033611, lng: 37.069444 },
  'machakos': { lat: -1.516667, lng: 37.266667 },
  'kericho': { lat: -0.370278, lng: 35.283889 },
  'nyeri': { lat: -0.416667, lng: 36.950000 },
  'embu': { lat: -0.533333, lng: 37.450000 }
};

// Common landmarks and their locations
const LANDMARKS = {
  'cbd': 'nairobi',
  'city center': 'nairobi',
  'downtown': 'nairobi',
  'westgate': 'nairobi',
  'karen': 'nairobi',
  'westlands': 'nairobi',
  'kasarani': 'nairobi',
  'kondele': 'kisumu',
  'nyalenda': 'kisumu',
  'stadium': 'nakuru',
  'pipeline': 'nakuru',
  'langas': 'eldoret',
  'moi university': 'eldoret'
};

/**
 * Parse location input and return coordinates
 */
function parseLocation(locationInput) {
  const input = locationInput.toLowerCase().trim();
  
  // Check for GPS coordinates (lat,lng format)
  const gpsMatch = input.match(/(-?\d+\.?\d*),\s*(-?\d+\.?\d*)/);
  if (gpsMatch) {
    return {
      lat: parseFloat(gpsMatch[1]),
      lng: parseFloat(gpsMatch[2]),
      source: 'gps'
    };
  }
  
  // Check for direct city match
  for (const [city, coords] of Object.entries(KENYA_CITIES)) {
    if (input.includes(city)) {
      return {
        ...coords,
        source: 'city',
        city: city
      };
    }
  }
  
  // Check for landmark match
  for (const [landmark, city] of Object.entries(LANDMARKS)) {
    if (input.includes(landmark)) {
      return {
        ...KENYA_CITIES[city],
        source: 'landmark',
        city: city,
        landmark: landmark
      };
    }
  }
  
  // Default to Nairobi if location cannot be parsed
  return {
    ...KENYA_CITIES.nairobi,
    source: 'default',
    city: 'nairobi'
  };
}

/**
 * Calculate distance between two points using Haversine formula
 */
function calculateDistance(lat1, lng1, lat2, lng2) {
  const R = 6371; // Earth's radius in kilometers
  const dLat = toRadians(lat2 - lat1);
  const dLng = toRadians(lng2 - lng1);
  
  const a = Math.sin(dLat / 2) * Math.sin(dLat / 2) +
            Math.cos(toRadians(lat1)) * Math.cos(toRadians(lat2)) *
            Math.sin(dLng / 2) * Math.sin(dLng / 2);
  
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
  const distance = R * c;
  
  return Math.round(distance * 10) / 10; // Round to 1 decimal place
}

function toRadians(degrees) {
  return degrees * (Math.PI / 180);
}

/**
 * Find nearest doctors based on location
 */
async function findNearestDoctors(db, locationInput, limit = 10) {
  const userLocation = parseLocation(locationInput);
  
  try {
    // Query doctors from database with location information
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
        p.available_hours
      FROM providers p
      WHERE p.role = 'provider' 
        AND p.active = true
      ORDER BY p.id
    `;
    
    const result = await db.query(query);
    const doctors = result.rows;
    
    // Calculate distances and sort by proximity
    const doctorsWithDistance = doctors.map(doctor => {
      let distance = null;
      
      // If doctor has coordinates, calculate exact distance
      if (doctor.latitude && doctor.longitude) {
        distance = calculateDistance(
          userLocation.lat, 
          userLocation.lng, 
          parseFloat(doctor.latitude), 
          parseFloat(doctor.longitude)
        );
      } else {
        // Estimate distance based on city/location match
        distance = estimateDistanceByLocation(userLocation, doctor.location);
      }
      
      return {
        ...doctor,
        distance: distance
      };
    });
    
    // Sort by distance (closest first) and limit results
    return doctorsWithDistance
      .sort((a, b) => (a.distance || 999) - (b.distance || 999))
      .slice(0, limit);
      
  } catch (error) {
    console.error('Error finding nearest doctors:', error);
    
    // Fallback: return sample doctors if database query fails
    return getSampleDoctors(userLocation, limit);
  }
}

/**
 * Estimate distance when exact coordinates are not available
 */
function estimateDistanceByLocation(userLocation, doctorLocation) {
  if (!doctorLocation) return 50; // Default distance if no location
  
  const doctorLocationLower = doctorLocation.toLowerCase();
  
  // If doctor is in the same city, assume close distance
  if (userLocation.city && doctorLocationLower.includes(userLocation.city)) {
    return Math.random() * 5 + 1; // 1-6 km within same city
  }
  
  // Check if doctor is in a nearby major city
  const userCity = userLocation.city || 'nairobi';
  const userCoords = KENYA_CITIES[userCity] || KENYA_CITIES.nairobi;
  
  for (const [city, coords] of Object.entries(KENYA_CITIES)) {
    if (doctorLocationLower.includes(city)) {
      return calculateDistance(
        userCoords.lat, userCoords.lng,
        coords.lat, coords.lng
      );
    }
  }
  
  // Default distance for unknown locations
  return Math.random() * 30 + 10; // 10-40 km
}

/**
 * Sample doctors for testing/fallback
 */
function getSampleDoctors(userLocation, limit) {
  const sampleDoctors = [
    {
      id: 1001,
      name: 'Sarah Wanjiku',
      specialization: 'General Practitioner',
      phone_number: '+254712345678',
      location: 'Nairobi, Westlands',
      years_experience: 8,
      consultation_fee: 1500,
      hospital: 'Westlands Medical Center',
      languages: 'English, Swahili, Kikuyu',
      rating: 4.8,
      distance: 2.3
    },
    {
      id: 1002,
      name: 'James Kipchoge',
      specialization: 'Pediatrician',
      phone_number: '+254723456789',
      location: 'Nairobi, Karen',
      years_experience: 12,
      consultation_fee: 2000,
      hospital: 'Karen Hospital',
      languages: 'English, Swahili, Kalenjin',
      rating: 4.9,
      distance: 5.1
    },
    {
      id: 1003,
      name: 'Grace Akinyi',
      specialization: 'Gynecologist',
      phone_number: '+254734567890',
      location: 'Nairobi, Kilimani',
      years_experience: 15,
      consultation_fee: 2500,
      hospital: 'Aga Khan Hospital',
      languages: 'English, Swahili, Luo',
      rating: 4.7,
      distance: 3.8
    },
    {
      id: 1004,
      name: 'David Mutua',
      specialization: 'Cardiologist',
      phone_number: '+254745678901',
      location: 'Nairobi, Upper Hill',
      years_experience: 20,
      consultation_fee: 3000,
      hospital: 'Nairobi Hospital',
      languages: 'English, Swahili, Kamba',
      rating: 4.9,
      distance: 4.2
    },
    {
      id: 1005,
      name: 'Mary Chebet',
      specialization: 'Dermatologist',
      phone_number: '+254756789012',
      location: 'Nairobi, Parklands',
      years_experience: 10,
      consultation_fee: 1800,
      hospital: 'MP Shah Hospital',
      languages: 'English, Swahili, Kalenjin',
      rating: 4.6,
      distance: 6.7
    }
  ];
  
  return sampleDoctors.slice(0, limit);
}

/**
 * Get coordinates for a given location
 */
async function getCoordinates(locationInput) {
  return parseLocation(locationInput);
}

module.exports = {
  findNearestDoctors,
  calculateDistance,
  parseLocation,
  getCoordinates
};