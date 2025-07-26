"""
Background scheduler for automated tasks
Handles backups, notifications, and maintenance tasks

PROJECT IDENTIFIER: Background task scheduler for govtracker2 Flask conversion
"""

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import logging
from datetime import datetime, timedelta
from app import app, db
from models import BackupSettings, NotificationSettings, ResponseTracking, DiscordServers
from backup_service import create_backup, cleanup_old_backups
from utils import initialize_default_settings

logger = logging.getLogger(__name__)

scheduler = BackgroundScheduler()

def check_unanswered_mentions():
    """Check for unanswered mentions and send reminders"""
    try:
        with app.app_context():
            # Find mentions older than 10 minutes without response
            cutoff_time = datetime.now() - timedelta(minutes=10)
            
            unanswered = db.session.query(ResponseTracking).filter(
                ResponseTracking.mention_timestamp < cutoff_time,
                ResponseTracking.response_timestamp.is_(None)
            ).all()
            
            if unanswered:
                logger.info(f"Found {len(unanswered)} unanswered mentions")
                # TODO: Send reminder notifications to Discord
            
    except Exception as e:
        logger.error(f"Unanswered mentions check error: {e}")

def perform_database_backup():
    """Perform automated database backup"""
    try:
        with app.app_context():
            backup_settings = db.session.query(BackupSettings).filter(
                BackupSettings.is_active == True
            ).first()
            
            if backup_settings:
                logger.info("Starting automated database backup")
                backup_result = create_backup()
                
                if backup_result['success']:
                    # Update backup settings
                    backup_settings.last_backup = datetime.now()
                    
                    # Calculate next backup time based on frequency
                    if backup_settings.frequency == 'hourly':
                        next_backup = datetime.now() + timedelta(hours=1)
                    elif backup_settings.frequency == '4hours':
                        next_backup = datetime.now() + timedelta(hours=4)
                    elif backup_settings.frequency == '12hours':
                        next_backup = datetime.now() + timedelta(hours=12)
                    elif backup_settings.frequency == 'daily':
                        next_backup = datetime.now() + timedelta(days=1)
                    elif backup_settings.frequency == 'weekly':
                        next_backup = datetime.now() + timedelta(weeks=1)
                    else:  # monthly
                        next_backup = datetime.now() + timedelta(days=30)
                    
                    backup_settings.next_backup = next_backup
                    db.session.commit()
                    
                    logger.info(f"Backup completed successfully. Next backup: {next_backup}")
                else:
                    logger.error(f"Backup failed: {backup_result.get('error', 'Unknown error')}")
            
            # Cleanup old backups (keep last 30 days)
            cleanup_old_backups(days=30)
            
    except Exception as e:
        logger.error(f"Database backup error: {e}")

def cleanup_old_activities():
    """Clean up old activity records (older than 6 months)"""
    try:
        with app.app_context():
            cutoff_date = datetime.now() - timedelta(days=180)
            
            from models import Activities
            old_activities = db.session.query(Activities).filter(
                Activities.timestamp < cutoff_date
            )
            
            count = old_activities.count()
            if count > 0:
                old_activities.delete()
                db.session.commit()
                logger.info(f"Cleaned up {count} old activity records")
            
    except Exception as e:
        logger.error(f"Activity cleanup error: {e}")
        db.session.rollback()

def update_server_statistics():
    """Update server statistics and rankings"""
    try:
        with app.app_context():
            servers = db.session.query(DiscordServers).filter(
                DiscordServers.is_active == True
            ).all()
            
            for server in servers:
                # Update server activity counts, rankings, etc.
                # This can be expanded based on requirements
                pass
            
            logger.debug("Server statistics updated")
            
    except Exception as e:
        logger.error(f"Server statistics update error: {e}")

def initialize_system():
    """Initialize system with default settings"""
    try:
        with app.app_context():
            initialize_default_settings()
            logger.info("System initialization completed")
    except Exception as e:
        logger.error(f"System initialization error: {e}")

def start_scheduler():
    """Start the background scheduler with all jobs"""
    try:
        # Check for unanswered mentions every 5 minutes
        scheduler.add_job(
            func=check_unanswered_mentions,
            trigger=CronTrigger(minute='*/5'),
            id='check_unanswered_mentions',
            name='Check Unanswered Mentions',
            replace_existing=True
        )
        
        # Database backup (daily at 3 AM)
        scheduler.add_job(
            func=perform_database_backup,
            trigger=CronTrigger(hour=3, minute=0),
            id='database_backup',
            name='Database Backup',
            replace_existing=True
        )
        
        # Cleanup old activities (weekly on Sunday at 4 AM)
        scheduler.add_job(
            func=cleanup_old_activities,
            trigger=CronTrigger(day_of_week='sun', hour=4, minute=0),
            id='cleanup_activities',
            name='Cleanup Old Activities',
            replace_existing=True
        )
        
        # Update server statistics (every 30 minutes)
        scheduler.add_job(
            func=update_server_statistics,
            trigger=CronTrigger(minute='*/30'),
            id='update_statistics',
            name='Update Server Statistics',
            replace_existing=True
        )
        
        # Initialize system on startup
        scheduler.add_job(
            func=initialize_system,
            trigger='date',
            run_date=datetime.now() + timedelta(seconds=5),
            id='initialize_system',
            name='System Initialization'
        )
        
        scheduler.start()
        logger.info("Background scheduler started with all jobs")
        
    except Exception as e:
        logger.error(f"Scheduler startup error: {e}")

def stop_scheduler():
    """Stop the background scheduler"""
    try:
        scheduler.shutdown()
        logger.info("Background scheduler stopped")
    except Exception as e:
        logger.error(f"Scheduler shutdown error: {e}")

if __name__ == "__main__":
    start_scheduler()
    
    # Keep the script running
    try:
        import time
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        stop_scheduler()
