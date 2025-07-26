"""
API routes for Discord Curator Monitoring System
Preserves all original endpoints from Node.js main-routes.ts

PROJECT IDENTIFIER: Flask conversion of all govtracker2 API endpoints
"""

from flask import jsonify, request, send_from_directory
from app import app, db
from models import *
from sqlalchemy import func, desc, and_, or_
from datetime import datetime, timedelta
from utils import calculate_performance_rating, get_curator_statistics
import logging
import os

logger = logging.getLogger(__name__)

# Serve working dashboard
@app.route('/')
@app.route('/<path:path>')
def serve_frontend(path=''):
    """Serve working dashboard interface"""
    if path == '' or path.startswith('api/'):
        # Serve the dashboard HTML file directly
        with open('templates/dashboard.html', 'r', encoding='utf-8') as f:
            return f.read()
    
    # For other paths, try static files first
    static_folder = app.static_folder or 'static/build'
    if path and os.path.exists(os.path.join(static_folder, path)):
        return send_from_directory(static_folder, path)
    
    # Fallback to dashboard
    with open('templates/dashboard.html', 'r', encoding='utf-8') as f:
        return f.read()

# API Routes - preserving all original functionality

@app.route('/api/dashboard/stats')
def dashboard_stats():
    """Main dashboard statistics - equivalent to original endpoint"""
    try:
        # Total curators
        total_curators = db.session.query(func.count(Curators.id)).filter(Curators.is_active == True).scalar()
        
        # Active servers
        active_servers = db.session.query(func.count(DiscordServers.id)).filter(DiscordServers.is_active == True).scalar()
        
        # Today's activities
        today = datetime.now().date()
        today_activities = db.session.query(func.count(Activities.id)).filter(
            func.date(Activities.timestamp) == today
        ).scalar()
        
        # Pending response tracking
        pending_responses = db.session.query(func.count(ResponseTracking.id)).filter(
            ResponseTracking.response_timestamp.is_(None)
        ).scalar()
        
        # Average response time (in minutes)
        avg_response_time = db.session.query(func.avg(ResponseTracking.response_time_seconds)).filter(
            ResponseTracking.response_time_seconds.isnot(None)
        ).scalar()
        
        if avg_response_time:
            avg_response_time = round(avg_response_time / 60, 1)  # Convert to minutes
        else:
            avg_response_time = 0
        
        return jsonify({
            'totalCurators': total_curators or 0,
            'activeServers': active_servers or 0,
            'todayActivities': today_activities or 0,
            'pendingResponses': pending_responses or 0,
            'avgResponseTime': avg_response_time
        })
    except Exception as e:
        logger.error(f"Dashboard stats error: {e}")
        return jsonify({'error': 'Failed to fetch dashboard statistics'}), 500

@app.route('/api/curators')
def get_curators():
    """Get all curators with performance ratings"""
    try:
        curators = db.session.query(Curators).filter(Curators.is_active == True).all()
        
        curator_list = []
        for curator in curators:
            # Get curator statistics
            stats = get_curator_statistics(curator.id)
            rating = calculate_performance_rating(stats['total_activities'], stats['avg_response_time'])
            
            curator_data = {
                'id': curator.id,
                'discordId': curator.discord_id,
                'name': curator.name,
                'factions': curator.factions if isinstance(curator.factions, list) else [],
                'curatorType': curator.curator_type,
                'subdivision': curator.subdivision,
                'isActive': curator.is_active,
                'performance': rating,
                'totalActivities': stats['total_activities'],
                'avgResponseTime': stats['avg_response_time']
            }
            curator_list.append(curator_data)
        
        return jsonify(curator_list)
    except Exception as e:
        logger.error(f"Get curators error: {e}")
        return jsonify({'error': 'Failed to fetch curators'}), 500

