"""
Configuration settings for Discord Curator Monitoring System
Centralized configuration management

PROJECT IDENTIFIER: Configuration for govtracker2 Flask backend
"""

import os
from datetime import timedelta

class Config:
    """Base configuration class"""
    
    # Flask settings
    SECRET_KEY = os.environ.get('SESSION_SECRET', 'govtracker2-discord-curator-monitoring')
    
    # Database settings
    DATABASE_URL = os.environ.get('DATABASE_URL')
    if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
    
    SQLALCHEMY_DATABASE_URI = DATABASE_URL or 'postgresql://localhost/govtracker2'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_recycle': 300,
        'pool_pre_ping': True,
        'pool_size': 10,
        'max_overflow': 20,
    }
    
    # Discord bot settings
    DISCORD_BOT_TOKEN = os.environ.get('DISCORD_BOT_TOKEN')
    
    # Monitored Discord servers (from original project)
    MONITORED_SERVERS = {
        '1315050639406825593': 'Government',
        '1315050639406825594': 'FIB',
        '1315050639406825595': 'LSPD',
        '1315050639406825596': 'SANG',
        '1315050639406825597': 'LSCSD',
        '1315050639406825598': 'EMS',
        '1315050639406825599': 'Weazel News',
        '1315050639406825600': 'Detectives'
    }
    
    # Notification settings
    NOTIFICATION_SERVER_ID = '805026457327108126'
    NOTIFICATION_CHANNEL_ID = '974783377465036861'
    
    # Curator role IDs for notifications
    CURATOR_ROLES = {
        'Detectives': '916616528395378708',
        'Weazel News': '1329213276587950080',
        'EMS': '1329212940540313644',
        'LSCSD': '1329213185579946106',
        'SANG': '1329213239996973116',
        'LSPD': '1329212725921976322',
        'FIB': '1329213307059437629',
        'Government': '1329213001814773780'
    }
    
    # Performance rating thresholds (from original system)
    RATING_THRESHOLDS = {
        'excellent': {'min_score': 50, 'text': 'Великолепно', 'color': 'green'},
        'good': {'min_score': 35, 'text': 'Хорошо', 'color': 'blue'},
        'normal': {'min_score': 20, 'text': 'Нормально', 'color': 'yellow'},
        'poor': {'min_score': 10, 'text': 'Плохо', 'color': 'orange'},
        'terrible': {'min_score': 0, 'text': 'Ужасно', 'color': 'red'}
    }
    
    # Activity point values
    ACTIVITY_POINTS = {
        'message': 3,
        'reaction': 1,
        'reply': 2,
        'task_verification': 5
    }
    
    # Response time thresholds (seconds)
    RESPONSE_TIME_GOOD = 60  # 1 minute
    RESPONSE_TIME_POOR = 300  # 5 minutes
    
    # Mention detection keywords
    MENTION_KEYWORDS = [
        'куратор', 'curator', 'помощь', 'help', 'вопрос', 'question',
        'админ', 'admin', 'поддержка', 'support', 'модератор', 'moderator'
    ]
    
    # Backup settings
    BACKUP_FREQUENCY_OPTIONS = ['hourly', '4hours', '12hours', 'daily', 'weekly', 'monthly']
    BACKUP_RETENTION_DAYS = 30
    
    # Logging settings
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    
    # Scheduler settings
    SCHEDULER_API_ENABLED = True
    JOBS = [
        {
            'id': 'check_unanswered_mentions',
            'func': 'scheduler:check_unanswered_mentions',
            'trigger': 'interval',
            'minutes': 5
        },
        {
            'id': 'database_backup',
            'func': 'scheduler:perform_database_backup',
            'trigger': 'cron',
            'hour': 3,
            'minute': 0
        },
        {
            'id': 'cleanup_old_activities',
            'func': 'scheduler:cleanup_old_activities',
            'trigger': 'cron',
            'day_of_week': 'sun',
            'hour': 4,
            'minute': 0
        }
    ]

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    TESTING = False

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    TESTING = False

class TestingConfig(Config):
    """Testing configuration"""
    DEBUG = True
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'

# Configuration mapping
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}

def get_config():
    """Get configuration based on environment"""
    env = os.environ.get('FLASK_ENV', 'development')
    return config.get(env, config['default'])
