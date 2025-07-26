"""
Database utilities and migration functions
PostgreSQL/MySQL compatibility layer

PROJECT IDENTIFIER: Database utilities for govtracker2 Flask migration
"""

import os
import logging
from app import app, db
from sqlalchemy import text, inspect
from models import *

logger = logging.getLogger(__name__)

def get_database_info():
    """Get database connection information"""
    try:
        with app.app_context():
            inspector = inspect(db.engine)
            
            # Get database URL info
            db_url = db.engine.url
            
            return {
                'database_type': db_url.drivername,
                'host': db_url.host,
                'port': db_url.port,
                'database': db_url.database,
                'username': db_url.username,
                'tables': inspector.get_table_names()
            }
    except Exception as e:
        logger.error(f"Database info error: {e}")
        return None

def check_database_connection():
    """Check if database connection is working"""
    try:
        with app.app_context():
            # Test connection with simple query
            result = db.session.execute(text("SELECT 1")).scalar()
            return result == 1
    except Exception as e:
        logger.error(f"Database connection error: {e}")
        return False

def initialize_database():
    """Initialize database with tables and default data"""
    try:
        with app.app_context():
            # Create all tables
            db.create_all()
            logger.info("Database tables created successfully")
            
            # Initialize default settings if they don't exist
            initialize_default_data()
            
            return True
    except Exception as e:
        logger.error(f"Database initialization error: {e}")
        return False

def initialize_default_data():
    """Initialize default system data"""
    try:
        with app.app_context():
            # Initialize rating settings
            existing_ratings = db.session.query(RatingSettings).count()
            if existing_ratings == 0:
                default_ratings = [
                    {'rating_name': 'excellent', 'rating_text': 'Великолепно', 'min_score': 50, 'color': 'green'},
                    {'rating_name': 'good', 'rating_text': 'Хорошо', 'min_score': 35, 'color': 'blue'},
                    {'rating_name': 'normal', 'rating_text': 'Нормально', 'min_score': 20, 'color': 'yellow'},
                    {'rating_name': 'poor', 'rating_text': 'Плохо', 'min_score': 10, 'color': 'orange'},
                    {'rating_name': 'terrible', 'rating_text': 'Ужасно', 'min_score': 0, 'color': 'red'}
                ]
                
                for rating_data in default_ratings:
                    rating = RatingSettings(**rating_data)
                    db.session.add(rating)
            
            # Initialize global rating config
            existing_config = db.session.query(GlobalRatingConfig).first()
            if not existing_config:
                config = GlobalRatingConfig(
                    activity_points_message=3,
                    activity_points_reaction=1,
                    activity_points_reply=2,
                    activity_points_task_verification=5,
                    response_time_good_seconds=60,
                    response_time_poor_seconds=300
                )
                db.session.add(config)
            
            # Initialize backup settings
            existing_backup = db.session.query(BackupSettings).first()
            if not existing_backup:
                backup_config = BackupSettings(
                    frequency='daily',
                    is_active=True
                )
                db.session.add(backup_config)
            
            db.session.commit()
            logger.info("Default data initialized successfully")
            
    except Exception as e:
        logger.error(f"Default data initialization error: {e}")
        db.session.rollback()

def migrate_to_mysql():
    """Migration helper for PostgreSQL to MySQL conversion"""
    migration_queries = [
        # Convert ARRAY columns to JSON for MySQL compatibility
        """
        -- This would be handled in the model definitions
        -- PostgreSQL ARRAY types are replaced with JSON in models.py
        """,
        
        # Update any PostgreSQL-specific functions
        """
        -- Replace PostgreSQL NOW() with MySQL equivalents if needed
        -- Most datetime functions are handled by SQLAlchemy
        """
    ]
    
    logger.info("MySQL migration queries prepared")
    return migration_queries

def get_table_statistics():
    """Get statistics about database tables"""
    try:
        with app.app_context():
            stats = {}
            
            # Count records in each main table
            table_models = [
                ('curators', Curators),
                ('discord_servers', DiscordServers),
                ('activities', Activities),
                ('response_tracking', ResponseTracking),
                ('task_reports', TaskReports),
                ('users', Users)
            ]
            
            for table_name, model_class in table_models:
                count = db.session.query(model_class).count()
                stats[table_name] = count
            
            return stats
    except Exception as e:
        logger.error(f"Table statistics error: {e}")
        return {}

def optimize_database():
    """Optimize database performance"""
    try:
        with app.app_context():
            # PostgreSQL optimization
            if 'postgresql' in str(db.engine.url):
                optimization_queries = [
                    "VACUUM ANALYZE;",
                    "REINDEX DATABASE;",
                ]
                
                for query in optimization_queries:
                    try:
                        db.session.execute(text(query))
                        db.session.commit()
                    except Exception as e:
                        logger.warning(f"Optimization query failed: {query} - {e}")
                        db.session.rollback()
            
            # MySQL optimization
            elif 'mysql' in str(db.engine.url):
                optimization_queries = [
                    "OPTIMIZE TABLE activities;",
                    "OPTIMIZE TABLE response_tracking;",
                    "ANALYZE TABLE curators;",
                ]
                
                for query in optimization_queries:
                    try:
                        db.session.execute(text(query))
                        db.session.commit()
                    except Exception as e:
                        logger.warning(f"Optimization query failed: {query} - {e}")
                        db.session.rollback()
            
            logger.info("Database optimization completed")
            return True
    except Exception as e:
        logger.error(f"Database optimization error: {e}")
        return False

def create_indexes():
    """Create performance indexes on important columns"""
    try:
        with app.app_context():
            index_queries = [
                "CREATE INDEX IF NOT EXISTS idx_activities_curator_id ON activities(curator_id);",
                "CREATE INDEX IF NOT EXISTS idx_activities_timestamp ON activities(timestamp);",
                "CREATE INDEX IF NOT EXISTS idx_response_tracking_mention_id ON response_tracking(mention_message_id);",
                "CREATE INDEX IF NOT EXISTS idx_response_tracking_timestamp ON response_tracking(mention_timestamp);",
                "CREATE INDEX IF NOT EXISTS idx_curators_discord_id ON curators(discord_id);",
                "CREATE INDEX IF NOT EXISTS idx_curators_active ON curators(is_active);",
            ]
            
            for query in index_queries:
                try:
                    db.session.execute(text(query))
                    db.session.commit()
                except Exception as e:
                    logger.warning(f"Index creation failed: {query} - {e}")
                    db.session.rollback()
            
            logger.info("Database indexes created successfully")
            return True
    except Exception as e:
        logger.error(f"Index creation error: {e}")
        return False

logger.info("Database utilities loaded")
