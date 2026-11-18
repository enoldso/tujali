"""Entry point.

Production:  gunicorn -c gunicorn.conf.py main:app
Development: flask --app main run --debug   (or: python main.py)
"""
import os

from app import app, IS_PRODUCTION

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=not IS_PRODUCTION)
