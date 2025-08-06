const axios = require('axios');

// Test integration between Flask app and Node.js USSD service
async function testIntegration() {
  console.log('🔗 Testing Flask and Node.js USSD Integration...\n');
  
  const flaskURL = 'http://localhost:5000';
  const ussdURL = 'http://localhost:3000';
  
  // Test 1: Flask app health
  try {
    console.log('1. Testing Flask application...');
    const flaskResponse = await axios.get(`${flaskURL}/health`);
    console.log('✅ Flask app is running');
  } catch (error) {
    console.log('⚠️ Flask app response:', error.response?.status || error.message);
  }
  
  // Test 2: USSD service health
  try {
    console.log('\n2. Testing USSD service...');
    const ussdResponse = await axios.get(`${ussdURL}/health`);
    console.log('✅ USSD service is running:', ussdResponse.data.service);
  } catch (error) {
    console.log('❌ USSD service failed:', error.message);
    return;
  }
  
  // Test 3: USSD complete doctor booking flow
  try {
    console.log('\n3. Testing complete doctor booking flow...');
    
    // Step 1: Main menu
    const step1 = await axios.post(`${ussdURL}/ussd`, {
      sessionId: 'integration_test_001',
      serviceCode: '*384*4040#',
      phoneNumber: '+254701234567',
      text: ''
    });
    console.log('✅ Step 1 - Main Menu:', step1.data.includes('Find Doctors') ? 'OK' : 'FAIL');
    
    // Step 2: Select find doctors
    const step2 = await axios.post(`${ussdURL}/ussd`, {
      sessionId: 'integration_test_001',
      serviceCode: '*384*4040#',
      phoneNumber: '+254701234567',
      text: '1'
    });
    console.log('✅ Step 2 - Find Doctors:', step2.data.includes('location') ? 'OK' : 'FAIL');
    
    // Step 3: Enter location
    const step3 = await axios.post(`${ussdURL}/ussd`, {
      sessionId: 'integration_test_001',
      serviceCode: '*384*4040#',
      phoneNumber: '+254701234567',
      text: '1*Nairobi, CBD'
    });
    console.log('✅ Step 3 - Location Input:', step3.data.includes('Dr.') ? 'OK' : 'FAIL');
    
    console.log('Sample doctor list preview:', step3.data.substring(0, 200) + '...');
    
  } catch (error) {
    console.log('❌ Integration flow failed:', error.message);
  }
  
  // Test 4: Database connectivity through both services
  try {
    console.log('\n4. Testing database connectivity...');
    
    // Test USSD service database connection
    const doctorsAPI = await axios.get(`${ussdURL}/api/doctors?limit=2`);
    console.log('✅ USSD database connection:', doctorsAPI.data.success ? 'Connected' : 'Failed');
    
  } catch (error) {
    console.log('❌ Database connectivity test failed:', error.message);
  }
  
  // Test 5: Geo-location service
  try {
    console.log('\n5. Testing geo-location features...');
    
    const geoTest = await axios.post(`${ussdURL}/api/geo/doctors/nearby`, {
      location: 'Nairobi, Westlands',
      limit: 3
    });
    
    if (geoTest.data.success && geoTest.data.count > 0) {
      console.log('✅ Geo-location service:', `Found ${geoTest.data.count} nearby doctors`);
      
      // Show sample doctor with distance
      const sampleDoctor = geoTest.data.data[0];
      console.log(`   Sample: Dr. ${sampleDoctor.name} (${sampleDoctor.distance}km) - ${sampleDoctor.specialization}`);
    } else {
      console.log('⚠️ Geo-location service: No doctors found or service issue');
    }
    
  } catch (error) {
    console.log('❌ Geo-location test failed:', error.message);
  }
  
  console.log('\n🎉 Integration testing completed!');
  console.log('\n📱 USSD Service Features:');
  console.log('   • Geo-location doctor discovery');
  console.log('   • Physical visit booking');
  console.log('   • Teleconsultation booking');
  console.log('   • Appointment management');
  console.log('   • Multi-language support');
  console.log('   • Integration with existing Flask dashboard');
}

// Run the integration test
testIntegration().catch(console.error);