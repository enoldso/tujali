from app import app, db_ext
from flask_migrate import Migrate

# Initialize Flask-Migrate
migrate = Migrate(app, db_ext)
