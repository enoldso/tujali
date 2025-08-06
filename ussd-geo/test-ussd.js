const axios = require('axios');

// Test the USSD flow
async function testUSSDFlow() {
  const baseURL = 'http://localhost:3000';
  
  console.log('🧪 Testing USSD Geo Service...\n');
  
  // Test 1: Health check
  try {
    console.log('1. Testing health check...');
    const healthResponse = await axios.get(`${baseURL}/health`);
    console.log('✅ Health check passed:', healthResponse.data.status);
  } catch (error) {
    console.log('❌ Health check failed:', error.message);
    return;
  }
  
  // Test 2: Main USSD menu
  try {
    console.log('\n2. Testing main USSD menu...');
    const ussdResponse = await axios.post(`${baseURL}/ussd`, {
      sessionId: 'test_session_001',
      serviceCode: '*384*4040#',
      phoneNumber: '+254701234567',
      text: ''
    });
    console.log('✅ Main menu response:');
    console.log(ussdResponse.data);
  } catch (error) {
    console.log('❌ Main menu test failed:', error.message);
  }
  
  // Test 3: Find doctors option
  try {
    console.log('\n3. Testing find doctors option...');
    const findDoctorsResponse = await axios.post(`${baseURL}/ussd`, {
      sessionId: 'test_session_002',
      serviceCode: '*384*4040#',
      phoneNumber: '+254701234567',
      text: '1'
    });
    console.log('✅ Find doctors response:');
    console.log(findDoctorsResponse.data);
  } catch (error) {
    console.log('❌ Find doctors test failed:', error.message);
  }
  
  // Test 4: Location input
  try {
    console.log('\n4. Testing location input...');
    const locationResponse = await axios.post(`${baseURL}/ussd`, {
      sessionId: 'test_session_003',
      serviceCode: '*384*4040#',
      phoneNumber: '+254701234567',
      text: '1*Nairobi'
    });
    console.log('✅ Location input response:');
    console.log(locationResponse.data);
  } catch (error) {
    console.log('❌ Location input test failed:', error.message);
  }
  
  // Test 5: API endpoints
  try {
    console.log('\n5. Testing API endpoints...');
    
    // Test geo service
    const geoResponse = await axios.post(`${baseURL}/api/geo/doctors/nearby`, {
      location: 'Nairobi',
      phone_number: '+254701234567',
      limit: 5
    });
    console.log('✅ Geo service response:', geoResponse.data.count, 'doctors found');
    
    // Test doctors endpoint
    const doctorsResponse = await axios.get(`${baseURL}/api/doctors?limit=3`);
    console.log('✅ Doctors API response:', doctorsResponse.data.count, 'doctors retrieved');
    
  } catch (error) {
    console.log('❌ API endpoints test failed:', error.message);
  }
  
  console.log('\n🎉 USSD Geo Service testing completed!');
}

// Run the test
testUSSDFlow().catch(console.error);