"""
Database backup and restore service
Provides backup functionality for PostgreSQL/MySQL databases

PROJECT IDENTIFIER: Backup service for govtracker2 data preservation
"""

import os
import json
import logging
from datetime import datetime, timedelta
from app import app, db
from models import *
from sqlalchemy import text
import gzip
import tempfile

logger = logging.getLogger(__name__)

def create_backup():
    """Create a complete database backup"""
    try:
        backup_data = {
            'metadata': {
                'timestamp': datetime.now().isoformat(),
                'version': '2.0',
                'database_type': 'postgresql',
                'backup_type': 'full'
            },
            'data': {}
        }
        
        with app.app_context():
            # Backup all tables
            tables_to_backup = [
                ('curators', Curators),
                ('discord_servers', DiscordServers),
                ('activities', Activities),
                ('response_tracking', ResponseTracking),
                ('task_reports', TaskReports),
                ('bot_settings', BotSettings),
                ('rating_settings', RatingSettings),
                ('global_rating_config', GlobalRatingConfig),
                ('notification_settings', NotificationSettings),
                ('backup_settings', BackupSettings),
                ('excluded_curators', ExcludedCurators),
                ('users', Users)
            ]
            
            for table_name, model_class in tables_to_backup:
                try:
                    records = db.session.query(model_class).all()
                    table_data = []
                    
                    for record in records:
                        record_dict = {}
                        for column in model_class.__table__.columns:
                            value = getattr(record, column.name)
                            
                            # Handle datetime serialization
                            if isinstance(value, datetime):
                                value = value.isoformat()
                            
                            record_dict[column.name] = value
                        
                        table_data.append(record_dict)
                    
                    backup_data['data'][table_name] = table_data
                    logger.info(f"Backed up {len(table_data)} records from {table_name}")
                    
                except Exception as e:
                    logger.error(f"Error backing up table {table_name}: {e}")
                    continue
            
            # Create compressed backup file
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_filename = f"govtracker2_backup_{timestamp}.json.gz"
            
            # Ensure backup directory exists
            backup_dir = 'backups'
            os.makedirs(backup_dir, exist_ok=True)
            backup_path = os.path.join(backup_dir, backup_filename)
            
            # Write compressed backup
            with gzip.open(backup_path, 'wt', encoding='utf-8') as f:
                json.dump(backup_data, f, indent=2, ensure_ascii=False)
            
            # Get file size
            file_size = os.path.getsize(backup_path)
            
            logger.info(f"Backup created successfully: {backup_filename} ({file_size} bytes)")
            
            return {
                'success': True,
                'filename': backup_filename,
                'size': file_size,
                'path': backup_path,
                'timestamp': backup_data['metadata']['timestamp']
            }
    
    except Exception as e:
        logger.error(f"Backup creation failed: {e}")
        return {
            'success': False,
            'error': str(e)
        }

def restore_backup(filename):
    """Restore database from backup file"""
    try:
        backup_dir = 'backups'
        backup_path = os.path.join(backup_dir, filename)
        
        if not os.path.exists(backup_path):
            return {'success': False, 'error': 'Backup file not found'}
        
        with app.app_context():
            # Read backup data
            with gzip.open(backup_path, 'rt', encoding='utf-8') as f:
                backup_data = json.load(f)
            
            # Validate backup format
            if 'metadata' not in backup_data or 'data' not in backup_data:
                return {'success': False, 'error': 'Invalid backup format'}
            
            logger.info(f"Starting restore from {filename}")
            
            # Clear existing data (be very careful!)
            tables_to_clear = [
                Activities, ResponseTracking, TaskReports, 
                BotSettings, RatingSettings, GlobalRatingConfig,
                NotificationSettings, BackupSettings, ExcludedCurators
            ]
            
            for table_class in tables_to_clear:
                try:
                    db.session.query(table_class).delete()
                    logger.info(f"Cleared table {table_class.__tablename__}")
                except Exception as e:
                    logger.warning(f"Could not clear table {table_class.__tablename__}: {e}")
            
            # Restore data
            restored_count = 0
            for table_name, table_data in backup_data['data'].items():
                try:
                    # Get model class
                    model_class = None
                    for cls in [Curators, DiscordServers, Activities, ResponseTracking, 
                               TaskReports, BotSettings, RatingSettings, GlobalRatingConfig,
                               NotificationSettings, BackupSettings, ExcludedCurators, Users]:
                        if cls.__tablename__ == table_name:
                            model_class = cls
                            break
                    
                    if not model_class:
                        logger.warning(f"Model class not found for table {table_name}")
                        continue
                    
                    # Insert records
                    for record_data in table_data:
                        # Convert datetime strings back to datetime objects
                        for key, value in record_data.items():
                            if key.endswith('_at') or key.endswith('_timestamp') and isinstance(value, str):
                                try:
                                    record_data[key] = datetime.fromisoformat(value.replace('Z', '+00:00'))
                                except (ValueError, TypeError):
                                    pass
                        
                        # Create new record
                        record = model_class(**record_data)
                        db.session.add(record)
                        restored_count += 1
                    
                    logger.info(f"Restored {len(table_data)} records to {table_name}")
                    
                except Exception as e:
                    logger.error(f"Error restoring table {table_name}: {e}")
                    continue
            
            db.session.commit()
            
            logger.info(f"Restore completed successfully: {restored_count} records restored")
            
            return {
                'success': True,
                'restored_records': restored_count,
                'backup_date': backup_data['metadata']['timestamp']
            }
    
    except Exception as e:
        logger.error(f"Restore failed: {e}")
        db.session.rollback()
        return {
            'success': False,
            'error': str(e)
        }

def cleanup_old_backups(retention_days=30):
    """Clean up old backup files"""
    try:
        backup_dir = 'backups'
        if not os.path.exists(backup_dir):
            return
        
        cutoff_date = datetime.now() - timedelta(days=retention_days)
        deleted_count = 0
        
        for filename in os.listdir(backup_dir):
            if filename.endswith('.json.gz'):
                filepath = os.path.join(backup_dir, filename)
                file_time = datetime.fromtimestamp(os.path.getmtime(filepath))
                
                if file_time < cutoff_date:
                    os.remove(filepath)
                    deleted_count += 1
                    logger.info(f"Deleted old backup: {filename}")
        
        if deleted_count > 0:
            logger.info(f"Cleanup completed: {deleted_count} old backups deleted")
    
    except Exception as e:
        logger.error(f"Backup cleanup failed: {e}")

logger.info("Backup service initialized")