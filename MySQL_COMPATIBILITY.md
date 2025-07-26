# MySQL Compatibility Guide

**PROJECT IDENTIFIER:** GovTracker2 MySQL Migration Instructions

## Overview
This guide provides instructions for migrating the Discord Curator Monitoring System from PostgreSQL to MySQL while maintaining full functionality.

## Database Configuration Changes

### 1. Environment Variables
```bash
# PostgreSQL (current)
DATABASE_URL=postgresql://user:password@host:port/database

# MySQL (target)
DATABASE_URL=mysql+pymysql://user:password@host:port/database
