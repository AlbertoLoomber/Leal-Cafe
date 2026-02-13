"""
WSGI entry point for production deployment
"""
import os
import sys

# Add app directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app import create_app
from database import init_database
import logging

logger = logging.getLogger(__name__)

# Create application instance
app = create_app()

# Initialize database on startup
try:
    with app.app_context():
        init_database()
        logger.info("Database initialized successfully")
except Exception as e:
    logger.warning(f"Database initialization warning: {str(e)}")

if __name__ == "__main__":
    app.run()
