"""
Database models for Discord Curator Monitoring System
PostgreSQL/MySQL compatible schema using SQLAlchemy

PROJECT IDENTIFIER: All models preserve original govtracker2 schema structure
"""

from app import db
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, JSON, Float, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from datetime import datetime

class BotSettings(db.Model):
    """Bot configuration settings"""
    __tablename__ = 'bot_settings'
    
    id = db.Column(db.Integer, primary_key=True)
    setting_key = db.Column(db.String(255), nullable=False, unique=True)
    setting_value = db.Column(db.Text, nullable=False)
    description = db.Column(db.Text)
    updated_at = db.Column(db.DateTime, default=func.now(), onupdate=func.now())

class NotificationSettings(db.Model):
    """Discord notification configuration"""
    __tablename__ = 'notification_settings'
    
    id = db.Column(db.Integer, primary_key=True)
    notification_server_id = db.Column(db.String(255), nullable=False)
    notification_channel_id = db.Column(db.String(255), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    updated_at = db.Column(db.DateTime, default=func.now(), onupdate=func.now())

class BackupSettings(db.Model):
    """Automated backup configuration"""
    __tablename__ = 'backup_settings'
    
    id = db.Column(db.Integer, primary_key=True)
    frequency = db.Column(db.String(50), nullable=False, default='daily')
    is_active = db.Column(db.Boolean, default=True)
    last_backup = db.Column(db.DateTime)
    next_backup = db.Column(db.DateTime)
    updated_at = db.Column(db.DateTime, default=func.now(), onupdate=func.now())

class RatingSettings(db.Model):
    """Performance rating thresholds"""
    __tablename__ = 'rating_settings'
    
    id = db.Column(db.Integer, primary_key=True)
    rating_name = db.Column(db.String(100), nullable=False)
    rating_text = db.Column(db.String(100), nullable=False)
    min_score = db.Column(db.Integer, nullable=False)
    color = db.Column(db.String(50), nullable=False)
    updated_at = db.Column(db.DateTime, default=func.now(), onupdate=func.now())

class GlobalRatingConfig(db.Model):
    """Global rating calculation parameters"""
    __tablename__ = 'global_rating_config'
    
    id = db.Column(db.Integer, primary_key=True)
    activity_points_message = db.Column(db.Integer, nullable=False, default=3)
    activity_points_reaction = db.Column(db.Integer, nullable=False, default=1)
    activity_points_reply = db.Column(db.Integer, nullable=False, default=2)
    activity_points_task_verification = db.Column(db.Integer, nullable=False, default=5)
    response_time_good_seconds = db.Column(db.Integer, nullable=False, default=60)
    response_time_poor_seconds = db.Column(db.Integer, nullable=False, default=300)
    updated_at = db.Column(db.DateTime, default=func.now(), onupdate=func.now())

class DiscordServers(db.Model):
    """Discord servers being monitored"""
    __tablename__ = 'discord_servers'
    
    id = db.Column(db.Integer, primary_key=True)
    server_id = db.Column(db.String(255), nullable=False, unique=True)
    name = db.Column(db.String(255), nullable=False)
    role_tag_id = db.Column(db.String(255))
    completed_tasks_channel_id = db.Column(db.String(255))
    is_active = db.Column(db.Boolean, default=True)
    
    # Relationships
    activities = relationship('Activities', backref='server', lazy='dynamic')
    response_trackings = relationship('ResponseTracking', backref='server', lazy='dynamic')

class Curators(db.Model):
    """Discord curators/moderators being tracked"""
    __tablename__ = 'curators'
    
    id = db.Column(db.Integer, primary_key=True)
    discord_id = db.Column(db.String(255), nullable=False, unique=True)
    name = db.Column(db.String(255), nullable=False)
    # MySQL compatibility: JSON instead of ARRAY for factions
    factions = db.Column(db.JSON, nullable=False)
    curator_type = db.Column(db.String(100), nullable=False)
    subdivision = db.Column(db.String(100))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=func.now())
    
    # Relationships
    activities = relationship('Activities', backref='curator', lazy='dynamic')
    response_trackings = relationship('ResponseTracking', backref='curator', lazy='dynamic')

class ResponseTracking(db.Model):
    """Critical: Curator response time tracking"""
    __tablename__ = 'response_tracking'
    
    id = db.Column(db.Integer, primary_key=True)
    server_id = db.Column(db.Integer, ForeignKey('discord_servers.id'), nullable=False)
    curator_id = db.Column(db.Integer, ForeignKey('curators.id'))
    mention_message_id = db.Column(db.String(255), nullable=False)
    mention_timestamp = db.Column(db.DateTime, nullable=False)
    response_message_id = db.Column(db.String(255))
    response_timestamp = db.Column(db.DateTime)
    response_type = db.Column(db.String(50))
    response_time_seconds = db.Column(db.Integer)

class TaskReports(db.Model):
    """Task completion reports from completed-tasks channels"""
    __tablename__ = 'task_reports'
    
    id = db.Column(db.Integer, primary_key=True)
    server_id = db.Column(db.Integer, ForeignKey('discord_servers.id'), nullable=False)
    author_id = db.Column(db.String(255), nullable=False)
    author_name = db.Column(db.String(255), nullable=False)
    message_id = db.Column(db.String(255), nullable=False, unique=True)
    channel_id = db.Column(db.String(255), nullable=False)
    content = db.Column(db.Text, nullable=False)
    task_count = db.Column(db.Integer, nullable=False)
    submitted_at = db.Column(db.DateTime, nullable=False)
    curator_id = db.Column(db.Integer, ForeignKey('curators.id'))
    curator_discord_id = db.Column(db.String(255))
    curator_name = db.Column(db.String(255))
    checked_at = db.Column(db.DateTime)
    approved_tasks = db.Column(db.Integer)
    status = db.Column(db.String(50), nullable=False, default='pending')
    week_start = db.Column(db.DateTime, nullable=False)

class Activities(db.Model):
    """Curator activity tracking (messages, reactions, replies)"""
    __tablename__ = 'activities'
    
    id = db.Column(db.Integer, primary_key=True)
    curator_id = db.Column(db.Integer, ForeignKey('curators.id'), nullable=False)
    server_id = db.Column(db.Integer, ForeignKey('discord_servers.id'), nullable=False)
    type = db.Column(db.String(50), nullable=False)
    channel_id = db.Column(db.String(255), nullable=False)
    channel_name = db.Column(db.String(255))
    message_id = db.Column(db.String(255))
    content = db.Column(db.Text)
    reaction_emoji = db.Column(db.String(100))
    target_message_id = db.Column(db.String(255))
    target_message_content = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, default=func.now())

class ExcludedCurators(db.Model):
    """Curators excluded from import/tracking"""
    __tablename__ = 'excluded_curators'
    
    id = db.Column(db.Integer, primary_key=True)
    discord_id = db.Column(db.String(255), nullable=False, unique=True)
    name = db.Column(db.String(255), nullable=False)
    reason = db.Column(db.Text)
    excluded_at = db.Column(db.DateTime, default=func.now())

class Users(db.Model):
    """System users for authentication"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(255), nullable=False, unique=True)
    password = db.Column(db.String(255), nullable=False)