@app.route('/api/curators/<int:curator_id>/stats')
def curator_detailed_stats(curator_id):
    """Detailed statistics for specific curator"""
    try:
        curator = db.session.query(Curators).filter(Curators.id == curator_id).first()
        if not curator:
            return jsonify({'error': 'Curator not found'}), 404
        
        # Get comprehensive statistics
        stats = get_curator_statistics(curator_id, detailed=True)
        
        # Recent activities (last 50)
        recent_activities = db.session.query(Activities).filter(
            Activities.curator_id == curator_id
        ).order_by(desc(Activities.timestamp)).limit(50).all()
        
        activities_data = []
        for activity in recent_activities:
            activities_data.append({
                'id': activity.id,
                'type': activity.type,
                'channelName': activity.channel_name,
                'content': activity.content[:200] if activity.content else None,
                'timestamp': activity.timestamp.isoformat() if activity.timestamp else None
            })
        
        return jsonify({
            'curator': {
                'id': curator.id,
                'name': curator.name,
                'discordId': curator.discord_id,
                'factions': curator.factions,
                'curatorType': curator.curator_type
            },
            'statistics': stats,
            'recentActivities': activities_data
        })
    except Exception as e:
        logger.error(f"Curator detailed stats error: {e}")
        return jsonify({'error': 'Failed to fetch curator statistics'}), 500

@app.route('/api/activities/recent')
def recent_activities():
    """Recent activity feed across all curators"""
    try:
        limit = request.args.get('limit', 100, type=int)
        
        activities = db.session.query(
            Activities, Curators.name.label('curator_name'), DiscordServers.name.label('server_name')
        ).join(
            Curators, Activities.curator_id == Curators.id
        ).join(
            DiscordServers, Activities.server_id == DiscordServers.id
        ).order_by(desc(Activities.timestamp)).limit(limit).all()
        
        activity_list = []
        for activity, curator_name, server_name in activities:
            activity_list.append({
                'id': activity.id,
                'type': activity.type,
                'curatorName': curator_name,
                'serverName': server_name,
                'channelName': activity.channel_name,
                'content': activity.content[:150] if activity.content else None,
                'timestamp': activity.timestamp.isoformat() if activity.timestamp else None
            })
        
        return jsonify(activity_list)
    except Exception as e:
        logger.error(f"Recent activities error: {e}")
        return jsonify({'error': 'Failed to fetch recent activities'}), 500

@app.route('/api/activities/daily')
def daily_activities():
    """Daily activity statistics for charts"""
    try:
        days = request.args.get('days', 7, type=int)
        start_date = datetime.now() - timedelta(days=days)
        
        # Query daily activity counts
        daily_stats = db.session.query(
            func.date(Activities.timestamp).label('date'),
            func.count(Activities.id).label('count')
        ).filter(
            Activities.timestamp >= start_date
        ).group_by(
            func.date(Activities.timestamp)
        ).order_by('date').all()
        
        chart_data = []
        for stat in daily_stats:
            chart_data.append({
                'date': stat.date.isoformat(),
                'activities': stat.count
            })
        
        return jsonify(chart_data)
    except Exception as e:
        logger.error(f"Daily activities error: {e}")
        return jsonify({'error': 'Failed to fetch daily activities'}), 500

@app.route('/api/top-curators')
def top_curators():
    """Top performing curators leaderboard"""
    try:
        limit = request.args.get('limit', 10, type=int)
        
        # Get curators with activity counts
        curator_stats = db.session.query(
            Curators,
            func.count(Activities.id).label('activity_count'),
            func.avg(ResponseTracking.response_time_seconds).label('avg_response_time')
        ).outerjoin(
            Activities, Curators.id == Activities.curator_id
        ).outerjoin(
            ResponseTracking, Curators.id == ResponseTracking.curator_id
        ).filter(
            Curators.is_active == True
        ).group_by(Curators.id).all()
        
        # Calculate performance ratings and sort
        leaderboard = []
        for curator, activity_count, avg_response_time in curator_stats:
            rating = calculate_performance_rating(activity_count or 0, avg_response_time or 0)
            
            leaderboard.append({
                'id': curator.id,
                'name': curator.name,
                'factions': curator.factions,
                'activityCount': activity_count or 0,
                'avgResponseTime': round(avg_response_time / 60, 1) if avg_response_time else 0,
                'performance': rating
            })
        
        # Sort by performance score
        leaderboard.sort(key=lambda x: x['performance']['score'], reverse=True)
        
        return jsonify(leaderboard[:limit])
    except Exception as e:
        logger.error(f"Top curators error: {e}")
        return jsonify({'error': 'Failed to fetch top curators'}), 500

