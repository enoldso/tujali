const { findNearestDoctors } = require('./geoService');
const { getDoctorDetails, getDoctorAvailability } = require('./doctorService');
const { createAppointment, getPatientAppointments } = require('./appointmentService');
const { getOrCreatePatient } = require('./patientService');

class USSDSession {
  constructor(sessionId, phoneNumber) {
    this.sessionId = sessionId;
    this.phoneNumber = phoneNumber;
    this.currentStep = 'main_menu';
    this.data = {};
  }
}

const sessions = new Map();

async function handleUSSDFlow(db, { sessionId, serviceCode, phoneNumber, text }) {
  let session = sessions.get(sessionId);
  
  if (!session) {
    session = new USSDSession(sessionId, phoneNumber);
    sessions.set(sessionId, session);
  }

  const textArray = text.split('*').filter(Boolean);
  const userInput = textArray[textArray.length - 1] || '';
  
  try {
    // Get or create patient with error handling
    let patient;
    try {
      patient = await getOrCreatePatient(db, phoneNumber);
    } catch (error) {
      console.log('Patient service error, using fallback:', error.message);
      patient = {
        id: Math.floor(Math.random() * 1000) + 1000,
        name: `Patient ${phoneNumber.slice(-4)}`,
        phone_number: phoneNumber,
        language: 'en'
      };
    }
    session.data.patient = patient;

    switch (session.currentStep) {
      case 'main_menu':
        return await handleMainMenu(db, session, userInput);
      
      case 'location_input':
        return await handleLocationInput(db, session, userInput);
      
      case 'doctor_selection':
        return await handleDoctorSelection(db, session, userInput);
      
      case 'doctor_details':
        return await handleDoctorDetails(db, session, userInput);
      
      case 'appointment_type':
        return await handleAppointmentType(db, session, userInput);
      
      case 'appointment_time':
        return await handleAppointmentTime(db, session, userInput);
      
      case 'appointment_confirmation':
        return await handleAppointmentConfirmation(db, session, userInput);
      
      case 'my_appointments':
        return await handleMyAppointments(db, session, userInput);
      
      default:
        return await handleMainMenu(db, session, userInput);
    }
  } catch (error) {
    console.error('USSD Flow Error:', error);
    return 'END Sorry, an error occurred. Please try again.';
  }
}

async function handleMainMenu(db, session, userInput) {
  if (!userInput) {
    return `CON Welcome to Tujali Health 🏥
Find doctors near you and book appointments

1. Find Doctors Near Me
2. My Appointments
3. Emergency Services
4. Health Information
0. Exit`;
  }

  switch (userInput) {
    case '1':
      session.currentStep = 'location_input';
      return `CON 📍 Find Doctors Near You

Please share your location by entering:
1. Your town/city name
2. Nearest landmark
3. GPS coordinates (if available)

Enter your location:`;

    case '2':
      session.currentStep = 'my_appointments';
      return await showMyAppointments(db, session);

    case '3':
      return `END 🚨 EMERGENCY SERVICES

For medical emergencies:
📞 Call: 999 (Free)
📞 Call: 112 (Free)

Or visit your nearest:
🏥 District Hospital
🚑 Health Center

Stay safe!`;

    case '4':
      return `CON 📚 Health Information

1. Common Symptoms Guide
2. Medication Reminders
3. Health Tips
4. Vaccination Schedule
0. Back to Main Menu`;

    case '0':
      sessions.delete(session.sessionId);
      return 'END Thank you for using Tujali Health. Stay healthy! 💚';

    default:
      return `CON Invalid option. Please try again.

1. Find Doctors Near Me
2. My Appointments
3. Emergency Services
4. Health Information
0. Exit`;
  }
}

async function handleLocationInput(db, session, userInput) {
  if (!userInput.trim()) {
    return `CON Please enter your location:

Examples:
- Nairobi, CBD
- Kisumu, Kondele
- Nakuru, Stadium
- Near Safaricom Shop

Enter location:`;
  }

  session.data.location = userInput.trim();
  
  try {
    // Find nearest doctors
    const doctors = await findNearestDoctors(db, userInput, 10);
    
    if (doctors.length === 0) {
      return `END Sorry, no doctors found near "${userInput}".

Try:
- A nearby town name
- A well-known landmark
- Contact us: *384*4040#

Thank you for using Tujali Health.`;
    }

    session.data.doctors = doctors;
    session.currentStep = 'doctor_selection';
    
    let response = `CON 👨‍⚕️ Doctors near "${userInput}":

`;
    
    doctors.slice(0, 8).forEach((doctor, index) => {
      const distance = doctor.distance ? `(${doctor.distance}km)` : '';
      response += `${index + 1}. Dr. ${doctor.name} ${distance}
   ${doctor.specialization}
`;
    });
    
    if (doctors.length > 8) {
      response += `9. View More Doctors
`;
    }
    
    response += `0. Back to Main Menu`;
    
    return response;

  } catch (error) {
    console.error('Location search error:', error);
    return 'END Unable to search for doctors. Please try again later.';
  }
}

