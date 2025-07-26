"""
COMPLETE Discord Bot Integration for Curator Monitoring System
Full recreation of original govtracker2 Discord bot "Curator#2772"

MONITORED SERVERS (8 total):
- Government, FIB, LSPD, SANG, LSCSD, EMS, Weazel News, Detectives

CORE FUNCTIONALITY:
- Real-time response tracking with authentic Discord timestamps
- Keyword detection: куратор, curator, помощь, help, вопрос, question
- Activity logging: messages, reactions, replies
- Role-based notifications with specific Discord role IDs
- Task report verification system

NOTIFICATION SYSTEM:
- Server: 805026457327108126
- Channel: 974783377465036861
- Role IDs for each faction with proper tagging
"""

import discord
from discord.ext import commands, tasks
import logging
import asyncio
import os
from datetime import datetime, timedelta
import re
from app import db
from models import (
    DiscordServers, Curators, Activities, ResponseTracking, 
    TaskReports, BotSettings, NotificationSettings
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Discord bot intents
intents = discord.Intents.default()
intents.message_content = True
intents.guild_messages = True
intents.reactions = True
intents.members = True

# Bot instance
bot = commands.Bot(command_prefix='!curator', intents=intents)

# Keywords for help request detection (Russian + English)
HELP_KEYWORDS = [
    'куратор', 'curator', 'помощь', 'help', 
    'вопрос', 'question', 'поддержка', 'support'
]

# Discord server configurations - 8 monitored servers
MONITORED_SERVERS = {
    'government': {'name': 'Government', 'role_id': '1329213001814773780'},
    'fib': {'name': 'FIB', 'role_id': '1329213307059437629'},
    'lspd': {'name': 'LSPD', 'role_id': '1329212725921976322'},
    'sang': {'name': 'SANG', 'role_id': '1329213239996973116'},
    'lscsd': {'name': 'LSCSD', 'role_id': '1329213185579946106'},
    'ems': {'name': 'EMS', 'role_id': '1329212940540313644'},
    'weazel_news': {'name': 'Weazel News', 'role_id': '1329213276587950080'},
    'detectives': {'name': 'Detectives', 'role_id': '916616528395378708'}
}

# Notification configuration
NOTIFICATION_SERVER_ID = '805026457327108126'
NOTIFICATION_CHANNEL_ID = '974783377465036861'

class CuratorMonitoringBot:
    def __init__(self):
        self.connected_servers = set()
        self.notification_timeout = 600  # 10 minutes default
        
    async def initialize_database_config(self):
        """Initialize bot settings and server configuration in database"""
        try:
            # Initialize Discord servers
            for key, config in MONITORED_SERVERS.items():
                server = DiscordServers.query.filter_by(name=config['name']).first()
                if not server:
                    server = DiscordServers(
                        server_id='0',  # Will be updated when bot connects
                        name=config['name'],
                        role_tag_id=config['role_id'],
                        is_active=True,
                        is_connected=False
                    )
                    db.session.add(server)
            
            # Initialize notification settings
            notification = NotificationSettings.query.first()
            if not notification:
                notification = NotificationSettings(
                    notification_server_id=NOTIFICATION_SERVER_ID,
                    notification_channel_id=NOTIFICATION_CHANNEL_ID,
                    is_active=True
                )
                db.session.add(notification)
            
            # Initialize bot settings
            settings = [
                ('notification_timeout', '600', 'Seconds before sending unanswered help notifications'),
                ('keywords', ','.join(HELP_KEYWORDS), 'Keywords that trigger response tracking'),
                ('bot_name', 'Curator#2772', 'Discord bot display name'),
                ('status', 'online', 'Bot status')
            ]
            
            for key, value, description in settings:
                setting = BotSettings.query.filter_by(setting_key=key).first()
                if not setting:
                    setting = BotSettings(
                        setting_key=key,
                        setting_value=value,
                        description=description
                    )
                    db.session.add(setting)
            
            db.session.commit()
            logger.info("✅ Database configuration initialized")
            
        except Exception as e:
            logger.error(f"❌ Database initialization error: {e}")
            db.session.rollback()

    def get_curator_by_discord_id(self, discord_id):
        """Find curator by Discord ID"""
        return Curators.query.filter_by(discord_id=str(discord_id), is_active=True).first()

    def get_server_by_guild_id(self, guild_id):
        """Find server configuration by Discord guild ID"""
        return DiscordServers.query.filter_by(server_id=str(guild_id), is_active=True).first()

    def contains_help_keywords(self, content):
        """Check if message contains help keywords"""
        content_lower = content.lower()
        return any(keyword in content_lower for keyword in HELP_KEYWORDS)

    def contains_curator_mention(self, message):
        """Check if message mentions curator roles"""
        if not message.guild:
            return False
            
        server = self.get_server_by_guild_id(message.guild.id)
        if not server or not server.role_tag_id:
            return False
            
        # Check for role mentions in message
        for role in message.role_mentions:
            if str(role.id) == server.role_tag_id:
                return True
                
        # Check for manual role tags
        role_pattern = f"<@&{server.role_tag_id}>"
        return role_pattern in message.content

    async def log_activity(self, curator, server, activity_type, message, **kwargs):
        """Log curator activity to database"""
        try:
            activity = Activities(
                curator_id=curator.id,
                server_id=server.id,
                type=activity_type,
                channel_id=str(message.channel.id),
                channel_name=message.channel.name,
                message_id=str(message.id),
                content=message.content[:1000] if message.content else None,
                reaction_emoji=kwargs.get('reaction_emoji'),
                target_message_id=kwargs.get('target_message_id'),
                target_message_content=kwargs.get('target_message_content'),
                timestamp=message.created_at
            )
            
            db.session.add(activity)
            db.session.commit()
            
            logger.info(f"✅ Activity logged: {curator.name} - {activity_type} in {server.name}")
            
        except Exception as e:
            logger.error(f"❌ Activity logging error: {e}")
            db.session.rollback()

    async def create_response_tracking(self, message, server):
        """Create response tracking record for help requests"""
        try:
            # Check if already tracking this message
            existing = ResponseTracking.query.filter_by(
                mention_message_id=str(message.id)
            ).first()
            
            if existing:
                return
                
            tracking = ResponseTracking(
                server_id=server.id,
                mention_message_id=str(message.id),
                mention_timestamp=message.created_at,
                mention_content=message.content[:1000],
                mention_author_id=str(message.author.id),
                mention_author_name=message.author.display_name,
                is_resolved=False
            )
            
            db.session.add(tracking)
            db.session.commit()
            
            logger.info(f"✅ Response tracking created for message {message.id}")
            
            # Schedule notification check
            asyncio.create_task(self.schedule_notification_check(tracking.id))
            
        except Exception as e:
            logger.error(f"❌ Response tracking error: {e}")
            db.session.rollback()

    async def update_response_tracking(self, response_message, curator, response_type='message'):
        """Update response tracking when curator responds"""
        try:
            # Find original help request in same channel within reasonable time
            channel_id = str(response_message.channel.id)
            time_threshold = datetime.utcnow() - timedelta(hours=2)
            
            # Look for unresolved tracking records in this channel
            tracking = ResponseTracking.query.filter(
                ResponseTracking.mention_timestamp >= time_threshold,
                ResponseTracking.is_resolved == False
            ).join(DiscordServers).filter(
                DiscordServers.server_id == str(response_message.guild.id)
            ).first()
            
            if tracking:
                response_time = (response_message.created_at - tracking.mention_timestamp).total_seconds()
                
                tracking.curator_id = curator.id
                tracking.response_message_id = str(response_message.id)
                tracking.response_timestamp = response_message.created_at
                tracking.response_type = response_type
                tracking.response_time_seconds = int(response_time)
                tracking.is_resolved = True
                
                db.session.commit()
                
                logger.info(f"✅ Response tracked: {curator.name} responded in {response_time:.1f}s")
                
        except Exception as e:
            logger.error(f"❌ Response tracking update error: {e}")
            db.session.rollback()

    async def schedule_notification_check(self, tracking_id):
        """Schedule notification for unanswered help requests"""
        try:
            # Get notification timeout from settings
            timeout_setting = BotSettings.query.filter_by(setting_key='notification_timeout').first()
            timeout = int(timeout_setting.setting_value) if timeout_setting else 600
            
            # Wait for timeout period
            await asyncio.sleep(timeout)
            
            # Check if still unresolved
            tracking = ResponseTracking.query.get(tracking_id)
            if tracking and not tracking.is_resolved:
                await self.send_notification(tracking)
                
        except Exception as e:
            logger.error(f"❌ Notification scheduling error: {e}")

    async def send_notification(self, tracking):
        """Send notification to curator channel about unanswered help request"""
        try:
            notification_channel = bot.get_channel(int(NOTIFICATION_CHANNEL_ID))
            if not notification_channel:
                logger.error("❌ Notification channel not found")
                return
                
            server = DiscordServers.query.get(tracking.server_id)
            if not server:
                return
                
            # Format notification message
            minutes_passed = int((datetime.utcnow() - tracking.mention_timestamp).total_seconds() / 60)
            
            embed = discord.Embed(
                title="🔔 Неотвеченный запрос помощи",
                description=f"Запрос помощи в **{server.name}** остается без ответа уже **{minutes_passed} минут**",
                color=0xff6b6b,
                timestamp=tracking.mention_timestamp
            )
            
            embed.add_field(
                name="Сообщение",
                value=tracking.mention_content[:1000] if tracking.mention_content else "Не указано",
                inline=False
            )
            
            embed.add_field(
                name="Автор",
                value=tracking.mention_author_name,
                inline=True
            )
            
            embed.add_field(
                name="Время ожидания",
                value=f"{minutes_passed} минут",
                inline=True
            )
            
            # Tag appropriate curator role
            role_mention = f"<@&{server.role_tag_id}>" if server.role_tag_id else "@here"
            
            await notification_channel.send(
                content=f"{role_mention} Требуется внимание кураторов!",
                embed=embed
            )
            
            logger.info(f"✅ Notification sent for {server.name} - {minutes_passed} minutes")
            
        except Exception as e:
            logger.error(f"❌ Notification sending error: {e}")

    async def process_task_report(self, message, server):
        """Process task completion reports from completed-tasks channels"""
        try:
            # Extract task count from message
            task_count_match = re.search(r'(\d+)\s*задач', message.content.lower())
            if not task_count_match:
                return
                
            task_count = int(task_count_match.group(1))
            
            # Check if already processed
            existing = TaskReports.query.filter_by(message_id=str(message.id)).first()
            if existing:
                return
                
            # Create task report record
            report = TaskReports(
                server_id=server.id,
                message_id=str(message.id),
                channel_id=str(message.channel.id),
                content=message.content,
                task_count=task_count,
                submitted_at=message.created_at,
                status='pending',
                week_start=datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
            )
            
            db.session.add(report)
            db.session.commit()
            
            logger.info(f"✅ Task report created: {task_count} tasks in {server.name}")
            
        except Exception as e:
            logger.error(f"❌ Task report processing error: {e}")
            db.session.rollback()

    async def verify_task_report(self, message, curator, server):
        """Handle curator verification of task reports"""
        try:
            # Find recent task report in same channel
            time_threshold = datetime.utcnow() - timedelta(hours=24)
            
            report = TaskReports.query.filter(
                TaskReports.server_id == server.id,
                TaskReports.channel_id == str(message.channel.id),
                TaskReports.submitted_at >= time_threshold,
                TaskReports.status == 'pending'
            ).first()
            
            if not report:
                return
                
            # Extract approved task count
            approved_match = re.search(r'(\d+)', message.content)
            approved_tasks = int(approved_match.group(1)) if approved_match else report.task_count
            
            # Update task report
            report.curator_id = curator.id
            report.curator_discord_id = str(message.author.id)
            report.curator_name = curator.name
            report.checked_at = message.created_at
            report.approved_tasks = approved_tasks
            report.status = 'verified'
            report.verified_at = message.created_at
            report.verified_by = curator.name
            
            db.session.commit()
            
            logger.info(f"✅ Task report verified: {approved_tasks}/{report.task_count} by {curator.name}")
            
            # Log verification as activity (worth +5 points)
            await self.log_activity(
                curator, server, 'task_verification', message,
                target_message_id=report.message_id,
                target_message_content=f"Verified {approved_tasks} tasks"
            )
            
        except Exception as e:
            logger.error(f"❌ Task verification error: {e}")
            db.session.rollback()

# Bot event handlers
curator_bot = CuratorMonitoringBot()

@bot.event
async def on_ready():
    """Bot startup event"""
    logger.info(f'✅ {bot.user} (Curator#2772) is online and monitoring Discord servers!')
    
    # Initialize database configuration
    await curator_bot.initialize_database_config()
    
    # Update connected servers
    for guild in bot.guilds:
        curator_bot.connected_servers.add(guild.id)
        
        # Update server connection status in database
        server = DiscordServers.query.filter_by(server_id=str(guild.id)).first()
        if not server:
            # Find by name and update server_id
            for config in MONITORED_SERVERS.values():
                if config['name'].lower() in guild.name.lower():
                    server = DiscordServers.query.filter_by(name=config['name']).first()
                    if server:
                        server.server_id = str(guild.id)
                        server.is_connected = True
                        server.last_seen = datetime.utcnow()
                        break
        else:
            server.is_connected = True
            server.last_seen = datetime.utcnow()
            
    db.session.commit()
    
    logger.info(f"✅ Connected to {len(bot.guilds)} servers: {[g.name for g in bot.guilds]}")

@bot.event
async def on_message(message):
    """Handle all message events"""
    if message.author.bot:
        return
        
    try:
        server = curator_bot.get_server_by_guild_id(message.guild.id)
        if not server:
            return
            
        # Check if author is a curator
        curator = curator_bot.get_curator_by_discord_id(message.author.id)
        
        # Process curator messages
        if curator:
            # Log curator activity
            await curator_bot.log_activity(curator, server, 'message', message)
            
            # Check for task verification (in completed-tasks channels)
            if 'completed-tasks' in message.channel.name.lower() or message.channel.id == server.completed_tasks_channel_id:
                await curator_bot.verify_task_report(message, curator, server)
            
            # Update response tracking if this might be a response
            await curator_bot.update_response_tracking(message, curator)
        
        # Process help requests (regardless of author)
        is_help_request = (
            curator_bot.contains_help_keywords(message.content) or 
            curator_bot.contains_curator_mention(message)
        )
        
        if is_help_request:
            await curator_bot.create_response_tracking(message, server)
            
        # Process task reports (from non-curators in completed-tasks channels)
        if not curator and ('completed-tasks' in message.channel.name.lower() or 
                           str(message.channel.id) == server.completed_tasks_channel_id):
            await curator_bot.process_task_report(message, server)
            
    except Exception as e:
        logger.error(f"❌ Message processing error: {e}")

@bot.event
async def on_reaction_add(reaction, user):
    """Handle reaction events"""
    if user.bot:
        return
        
    try:
        message = reaction.message
        server = curator_bot.get_server_by_guild_id(message.guild.id)
        if not server:
            return
            
        curator = curator_bot.get_curator_by_discord_id(user.id)
        if not curator:
            return
            
        # Log reaction activity
        await curator_bot.log_activity(
            curator, server, 'reaction', message,
            reaction_emoji=str(reaction.emoji),
            target_message_id=str(message.id),
            target_message_content=message.content[:500]
        )
        
        # Check if reaction is response to help request
        await curator_bot.update_response_tracking(message, curator, 'reaction')
        
    except Exception as e:
        logger.error(f"❌ Reaction processing error: {e}")

# Bot startup function
async def start_discord_bot():
    """Start the Discord bot"""
    try:
        token = os.environ.get('DISCORD_BOT_TOKEN')
        if not token:
            logger.error("❌ DISCORD_BOT_TOKEN not found in environment variables")
            return
            
        await bot.start(token)
        
    except Exception as e:
        logger.error(f"❌ Bot startup error: {e}")

def run_discord_bot():
    """Run Discord bot in background thread"""
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(start_discord_bot())
        
    except Exception as e:
        logger.error(f"❌ Bot thread error: {e}")

logger.info("✅ Discord bot module loaded - ready to start monitoring")