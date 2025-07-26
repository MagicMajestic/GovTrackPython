"""
Discord bot implementation for curator monitoring
Converted from Discord.js to discord.py with preserved functionality

PROJECT IDENTIFIER: Discord.py conversion of original govtracker2 bot logic
"""

import discord
from discord.ext import commands
import asyncio
import logging
import os
import re
from datetime import datetime
from sqlalchemy import and_
from app import app, db
from models import *
from utils import detect_mention_keywords, process_curator_response

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Bot configuration
BOT_TOKEN = os.environ.get('DISCORD_BOT_TOKEN')
if not BOT_TOKEN:
    logger.error("DISCORD_BOT_TOKEN not found in environment variables")

# Bot intents
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.guild_messages = True
intents.guild_reactions = True
intents.members = True

# Initialize bot
bot = commands.Bot(command_prefix='!', intents=intents)

# Server and role configuration (from original project)
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

NOTIFICATION_SERVER_ID = '805026457327108126'
NOTIFICATION_CHANNEL_ID = '974783377465036861'

# Role IDs for notifications
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

@bot.event
async def on_ready():
    """Bot startup event"""
    logger.info(f'{bot.user} has connected to Discord!')
    logger.info(f'Bot is in {len(bot.guilds)} guilds')
    
    # Initialize database servers
    await initialize_servers()

async def initialize_servers():
    """Initialize monitored servers in database"""
    try:
        with app.app_context():
            for server_id, server_name in MONITORED_SERVERS.items():
                existing_server = db.session.query(DiscordServers).filter(
                    DiscordServers.server_id == server_id
                ).first()
                
                if not existing_server:
                    new_server = DiscordServers()
                    new_server.server_id = server_id
                    new_server.name = server_name
                    new_server.is_active = True
                    db.session.add(new_server)
            
            db.session.commit()
            logger.info("Discord servers initialized in database")
    except Exception as e:
        logger.error(f"Server initialization error: {e}")

@bot.event
async def on_message(message):
    """Process messages for curator monitoring"""
    # Ignore bot messages
    if message.author.bot:
        return
    
    # Only monitor configured servers
    if str(message.guild.id) not in MONITORED_SERVERS:
        return
    
    try:
        with app.app_context():
            # Get server from database
            server = db.session.query(DiscordServers).filter(
                DiscordServers.server_id == str(message.guild.id)
            ).first()
            
            if not server or server.is_active == False:
                return
            
            # Check if author is a curator
            curator = db.session.query(Curators).filter(
                Curators.discord_id == str(message.author.id),
                Curators.is_active == True
            ).first()
            
            if curator:
                # Log curator activity
                await log_curator_activity(curator, server, message, 'message')
                
                # Check if this is a response to a tracked mention
                await process_curator_response(message, curator, server)
            
            # Check for mentions/help requests
            if detect_mention_keywords(message.content):
                await track_mention_request(message, server)
    
    except Exception as e:
        logger.error(f"Message processing error: {e}")

@bot.event
async def on_reaction_add(reaction, user):
    """Track curator reactions"""
    if user.bot:
        return
    
    if str(reaction.message.guild.id) not in MONITORED_SERVERS:
        return
    
    try:
        with app.app_context():
            server = db.session.query(DiscordServers).filter(
                DiscordServers.server_id == str(reaction.message.guild.id)
            ).first()
            
            curator = db.session.query(Curators).filter(
                Curators.discord_id == str(user.id),
                Curators.is_active == True
            ).first()
            
            if curator and server:
                # Log reaction activity
                await log_curator_reaction(curator, server, reaction)
                
                # Check if this is a response to tracked mention
                await process_reaction_response(reaction, curator, server)
    
    except Exception as e:
        logger.error(f"Reaction processing error: {e}")

async def log_curator_activity(curator, server, message, activity_type):
    """Log curator activity to database"""
    try:
        activity = Activities()
        activity.curator_id = curator.id
        activity.server_id = server.id
        activity.type = activity_type
        activity.channel_id = str(message.channel.id)
        activity.channel_name = message.channel.name
        activity.message_id = str(message.id)
        activity.content = message.content[:1000] if message.content else None
        activity.timestamp = message.created_at
        
        db.session.add(activity)
        db.session.commit()
        
        logger.debug(f"Logged {activity_type} activity for curator {curator.name}")
    except Exception as e:
        logger.error(f"Activity logging error: {e}")
        db.session.rollback()

