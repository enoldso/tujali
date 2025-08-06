/**
 * Models Adapter - Bridges Python models with Node.js backend
 * 
 * This adapter allows us to use the existing Python models from the
 * Flask application in our Node.js backend during the transition period.
 * 
 * In production, this would be replaced with proper Sequelize models.
 */

// Import Python models through child_process
const { execSync } = require('child_process');
const path = require('path');

// For demo purposes, we'll use a simplified model bridge
// In a real implementation, we'd use a more robust approach

// Mock User data for demo
const users = [
  {
    id: '1',
    username: 'admin',
    email: 'admin@tujali.com',
    password_hash: '$2a$10$yfJc4f3vM.C2y.5CKKGnJ.6pZBHZCQ3m1Bc/oNcL3o18UoXvRdlQq', // admin123
  }
];

// Mock Providers data
const providers = [
  {
    id: '1',
    user_id: '1',
    name: 'Dr. John Doe',
    specialization: 'General Practice',
    languages: ['en', 'sw']
  }
];

// Mock Patients data
const patients = [
  {
    id: '1',
    phone_number: '+254712345678',
    name: 'Jane Smith',
    age: 35,
    gender: 'Female',
    location: 'Nairobi',
    language: 'en',
    created_at: new Date(2023, 0, 15).toISOString(),
    symptoms: ['Headache', 'Fever', 'Cough']
  },
  {
    id: '2',
    phone_number: '+254723456789',
    name: 'James Wafula',
    age: 42,
    gender: 'Male',
    location: 'Mombasa',
    language: 'sw',
    created_at: new Date(2023, 1, 5).toISOString(),
    symptoms: ['Back Pain', 'Fatigue']
  },
  {
    id: '3',
    phone_number: '+254734567890',
    name: 'Mary Akinyi',
    age: 28,
    gender: 'Female',
    location: 'Kisumu',
    language: 'en',
    created_at: new Date(2023, 1, 20).toISOString(),
    symptoms: ['Sore Throat', 'Runny Nose']
  }
];

// Mock Appointments data
const appointments = [
  {
    id: '1',
    patient_id: '1',
    provider_id: '1',
    date: '2023-03-20',
    time: '10:00 AM',
    status: 'confirmed',
    notes: 'Follow-up consultation',
    created_at: new Date(2023, 2, 15).toISOString()
  },
  {
    id: '2',
    patient_id: '2',
    provider_id: '1',
    date: '2023-03-22',
    time: '2:30 PM',
    status: 'pending',
    notes: 'Initial consultation',
    created_at: new Date(2023, 2, 17).toISOString()
  },
  {
    id: '3',
    patient_id: '3',
    provider_id: '1',
    date: '2023-03-25',
    time: '11:15 AM',
    status: 'pending',
    notes: 'Prescription renewal',
    created_at: new Date(2023, 2, 18).toISOString()
  }
];

// Mock Messages data
const messages = [
  {
    id: '1',
    provider_id: '1',
    patient_id: '1',
    content: 'Good morning, how are you feeling today?',
    sender_type: 'provider',
    is_read: true,
    created_at: new Date(2023, 2, 18, 9, 0).toISOString()
  },
  {
    id: '2',
    provider_id: '1',
    patient_id: '1',
    content: 'Much better, thank you. The medication is helping.',
    sender_type: 'patient',
    is_read: true,
    created_at: new Date(2023, 2, 18, 9, 15).toISOString()
  },
  {
    id: '3',
    provider_id: '1',
    patient_id: '2',
    content: 'Hello, I have been experiencing back pain for the past week.',
    sender_type: 'patient',
    is_read: false,
    created_at: new Date(2023, 2, 17, 14, 30).toISOString()
  }
];

// Mock Health Info data
const healthInfo = [
  {
    id: '1',
    title: 'COVID-19 Prevention',
    content: 'Wash your hands frequently, wear a mask in public, and maintain social distancing.',
    language: 'en',
    created_at: new Date(2023, 0, 5).toISOString()
  },
  {
    id: '2',
    title: 'Kuzuia COVID-19',
    content: 'Osha mikono mara kwa mara, vaa barakoa katika maeneo ya umma, na dumisha umbali wa kijamii.',
    language: 'sw',
    created_at: new Date(2023, 0, 5).toISOString()
  }
];

