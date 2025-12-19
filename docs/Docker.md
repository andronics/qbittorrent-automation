# qbt-rules Docker Deployment Guide

Complete guide for deploying qbt-rules using Docker.

## Table of Contents

- [Quick Start](#quick-start)
- [Installation](#installation)
- [Configuration](#configuration)
- [Deployment Scenarios](#deployment-scenarios)
- [Queue Backends](#queue-backends)
- [Secrets Management](#secrets-management)
- [Networking](#networking)
- [Monitoring](#monitoring)
- [Troubleshooting](#troubleshooting)
- [Advanced Topics](#advanced-topics)

## Quick Start

### Minimal Setup (SQLite Queue)

1. **Create directory structure**:
   ```bash
   mkdir -p qbt-rules/config
   cd qbt-rules
   ```

2. **Create config files**:
   ```bash
   # Download default configs
   wget -O config/config.yml https://raw.githubusercontent.com/andronics/qbt-rules/main/config/config.default.yml
   wget -O config/rules.yml https://raw.githubusercontent.com/andronics/qbt-rules/main/config/rules.default.yml
   ```

3. **Edit configuration**:
   ```bash
   nano config/config.yml
   # Update qBittorrent host, username, password
   # Set server API key
   ```

4. **Create docker-compose.yml**:
   ```yaml
   version: '3.8'
   services:
     qbt-rules:
       image: ghcr.io/andronics/qbt-rules:latest
       container_name: qbt-rules
       restart: unless-stopped
       ports:
         - "5000:5000"
       volumes:
         - ./config:/config
       environment:
         QBT_RULES_SERVER_API_KEY: "change-this-secret-key"
         QBT_RULES_QBITTORRENT_HOST: "http://qbittorrent:8080"
         QBT_RULES_QBITTORRENT_USERNAME: "admin"
         QBT_RULES_QBITTORRENT_PASSWORD: "adminpass"
   ```

5. **Start container**:
   ```bash
   docker-compose up -d
   ```

6. **Verify health**:
   ```bash
   curl http://localhost:5000/api/health
   ```

## Installation

### Pull from GitHub Container Registry

```bash
# Latest stable version
docker pull ghcr.io/andronics/qbt-rules:latest

# Specific version
docker pull ghcr.io/andronics/qbt-rules:0.4.0

# Development version
docker pull ghcr.io/andronics/qbt-rules:main
```

### Build from Source

```bash
git clone https://github.com/andronics/qbt-rules.git
cd qbt-rules
docker build -t qbt-rules:local .
```

### Image Tags

| Tag | Description | Recommended For |
|-----|-------------|-----------------|
| `latest` | Latest stable release | Production |
| `0.4.0` | Specific version | Production (pinned) |
| `main` | Latest main branch | Testing/Development |
| `0.4` | Latest 0.4.x patch | Production (auto-updates) |

## Configuration

### Configuration Methods

qbt-rules supports three configuration methods (in priority order):

1. **Environment Variables** (highest priority)
2. **Config Files** (mounted volumes)
3. **Defaults** (lowest priority)

### Environment Variables

All variables support the `_FILE` suffix for Docker secrets:

```yaml
environment:
  # Server
  QBT_RULES_SERVER_HOST: "0.0.0.0"
  QBT_RULES_SERVER_PORT: "5000"
  QBT_RULES_SERVER_API_KEY: "your-secret-key"
  # OR use secret file:
  # QBT_RULES_SERVER_API_KEY_FILE: "/run/secrets/api_key"

  # Queue
  QBT_RULES_QUEUE_BACKEND: "sqlite"
  QBT_RULES_QUEUE_SQLITE_PATH: "/config/qbt-rules.db"
  QBT_RULES_QUEUE_CLEANUP_AFTER: "7d"

  # qBittorrent
  QBT_RULES_QBITTORRENT_HOST: "http://qbittorrent:8080"
  QBT_RULES_QBITTORRENT_USERNAME: "admin"
  QBT_RULES_QBITTORRENT_PASSWORD: "adminpass"

  # Logging
  LOG_LEVEL: "INFO"
  TRACE_MODE: "false"
```

### Volume Mounts

Required volumes:

```yaml
volumes:
  # Configuration files (required)
  - ./config:/config:ro  # Read-only recommended for security

  # Database (SQLite only, read-write required)
  - ./config:/config  # Must be read-write for qbt-rules.db
```

**Files in `/config`**:
- `config.yml` - Server configuration (optional if using ENV)
- `rules.yml` - Rules definitions (required)
- `qbt-rules.db` - SQLite database (auto-created)

## Deployment Scenarios

### Scenario 1: Standalone with SQLite

**Use Case**: Single-user, home deployment

**Docker Compose**:
```yaml
version: '3.8'

services:
  qbt-rules:
    image: ghcr.io/andronics/qbt-rules:latest
    container_name: qbt-rules
    restart: unless-stopped
    ports:
      - "5000:5000"
    volumes:
      - ./config:/config
    environment:
      QBT_RULES_SERVER_API_KEY: "your-secret-key"
      QBT_RULES_QBITTORRENT_HOST: "http://192.168.1.100:8080"
      QBT_RULES_QBITTORRENT_USERNAME: "admin"
      QBT_RULES_QBITTORRENT_PASSWORD: "adminpass"
```

**Pros**: Simple, no dependencies
**Cons**: Single-writer queue (fine for home use)

---

### Scenario 2: With Redis Queue

**Use Case**: High webhook volume, multiple potential workers

**Docker Compose**:
```yaml
version: '3.8'

services:
  qbt-rules:
    image: ghcr.io/andronics/qbt-rules:latest
    container_name: qbt-rules
    restart: unless-stopped
    ports:
      - "5000:5000"
    volumes:
      - ./config:/config
    environment:
      QBT_RULES_SERVER_API_KEY: "your-secret-key"
      QBT_RULES_QUEUE_BACKEND: "redis"
      QBT_RULES_QUEUE_REDIS_URL: "redis://redis:6379/0"
      QBT_RULES_QBITTORRENT_HOST: "http://qbittorrent:8080"
      QBT_RULES_QBITTORRENT_USERNAME: "admin"
      QBT_RULES_QBITTORRENT_PASSWORD: "adminpass"
    depends_on:
      redis:
        condition: service_healthy
    networks:
      - qbt-network

  redis:
    image: redis:7-alpine
    container_name: qbt-rules-redis
    restart: unless-stopped
    command: redis-server --appendonly yes
    volumes:
      - redis-data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 3
    networks:
      - qbt-network

networks:
  qbt-network:

volumes:
  redis-data:
```

**Pros**: High performance, scalable
**Cons**: Additional Redis container

---

### Scenario 3: Full Stack (qBittorrent + qbt-rules + Redis)

**Use Case**: Complete setup from scratch

**Docker Compose**: See [docker-compose.full-stack.yml](../docker-compose.full-stack.yml)

```bash
# Download full-stack compose file
wget https://raw.githubusercontent.com/andronics/qbt-rules/main/docker-compose.full-stack.yml

# Create config directories
mkdir -p qbittorrent/config qbittorrent/downloads qbt-rules/config

# Start stack
docker-compose -f docker-compose.full-stack.yml up -d
```

**Access**:
- qBittorrent WebUI: `http://localhost:8080`
- qbt-rules API: `http://localhost:5000`

---

### Scenario 4: Behind Reverse Proxy

**Use Case**: HTTPS access, multiple services

**Traefik Example**:
```yaml
version: '3.8'

services:
  qbt-rules:
    image: ghcr.io/andronics/qbt-rules:latest
    restart: unless-stopped
    volumes:
      - ./config:/config
    environment:
      QBT_RULES_SERVER_API_KEY_FILE: "/run/secrets/api_key"
      # ... other config
    secrets:
      - api_key
    networks:
      - traefik-proxy
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.qbt-rules.rule=Host(`qbt-rules.example.com`)"
      - "traefik.http.routers.qbt-rules.entrypoints=websecure"
      - "traefik.http.routers.qbt-rules.tls.certresolver=letsencrypt"
      - "traefik.http.services.qbt-rules.loadbalancer.server.port=5000"

networks:
  traefik-proxy:
    external: true

secrets:
  api_key:
    file: ./secrets/api_key.txt
```

## Queue Backends

### SQLite (Default)

**Configuration**:
```yaml
environment:
  QBT_RULES_QUEUE_BACKEND: "sqlite"
  QBT_RULES_QUEUE_SQLITE_PATH: "/config/qbt-rules.db"
```

**Volume Requirements**:
```yaml
volumes:
  - ./config:/config  # Must be read-write for database
```

**Backup**:
```bash
# Stop container
docker-compose stop qbt-rules

# Backup database
cp config/qbt-rules.db config/qbt-rules.db.backup

# Restart container
docker-compose start qbt-rules
```

---

### Redis

**Configuration**:
```yaml
environment:
  QBT_RULES_QUEUE_BACKEND: "redis"
  QBT_RULES_QUEUE_REDIS_URL: "redis://redis:6379/0"
  # With password:
  # QBT_RULES_QUEUE_REDIS_URL: "redis://:password@redis:6379/0"
```

**Redis Container**:
```yaml
redis:
  image: redis:7-alpine
  command: redis-server --appendonly yes --requirepass mypassword
  volumes:
    - redis-data:/data
```

**Persistence Options**:

1. **AOF (Append-Only File)** - Recommended:
   ```bash
   redis-server --appendonly yes --appendfsync everysec
   ```

2. **RDB (Snapshots)**:
   ```bash
   redis-server --save 900 1 --save 300 10 --save 60 10000
   ```

## Secrets Management

### Docker Secrets (Swarm Mode)

**docker-compose.yml**:
```yaml
version: '3.8'

services:
  qbt-rules:
    image: ghcr.io/andronics/qbt-rules:latest
    environment:
      QBT_RULES_SERVER_API_KEY_FILE: "/run/secrets/api_key"
      QBT_RULES_QBITTORRENT_PASSWORD_FILE: "/run/secrets/qbt_password"
    secrets:
      - api_key
      - qbt_password

secrets:
  api_key:
    file: ./secrets/api_key.txt
  qbt_password:
    file: ./secrets/qbt_password.txt
```

**Create secrets**:
```bash
mkdir -p secrets
echo "your-api-key" > secrets/api_key.txt
echo "qbt-password" > secrets/qbt_password.txt
chmod 600 secrets/*.txt
```

### Environment File (.env)

**Create `.env`**:
```bash
QBT_RULES_SERVER_API_KEY=your-secret-key
QBT_RULES_QBITTORRENT_PASSWORD=qbt-password
```

**docker-compose.yml**:
```yaml
services:
  qbt-rules:
    env_file:
      - .env
```

**Security**:
```bash
chmod 600 .env
echo ".env" >> .gitignore
```

## Networking

### Host Network Mode

**Use Case**: Direct access to host's qBittorrent

```yaml
services:
  qbt-rules:
    network_mode: "host"
    environment:
      QBT_RULES_QBITTORRENT_HOST: "http://localhost:8080"
```

**Note**: Port mapping not needed in host mode.

---

### Bridge Network (Recommended)

**Use Case**: Isolated network for services

```yaml
networks:
  qbt-network:
    driver: bridge
    ipam:
      config:
        - subnet: 172.20.0.0/16

services:
  qbt-rules:
    networks:
      qbt-network:
        ipv4_address: 172.20.0.10
```

---

### External Network

**Use Case**: Connect to existing network

```yaml
networks:
  existing-network:
    external: true

services:
  qbt-rules:
    networks:
      - existing-network
```

## Monitoring

### Health Checks

**Docker Compose**:
```yaml
services:
  qbt-rules:
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:5000/api/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 5s
```

**Check health**:
```bash
docker inspect --format='{{json .State.Health}}' qbt-rules | jq
```

---

### Logging

**View logs**:
```bash
# Follow logs
docker-compose logs -f qbt-rules

# Last 100 lines
docker-compose logs --tail=100 qbt-rules

# With timestamps
docker-compose logs -t qbt-rules
```

**Log driver configuration**:
```yaml
services:
  qbt-rules:
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

---

### Prometheus Metrics

Export metrics via sidecar:

```yaml
services:
  qbt-rules-exporter:
    image: python:3.11-slim
    restart: unless-stopped
    volumes:
      - ./exporter.py:/app/exporter.py:ro
    command: python /app/exporter.py
    ports:
      - "8000:8000"
    environment:
      QBT_RULES_URL: "http://qbt-rules:5000"
      QBT_RULES_API_KEY: "your-api-key"
    depends_on:
      - qbt-rules
```

See [API.md](./API.md#monitoring-with-prometheus) for exporter code.

## Troubleshooting

### Container Won't Start

**Check logs**:
```bash
docker-compose logs qbt-rules
```

**Common issues**:

1. **Port already in use**:
   ```bash
   # Find process using port 5000
   sudo lsof -i :5000

   # Change port in docker-compose.yml
   ports:
     - "5001:5000"
   ```

2. **Volume permission errors**:
   ```bash
   # Fix permissions
   sudo chown -R 1000:1000 ./config
   ```

3. **Missing config files**:
   ```bash
   # Create from defaults
   wget -O config/config.yml https://raw.githubusercontent.com/andronics/qbt-rules/main/config/config.default.yml
   wget -O config/rules.yml https://raw.githubusercontent.com/andronics/qbt-rules/main/config/rules.default.yml
   ```

---

### Health Check Fails

**Test manually**:
```bash
# Note: Container name may vary (qbt-rules, qbt-rules-1, or your custom name)
docker exec qbt-rules curl -f http://localhost:5000/api/health
```

**Check**:
- Server started successfully (logs)
- Worker thread running
- Queue backend accessible

---

### Can't Connect to qBittorrent

**Test from container**:
```bash
docker exec qbt-rules curl http://qbittorrent:8080/api/v2/app/version
```

**Common issues**:

1. **Wrong hostname**: Use container name or IP
2. **Network isolation**: Ensure both containers on same network
3. **Firewall**: Check qBittorrent allows connections
4. **Authentication**: Verify username/password

---

### Jobs Not Processing

**Check worker status**:
```bash
curl "http://localhost:5000/api/health?key=your-api-key" | jq '.worker'
```

**Check queue depth**:
```bash
curl "http://localhost:5000/api/stats?key=your-api-key" | jq '.queue.depth'
```

**List pending jobs**:
```bash
curl "http://localhost:5000/api/jobs?status=pending&key=your-api-key" | jq
```

---

### Database Locked (SQLite)

**Cause**: Multiple processes accessing database

**Solution**: Ensure only one qbt-rules instance running

```bash
# Stop all instances
docker-compose down

# Remove lock files
rm -f config/qbt-rules.db-shm config/qbt-rules.db-wal

# Start single instance
docker-compose up -d
```

## Advanced Topics

### Scheduled Execution

**Option 1: Cron Container** (Recommended)

```yaml
services:
  qbt-rules-cron:
    image: alpine:latest
    restart: unless-stopped
    command: >
      sh -c "
        apk add --no-cache curl &&
        echo '*/5 * * * * curl -X POST http://qbt-rules:5000/api/execute?context=scheduled&key=YOUR_KEY' | crontab - &&
        crond -f -l 2
      "
    depends_on:
      - qbt-rules
    networks:
      - qbt-network
```

**Option 2: Host Cron**

```cron
# /etc/cron.d/qbt-rules
*/5 * * * * user curl -X POST "http://localhost:5000/api/execute?context=scheduled&key=YOUR_KEY"
```

---

### Multi-Stage Deployment

**Development**:
```bash
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up
```

**docker-compose.dev.yml**:
```yaml
version: '3.8'
services:
  qbt-rules:
    build: .
    environment:
      LOG_LEVEL: "DEBUG"
      TRACE_MODE: "true"
    volumes:
      - ./src:/app/src  # Mount source for hot reload
```

**Production**:
```bash
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

**docker-compose.prod.yml**:
```yaml
version: '3.8'
services:
  qbt-rules:
    image: ghcr.io/andronics/qbt-rules:0.4.0  # Pinned version
    restart: always
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "5"
```

---

### Resource Limits

```yaml
services:
  qbt-rules:
    deploy:
      resources:
        limits:
          cpus: '1.0'
          memory: 512M
        reservations:
          cpus: '0.25'
          memory: 128M
```

---

### Auto-Update with Watchtower

```yaml
services:
  watchtower:
    image: containrrr/watchtower:latest
    restart: unless-stopped
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
    environment:
      WATCHTOWER_CLEANUP: "true"
      WATCHTOWER_INCLUDE_RESTARTING: "true"
      WATCHTOWER_SCHEDULE: "0 0 4 * * *"  # 4 AM daily
    command: qbt-rules
```

---

### Backup and Restore

**Automated Backup Script**:
```bash
#!/bin/bash
# backup-qbt-rules.sh

BACKUP_DIR="./backups"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p "$BACKUP_DIR"

# Stop container
docker-compose stop qbt-rules

# Backup database (SQLite)
cp config/qbt-rules.db "$BACKUP_DIR/qbt-rules_$DATE.db"

# Backup config
tar -czf "$BACKUP_DIR/config_$DATE.tar.gz" config/

# Restart container
docker-compose start qbt-rules

# Keep only last 7 backups
ls -t "$BACKUP_DIR"/qbt-rules_*.db | tail -n +8 | xargs -r rm
ls -t "$BACKUP_DIR"/config_*.tar.gz | tail -n +8 | xargs -r rm

echo "Backup completed: $DATE"
```

**Restore**:
```bash
#!/bin/bash
# restore-qbt-rules.sh

BACKUP_FILE="$1"

if [ -z "$BACKUP_FILE" ]; then
  echo "Usage: $0 <backup-file>"
  exit 1
fi

docker-compose stop qbt-rules
cp "$BACKUP_FILE" config/qbt-rules.db
docker-compose start qbt-rules

echo "Restore completed"
```

## See Also

- [Architecture Documentation](./Architecture.md)
- [API Reference](./API.md)
- [Configuration Examples](../config/config.default.yml)
- [Docker Compose Examples](../docker-compose.yml)
