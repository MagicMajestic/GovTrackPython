# MySQL Configuration for GovTracker2

## Environment Variables for MySQL

To use MySQL instead of PostgreSQL, set one of these environment variables:

```bash
# Option 1: MySQL URL
MYSQL_URL=mysql://username:password@host:port/database_name

# Option 2: MySQL Database URL
MYSQL_DATABASE_URL=mysql://username:password@host:port/database_name

# Option 3: Standard DATABASE_URL with MySQL
DATABASE_URL=mysql://username:password@host:port/database_name
```

## MySQL Connection Examples

### Local MySQL
```bash
DATABASE_URL=mysql://root:password@localhost:3306/govtracker2
```

### MySQL on Remote Server
```bash
DATABASE_URL=mysql://user:pass@mysql.example.com:3306/govtracker2
```

### MySQL with SSL
```bash
DATABASE_URL=mysql://user:pass@host:3306/govtracker2?ssl=true
```

## MySQL Requirements

1. **MySQL Version**: 5.7+ or MySQL 8.0+
2. **Required Python Package**: `PyMySQL` (already included in dependencies)
3. **Character Set**: UTF-8 support for Russian text
4. **Timezone**: Configure MySQL to handle timezone-aware datetimes

## Database Creation

```sql
CREATE DATABASE govtracker2 
CHARACTER SET utf8mb4 
COLLATE utf8mb4_unicode_ci;

CREATE USER 'govtracker2'@'%' IDENTIFIED BY 'secure_password';
GRANT ALL PRIVILEGES ON govtracker2.* TO 'govtracker2'@'%';
FLUSH PRIVILEGES;
```

## MySQL-Specific Features

The application automatically detects MySQL and adjusts:

1. **Text Storage**: Uses TEXT for long content instead of PostgreSQL's unlimited text
2. **JSON Fields**: Uses JSON type for MySQL 5.7+ or TEXT for older versions  
3. **DateTime**: Handles both timezone-aware and naive datetimes
4. **Character Encoding**: Properly handles Russian Cyrillic characters

## Migration from PostgreSQL

To migrate from PostgreSQL to MySQL:

1. Export data from PostgreSQL
2. Set MySQL environment variables
3. Restart the application
4. Tables will be created automatically
5. Import data using backup/restore functionality

The application maintains full compatibility between both database systems.