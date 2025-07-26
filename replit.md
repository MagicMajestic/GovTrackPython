# GovTracker2 Discord Curator Monitoring System

## Overview

This is a Discord bot monitoring system designed for the Russian roleplay community "Majestic RP SF". The application tracks curator activity across 8 Discord servers, monitors response times to help requests, and provides performance analytics. This is a complete migration from Node.js/TypeScript to Python 3.12/Flask while preserving all original functionality, algorithms, and data structures.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

The system follows a Flask-based web application architecture with the following key components:

### Backend Framework
- **Flask** - Main web framework serving both API endpoints and static files
- **SQLAlchemy** - ORM for database operations with PostgreSQL/MySQL compatibility
- **discord.py** - Discord bot integration replacing the original Discord.js implementation

### Database Design
- **Primary Database**: PostgreSQL (with MySQL compatibility built-in)
- **ORM**: SQLAlchemy with declarative base models
- **Connection Pooling**: Configured with pool recycling and health checks

### Bot Architecture
- **Discord Integration**: Single bot monitoring 8 servers simultaneously
- **Event-Driven**: Message, reaction, and response tracking
- **Background Processing**: APScheduler for automated tasks and backups

## Key Components

### Core Models
1. **Curators** - Curator profiles and activity tracking
2. **DiscordServers** - Server configuration and monitoring settings
3. **Activities** - Message, reaction, and interaction logging
4. **ResponseTracking** - Help request response time monitoring
5. **TaskReports** - Report verification system
6. **RatingSettings** - Performance threshold configuration

### Discord Bot Features
- **Keyword Detection**: Monitors for help requests using Russian and English keywords
- **Response Tracking**: Measures curator response times to help mentions
- **Activity Logging**: Records messages, reactions, and replies across all monitored servers
- **Role-Based Notifications**: Sends performance alerts to designated channels

### API System
- **Dashboard Statistics**: Real-time performance metrics
- **Curator Management**: CRUD operations for curator profiles
- **Activity Analytics**: Daily charts and recent activity feeds
- **Performance Leaderboards**: Top curator rankings

### Background Services
- **Automated Backups**: Scheduled database backups with retention policies
- **Notification System**: Reminder alerts for unanswered help requests
- **Maintenance Tasks**: Database cleanup and optimization

## Data Flow

### Activity Monitoring Flow
1. Discord bot receives message/reaction events
2. Content is analyzed for curator mentions and help keywords
3. Activity is logged to database with timestamp and metadata
4. Response tracking is initiated for help requests
5. Performance metrics are updated in real-time

### Rating Calculation Process
1. Activity points calculated based on message/reaction counts
2. Response time modifiers applied to base scores
3. Russian language ratings assigned (Великолепно, Хорошо, etc.)
4. Thresholds: 50+ (Excellent), 35+ (Good), 20+ (Normal), 10+ (Poor), 0+ (Terrible)

### Notification Pipeline
1. Unanswered help requests identified after 10-minute threshold
2. Notifications sent to designated Discord channel
3. Role-based tagging for appropriate curator groups
4. Escalation system for prolonged response delays

## External Dependencies

### Discord Integration
- **discord.py** - Official Discord API wrapper
- **Bot Token** - Required for Discord API authentication
- **Server IDs** - 8 monitored Discord servers with specific role configurations

### Database Systems
- **PostgreSQL** - Primary database (production recommended)
- **MySQL** - Alternative database option with full compatibility
- **Connection String** - Flexible DATABASE_URL environment variable

### Scheduling System
- **APScheduler** - Background task execution
- **Cron-style Scheduling** - Daily backups and maintenance windows

### Frontend Assets
- **React Build** - Static files served by Flask
- **Static File Serving** - All routes fallback to React SPA

## Deployment Strategy

### Environment Configuration
- **DATABASE_URL** - PostgreSQL/MySQL connection string
- **DISCORD_BOT_TOKEN** - Discord bot authentication
- **SESSION_SECRET** - Flask session security key
- **PORT** - Application port (defaults to 5000)

### Application Startup
1. **Flask Application** - Main web server initialization
2. **Discord Bot Thread** - Background Discord bot process
3. **Scheduler Thread** - Background task execution
4. **Database Migration** - Automatic table creation and seeding

### Database Compatibility
- PostgreSQL URL auto-correction for Heroku deployment
- MySQL support through SQLAlchemy dialect switching
- Connection pooling with automatic reconnection
- Backup/restore functionality for both database types

### Production Considerations
- **Static File Serving** - React build files served directly by Flask
- **CORS Configuration** - API endpoints accessible to frontend
- **Proxy Support** - ProxyFix middleware for reverse proxy deployments
- **Error Handling** - Comprehensive logging and error recovery

The system maintains complete feature parity with the original Node.js version while providing improved Python ecosystem integration and simplified deployment options.