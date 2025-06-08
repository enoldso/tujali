# Tujali - Healthcare Management System

A comprehensive healthcare management system with patient records, appointments, prescriptions, and more.

## Getting Started

### Prerequisites

- Python 3.8+
- pip (Python package manager)
- SQLite (for development) or PostgreSQL (for production)

### Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd tujali
   ```

2. Create and activate a virtual environment:
   ```bash
   # On Windows
   python -m venv venv
   .\venv\Scripts\activate
   
   # On macOS/Linux
   python3 -m venv venv
   source venv/bin/activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

### Configuration

1. Set up environment variables:
   ```bash
   # Run the setup script (recommended)
   python setup_env.py
   
   # Or manually create a .env file by copying .env.example
   cp .env.example .env
   # Then edit .env with your configuration
   ```

2. Initialize the database:
   ```bash
   # Create database tables
   flask db upgrade
   
   # Create an admin user (run in Python shell)
   python -c "from app import app, db; from models_sqlalchemy import User; \
   with app.app_context(): \
       user = User(username='admin', email='admin@example.com'); \
       user.set_password('admin123'); \
       db.session.add(user); \
       db.session.commit()"
   ```

### Running the Application

#### Development Mode

```bash
# Set Flask environment to development
export FLASK_ENV=development  # On Windows: set FLASK_ENV=development

# Run the development server
flask run
```

#### Production Mode

For production, use a production WSGI server like Gunicorn:

```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

### Environment Variables

Key environment variables that can be set in `.env`:

- `FLASK_ENV`: Application environment (development/production)
- `SECRET_KEY`: Secret key for session management
- `DATABASE_URL`: Database connection URL
- `WTF_CSRF_SECRET_KEY`: CSRF protection secret key
- `DEBUG`: Enable/disable debug mode
- `UPLOAD_FOLDER`: Directory for file uploads
- `ALLOWED_EXTENSIONS`: Allowed file extensions for uploads

### Security Considerations

1. Never commit the `.env` file to version control
2. In production:
   - Set `FLASK_ENV=production`
   - Set `DEBUG=False`
   - Use a strong `SECRET_KEY`
   - Enable `WTF_CSRF_SSL_STRICT`
   - Use HTTPS with proper certificates

### License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
