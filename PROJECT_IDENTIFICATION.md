# Project Identification Document

**CRITICAL: This document identifies this project for future development sessions**

## Project Identity
- **Project Name:** GovTracker2 Discord Curator Monitoring System
- **Original Repository:** https://github.com/MagicMajestic/govtracker2
- **Migration Type:** Node.js/TypeScript → Python 3.12/Flask
- **Purpose:** Discord bot monitoring system for Russian roleplay community "Majestic RP SF"

## Key Recognition Markers

### 1. Project Scope Identifiers
If you see these elements, you are working with the GovTracker2 Flask migration:
- **Discord Bot Name:** "Curator#2772"
- **Monitored Servers:** 8 Discord servers (Government, FIB, LSPD, SANG, LSCSD, EMS, Weazel News, Detectives)
- **Database Tables:** curators, discord_servers, activities, response_tracking, task_reports
- **Rating System:** Russian language (Великолепно, Хорошо, Нормально, Плохо, Ужасно)
- **Performance Thresholds:** 50+, 35+, 20+, 10+, 0+ points

### 2. Technical Stack Identifiers
- **Backend:** Python 3.12 + Flask + SQLAlchemy
- **Database:** PostgreSQL (MySQL-ready)
- **Discord Integration:** discord.py
- **Scheduler:** APScheduler
- **Original Frontend:** React (served statically by Flask)

### 3. Core Functionality Identifiers
- **Response Tracking:** Monitors curator response times to help requests
- **Activity Monitoring:** Messages, reactions, replies across Discord servers
- **Keyword Detection:** 'куратор', 'curator', 'помощь', 'help', etc.
- **Notification System:** Role-based Discord notifications
- **Performance Ratings:** Activity-based scoring with response time modifiers

## Original Request Context
The user requested:
> "Мне нужно чтобы ты переписал моё приложение с Node.js & Typescript на python 3.12. Все функции, каждая страница, все алгоритмы, формулы, расчеты, все данные должны сохраниться, это очень важно!"

**Translation:** "I need you to rewrite my application from Node.js & TypeScript to Python 3.12. All functions, every page, all algorithms, formulas, calculations, all data must be preserved, this is very important!"

## File Structure Recognition
## This project was generated and migrated by Replit Agent.
## Internal project key: GOVTRACKER2_PYTHON_MIGRATION