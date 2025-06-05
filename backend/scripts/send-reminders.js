
const { models } = require('../models');
const notificationService = require('../services/notificationService');

async function sendReminders() {
  try {
    const tomorrow = new Date();
    tomorrow.setDate(tomorrow.getDate() + 1);
    const tomorrowDate = tomorrow.toISOString().split('T')[0];

    // Get tomorrow's appointments
    const appointments = models.Appointment.get_all().filter(a => 
      a.date === tomorrowDate && !a.reminder_sent && a.status === 'confirmed'
    );

    for (const appointment of appointments) {
      const patient = models.Patient.get_by_id(appointment.patient_id);
      const provider = models.Provider.get_by_id(appointment.provider_id);

      // Send SMS
      await notificationService.sendSMS(
        patient.phone_number,
        `Reminder: Your appointment with ${provider.name} is tomorrow at ${appointment.time}`
      );

      // Send WhatsApp
      await notificationService.sendWhatsApp(
        patient.phone_number,
        `*Appointment Reminder*\nDoctor: ${provider.name}\nDate: Tomorrow\nTime: ${appointment.time}`
      );

      // Send calendar invite to provider
      await notificationService.sendCalendarInvite(provider, {
        ...appointment,
        patient_name: patient.name
      });

      // Mark reminder as sent
      appointment.reminder_sent = true;
    }

    console.log(`Sent reminders for ${appointments.length} appointments`);
  } catch (error) {
    console.error('Error sending reminders:', error);
  }
}

sendReminders();
