#!/usr/bin/env python3
"""
Setup environment variables for the Tujali application.
This script will help you create a .env file with secure values.
"""
import os
import secrets
import sys
from pathlib import Path

def generate_secret_key():
    """Generate a secure secret key."""
    return secrets.token_hex(32)

def setup_environment():
    """Create or update the .env file with user input."""
    env_path = Path('.env')
    
    # Check if .env exists and ask for confirmation to overwrite
    if env_path.exists():
        print("Warning: .env file already exists!")
        response = input("Do you want to overwrite it? (y/N): ").strip().lower()
        if response != 'y':
            print("Setup cancelled.")
            return
    
    # Default values
    env_vars = {
        '# Flask Configuration': '',
        'FLASK_ENV': 'development',
        'SECRET_KEY': generate_secret_key(),
        
        '\n# Database Configuration': '',
        'DATABASE_URL': f'sqlite:///{os.path.abspath(os.path.join(os.path.dirname(__file__), "app.db"))}',
        
        '\n# Session Configuration': '',
        'SESSION_COOKIE_SECURE': 'False',
        'SESSION_COOKIE_HTTPONLY': 'True',
        'SESSION_COOKIE_SAMESITE': 'Lax',
        'PERMANENT_SESSION_LIFETIME': '86400',
        
        '\n# CSRF Protection': '',
        'WTF_CSRF_ENABLED': 'True',
        'WTF_CSRF_SECRET_KEY': generate_secret_key(),
        'WTF_CSRF_TIME_LIMIT': '3600',
        'WTF_CSRF_SSL_STRICT': 'False',
        
        '\n# Debug Settings': '',
        'DEBUG': 'True',
        'SQLALCHEMY_ECHO': 'True',
        
        '\n# Server Configuration': '',
        'HOST': '0.0.0.0',
        'PORT': '5000',
        
        '\n# File Uploads': '',
        'MAX_CONTENT_LENGTH': '16777216',
        'UPLOAD_FOLDER': 'uploads',
        'ALLOWED_EXTENSIONS': 'png,jpg,jpeg,gif,pdf',
    }
    
    # Write to .env file
    try:
        with open(env_path, 'w') as f:
            for key, value in env_vars.items():
                if key.startswith('\n#'):
                    f.write(f'\n{key}\n')
                elif key.startswith('#'):
                    f.write(f'{key}\n')
                else:
                    f.write(f'{key}={value}\n')
        
        print(f"Successfully created {env_path.absolute()}")
        print("\nPlease review the configuration and make any necessary changes.")
        print("For production, make sure to set FLASK_ENV=production and DEBUG=False")
        
    except Exception as e:
        print(f"Error creating .env file: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    print("Setting up Tujali environment variables...")
    setup_environment()
