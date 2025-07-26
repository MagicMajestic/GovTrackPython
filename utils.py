"""
Utility functions for Discord Curator Monitoring System
Preserves all calculation algorithms from original Node.js version

PROJECT IDENTIFIER: Utility functions converted from govtracker2 TypeScript
"""

import re
from datetime import datetime, timedelta
from app import db
from models import Activities, ResponseTracking, RatingSettings, GlobalRatingConfig
from sqlalchemy import func, and_
import logging

logger = logging.getLogger(__name__)

def detect_mention_keywords(content):
    """
    Detect mention keywords in message content
    Preserves original keyword detection logic
    """
    if not content:
        return False
    
    # Keywords that trigger curator response tracking
    keywords = [
        'куратор', 'curator', 'помощь', 'help', 'вопрос', 'question',
        'админ', 'admin', 'поддержка', 'support', 'модератор', 'moderator'
    ]
    
    content_lower = content.lower()
    return any(keyword in content_lower for keyword in keywords)

def calculate_performance_rating(activity_count, avg_response_time):
    """
    Calculate curator performance rating based on activity and response time
    Preserves exact algorithm from original system
    """
    try:
        # Get rating configuration
        with db.session() as session:
            # Get global rating config
            config = session.query(GlobalRatingConfig).first()
            if not config:
                # Default values if config not found
                points_per_message = 3
                response_good_threshold = 60  # seconds
                response_poor_threshold = 300  # seconds
            else:
                points_per_message = config.activity_points_message
                response_good_threshold = config.response_time_good_seconds
                response_poor_threshold = config.response_time_poor_seconds
            
            # Calculate base score from activities
            base_score = activity_count * points_per_message
            
            # Apply response time modifiers
            if avg_response_time and avg_response_time > 0:
                if avg_response_time <= response_good_threshold:
                    response_modifier = 1.2  # 20% bonus for fast responses
                elif avg_response_time >= response_poor_threshold:
                    response_modifier = 0.8  # 20% penalty for slow responses
                else:
                    response_modifier = 1.0  # No modifier for average responses
            else:
                response_modifier = 1.0
            
            # Calculate final score
            final_score = int(base_score * response_modifier)
            
            # Get rating settings
            ratings = session.query(RatingSettings).order_by(RatingSettings.min_score.desc()).all()
            
            # Default ratings if not configured
            if not ratings:
                if final_score >= 50:
                    rating_info = {'name': 'excellent', 'text': 'Великолепно', 'color': 'green'}
                elif final_score >= 35:
                    rating_info = {'name': 'good', 'text': 'Хорошо', 'color': 'blue'}
                elif final_score >= 20:
                    rating_info = {'name': 'normal', 'text': 'Нормально', 'color': 'yellow'}
                elif final_score >= 10:
                    rating_info = {'name': 'poor', 'text': 'Плохо', 'color': 'orange'}
                else:
                    rating_info = {'name': 'terrible', 'text': 'Ужасно', 'color': 'red'}
            else:
                # Find appropriate rating
                rating_info = {'name': 'terrible', 'text': 'Ужасно', 'color': 'red'}
                for rating in ratings:
                    if final_score >= rating.min_score:
                        rating_info = {
                            'name': rating.rating_name,
                            'text': rating.rating_text,
                            'color': rating.color
                        }
                        break
            
            return {
                'score': final_score,
                'rating': rating_info['name'],
                'text': rating_info['text'],
                'color': rating_info['color']
            }
    
    except Exception as e:
        logger.error(f"Performance rating calculation error: {e}")
        return {
            'score': 0,
            'rating': 'unknown',
            'text': 'Неизвестно',
            'color': 'gray'
        }