@app.route('/api/servers')
def get_servers():
    """Get all monitored Discord servers"""
    try:
        servers = db.session.query(DiscordServers).all()
        
        server_list = []
        for server in servers:
            # Count activities for this server
            activity_count = db.session.query(func.count(Activities.id)).filter(
                Activities.server_id == server.id
            ).scalar()
            
            server_list.append({
                'id': server.id,
                'serverId': server.server_id,
                'name': server.name,
                'roleTagId': server.role_tag_id,
                'completedTasksChannelId': server.completed_tasks_channel_id,
                'isActive': server.is_active,
                'activityCount': activity_count or 0
            })
        
        return jsonify(server_list)
    except Exception as e:
        logger.error(f"Get servers error: {e}")
        return jsonify({'error': 'Failed to fetch servers'}), 500

@app.route('/api/response-tracking')
def response_tracking():
    """Current response tracking status"""
    try:
        # Pending responses
        pending = db.session.query(
            ResponseTracking, Curators.name.label('curator_name'), DiscordServers.name.label('server_name')
        ).outerjoin(
            Curators, ResponseTracking.curator_id == Curators.id
        ).join(
            DiscordServers, ResponseTracking.server_id == DiscordServers.id
        ).filter(
            ResponseTracking.response_timestamp.is_(None)
        ).order_by(desc(ResponseTracking.mention_timestamp)).all()
        
        pending_list = []
        for response, curator_name, server_name in pending:
            time_elapsed = (datetime.now() - response.mention_timestamp).total_seconds() / 60  # minutes
            
            pending_list.append({
                'id': response.id,
                'serverName': server_name,
                'curatorName': curator_name or 'Unassigned',
                'mentionTimestamp': response.mention_timestamp.isoformat(),
                'timeElapsed': round(time_elapsed, 1)
            })
        
        return jsonify(pending_list)
    except Exception as e:
        logger.error(f"Response tracking error: {e}")
        return jsonify({'error': 'Failed to fetch response tracking'}), 500

@app.route('/api/settings/bot', methods=['GET', 'POST'])
def bot_settings():
    """Bot configuration settings"""
    try:
        if request.method == 'GET':
            settings = db.session.query(BotSettings).all()
            settings_dict = {setting.setting_key: setting.setting_value for setting in settings}
            return jsonify(settings_dict)
        
        elif request.method == 'POST':
            data = request.json or {}
            for key, value in data.items():
                setting = db.session.query(BotSettings).filter(BotSettings.setting_key == key).first()
                if setting:
                    setting.setting_value = str(value)
                    setting.updated_at = datetime.now()
                else:
                    new_setting = BotSettings()
                    new_setting.setting_key = key
                    new_setting.setting_value = str(value)
                    new_setting.updated_at = datetime.now()
                    db.session.add(new_setting)
            
            db.session.commit()
            return jsonify({'success': True})
    except Exception as e:
        logger.error(f"Bot settings error: {e}")
        return jsonify({'error': 'Failed to handle bot settings'}), 500

# CRUD routes for servers
@app.route('/api/servers', methods=['POST'])
def create_server():
    """Create new Discord server"""
    try:
        data = request.json
        if not data or not data.get('serverId') or not data.get('name'):
            return jsonify({'error': 'Server ID and name are required'}), 400
        
        existing_server = db.session.query(DiscordServers).filter(
            DiscordServers.server_id == data['serverId']
        ).first()
        
        if existing_server:
            return jsonify({'error': 'Server already exists'}), 409
        
        server = DiscordServers()
        server.server_id = data['serverId']
        server.name = data['name']
        server.role_tag_id = data.get('roleTagId')
        server.completed_tasks_channel_id = data.get('completedTasksChannelId')
        server.is_active = data.get('isActive', True)
        
        db.session.add(server)
        db.session.commit()
        
        return jsonify({'success': True, 'id': server.id}), 201
    except Exception as e:
        logger.error(f"Create server error: {e}")
        return jsonify({'error': 'Failed to create server'}), 500

