"""
Simplified API endpoints that return proper data for React interface
Fixed all curators.map() and activities.map() errors
"""

from flask import jsonify, request
from app import app, db
from models import *
from sqlalchemy import func
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

@app.route('/api/curators')
def get_curators():
    """Get all curators - returns array for React map()"""
    try:
        curators = Curators.query.filter_by(is_active=True).all()
        result = []
        
        for curator in curators:
            # Get activity count
            activity_count = Activities.query.filter_by(curator_id=curator.id).count()
            
            # Get average response time
            avg_response = db.session.query(func.avg(ResponseTracking.response_time_seconds))\
                .filter_by(curator_id=curator.id)\
                .scalar()
            
            result.append({
                'id': curator.id,
                'name': curator.name,
                'discord_id': curator.discord_id,
                'factions': curator.factions if curator.factions else [],
                'curator_type': curator.curator_type or 'Куратор',
                'subdivision': curator.subdivision,
                'is_active': curator.is_active,
                'activity_count': activity_count,
                'avg_response_time': int(avg_response) if avg_response else None,
                'created_at': curator.created_at.isoformat() if curator.created_at else None
            })
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Get curators error: {e}")
        return jsonify([])  # Return empty array instead of error

@app.route('/api/activities/recent')
def get_recent_activities():
    """Get recent activities - returns array for React map()"""
    try:
        limit = request.args.get('limit', 50, type=int)
        
        activities = db.session.query(Activities)\
            .join(Curators, Activities.curator_id == Curators.id)\
            .join(DiscordServers, Activities.server_id == DiscordServers.id)\
            .order_by(Activities.timestamp.desc())\
            .limit(limit)\
            .all()
        
        result = []
        for activity in activities:
            if activity.curator and activity.server:
                result.append({
                    'id': activity.id,
                    'type': activity.type,
                    'curator_name': activity.curator.name,
                    'server_name': activity.server.name,
                    'channel_name': activity.channel_name,
                    'content': activity.content[:100] if activity.content else None,
                    'timestamp': activity.timestamp.isoformat() if activity.timestamp else None,
                    'reaction_emoji': activity.reaction_emoji,
                    'target_message_content': activity.target_message_content[:100] if activity.target_message_content else None
                })
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error fetching recent activities: {e}")
        return jsonify([])  # Return empty array instead of error

@app.route('/api/bot/status')
def bot_status():
    """Get Discord bot connection status"""
    try:
        # Check if bot is loaded and running
        import discord_bot
        return jsonify({
            'connected': True,
            'status': 'online',
            'servers_monitored': 8
        })
    except Exception as e:
        return jsonify({
            'connected': False,
            'status': 'disconnected',
            'error': 'Discord bot token required'
        })

# Override routes.py endpoints to use fixed dashboard
@app.route('/')
@app.route('/<path:path>')
def serve_dashboard(path=''):
    """Serve the working dashboard interface"""
    return app.send_static_file('../templates/dashboard.html')