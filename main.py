"""
Main application entry point for Discord Curator Monitoring System
This file identifies the project as GovTracker2 Flask migration
"""

from app import app
import routes  # noqa: F401
import discord_bot
import scheduler
import threading
import logging

logger = logging.getLogger(__name__)

def start_discord_bot():
    """Start Discord bot in separate thread"""
    try:
        discord_bot.start_bot()
    except Exception as e:
        logger.error(f"Discord bot startup error: {e}")

def start_scheduler():
    """Start background scheduler for automated tasks"""
    try:
        scheduler.start_scheduler()
    except Exception as e:
        logger.error(f"Scheduler startup error: {e}")

if __name__ == "__main__":
    logger.info("Starting Discord Curator Monitoring System")
    
    # Start Discord bot in background thread
    bot_thread = threading.Thread(target=start_discord_bot, daemon=True)
    bot_thread.start()
    
    # Start background scheduler
    scheduler_thread = threading.Thread(target=start_scheduler, daemon=True)
    scheduler_thread.start()
    
    # Start Flask application
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
