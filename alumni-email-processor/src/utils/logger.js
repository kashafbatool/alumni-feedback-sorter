export class Logger {
  static info(message, data = {}) {
    console.log(`[INFO] ${new Date().toISOString()} - ${message}`, data);
  }

  static error(message, error = {}) {
    console.error(`[ERROR] ${new Date().toISOString()} - ${message}`, {
      message: error.message,
      stack: error.stack,
      ...error,
    });
  }

  static warn(message, data = {}) {
    console.warn(`[WARN] ${new Date().toISOString()} - ${message}`, data);
  }

  static success(message, data = {}) {
    console.log(`[SUCCESS] ${new Date().toISOString()} - ${message}`, data);
  }
}