// Model adapter object
const models = {
  User: {
    get_by_id: (id) => users.find(user => user.id === id) || null,
    get_by_username: (username) => users.find(user => user.username === username) || null,
  },
  
  Provider: {
    get_by_user_id: (user_id) => providers.find(provider => provider.user_id === user_id) || null,
    get_by_id: (id) => providers.find(provider => provider.id === id) || null,
    get_all: () => [...providers],
  },
  
  Patient: {
    get_by_phone: (phone) => patients.find(patient => patient.phone_number === phone) || null,
    get_by_id: (id) => patients.find(patient => patient.id === id) || null,
    get_all: () => [...patients],
    get_recent: (limit = 5) => [...patients].sort((a, b) => 
      new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
    ).slice(0, limit),
    get_count: () => patients.length,
  },
  
  Appointment: {
    get_by_id: (id) => appointments.find(appointment => appointment.id === id) || null,
    get_by_patient: (patient_id) => appointments.filter(appointment => appointment.patient_id === patient_id),
    get_by_provider: (provider_id) => appointments.filter(appointment => appointment.provider_id === provider_id),
    get_recent_by_provider: (provider_id, limit = 5) => 
      appointments
        .filter(appointment => appointment.provider_id === provider_id)
        .sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())
        .slice(0, limit),
    get_count_by_status: (provider_id, status) => 
      appointments.filter(appointment => 
        appointment.provider_id === provider_id && appointment.status === status
      ).length,
    update_status: (id, status) => {
      const appointment = appointments.find(appointment => appointment.id === id);
      if (appointment) {
        appointment.status = status;
        return true;
      }
      return false;
    },
  },
  
  Message: {
    get_conversation: (provider_id, patient_id) => 
      messages
        .filter(message => 
          message.provider_id === provider_id && message.patient_id === patient_id
        )
        .sort((a, b) => new Date(a.created_at).getTime() - new Date(b.created_at).getTime()),
        
    get_conversations: (provider_id) => {
      // Get all patient IDs that have conversations with this provider
      const patientIds = [...new Set(
        messages
          .filter(message => message.provider_id === provider_id)
          .map(message => message.patient_id)
      )];
      
      // For each patient, get the latest message and patient info
      return patientIds.map(patientId => {
        const patientMessages = messages
          .filter(message => 
            message.provider_id === provider_id && message.patient_id === patientId
          )
          .sort((a, b) => 
            new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
          );
        
        const patient = models.Patient.get_by_id(patientId);
        const lastMessage = patientMessages[0];
        const unreadCount = patientMessages.filter(
          message => message.sender_type === 'patient' && !message.is_read
        ).length;
        
        return {
          patient_id: patientId,
          patient_name: patient ? patient.name : 'Unknown Patient',
          last_message: lastMessage ? lastMessage.content : '',
          last_message_time: lastMessage ? lastMessage.created_at : '',
          unread_count: unreadCount
        };
      });
    },
    
    mark_as_read: (patient_id, provider_id) => {
      messages
        .filter(message => 
          message.provider_id === provider_id && 
          message.patient_id === patient_id &&
          message.sender_type === 'patient' &&
          !message.is_read
        )
        .forEach(message => {
          message.is_read = true;
        });
      return true;
    },
    
    get_recent_by_provider: (provider_id, limit = 5) => 
      messages
        .filter(message => message.provider_id === provider_id)
        .sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())
        .slice(0, limit),
        
    get_unread_count: (provider_id) => 
      messages.filter(message => 
        message.provider_id === provider_id && 
        message.sender_type === 'patient' && 
        !message.is_read
      ).length,
  },
  
  HealthInfo: {
    get_by_language: (language) => healthInfo.filter(info => info.language === language),
    get_all: () => [...healthInfo],
  }
};

module.exports = { models };