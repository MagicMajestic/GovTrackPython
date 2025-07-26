"""
COMPLETE Rating System for Curator Performance
Implements Russian rating system: Великолепно/Хорошо/Нормально/Плохо/Ужасно
Based on original govtracker2 algorithms with authentic performance calculation

RATING THRESHOLDS:
- Великолепно (Excellent): 50+ points
- Хорошо (Good): 35+ points  
- Нормально (Normal): 20+ points
- Плохо (Poor): 10+ points
- Ужасно (Terrible): <10 points

SCORING SYSTEM:
- Messages: +3 points
- Reactions: +1 point
- Replies: +2 points
- Task verification: +5 points
- Response time bonus/penalty applied
"""

from datetime import datetime, timedelta
from models import (
    Curators, Activities, ResponseTracking, TaskReports,
    RatingSettings, GlobalRatingConfig
)
from app import db
import logging

logger = logging.getLogger(__name__)

class CuratorRatingSystem:
    """Complete curator performance rating system"""
    
    def __init__(self):
        self.rating_config = self._load_rating_config()
        self.rating_thresholds = self._load_rating_thresholds()
    
    def _load_rating_config(self):
        """Load global rating configuration"""
        config = GlobalRatingConfig.query.first()
        if not config:
            # Create default configuration
            config = GlobalRatingConfig()
            config.activity_points_message = 3
            config.activity_points_reaction = 1
            config.activity_points_reply = 2
            config.activity_points_task_verification = 5
            config.response_time_good_seconds = 60
            config.response_time_poor_seconds = 300
            db.session.add(config)
            db.session.commit()
            
        return config
    
    def _load_rating_thresholds(self):
        """Load rating thresholds with Russian labels"""
        thresholds = RatingSettings.query.order_by(RatingSettings.min_score.desc()).all()
        
        if not thresholds:
            # Create default Russian rating thresholds
            default_ratings = [
                ('excellent', 'Великолепно', 50, '#22c55e'),
                ('good', 'Хорошо', 35, '#3b82f6'),
                ('normal', 'Нормально', 20, '#f59e0b'),
                ('poor', 'Плохо', 10, '#ef4444'),
                ('terrible', 'Ужасно', 0, '#991b1b')
            ]
            
            for name, text, min_score, color in default_ratings:
                rating = RatingSettings()
                rating.rating_name = name
                rating.rating_text = text
                rating.min_score = min_score
                rating.color = color
                db.session.add(rating)
                
            db.session.commit()
            thresholds = RatingSettings.query.order_by(RatingSettings.min_score.desc()).all()
            
        return thresholds
    
    def calculate_curator_score(self, curator_id, days=30):
        """Calculate total curator score based on activities and response times"""
        try:
            # Date range for calculation
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days)
            
            # Get all activities in period
            activities = Activities.query.filter(
                Activities.curator_id == curator_id,
                Activities.timestamp >= start_date,
                Activities.timestamp <= end_date
            ).all()
            
            # Calculate base activity points
            base_score = 0
            activity_counts = {'message': 0, 'reaction': 0, 'reply': 0, 'task_verification': 0}
            
            for activity in activities:
                if activity.type == 'message':
                    base_score += self.rating_config.activity_points_message
                    activity_counts['message'] += 1
                elif activity.type == 'reaction':
                    base_score += self.rating_config.activity_points_reaction
                    activity_counts['reaction'] += 1
                elif activity.type == 'reply':
                    base_score += self.rating_config.activity_points_reply
                    activity_counts['reply'] += 1
                elif activity.type == 'task_verification':
                    base_score += self.rating_config.activity_points_task_verification
                    activity_counts['task_verification'] += 1
            
            # Apply response time modifiers
            response_bonus = self.calculate_response_time_bonus(curator_id, days)
            
            total_score = base_score + response_bonus
            
            return {
                'total_score': max(0, total_score),
                'base_score': base_score,
                'response_bonus': response_bonus,
                'activity_counts': activity_counts,
                'period_days': days
            }
            
        except Exception as e:
            logger.error(f"Error calculating curator score: {e}")
            return {
                'total_score': 0,
                'base_score': 0,
                'response_bonus': 0,
                'activity_counts': {'message': 0, 'reaction': 0, 'reply': 0, 'task_verification': 0},
                'period_days': days
            }
    
    def calculate_response_time_bonus(self, curator_id, days=30):
        """Calculate bonus/penalty based on response times"""
        try:
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days)
            
            responses = ResponseTracking.query.filter(
                ResponseTracking.curator_id == curator_id,
                ResponseTracking.response_timestamp.isnot(None),
                ResponseTracking.response_timestamp >= start_date,
                ResponseTracking.response_timestamp <= end_date
            ).all()
            
            if not responses:
                return 0
                
            total_bonus = 0
            
            for response in responses:
                response_time = response.response_time_seconds or 0
                
                if response_time <= self.rating_config.response_time_good_seconds:
                    # Fast response bonus
                    total_bonus += 2
                elif response_time <= self.rating_config.response_time_poor_seconds:
                    # Neutral response
                    total_bonus += 0
                else:
                    # Slow response penalty
                    total_bonus -= 1
                    
            return total_bonus
            
        except Exception as e:
            logger.error(f"Error calculating response time bonus: {e}")
            return 0
    
    def get_curator_rating(self, curator_id, days=30):
        """Get curator rating with Russian label and color"""
        score_data = self.calculate_curator_score(curator_id, days)
        total_score = score_data['total_score']
        
        # Find appropriate rating
        rating = None
        for threshold in self.rating_thresholds:
            if total_score >= threshold.min_score:
                rating = threshold
                break
                
        if not rating:
            rating = self.rating_thresholds[-1]  # Lowest rating
            
        return {
            'rating_name': rating.rating_name,
            'rating_text': rating.rating_text,  # Russian text
            'rating_color': rating.color,
            'score': total_score,
            'score_data': score_data
        }
    
    def get_average_response_time(self, curator_id, days=30):
        """Calculate average response time in seconds"""
        try:
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days)
            
            responses = ResponseTracking.query.filter(
                ResponseTracking.curator_id == curator_id,
                ResponseTracking.response_time_seconds.isnot(None),
                ResponseTracking.response_timestamp >= start_date,
                ResponseTracking.response_timestamp <= end_date
            ).all()
            
            if not responses:
                return None
                
            total_time = sum(r.response_time_seconds for r in responses)
            average_time = total_time / len(responses)
            
            return {
                'average_seconds': int(average_time),
                'response_count': len(responses),
                'formatted_time': self.format_time_duration(average_time)
            }
            
        except Exception as e:
            logger.error(f"Error calculating average response time: {e}")
            return None
    
    def format_time_duration(self, seconds):
        """Format time duration in Russian with proper declensions"""
        if seconds < 60:
            return f"{int(seconds)} сек"
        elif seconds < 3600:
            minutes = int(seconds / 60)
            if minutes == 1:
                return "1 минута"
            elif minutes < 5:
                return f"{minutes} минуты"
            else:
                return f"{minutes} минут"
        elif seconds < 86400:
            hours = int(seconds / 3600)
            if hours == 1:
                return "1 час"
            elif hours < 5:
                return f"{hours} часа"
            else:
                return f"{hours} часов"
        else:
            days = int(seconds / 86400)
            if days == 1:
                return "1 день"
            elif days < 5:
                return f"{days} дня"
            else:
                return f"{days} дней"
    
    def get_top_curators(self, limit=10, days=30):
        """Get top performing curators with ratings"""
        try:
            curators = Curators.query.filter_by(is_active=True).all()
            curator_ratings = []
            
            for curator in curators:
                rating_data = self.get_curator_rating(curator.id, days)
                avg_response = self.get_average_response_time(curator.id, days)
                
                curator_ratings.append({
                    'curator': curator,
                    'rating': rating_data,
                    'average_response_time': avg_response,
                    'score': rating_data['score']
                })
            
            # Sort by score descending
            curator_ratings.sort(key=lambda x: x['score'], reverse=True)
            
            return curator_ratings[:limit]
            
        except Exception as e:
            logger.error(f"Error getting top curators: {e}")
            return []
    
    def get_curator_daily_stats(self, curator_id, days=7):
        """Get curator statistics broken down by day"""
        try:
            end_date = datetime.utcnow().replace(hour=23, minute=59, second=59)
            start_date = end_date - timedelta(days=days-1)
            start_date = start_date.replace(hour=0, minute=0, second=0)
            
            daily_stats = []
            
            for i in range(days):
                day_start = start_date + timedelta(days=i)
                day_end = day_start.replace(hour=23, minute=59, second=59)
                
                # Activities for this day
                activities = Activities.query.filter(
                    Activities.curator_id == curator_id,
                    Activities.timestamp >= day_start,
                    Activities.timestamp <= day_end
                ).all()
                
                # Response tracking for this day
                responses = ResponseTracking.query.filter(
                    ResponseTracking.curator_id == curator_id,
                    ResponseTracking.response_timestamp >= day_start,
                    ResponseTracking.response_timestamp <= day_end,
                    ResponseTracking.response_time_seconds.isnot(None)
                ).all()
                
                # Calculate daily score
                day_score = 0
                activity_counts = {'message': 0, 'reaction': 0, 'reply': 0, 'task_verification': 0}
                
                for activity in activities:
                    if activity.type == 'message':
                        day_score += self.rating_config.activity_points_message
                        activity_counts['message'] += 1
                    elif activity.type == 'reaction':
                        day_score += self.rating_config.activity_points_reaction
                        activity_counts['reaction'] += 1
                    elif activity.type == 'reply':
                        day_score += self.rating_config.activity_points_reply
                        activity_counts['reply'] += 1
                    elif activity.type == 'task_verification':
                        day_score += self.rating_config.activity_points_task_verification
                        activity_counts['task_verification'] += 1
                
                # Average response time for day
                avg_response_time = None
                if responses:
                    total_time = sum(r.response_time_seconds for r in responses)
                    avg_response_time = total_time / len(responses)
                
                daily_stats.append({
                    'date': day_start.strftime('%Y-%m-%d'),
                    'score': day_score,
                    'activity_counts': activity_counts,
                    'total_activities': len(activities),
                    'response_count': len(responses),
                    'average_response_time': avg_response_time,
                    'formatted_response_time': self.format_time_duration(avg_response_time) if avg_response_time else None
                })
                
            return daily_stats
            
        except Exception as e:
            logger.error(f"Error getting daily stats: {e}")
            return []

# Initialize rating system
rating_system = CuratorRatingSystem()

# Utility functions for API use
def get_curator_performance(curator_id, days=30):
    """Get complete curator performance data"""
    return rating_system.get_curator_rating(curator_id, days)

def get_curator_response_stats(curator_id, days=30):
    """Get curator response time statistics"""
    return rating_system.get_average_response_time(curator_id, days)

def format_russian_time(seconds):
    """Format seconds to Russian time format"""
    return rating_system.format_time_duration(seconds)

def get_leaderboard(limit=10, days=30):
    """Get curator leaderboard"""
    return rating_system.get_top_curators(limit, days)

def get_daily_performance(curator_id, days=7):
    """Get daily breakdown of curator performance"""
    return rating_system.get_curator_daily_stats(curator_id, days)

logger.info("✅ Rating system initialized with Russian ratings (Великолепно/Хорошо/Нормально/Плохо/Ужасно)")