async def log_curator_reaction(curator, server, reaction):
    """Log curator reaction activity"""
    try:
        activity = Activities()
        activity.curator_id = curator.id
        activity.server_id = server.id
        activity.type = 'reaction'
        activity.channel_id = str(reaction.message.channel.id)
        activity.channel_name = reaction.message.channel.name
        activity.message_id = str(reaction.message.id)
        activity.reaction_emoji = str(reaction.emoji)
        activity.target_message_id = str(reaction.message.id)
        activity.target_message_content = reaction.message.content[:500] if reaction.message.content else None
        activity.timestamp = datetime.now()
        
        db.session.add(activity)
        db.session.commit()
        
        logger.debug(f"Logged reaction activity for curator {curator.name}")
    except Exception as e:
        logger.error(f"Reaction logging error: {e}")
        db.session.rollback()

async def track_mention_request(message, server):
    """Track mention requests that need curator response"""
    try:
        # Create response tracking record
        tracking = ResponseTracking()
        tracking.server_id = server.id
        tracking.mention_message_id = str(message.id)
        tracking.mention_timestamp = message.created_at
        
        db.session.add(tracking)
        db.session.commit()
        
        logger.info(f"Tracking mention request in {server.name}: {message.content[:100]}")
        
        # Send notification to curator notification channel
        await send_curator_notification(message, server)
        
    except Exception as e:
        logger.error(f"Mention tracking error: {e}")
        db.session.rollback()

async def send_curator_notification(message, server):
    """Send notification to curator notification channel"""
    try:
        notification_channel = bot.get_channel(int(NOTIFICATION_CHANNEL_ID))
        if not notification_channel:
            logger.error("Notification channel not found")
            return
        
        # Check if channel supports sending messages
        if not hasattr(notification_channel, 'send'):
            logger.error("Channel does not support sending messages")
            return
        
        # Get appropriate role to mention
        server_name = server.name
        role_id = CURATOR_ROLES.get(server_name)
        
        if role_id:
            role_mention = f"<@&{role_id}>"
        else:
            role_mention = "@everyone"
        
        embed = discord.Embed(
            title="🔔 Запрос помощи куратора",
            description=f"**Сервер:** {server.name}\n**Канал:** {message.channel.name}\n**Автор:** {message.author.mention}",
            color=0xff6b6b,
            timestamp=message.created_at
        )
        
        embed.add_field(
            name="Сообщение",
            value=message.content[:1000] if message.content else "Нет текста",
            inline=False
        )
        
        embed.add_field(
            name="Ссылка",
            value=f"[Перейти к сообщению]({message.jump_url})",
            inline=False
        )
        
        await notification_channel.send(content=role_mention, embed=embed)
        
        logger.info(f"Notification sent for {server.name}")
        
    except Exception as e:
        logger.error(f"Notification sending error: {e}")

async def process_reaction_response(reaction, curator, server):
    """Process curator reaction as response to tracked mention"""
    try:
        # Find pending response tracking for this message
        tracking = db.session.query(ResponseTracking).filter(
            and_(
                ResponseTracking.server_id == server.id,
                ResponseTracking.mention_message_id == str(reaction.message.id),
                ResponseTracking.response_timestamp.is_(None)
            )
        ).first()
        
        if tracking:
            # Calculate response time
            response_time = (datetime.now() - tracking.mention_timestamp).total_seconds()
            
            # Update tracking record
            tracking.curator_id = curator.id
            tracking.response_message_id = str(reaction.message.id)
            tracking.response_timestamp = datetime.now()
            tracking.response_type = 'reaction'
            tracking.response_time_seconds = int(response_time)
            
            db.session.commit()
            
            logger.info(f"Curator {curator.name} responded with reaction in {response_time:.1f} seconds")
    
    except Exception as e:
        logger.error(f"Reaction response processing error: {e}")
        db.session.rollback()

def start_bot():
    """Start the Discord bot"""
    if not BOT_TOKEN:
        logger.error("Cannot start bot: DISCORD_BOT_TOKEN not provided")
        return
    
    try:
        bot.run(BOT_TOKEN)
    except Exception as e:
        logger.error(f"Bot startup error: {e}")

if __name__ == "__main__":
    start_bot()
