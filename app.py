"""
Discord Curator Monitoring System - Flask Backend
Migrated from Node.js to Python Flask with PostgreSQL/MySQL compatibility

PROJECT IDENTIFIER: GovTracker2 - Discord Curator Monitoring Backend
Original: https://github.com/MagicMajestic/govtracker2
Migration: Node.js/TypeScript → Python 3.12/Flask
"""

import os
import logging
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix

# Configure logging for debugging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class Base(DeclarativeBase):
    pass

# Initialize Flask app
app = Flask(__name__, static_folder='static/build', static_url_path='')
app.secret_key = os.environ.get("SESSION_SECRET", "discord-curator-monitoring-secret-key")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Enable CORS for API endpoints
CORS(app, origins=['*'])

# Database configuration with PostgreSQL/MySQL compatibility
database_url = os.environ.get("DATABASE_URL")
if database_url and database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)

# Support MySQL URLs as well
if not database_url:
    # Try MySQL first, then PostgreSQL as fallback
    mysql_url = os.environ.get("MYSQL_URL") or os.environ.get("MYSQL_DATABASE_URL")
    if mysql_url:
        database_url = mysql_url
    else:
        database_url = "postgresql://localhost/govtracker2"

app.config["SQLALCHEMY_DATABASE_URI"] = database_url
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
    "pool_size": 10,
    "max_overflow": 20,
}

# Initialize SQLAlchemy
db = SQLAlchemy(model_class=Base)
db.init_app(app)

# Create application context and tables
with app.app_context():
    # Import models to ensure tables are created
    import models  # noqa: F401
    
    try:
        db.create_all()
        
        # Initialize default settings if they don't exist
        from utils import initialize_default_settings
        initialize_default_settings()
        
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Database initialization error: {e}")

logger.info("Discord Curator Monitoring System - Flask backend initialized")