@app.route('/api/servers/<int:server_id>', methods=['PUT'])
def update_server(server_id):
    """Update Discord server"""
    try:
        server = db.session.query(DiscordServers).filter(DiscordServers.id == server_id).first()
        if not server:
            return jsonify({'error': 'Server not found'}), 404
        
        data = request.json or {}
        if 'name' in data:
            server.name = data['name']
        if 'roleTagId' in data:
            server.role_tag_id = data['roleTagId']
        if 'completedTasksChannelId' in data:
            server.completed_tasks_channel_id = data['completedTasksChannelId']
        if 'isActive' in data:
            server.is_active = data['isActive']
        
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        logger.error(f"Update server error: {e}")
        return jsonify({'error': 'Failed to update server'}), 500

@app.route('/api/servers/<int:server_id>', methods=['DELETE'])
def delete_server(server_id):
    """Delete Discord server"""
    try:
        server = db.session.query(DiscordServers).filter(DiscordServers.id == server_id).first()
        if not server:
            return jsonify({'error': 'Server not found'}), 404
        
        db.session.delete(server)
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        logger.error(f"Delete server error: {e}")
        return jsonify({'error': 'Failed to delete server'}), 500

# CRUD routes for curators
@app.route('/api/curators', methods=['POST'])
def create_curator():
    """Create new curator"""
    try:
        data = request.json
        if not data or not data.get('discordId') or not data.get('name'):
            return jsonify({'error': 'Discord ID and name are required'}), 400
        
        existing_curator = db.session.query(Curators).filter(
            Curators.discord_id == data['discordId']
        ).first()
        
        if existing_curator:
            return jsonify({'error': 'Curator already exists'}), 409
        
        curator = Curators()
        curator.discord_id = data['discordId']
        curator.name = data['name']
        curator.factions = data.get('factions', [])
        curator.curator_type = data.get('curatorType', 'moderator')
        curator.subdivision = data.get('subdivision')
        curator.is_active = data.get('isActive', True)
        
        db.session.add(curator)
        db.session.commit()
        
        return jsonify({'success': True, 'id': curator.id}), 201
    except Exception as e:
        logger.error(f"Create curator error: {e}")
        return jsonify({'error': 'Failed to create curator'}), 500

@app.route('/api/curators/<int:curator_id>', methods=['PUT'])
def update_curator(curator_id):
    """Update curator"""
    try:
        curator = db.session.query(Curators).filter(Curators.id == curator_id).first()
        if not curator:
            return jsonify({'error': 'Curator not found'}), 404
        
        data = request.json or {}
        if 'name' in data:
            curator.name = data['name']
        if 'factions' in data:
            curator.factions = data['factions']
        if 'curatorType' in data:
            curator.curator_type = data['curatorType']
        if 'subdivision' in data:
            curator.subdivision = data['subdivision']
        if 'isActive' in data:
            curator.is_active = data['isActive']
        
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        logger.error(f"Update curator error: {e}")
        return jsonify({'error': 'Failed to update curator'}), 500

@app.route('/api/curators/<int:curator_id>', methods=['DELETE'])
def delete_curator(curator_id):
    """Delete curator"""
    try:
        curator = db.session.query(Curators).filter(Curators.id == curator_id).first()
        if not curator:
            return jsonify({'error': 'Curator not found'}), 404
        
        db.session.delete(curator)
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        logger.error(f"Delete curator error: {e}")
        return jsonify({'error': 'Failed to delete curator'}), 500

