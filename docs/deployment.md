# Production Deployment Guide

**For**: System administrators and DevOps engineers

This guide covers deploying the classifier system to production environments.

## Table of Contents

1. [Pre-Deployment Checklist](#pre-deployment-checklist)
2. [Database Setup](#database-setup)
3. [Environment Configuration](#environment-configuration)
4. [Application Deployment](#application-deployment)
5. [Performance Tuning](#performance-tuning)
6. [Monitoring and Alerting](#monitoring-and-alerting)
7. [Backup and Disaster Recovery](#backup-and-disaster-recovery)
8. [Troubleshooting](#troubleshooting)

---

## Pre-Deployment Checklist

Before deploying to production, verify the following:

- [ ] PostgreSQL 12+ is installed and running
- [ ] Python 3.8+ is available
- [ ] All required environment variables are configured
- [ ] Database user has appropriate permissions
- [ ] Database backups are scheduled
- [ ] Monitoring and alerting are configured
- [ ] Log rotation is set up
- [ ] Firewall rules allow necessary connections
- [ ] SSL/TLS certificates are valid (for remote connections)
- [ ] All tests pass: `pytest tests/ --cov=src/classifier`
- [ ] Code review completed and approved
- [ ] Deployment plan documented
- [ ] Rollback plan documented

---

## Database Setup

### 1. Create Database User

```bash
# Connect as PostgreSQL superuser
sudo -u postgres psql

-- Create application user
CREATE USER classifier_prod WITH PASSWORD 'secure_password_here';

-- Create database
CREATE DATABASE classifier_prod;

-- Grant permissions
GRANT CONNECT ON DATABASE classifier_prod TO classifier_prod;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO classifier_prod;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT USAGE ON SEQUENCES TO classifier_prod;
```

### 2. Apply Migrations

```bash
# Configure environment
export DB_HOST=localhost
export DB_PORT=5432
export DB_NAME=classifier_prod
export DB_USER=classifier_prod
export DB_PASSWORD=secure_password_here

# Run migrations
cd /opt/classifier
python3 -m classifier.utils --init-db

# Verify migrations
python3 -m classifier.utils --verify-db
```

### 3. Create Backup User (Recommended)

```sql
-- Create read-only backup user
CREATE USER classifier_backup WITH PASSWORD 'backup_password';
GRANT CONNECT ON DATABASE classifier_prod TO classifier_backup;
GRANT USAGE ON SCHEMA public TO classifier_backup;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO classifier_backup;
```

### 4. Configure PostgreSQL for Production

Edit `/etc/postgresql/12/main/postgresql.conf`:

```ini
# Performance tuning
max_connections = 200
shared_buffers = 256MB
effective_cache_size = 1GB
maintenance_work_mem = 64MB
checkpoint_completion_target = 0.9
wal_buffers = 16MB
default_statistics_target = 100
random_page_cost = 1.1
effective_io_concurrency = 200
work_mem = 4MB
min_wal_size = 1GB
max_wal_size = 4GB

# Logging
logging_collector = on
log_directory = 'pg_log'
log_filename = 'postgresql-%Y-%m-%d_%H%M%S.log'
log_truncate_on_rotation = on
log_rotation_age = 1d
log_rotation_size = 100MB
log_min_duration_statement = 100  # Log queries slower than 100ms
log_connections = on
log_disconnections = on
log_statement = 'mod'

# Security
ssl = on
ssl_cert_file = '/path/to/server.crt'
ssl_key_file = '/path/to/server.key'
password_encryption = scram-sha-256
```

Restart PostgreSQL:
```bash
sudo systemctl restart postgresql
```

---

## Environment Configuration

### 1. Create Production .env File

Create `/opt/classifier/.env`:

```env
# Database
DB_HOST=db-prod.example.com
DB_PORT=5432
DB_NAME=classifier_prod
DB_USER=classifier_prod
DB_PASSWORD=your_secure_password_here
DB_CONNECTION_TIMEOUT=30

# Application
APP_ENV=production
APP_LOG_LEVEL=INFO
ENABLE_RULE_CACHING=true
ENABLE_AUDIT_LOGGING=true

# Performance
RULE_CACHE_TTL=3600  # 1 hour
MAX_CONNECTIONS=10
```

### 2. Set File Permissions

```bash
# Restrict .env file access
chmod 600 /opt/classifier/.env
chown classifier:classifier /opt/classifier/.env

# Create logs directory
mkdir -p /var/log/classifier
chmod 755 /var/log/classifier
chown classifier:classifier /var/log/classifier
```

### 3. Use Secrets Management (Recommended)

For production, use a secrets manager instead of .env:

```python
# Example: Using AWS Secrets Manager
import json
import boto3

def get_db_password():
    """Retrieve database password from AWS Secrets Manager"""
    client = boto3.client('secretsmanager')
    secret = client.get_secret_value(SecretId='classifier-prod/db-password')
    return json.loads(secret['SecretString'])['password']
```

---

## Application Deployment

### 1. Install Package

```bash
# Clone repository
git clone https://github.com/yourcompany/classifier.git /opt/classifier
cd /opt/classifier

# Create virtual environment
python3 -m venv /opt/classifier/venv

# Activate virtual environment
source /opt/classifier/venv/bin/activate

# Install package
pip install -e .
pip install -r requirements.txt
```

### 2. Systemd Service Unit

Create `/etc/systemd/system/classifier.service`:

```ini
[Unit]
Description=Classifier Rule Engine
After=network.target postgresql.service

[Service]
Type=simple
User=classifier
Group=classifier
WorkingDirectory=/opt/classifier
Environment="PATH=/opt/classifier/venv/bin"
EnvironmentFile=/opt/classifier/.env
ExecStart=/opt/classifier/venv/bin/python3 -m classifier.api
Restart=on-failure
RestartSec=10
StandardOutput=journal
StandardError=journal

# Resource limits
MemoryLimit=512M
CPUQuota=50%

[Install]
WantedBy=multi-user.target
```

### 3. Start Service

```bash
# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable classifier
sudo systemctl start classifier

# Check status
sudo systemctl status classifier

# View logs
sudo journalctl -u classifier -f
```

### 4. Nginx Reverse Proxy (If Using API)

Create `/etc/nginx/sites-available/classifier`:

```nginx
upstream classifier {
    server 127.0.0.1:8000;
    keepalive 32;
}

server {
    listen 443 ssl http2;
    server_name classifier.example.com;

    ssl_certificate /etc/letsencrypt/live/classifier.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/classifier.example.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    location / {
        proxy_pass http://classifier;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
}

# Redirect HTTP to HTTPS
server {
    listen 80;
    server_name classifier.example.com;
    return 301 https://$server_name$request_uri;
}
```

Enable site:
```bash
sudo ln -s /etc/nginx/sites-available/classifier /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

---

## Performance Tuning

### 1. Database Indexing

Create optimal indexes for production:

```sql
-- Index for rule loading (most common query)
CREATE INDEX idx_regras_ativo_prioridade
ON regras_de_classificacao(ativo, prioridade DESC, data_criacao ASC)
WHERE ativo = true;

-- Index for audit log queries by product
CREATE INDEX idx_auditoria_produto_data
ON auditoria_classificacao(id_produto, data_classificacao DESC);

-- Index for audit log queries by rule
CREATE INDEX idx_auditoria_regra_data
ON auditoria_classificacao(id_regra, data_classificacao DESC);

-- Index for no-match queries
CREATE INDEX idx_auditoria_no_match
ON auditoria_classificacao(id_regra, data_classificacao)
WHERE id_regra IS NULL;

-- ANALYZE tables
ANALYZE regras_de_classificacao;
ANALYZE auditoria_classificacao;
```

### 2. Connection Pooling

Use PgBouncer for connection pooling:

```bash
# Install pgbouncer
sudo apt-get install pgbouncer

# Configure /etc/pgbouncer/pgbouncer.ini
```

```ini
[databases]
classifier_prod = host=localhost port=5432 dbname=classifier_prod

[pgbouncer]
pool_mode = transaction
max_client_conn = 1000
default_pool_size = 20
min_pool_size = 10
reserve_pool_size = 5
reserve_pool_timeout = 3
max_db_connections = 100
server_lifetime = 3600
server_idle_timeout = 600
```

Start PgBouncer:
```bash
sudo systemctl start pgbouncer
sudo systemctl enable pgbouncer
```

Update connection string to use PgBouncer:
```env
DB_HOST=localhost
DB_PORT=6432  # PgBouncer default port
```

### 3. Query Optimization

Monitor and optimize slow queries:

```sql
-- Find slow queries
SELECT
    query,
    calls,
    total_time,
    mean_time
FROM pg_stat_statements
WHERE mean_time > 100
ORDER BY mean_time DESC
LIMIT 20;

-- Reset statistics
SELECT pg_stat_statements_reset();
```

### 4. Caching Configuration

Update application config for caching:

```python
# In src/classifier/engine.py
class RuleEngine:
    CACHE_TTL = 3600  # 1 hour - adjust based on rule change frequency

    def get_rules(self):
        # Rules are cached to reduce database hits
        # Update TTL in production based on your needs
        pass
```

### 5. Load Testing

Benchmark performance:

```bash
# Load test (requires Apache Bench)
ab -n 10000 -c 50 http://classifier.example.com/api/evaluate

# Expected results:
# - Requests/sec: > 1000 (depends on hardware)
# - 95th percentile response time: < 500ms
```

---

## Monitoring and Alerting

### 1. Application Monitoring

Set up monitoring for:

```python
# In application code, track these metrics
metrics = {
    'evaluation_time_ms': result.evaluation_time_ms,
    'rule_matched': result.success,
    'classification': result.classification,
}

# Ship to monitoring system (e.g., DataDog, New Relic)
```

### 2. Database Monitoring

Monitor PostgreSQL:

```sql
-- Monitor active connections
SELECT datname, usename, state, count(*)
FROM pg_stat_activity
GROUP BY datname, usename, state;

-- Check for long-running queries
SELECT
    pid,
    now() - query_start as duration,
    query
FROM pg_stat_activity
WHERE state != 'idle'
AND query_start < now() - interval '1 minute';

-- Monitor table sizes
SELECT schemaname, tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
FROM pg_tables
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

### 3. Alerting Rules

Configure alerts for:

```yaml
# Example Prometheus alert rules
groups:
  - name: classifier
    rules:
      - alert: ClassifierHighEvaluationTime
        expr: classifier_evaluation_time_p95 > 500
        for: 5m
        annotations:
          summary: "Classifier evaluation time is high (> 500ms)"

      - alert: ClassifierHighNoMatchRate
        expr: classifier_no_match_rate > 0.1
        for: 15m
        annotations:
          summary: "More than 10% of products are not matching any rule"

      - alert: PostgreSQLDown
        expr: pg_up == 0
        for: 1m
        annotations:
          summary: "PostgreSQL is down"

      - alert: PostgreSQLHighConnections
        expr: pg_stat_activity_count > 180
        for: 5m
        annotations:
          summary: "PostgreSQL connection count is high (> 180)"
```

---

## Backup and Disaster Recovery

### 1. Automated Daily Backups

Create `/opt/backup/backup_classifier.sh`:

```bash
#!/bin/bash

BACKUP_DIR="/opt/backups"
DB_NAME="classifier_prod"
DB_USER="classifier_backup"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="${BACKUP_DIR}/classifier_${TIMESTAMP}.sql.gz"

# Create backup
pg_dump -h localhost -U $DB_USER -d $DB_NAME | gzip > $BACKUP_FILE

# Verify backup
if [ -f $BACKUP_FILE ] && [ -s $BACKUP_FILE ]; then
    echo "✓ Backup successful: $BACKUP_FILE"

    # Keep only last 30 days
    find $BACKUP_DIR -name "classifier_*.sql.gz" -mtime +30 -delete
else
    echo "✗ Backup failed!"
    exit 1
fi
```

Schedule with cron:

```bash
# Add to crontab (0 2 AM daily)
0 2 * * * /opt/backup/backup_classifier.sh >> /var/log/backup.log 2>&1
```

### 2. Restore from Backup

```bash
# Decompress backup
gunzip classifier_20250115_020000.sql.gz

# Restore to database
psql -h localhost -U classifier_prod -d classifier_prod < classifier_20250115_020000.sql

# Verify restore
psql -h localhost -U classifier_prod -d classifier_prod -c "SELECT COUNT(*) FROM regras_de_classificacao;"
```

### 3. Point-in-Time Recovery

PostgreSQL WAL archiving enables point-in-time recovery:

```ini
# In postgresql.conf
wal_level = replica
archive_mode = on
archive_command = 'test ! -f /archive/%f && cp %p /archive/%f'
```

---

## Troubleshooting

### Issue: Service Won't Start

Check logs:
```bash
sudo journalctl -u classifier -n 50
```

Verify configuration:
```bash
python3 -c "from classifier.utils import load_config; print(load_config())"
```

### Issue: Slow Evaluations

Check metrics:
```sql
SELECT id_regra, AVG(tempo_avaliacao_ms) as avg_time
FROM auditoria_classificacao
WHERE data_classificacao > NOW() - INTERVAL '1 hour'
GROUP BY id_regra
ORDER BY avg_time DESC;
```

Optimize:
- Deactivate unused rules
- Add database indexes
- Increase PostgreSQL memory

### Issue: Database Out of Disk Space

Archive old audit entries:
```sql
-- Archive entries older than 1 year
CREATE TABLE auditoria_classificacao_archive_2024 AS
SELECT * FROM auditoria_classificacao
WHERE EXTRACT(YEAR FROM data_classificacao) = 2024;

DELETE FROM auditoria_classificacao
WHERE EXTRACT(YEAR FROM data_classificacao) = 2024;

VACUUM ANALYZE auditoria_classificacao;
```

### Issue: High Database Load

Increase connection pool size:
```ini
# In pgbouncer.ini
default_pool_size = 30  # Increase from 20
```

Enable query caching:
```bash
# Add Redis caching (optional)
pip install redis
```

---

## Security Best Practices

1. **Use HTTPS/TLS**: Encrypt all connections to the application
2. **Use VPN/Firewall**: Restrict database access to application servers only
3. **Rotate Credentials**: Change passwords every 90 days
4. **Monitor Access**: Enable and review database logs
5. **Backup Security**: Encrypt backups and store off-site
6. **Code Review**: Review all deployments before production
7. **Patch Management**: Keep PostgreSQL and Python updated
8. **Rate Limiting**: Implement rate limits on API endpoints

---

## Scaling Strategies

### Horizontal Scaling

For multiple application instances:

```nginx
# Load balance across multiple instances
upstream classifier {
    server 127.0.0.1:8000;
    server 127.0.0.1:8001;
    server 127.0.0.1:8002;
    keepalive 32;
}
```

### Vertical Scaling

Increase resources if single instance is overloaded:
- PostgreSQL: Increase memory, disk, CPU
- Application: Increase connection pool size
- Operating System: Increase file descriptors, memory

### Caching

Use Redis for rule caching in high-throughput scenarios:

```python
# Example: Redis-backed caching
import redis

cache = redis.Redis(host='localhost', port=6379, db=0)

def get_rules():
    rules = cache.get('classifier:rules')
    if not rules:
        rules = load_rules_from_db()
        cache.setex('classifier:rules', 3600, rules)
    return rules
```

---

## Maintenance

### Weekly

- Monitor database size
- Check error rates
- Review slow query log
- Verify backups completed

### Monthly

- Analyze database statistics
- Review rule effectiveness
- Check disk usage trends
- Test backup restoration

### Quarterly

- Update dependencies
- Review security logs
- Performance benchmarking
- Disaster recovery drill

---

## Support

For deployment issues:
1. Check `/var/log/classifier/` application logs
2. Check PostgreSQL logs: `/var/log/postgresql/`
3. Run health checks: `python3 -m classifier.utils --verify-db`
4. Review TROUBLESHOOTING.md for common issues