async function handleDoctorSelection(db, session, userInput) {
  const doctorIndex = parseInt(userInput) - 1;
  const doctors = session.data.doctors || [];

  if (userInput === '0') {
    session.currentStep = 'main_menu';
    return await handleMainMenu(db, session, '');
  }

  if (userInput === '9' && doctors.length > 8) {
    // Show more doctors
    let response = `CON More doctors near "${session.data.location}":

`;
    
    doctors.slice(8, 16).forEach((doctor, index) => {
      const distance = doctor.distance ? `(${doctor.distance}km)` : '';
      response += `${index + 9}. Dr. ${doctor.name} ${distance}
   ${doctor.specialization}
`;
    });
    
    response += `0. Back to Doctor List`;
    return response;
  }

  if (doctorIndex >= 0 && doctorIndex < doctors.length) {
    const selectedDoctor = doctors[doctorIndex];
    session.data.selectedDoctor = selectedDoctor;
    session.currentStep = 'doctor_details';
    
    const distance = selectedDoctor.distance ? ` (${selectedDoctor.distance}km away)` : '';
    
    return `CON 👨‍⚕️ Dr. ${selectedDoctor.name}${distance}

🏥 Specialty: ${selectedDoctor.specialization}
📍 Location: ${selectedDoctor.location || 'Location available'}
📞 Phone: ${selectedDoctor.phone_number || 'Contact via appointment'}
⭐ Rating: ${selectedDoctor.rating || 'New'}/5

1. Book Physical Visit
2. Book Teleconsultation
3. View Full Profile
0. Back to Doctor List`;
  }

  return `CON Invalid selection. Please choose a valid doctor number or 0 to go back.`;
}

async function handleDoctorDetails(db, session, userInput) {
  const doctor = session.data.selectedDoctor;

  switch (userInput) {
    case '1':
      session.data.appointmentType = 'physical';
      session.currentStep = 'appointment_time';
      return await showAvailableSlots(db, session, doctor.id);

    case '2':
      session.data.appointmentType = 'teleconsult';
      session.currentStep = 'appointment_time';
      return await showAvailableSlots(db, session, doctor.id);

    case '3':
      return `CON 👨‍⚕️ Dr. ${doctor.name} - Full Profile

🏥 Specialization: ${doctor.specialization}
🎓 Experience: ${doctor.years_experience || 'N/A'} years
📍 Practice Location: ${doctor.location}
📞 Contact: ${doctor.phone_number || 'Via appointment'}
🏥 Hospital: ${doctor.hospital || 'Private Practice'}
⏰ Consultation Fee: KSh ${doctor.consultation_fee || '500'}

Languages: ${doctor.languages || 'English, Swahili'}

1. Book Physical Visit
2. Book Teleconsultation
0. Back`;

    case '0':
      session.currentStep = 'doctor_selection';
      return await handleDoctorSelection(db, session, '');

    default:
      return `CON Invalid option. Please choose:

1. Book Physical Visit
2. Book Teleconsultation  
3. View Full Profile
0. Back to Doctor List`;
  }
}

async function showAvailableSlots(db, session, doctorId) {
  try {
    const availability = await getDoctorAvailability(db, doctorId);
    const appointmentType = session.data.appointmentType;
    
    let response = `CON 📅 Available ${appointmentType === 'physical' ? 'Physical Visit' : 'Teleconsultation'} Times:

`;

    if (availability.length === 0) {
      return `CON No available slots found.

Contact doctor directly:
📞 ${session.data.selectedDoctor.phone_number || 'Phone not available'}

1. Try Different Date
2. Choose Another Doctor
0. Back to Main Menu`;
    }

    availability.slice(0, 7).forEach((slot, index) => {
      response += `${index + 1}. ${slot.date} at ${slot.time}
`;
    });

    response += `0. Back to Doctor Profile`;
    
    session.data.availableSlots = availability;
    return response;

  } catch (error) {
    console.error('Availability error:', error);
    return `CON Unable to load availability.

1. Try Again
2. Contact Doctor Directly
0. Back`;
  }
}