def get_curator_statistics(curator_id, detailed=False):
    """
    Get comprehensive curator statistics
    Preserves all statistical calculations from original system
    """
    try:
        with db.session() as session:
            # Total activities
            total_activities = session.query(func.count(Activities.id)).filter(
                Activities.curator_id == curator_id
            ).scalar() or 0
            
            # Activity breakdown by type
            activity_breakdown = session.query(
                Activities.type,
                func.count(Activities.id).label('count')
            ).filter(
                Activities.curator_id == curator_id
            ).group_by(Activities.type).all()
            
            breakdown = {activity_type: count for activity_type, count in activity_breakdown}
            
            # Average response time
            avg_response_time = session.query(
                func.avg(ResponseTracking.response_time_seconds)
            ).filter(
                and_(
                    ResponseTracking.curator_id == curator_id,
                    ResponseTracking.response_time_seconds.isnot(None)
                )
            ).scalar()
            
            # Convert to minutes for display
            avg_response_minutes = round(avg_response_time / 60, 1) if avg_response_time else 0
            
            stats = {
                'total_activities': total_activities,
                'activity_breakdown': breakdown,
                'avg_response_time': avg_response_minutes,
                'messages': breakdown.get('message', 0),
                'reactions': breakdown.get('reaction', 0),
                'replies': breakdown.get('reply', 0)
            }
            
            if detailed:
                # Additional detailed statistics
                
                # Activities in last 7 days
                week_ago = datetime.now() - timedelta(days=7)
                weekly_activities = session.query(func.count(Activities.id)).filter(
                    and_(
                        Activities.curator_id == curator_id,
                        Activities.timestamp >= week_ago
                    )
                ).scalar() or 0
                
                # Activities in last 30 days
                month_ago = datetime.now() - timedelta(days=30)
                monthly_activities = session.query(func.count(Activities.id)).filter(
                    and_(
                        Activities.curator_id == curator_id,
                        Activities.timestamp >= month_ago
                    )
                ).scalar() or 0
                
                # Response count
                response_count = session.query(func.count(ResponseTracking.id)).filter(
                    and_(
                        ResponseTracking.curator_id == curator_id,
                        ResponseTracking.response_timestamp.isnot(None)
                    )
                ).scalar() or 0
                
                # Fastest response time
                fastest_response = session.query(
                    func.min(ResponseTracking.response_time_seconds)
                ).filter(
                    and_(
                        ResponseTracking.curator_id == curator_id,
                        ResponseTracking.response_time_seconds.isnot(None)
                    )
                ).scalar()
                
                fastest_minutes = round(fastest_response / 60, 1) if fastest_response else 0
                
                stats.update({
                    'weekly_activities': weekly_activities,
                    'monthly_activities': monthly_activities,
                    'response_count': response_count,
                    'fastest_response_time': fastest_minutes
                })
            
            return stats
    
    except Exception as e:
        logger.error(f"Curator statistics error: {e}")
        return {
            'total_activities': 0,
            'activity_breakdown': {},
            'avg_response_time': 0,
            'messages': 0,
            'reactions': 0,
            'replies': 0
        }

async def process_curator_response(message, curator, server):
    """
    Process curator message as potential response to tracked mention
    Preserves response tracking logic from original system
    """
    try:
        with db.session() as session:
            # Check if this message is in reply to a tracked mention
            if message.reference and message.reference.message_id:
                reference_id = str(message.reference.message_id)
                
                # Find pending response tracking
                tracking = session.query(ResponseTracking).filter(
                    and_(
                        ResponseTracking.server_id == server.id,
                        ResponseTracking.mention_message_id == reference_id,
                        ResponseTracking.response_timestamp.is_(None)
                    )
                ).first()
                
                if tracking:
                    # Calculate response time using actual message timestamps
                    response_time = (message.created_at - tracking.mention_timestamp).total_seconds()
                    
                    # Update tracking record
                    tracking.curator_id = curator.id
                    tracking.response_message_id = str(message.id)
                    tracking.response_timestamp = message.created_at
                    tracking.response_type = 'reply'
                    tracking.response_time_seconds = int(response_time)
                    
                    session.commit()
                    
                    logger.info(f"Curator {curator.name} replied in {response_time:.1f} seconds")
    
    except Exception as e:
        logger.error(f"Response processing error: {e}")
        if db.session:
            db.session.rollback()

def initialize_default_settings():
    """
    Initialize default system settings
    Preserves configuration from original system
    """
    try:
        with db.session() as session:
            # Initialize rating settings if not exist
            existing_ratings = session.query(RatingSettings).count()
            if existing_ratings == 0:
                default_ratings = [
                    {'name': 'excellent', 'text': 'Великолепно', 'min_score': 50, 'color': 'green'},
                    {'name': 'good', 'text': 'Хорошо', 'min_score': 35, 'color': 'blue'},
                    {'name': 'normal', 'text': 'Нормально', 'min_score': 20, 'color': 'yellow'},
                    {'name': 'poor', 'text': 'Плохо', 'min_score': 10, 'color': 'orange'},
                    {'name': 'terrible', 'text': 'Ужасно', 'min_score': 0, 'color': 'red'}
                ]
                
                for rating_data in default_ratings:
                    rating = RatingSettings()
                    rating.rating_name = rating_data['name']
                    rating.rating_text = rating_data['text']
                    rating.min_score = rating_data['min_score']
                    rating.color = rating_data['color']
                    session.add(rating)
            
            # Initialize global rating config if not exist
            existing_config = session.query(GlobalRatingConfig).first()
            if not existing_config:
                config = GlobalRatingConfig()
                config.activity_points_message = 3
                config.activity_points_reaction = 1
                config.activity_points_reply = 2
                config.activity_points_task_verification = 5
                config.response_time_good_seconds = 60
                config.response_time_poor_seconds = 300
                session.add(config)
            
            session.commit()
            logger.info("Default settings initialized")
    
    except Exception as e:
        logger.error(f"Settings initialization error: {e}")
        if db.session:
            db.session.rollback()

def format_time_duration(seconds):
    """Format time duration in human-readable format"""
    if not seconds:
        return "0 сек"
    
    if seconds < 60:
        return f"{int(seconds)} сек"
    elif seconds < 3600:
        minutes = int(seconds / 60)
        return f"{minutes} мин"
    else:
        hours = int(seconds / 3600)
        minutes = int((seconds % 3600) / 60)
        return f"{hours}ч {minutes}м"

logger.info("Utility functions loaded successfully")
