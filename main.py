from app import app
from models import init_db

# Ensure database is initialized
init_db()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
