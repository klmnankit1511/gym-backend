# Database Backup and Volume Management

This guide covers backing up, restoring, and managing database volumes for your Gym Manager API.

## Quick Reference

```bash
# Create a backup
./scripts/backup-db.sh local ./backups

# Restore from backup
./scripts/restore-db.sh local ./backups/gym_db_backup_local_20240101_120000.bak

# View volume information
docker volume ls | grep gym

# Download Docker volume (advanced)
./scripts/backup-db.sh local ./backups
```

## Automatic Dummy Data

When you start the local environment with `./scripts/docker-run.sh local up`, the database is automatically populated with dummy data including:

- **3 Tenants**: FitZone Gym, PowerLift Studios, Yoga Haven
- **4 Branches**: Multiple locations per tenant
- **6 Users**: Admins, managers, trainers, staff
- **8 Members**: Sample gym members with complete profiles
- **5 Membership Plans**: Various pricing tiers
- **8 Active Memberships**: Members with active subscriptions
- **8 Payment Records**: Transaction history
- **8 Attendance Records**: Check-in/check-out history

## Tables Created

### Core Tables (Existing)
- `tenants` - Multi-tenant organizations
- `branches` - Gym locations
- `users` - System users
- `roles` - User roles (admin, manager, trainer, staff, member)
- `user_roles` - User-role assignments

### Gym-Specific Tables (Created on First Run)
- `members` - Gym members with personal information
- `membership_plans` - Plan types and pricing
- `memberships` - Active/inactive memberships
- `payments` - Payment records
- `attendance` - Check-in/check-out logs

## Local Database Backup

### Creating a Backup

```bash
# Backup with default location (current directory)
./scripts/backup-db.sh local

# Backup to specific directory
./scripts/backup-db.sh local ./backups

# Manual backup using docker
docker exec gym-db-local \
  /opt/mssql-tools18/bin/sqlcmd -S localhost -U sa -P GymAdmin@123! -Q \
  "BACKUP DATABASE [gym] TO DISK = N'/var/opt/mssql/backup/gym_backup.bak'"
```

### Backup File Format

- **Filename**: `gym_db_backup_local_YYYYMMDD_HHMMSS.bak`
- **Example**: `gym_db_backup_local_20240125_143022.bak`
- **Size**: Typically 1-5 MB with dummy data
- **Format**: Native SQL Server .bak format

### Restoring a Backup

```bash
# Restore with prompt confirmation
./scripts/restore-db.sh local ./gym_db_backup_local_20240125_143022.bak

# Automatic restore (no prompt)
./scripts/restore-db.sh local ./gym_db_backup_local_20240125_143022.bak << EOF
y
EOF
```

## Docker Volume Management

### View Volumes

```bash
# List all volumes
docker volume ls

# Inspect a specific volume
docker volume inspect gym-sqlserver_data

# View volume location on host
docker volume inspect gym-sqlserver_data -f '{{.Mountpoint}}'
```

### Backup Volume (Manual)

```bash
# Stop the container
./scripts/docker-run.sh local down

# Backup the volume data
docker run --rm \
  -v gym-backend_sqlserver_data:/data \
  -v $(pwd)/backups:/backup \
  alpine tar czf /backup/volume_backup.tar.gz -C /data .

# Restart the container
./scripts/docker-run.sh local up
```

### Restore Volume (Manual)

```bash
# Stop the container
./scripts/docker-run.sh local down

# Remove old volume (CAREFUL!)
docker volume rm gym-backend_sqlserver_data

# Create new volume and restore
docker volume create gym-backend_sqlserver_data

docker run --rm \
  -v gym-backend_sqlserver_data:/data \
  -v $(pwd)/backups:/backup \
  alpine tar xzf /backup/volume_backup.tar.gz -C /data

# Restart the container
./scripts/docker-run.sh local up
```

## Database Size

- **Empty Database**: ~100 MB
- **With Dummy Data**: ~100 MB
- **Volume Allocation**: 5 GB default

### Checking Database Size

```bash
# In SQL Server
docker exec gym-db-local \
  /opt/mssql-tools18/bin/sqlcmd -S localhost -U sa -P GymAdmin@123! -Q \
  "EXEC sp_spaceused @updateusage = N'TRUE';"
```

## Export Data as CSV/JSON

### Export to CSV

```bash
docker exec gym-db-local \
  /opt/mssql-tools18/bin/sqlcmd -S localhost -U sa -P GymAdmin@123! \
  -d gym \
  -Q "SELECT * FROM members" \
  -o members.csv -s ',' -W
```

### Export to JSON (via Python)