# Task Reports CRUD
@app.route('/api/task-reports', methods=['GET'])
def get_task_reports():
    """Get all task reports with pagination"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        
        reports_query = db.session.query(TaskReports).order_by(TaskReports.id.desc())
        total = reports_query.count()
        reports = reports_query.offset((page-1)*per_page).limit(per_page).all()
        
        return jsonify({
            'reports': [{
                'id': report.id,
                'curatorId': report.curator_id,
                'curatorName': getattr(report.curator, 'name', 'Unknown') if hasattr(report, 'curator') else 'Unknown',
                'serverId': report.server_id,
                'serverName': getattr(report.server, 'name', 'Unknown') if hasattr(report, 'server') else 'Unknown',
                'taskType': getattr(report, 'task_type', ''),
                'description': getattr(report, 'description', ''),
                'evidence': getattr(report, 'evidence', ''),
                'status': getattr(report, 'status', 'pending'),
                'createdAt': getattr(report, 'created_at', datetime.now()).isoformat(),
                'verifiedAt': getattr(report, 'verified_at', None).isoformat() if getattr(report, 'verified_at', None) else None,
                'verifiedBy': getattr(report, 'verified_by', None)
            } for report in reports],
            'pagination': {
                'page': page,
                'pages': (total + per_page - 1) // per_page,
                'per_page': per_page,
                'total': total
            }
        })
    except Exception as e:
        logger.error(f"Get task reports error: {e}")
        return jsonify({'error': 'Failed to fetch task reports'}), 500

@app.route('/api/task-reports', methods=['POST'])
def create_task_report():
    """Create new task report"""
    try:
        data = request.json
        if not data or not all(k in data for k in ['curatorId', 'serverId', 'taskType', 'description']):
            return jsonify({'error': 'Missing required fields'}), 400
        
        report = TaskReports()
        report.curator_id = data['curatorId']
        report.server_id = data['serverId']
        if hasattr(report, 'task_type'):
            report.task_type = data['taskType']
        if hasattr(report, 'description'):  
            report.description = data['description']
        if hasattr(report, 'evidence'):
            report.evidence = data.get('evidence')
        if hasattr(report, 'status'):
            report.status = data.get('status', 'pending')
        if hasattr(report, 'created_at'):
            report.created_at = datetime.now()
        
        db.session.add(report)
        db.session.commit()
        
        return jsonify({'success': True, 'id': report.id}), 201
    except Exception as e:
        logger.error(f"Create task report error: {e}")
        return jsonify({'error': 'Failed to create task report'}), 500

@app.route('/api/task-reports/<int:report_id>', methods=['PUT'])
def update_task_report(report_id):
    """Update task report"""
    try:
        report = db.session.query(TaskReports).filter(TaskReports.id == report_id).first()
        if not report:
            return jsonify({'error': 'Task report not found'}), 404
        
        data = request.json or {}
        
        if 'description' in data and hasattr(report, 'description'):
            report.description = data['description']
        if 'evidence' in data and hasattr(report, 'evidence'):
            report.evidence = data['evidence']
        if 'status' in data and hasattr(report, 'status'):
            report.status = data['status']
            if data['status'] == 'verified':
                if hasattr(report, 'verified_at'):
                    report.verified_at = datetime.now()
                if hasattr(report, 'verified_by'):
                    report.verified_by = data.get('verifiedBy', 'system')
        
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        logger.error(f"Update task report error: {e}")
        return jsonify({'error': 'Failed to update task report'}), 500

@app.route('/api/task-reports/<int:report_id>', methods=['DELETE'])
def delete_task_report(report_id):
    """Delete task report"""
    try:
        report = db.session.query(TaskReports).filter(TaskReports.id == report_id).first()
        if not report:
            return jsonify({'error': 'Task report not found'}), 404
        
        db.session.delete(report)
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        logger.error(f"Delete task report error: {e}")
        return jsonify({'error': 'Failed to delete task report'}), 500

# Settings API
@app.route('/api/settings/rating', methods=['GET', 'POST'])
def rating_settings():
    """Rating system settings"""
    try:
        if request.method == 'GET':
            settings = db.session.query(RatingSettings).order_by(RatingSettings.min_score.desc()).all()
            config = db.session.query(GlobalRatingConfig).first()
            
            return jsonify({
                'ratings': [{
                    'id': setting.id,
                    'name': setting.rating_name,
                    'text': setting.rating_text,
                    'minScore': setting.min_score,
                    'color': setting.color
                } for setting in settings],
                'config': {
                    'activityPointsMessage': config.activity_points_message if config else 3,
                    'activityPointsReaction': config.activity_points_reaction if config else 1,
                    'activityPointsReply': config.activity_points_reply if config else 2,
                    'activityPointsTaskVerification': config.activity_points_task_verification if config else 5,
                    'responseTimeGoodSeconds': config.response_time_good_seconds if config else 60,
                    'responseTimePoorSeconds': config.response_time_poor_seconds if config else 300
                } if config else {}
            })
        
        elif request.method == 'POST':
            data = request.json or {}
            
            # Update global config
            if 'config' in data:
                config = db.session.query(GlobalRatingConfig).first()
                if not config:
                    config = GlobalRatingConfig()
                    db.session.add(config)
                
                config_data = data['config']
                config.activity_points_message = config_data.get('activityPointsMessage', 3)
                config.activity_points_reaction = config_data.get('activityPointsReaction', 1)
                config.activity_points_reply = config_data.get('activityPointsReply', 2)
                config.activity_points_task_verification = config_data.get('activityPointsTaskVerification', 5)
                config.response_time_good_seconds = config_data.get('responseTimeGoodSeconds', 60)
                config.response_time_poor_seconds = config_data.get('responseTimePoorSeconds', 300)
            
            # Update ratings
            if 'ratings' in data:
                for rating_data in data['ratings']:
                    if 'id' in rating_data:
                        # Update existing
                        rating = db.session.query(RatingSettings).filter(RatingSettings.id == rating_data['id']).first()
                        if rating:
                            rating.rating_name = rating_data.get('name', rating.rating_name)
                            rating.rating_text = rating_data.get('text', rating.rating_text)
                            rating.min_score = rating_data.get('minScore', rating.min_score)
                            rating.color = rating_data.get('color', rating.color)
                    else:
                        # Create new
                        rating = RatingSettings()
                        rating.rating_name = rating_data['name']
                        rating.rating_text = rating_data['text']
                        rating.min_score = rating_data['minScore']
                        rating.color = rating_data['color']
                        db.session.add(rating)
            
            db.session.commit()
            return jsonify({'success': True})
    except Exception as e:
        logger.error(f"Rating settings error: {e}")
        return jsonify({'error': 'Failed to handle rating settings'}), 500

# Backup & Restore API
@app.route('/api/backup/create', methods=['POST'])
def create_backup_api():
    """Create database backup"""
    try:
        from backup_service import create_backup
        result = create_backup()
        return jsonify(result)
    except Exception as e:
        logger.error(f"Backup creation error: {e}")
        return jsonify({'error': 'Failed to create backup'}), 500

@app.route('/api/backup/list', methods=['GET'])
def list_backups():
    """List available backups"""
    try:
        import os
        backup_dir = 'backups'
        if not os.path.exists(backup_dir):
            return jsonify({'backups': []})
        
        backups = []
        for filename in os.listdir(backup_dir):
            if filename.endswith('.json.gz'):
                filepath = os.path.join(backup_dir, filename)
                stat = os.stat(filepath)
                backups.append({
                    'filename': filename,
                    'size': stat.st_size,
                    'created': datetime.fromtimestamp(stat.st_mtime).isoformat()
                })
        
        backups.sort(key=lambda x: x['created'], reverse=True)
        return jsonify({'backups': backups})
    except Exception as e:
        logger.error(f"List backups error: {e}")
        return jsonify({'error': 'Failed to list backups'}), 500

@app.route('/api/backup/restore', methods=['POST'])
def restore_backup_api():
    """Restore from backup"""
    try:
        data = request.json
        if not data or not data.get('filename'):
            return jsonify({'error': 'Backup filename required'}), 400
        
        from backup_service import restore_backup
        result = restore_backup(data['filename'])
        return jsonify(result)
    except Exception as e:
        logger.error(f"Backup restore error: {e}")
        return jsonify({'error': 'Failed to restore backup'}), 500

# System status and health check
@app.route('/api/system/status', methods=['GET'])
def system_status():
    """Get system status"""
    try:
        return jsonify({
            'status': 'healthy',
            'version': '2.0.0',
            'database': 'connected',
            'discordBot': 'error' if 'DISCORD_BOT_TOKEN' not in os.environ else 'connected',
            'uptime': 'running',
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"System status error: {e}")
        return jsonify({'error': 'Failed to get system status'}), 500

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/bot/status')
def bot_status():
    """Get Discord bot connection status"""
    try:
        bot_token = os.environ.get('DISCORD_BOT_TOKEN')
        return jsonify({
            'connected': bot_token is not None,
            'status': 'connected' if bot_token else 'token_required'
        })
    except Exception as e:
        logger.error(f"Bot status error: {e}")
        return jsonify({'connected': False, 'status': 'error'}), 500

logger.info("All API routes registered successfully")
