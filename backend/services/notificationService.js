
const axios = require('axios');

class NotificationService {
  async sendSMS(phoneNumber, message) {
    // Africa's Talking SMS API integration
    try {
      // Implementation will use AT API when credentials are added
      console.log(`SMS to ${phoneNumber}: ${message}`);
      return true;
    } catch (error) {
      console.error('SMS sending failed:', error);
      return false;
    }
  }

  async sendWhatsApp(phoneNumber, message) {
    // Africa's Talking WhatsApp API integration  
    try {
      // Implementation will use AT API when credentials are added
      console.log(`WhatsApp to ${phoneNumber}: ${message}`);
      return true;
    } catch (error) {
      console.error('WhatsApp sending failed:', error);
      return false;
    }
  }

  async sendCalendarInvite(provider, appointment) {
    // Calendar integration using iCal format
    try {
      const icalData = this.generateICalEvent(appointment);
      // Send to provider's email when email service is configured
      console.log(`Calendar invite for appointment ${appointment.id}`);
      return true;
    } catch (error) {
      console.error('Calendar invite failed:', error);
      return false;
    }
  }

  generateICalEvent(appointment) {
    const event = {
      start: new Date(appointment.date + ' ' + appointment.time),
      end: new Date(appointment.date + ' ' + appointment.time),
      summary: `Patient Appointment: ${appointment.patient_name}`,
      description: appointment.notes || 'No additional notes',
      location: 'Tujali Telehealth'
    };
    
    // Generate iCal format string
    return `BEGIN:VCALENDAR
VERSION:2.0
BEGIN:VEVENT
UID:${appointment.id}
DTSTAMP:${new Date().toISOString()}
DTSTART:${event.start.toISOString()}
DTEND:${event.end.toISOString()}
SUMMARY:${event.summary}
DESCRIPTION:${event.description}
LOCATION:${event.location}
END:VEVENT
END:VCALENDAR`;
  }
}

module.exports = new NotificationService();