async function handleAppointmentTime(db, session, userInput) {
  const slotIndex = parseInt(userInput) - 1;
  const slots = session.data.availableSlots || [];

  if (userInput === '0') {
    session.currentStep = 'doctor_details';
    return await handleDoctorDetails(db, session, '');
  }

  if (slotIndex >= 0 && slotIndex < slots.length) {
    const selectedSlot = slots[slotIndex];
    session.data.selectedSlot = selectedSlot;
    session.currentStep = 'appointment_confirmation';
    
    const doctor = session.data.selectedDoctor;
    const appointmentType = session.data.appointmentType;
    const fee = doctor.consultation_fee || 500;
    
    return `CON 📋 Confirm Your Appointment

👨‍⚕️ Doctor: Dr. ${doctor.name}
📅 Date: ${selectedSlot.date}
⏰ Time: ${selectedSlot.time}
🏥 Type: ${appointmentType === 'physical' ? 'Physical Visit' : 'Teleconsultation'}
📍 Location: ${appointmentType === 'physical' ? doctor.location : 'Phone/Video Call'}
💰 Fee: KSh ${fee}

1. Confirm Appointment
2. Change Time
0. Cancel`;
  }

  return `CON Invalid time slot. Please select a valid option.`;
}

async function handleAppointmentConfirmation(db, session, userInput) {
  switch (userInput) {
    case '1':
      try {
        const appointment = await createAppointment(db, {
          patient_id: session.data.patient.id,
          doctor_id: session.data.selectedDoctor.id,
          appointment_date: session.data.selectedSlot.date,
          appointment_time: session.data.selectedSlot.time,
          appointment_type: session.data.appointmentType,
          status: 'confirmed',
          source: 'ussd_geo'
        });

        const doctor = session.data.selectedDoctor;
        const slot = session.data.selectedSlot;
        
        sessions.delete(session.sessionId);
        
        return `END ✅ Appointment Confirmed!

📋 Booking ID: ${appointment.id}
👨‍⚕️ Dr. ${doctor.name}
📅 ${slot.date} at ${slot.time}
🏥 ${session.data.appointmentType === 'physical' ? doctor.location : 'Teleconsultation'}

📱 You will receive SMS reminders
💰 Payment: KSh ${doctor.consultation_fee || 500}

Thank you for using Tujali Health! 💚`;

      } catch (error) {
        console.error('Appointment creation error:', error);
        return 'END Sorry, unable to confirm appointment. Please try again or call us directly.';
      }

    case '2':
      session.currentStep = 'appointment_time';
      return await showAvailableSlots(db, session, session.data.selectedDoctor.id);

    case '0':
      sessions.delete(session.sessionId);
      return 'END Appointment cancelled. Thank you for using Tujali Health.';

    default:
      return `CON Please choose:

1. Confirm Appointment
2. Change Time
0. Cancel`;
  }
}

async function showMyAppointments(db, session) {
  try {
    const appointments = await getPatientAppointments(db, session.data.patient.id);
    
    if (appointments.length === 0) {
      return `CON 📅 My Appointments

You have no upcoming appointments.

1. Find a Doctor
2. Book Appointment
0. Back to Main Menu`;
    }

    let response = `CON 📅 My Appointments:

`;
    
    appointments.slice(0, 5).forEach((apt, index) => {
      response += `${index + 1}. Dr. ${apt.doctor_name}
   ${apt.appointment_date} ${apt.appointment_time}
   ${apt.appointment_type === 'physical' ? '🏥' : '📞'} ${apt.status}
`;
    });
    
    response += `
1-${appointments.length}. View Details
0. Back to Main Menu`;
    
    session.data.appointments = appointments;
    return response;

  } catch (error) {
    console.error('Appointments error:', error);
    return `CON Unable to load appointments.

1. Try Again
0. Back to Main Menu`;
  }
}

async function handleMyAppointments(db, session, userInput) {
  if (userInput === '0') {
    session.currentStep = 'main_menu';
    return await handleMainMenu(db, session, '');
  }

  const aptIndex = parseInt(userInput) - 1;
  const appointments = session.data.appointments || [];

  if (aptIndex >= 0 && aptIndex < appointments.length) {
    const appointment = appointments[aptIndex];
    
    return `CON 📋 Appointment Details

👨‍⚕️ Doctor: Dr. ${appointment.doctor_name}
🏥 Specialty: ${appointment.specialization}
📅 Date: ${appointment.appointment_date}
⏰ Time: ${appointment.appointment_time}
📍 Type: ${appointment.appointment_type === 'physical' ? 'Physical Visit' : 'Teleconsultation'}
📊 Status: ${appointment.status}
💰 Fee: KSh ${appointment.consultation_fee || '500'}

1. Cancel Appointment
2. Reschedule
3. Contact Doctor
0. Back to Appointments`;
  }

  return await showMyAppointments(db, session);
}

module.exports = {
  handleUSSDFlow
};