# Migration Notes - Node.js to Python Flask

**PROJECT IDENTIFIER:** GovTracker2 Discord Curator Monitoring System Migration

## Overview
Complete migration from Node.js/TypeScript to Python 3.12/Flask while preserving all functionality, algorithms, and data structures from the original govtracker2 system.

## Key Changes Made

### 1. Backend Framework Migration
- **From:** Express.js + TypeScript
- **To:** Flask + Python 3.12
- **Preserved:** All API endpoints, response formats, and business logic

### 2. Database Migration
- **From:** Drizzle ORM with PostgreSQL
- **To:** SQLAlchemy with PostgreSQL/MySQL compatibility
- **Preserved:** Complete schema structure, all tables, relationships, and data types

### 3. Discord Bot Migration
- **From:** Discord.js v14
- **To:** discord.py
- **Preserved:** All monitoring logic, event handlers, response tracking, and notification systems

### 4. Background Tasks Migration
- **From:** Node.js cron jobs
- **To:** APScheduler with BackgroundScheduler
- **Preserved:** Backup schedules, maintenance tasks, and notification timers

## Preserved Functionality

### Core Features ✅
- [x] Curator activity monitoring (messages, reactions, replies)
- [x] Response time tracking with exact timestamp calculations
- [x] Performance rating system with original thresholds
- [x] Discord server management and configuration
- [x] Task report verification system
- [x] Automated database backups
- [x] Real-time statistics and analytics
- [x] User authentication system

### API Endpoints ✅
All original endpoints preserved with identical functionality:
- `/api/dashboard/stats` - Dashboard statistics
- `/api/curators` - Curator management
- `/api/curators/:id/stats` - Individual curator statistics
- `/api/activities/recent` - Recent activity feed
- `/api/activities/daily` - Daily activity charts
- `/api/top-curators` - Performance leaderboard
- `/api/servers` - Discord server management
- `/api/response-tracking` - Response tracking status
- `/api/settings/bot` - Bot configuration

### Discord Bot Features ✅
- [x] Multi-server monitoring (8 Discord servers)
- [x] Keyword detection for help requests
- [x] Curator response tracking with real timestamps
- [x] Role-based notifications to curator channels
- [x] Activity logging (messages, reactions, replies)
- [x] Automatic curator assignment and response correlation

### Performance Calculations ✅
Preserved exact algorithms:
- **Rating System:** Великолепно (50+), Хорошо (35+), Нормально (20+), Плохо (10+), Ужасно (<10)
- **Activity Points:** Messages (3pts), Reactions (1pt), Replies (2pts), Task Verification (5pts)
- **Response Time Scoring:** <60s (excellent), >300s (poor)
- **Performance Modifiers:** Response time bonus/penalty system

## Technical Implementation

### Database Schema Compatibility
```python
# PostgreSQL Arrays converted to JSON for MySQL compatibility
factions = Column(JSON, nullable=False)  # Was: ARRAY in PostgreSQL

# Preserved all original table structures:
- curators (with factions, curator_type, subdivision)
- discord_servers (server_id, role_tag_id, completed_tasks_channel_id)
- activities (type, content, timestamp, reaction_emoji)
- response_tracking (mention_timestamp, response_timestamp, response_time_seconds)
- task_reports (task_count, approved_tasks, week_start)