```python
import pyodbc
import json
from datetime import datetime, date

conn_str = "Driver={ODBC Driver 18 for SQL Server};Server=localhost;Database=gym;UID=sa;PWD=GymAdmin@123!;"
conn = pyodbc.connect(conn_str)
cursor = conn.cursor()

# Query data
cursor.execute("SELECT * FROM members")
columns = [desc[0] for desc in cursor.description]
rows = cursor.fetchall()

# Convert to JSON (handling datetime)
data = []
for row in rows:
    row_dict = {}
    for i, col in enumerate(columns):
        value = row[i]
        if isinstance(value, (datetime, date)):
            value = value.isoformat()
        row_dict[col] = value
    data.append(row_dict)

# Save to file
with open('members.json', 'w') as f:
    json.dump(data, f, indent=2)

conn.close()
```

## Scheduled Backups

### Linux/macOS (using cron)

```bash
# Add to crontab: crontab -e
# Daily backup at 2 AM
0 2 * * * cd /Users/ankitkumar/Documents/gym-backend && ./scripts/backup-db.sh local ./backups

# Weekly backup on Sunday at 3 AM
0 3 * * 0 cd /Users/ankitkumar/Documents/gym-backend && ./scripts/backup-db.sh local ./backups/weekly
```

### Docker Compose (scheduled via container)

You can add a backup service to docker-compose:

```yaml
backup-service:
  image: mcr.microsoft.com/mssql/server:2022-latest
  container_name: gym-db-backup
  depends_on:
    - db
  volumes:
    - ./backups:/backups
  command: |
    bash -c "
    while true; do
      /opt/mssql-tools18/bin/sqlcmd -S db -U sa -P ${SQL_PASSWORD} -Q \
      'BACKUP DATABASE [gym] TO DISK = N'\''/backups/gym_backup_\$(date +%Y%m%d_%H%M%S).bak'\'''
      sleep 86400
    done
    "
  networks:
    - gym-network
```

## Disaster Recovery

### Total Data Loss Recovery

1. **Stop all containers**:
   ```bash
   ./scripts/docker-run.sh local down
   ```

2. **Remove the corrupted volume**:
   ```bash
   docker volume rm gym-backend_sqlserver_data
   ```

3. **Restart containers** (creates fresh volume):
   ```bash
   ./scripts/docker-run.sh local up
   ```

4. **Restore from backup**:
   ```bash
   ./scripts/restore-db.sh local ./gym_db_backup_local_20240125_143022.bak
   ```

### Incremental Backups

For production, use SQL Server maintenance plans:

```bash
docker exec gym-db-local \
  /opt/mssql-tools18/bin/sqlcmd -S localhost -U sa -P GymAdmin@123! -Q \
  "BACKUP LOG [gym] TO DISK = N'/var/opt/mssql/backup/gym_incremental.bak'"
```

## Best Practices

1. **Backup Frequency**
   - Development: Weekly
   - Staging: Daily
   - Production: Hourly (via Azure managed backups)

2. **Retention Policy**
   - Keep last 7 daily backups
   - Keep last 4 weekly backups
   - Keep last 12 monthly backups

3. **Testing**
   - Test restores monthly
   - Document recovery procedures
   - Maintain recovery playbooks

4. **Security**
   - Store backups securely
   - Encrypt backup files for production
   - Track backup access logs

5. **Monitoring**
   - Alert on failed backups
   - Monitor backup file sizes
   - Verify backup integrity

## Troubleshooting

### Backup Command Fails

```bash
# Check container is running
docker ps | grep gym-db-local

# Check SQL Server logs
docker logs gym-db-local

# Try manual backup with full output
docker exec gym-db-local /opt/mssql-tools18/bin/sqlcmd \
  -S localhost -U sa -P GymAdmin@123! \
  -Q "BACKUP DATABASE [gym] TO DISK = N'/var/opt/mssql/backup/gym_backup.bak'"
```

### Restore Fails

```bash
# Ensure database is accessible
docker exec gym-db-local /opt/mssql-tools18/bin/sqlcmd \
  -S localhost -U sa -P GymAdmin@123! -Q "SELECT 1"

# Check backup file integrity
ls -lh ./gym_db_backup_local_*.bak

# Verify file is readable inside container
docker exec gym-db-local ls -lh /var/opt/mssql/backup/
```

## Related Commands

```bash
# Clean up old backups (keep last 10)
ls -1t backups/gym_db_backup_local_*.bak | tail -n +11 | xargs rm -f

# Compress backups
tar czf backups.tar.gz backups/

# Check backup sizes
du -sh backups/gym_db_backup_local_*.bak

# View database integrity
docker exec gym-db-local /opt/mssql-tools18/bin/sqlcmd \
  -S localhost -U sa -P GymAdmin@123! -Q "DBCC CHECKDB (gym)"
```
