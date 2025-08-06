const winston = require('winston');

// Create logger instance
const logger = winston.createLogger({
  level: 'info',
  format: winston.format.combine(
    winston.format.timestamp(),
    winston.format.errors({ stack: true }),
    winston.format.json()
  ),
  defaultMeta: { service: 'ussd-geo' },
  transports: [
    new winston.transports.File({ filename: 'logs/error.log', level: 'error' }),
    new winston.transports.File({ filename: 'logs/combined.log' }),
    new winston.transports.Console({
      format: winston.format.combine(
        winston.format.colorize(),
        winston.format.simple()
      )
    })
  ]
});

/**
 * Log USSD session data
 */
async function logUSSDSession(db, sessionData) {
  try {
    const {
      session_id,
      phone_number,
      service_code,
      input_text,
      response_text,
      timestamp
    } = sessionData;

    // Try to log to database, but don't fail if it doesn't work
    try {
      const query = `
        INSERT INTO ussd_sessions (
          session_id,
          phone_number,
          service_code,
          input_text,
          response_text,
          timestamp,
          created_at
        ) VALUES ($1, $2, $3, $4, $5, $6, NOW())
      `;

      await db.query(query, [
        session_id,
        phone_number,
        service_code,
        input_text || null,
        response_text || null,
        timestamp
      ]);
    } catch (dbError) {
      // Silent fail for database logging
      console.log('Database logging failed, continuing with file logging');
    }

    // Log to file
    logger.info('USSD Session', {
      session_id,
      phone_number,
      service_code,
      input_text,
      response_text,
      timestamp
    });

  } catch (error) {
    logger.error('Error logging USSD session:', error);
  }
}

/**
 * Log appointment booking
 */
async function logAppointmentBooking(db, bookingData) {
  try {
    const {
      patient_id,
      doctor_id,
      appointment_id,
      booking_source,
      phone_number
    } = bookingData;

    logger.info('Appointment Booked', {
      patient_id,
      doctor_id,
      appointment_id,
      booking_source,
      phone_number,
      timestamp: new Date()
    });

  } catch (error) {
    logger.error('Error logging appointment booking:', error);
  }
}

/**
 * Log geo-location search
 */
async function logGeoSearch(db, searchData) {
  try {
    const {
      phone_number,
      location_input,
      results_count,
      search_timestamp
    } = searchData;

    logger.info('Geo Search', {
      phone_number,
      location_input,
      results_count,
      search_timestamp,
      timestamp: new Date()
    });

  } catch (error) {
    logger.error('Error logging geo search:', error);
  }
}

/**
 * Log system errors
 */
function logError(error, context = {}) {
  logger.error('System Error', {
    error: error.message,
    stack: error.stack,
    context,
    timestamp: new Date()
  });
}

/**
 * Log system info
 */
function logInfo(message, data = {}) {
  logger.info(message, {
    ...data,
    timestamp: new Date()
  });
}

module.exports = {
  logUSSDSession,
  logAppointmentBooking,
  logGeoSearch,
  logError,
  logInfo,
  logger
};