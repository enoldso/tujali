# Tujali USSD Geo Service

A Node.js USSD service with geo-location capabilities for finding nearby doctors and booking appointments in Kenya.

## Features

- **Geo-location Services**: Find doctors near user's location
- **Doctor Discovery**: Search by location, specialization, and availability
- **Appointment Booking**: Book physical visits or teleconsultations
- **USSD Integration**: Works with Africa's Talking USSD gateway
- **Multi-language Support**: English, Swahili, and other local languages
- **Real-time Availability**: Check doctor schedules and book appointments

## API Endpoints

### USSD Routes
- `POST /ussd` - Main USSD endpoint
- `POST /ussd/callback` - USSD callback handler

### Doctor Routes
- `GET /api/doctors` - Get all doctors
- `GET /api/doctors/near/:location` - Find doctors near location
- `GET /api/doctors/specialization/:specialization` - Search by specialization
- `GET /api/doctors/:id` - Get doctor details
- `GET /api/doctors/:id/availability` - Get doctor availability

### Appointment Routes
- `POST /api/appointments` - Create appointment
- `GET /api/appointments/patient/:patientId` - Get patient appointments
- `GET /api/appointments/:id` - Get appointment details
- `PATCH /api/appointments/:id/status` - Update appointment status
- `PATCH /api/appointments/:id/cancel` - Cancel appointment
- `PATCH /api/appointments/:id/reschedule` - Reschedule appointment

### Geo Routes
- `POST /api/geo/doctors/nearby` - Find nearby doctors
- `POST /api/geo/location/parse` - Parse location input
- `POST /api/geo/distance/calculate` - Calculate distance between points
- `GET /api/geo/locations/supported` - Get supported locations

## USSD Flow

```
*384*4040# - Main Menu
├── 1. Find Doctors Near Me
│   ├── Enter location
│   ├── Select doctor
│   ├── View doctor details
│   └── Book appointment (Physical/Teleconsult)
├── 2. My Appointments
│   ├── View upcoming appointments
│   ├── Cancel appointment
│   └── Reschedule appointment
├── 3. Emergency Services
└── 4. Health Information
```

## Installation

1. Clone the repository
2. Install dependencies:
   ```bash
   npm install
   ```

3. Set up environment variables:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

4. Run the service:
   ```bash
   npm start
   ```

## Development

```bash
npm run dev  # Start with nodemon for development
npm test     # Run tests
```

## Database Schema

The service integrates with the existing Tujali Health database and uses the following tables:
- `patients` - Patient information
- `providers` - Doctor/healthcare provider information
- `appointments` - Appointment bookings
- `ussd_sessions` - USSD session logs

## Location Support

### Supported Cities
- Nairobi, Mombasa, Kisumu, Nakuru, Eldoret
- Meru, Kikuyu, Malindi, Garissa, Kitale
- Thika, Machakos, Kericho, Nyeri, Embu

### Location Formats
- City name: "Nairobi"
- City with area: "Nairobi, Westlands"
- Landmark: "Near Westgate Mall"
- GPS coordinates: "-1.286389, 36.817223"

## Integration

This service works alongside the existing Flask web dashboard and shares the same database. Healthcare providers can manage appointments through the web interface while patients book through USSD.

## License

MIT License - see LICENSE file for details.