# Deployment Guide

This guide covers deploying the AI Data Analyst Agent to production using Docker, PostgreSQL, Nginx, and CI/CD.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Environment Configuration](#environment-configuration)
3. [Local Deployment](#local-deployment)
4. [Production Deployment](#production-deployment)
5. [CI/CD Pipeline](#cicd-pipeline)
6. [Monitoring & Health Checks](#monitoring--health-checks)
7. [Troubleshooting](#troubleshooting)
8. [Scaling Considerations](#scaling-considerations)

## Prerequisites

### Required Software

- **Docker**: 20.10+
- **Docker Compose**: 2.0+
- **Git**: For cloning the repository
- **OpenAI API Key**: Required for AI analysis features

### System Requirements

- **Minimum**: 2 CPU cores, 4GB RAM, 20GB disk
- **Recommended**: 4 CPU cores, 8GB RAM, 50GB disk
- **Production**: 8+ CPU cores, 16GB+ RAM, 100GB+ disk with SSD

## Environment Configuration

### 1. Clone the Repository

```bash
git clone <your-repo-url>
cd analysis-agent
```

### 2. Configure Environment Variables

```bash
cp .env.example .env
```

Edit `.env` with your production values:

```bash
# ─── App ───────────────────────────────────────────────
APP_ENV=production
SECRET_KEY=<generate-a-long-random-secret-key>
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# ─── Database ──────────────────────────────────────────
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
POSTGRES_DB=ai_analyst
POSTGRES_USER=<secure-username>
POSTGRES_PASSWORD=<secure-password>
DATABASE_URL=postgresql+asyncpg://<user>:<password>@postgres:5432/ai_analyst

# ─── Redis ─────────────────────────────────────────────
REDIS_URL=redis://redis:6379/0
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/1

# ─── OpenAI ────────────────────────────────────────────
OPENAI_API_KEY=sk-your-actual-openai-key
OPENAI_MODEL=gpt-4o

# ─── File Storage ──────────────────────────────────────
UPLOAD_DIR=/app/uploads
MAX_UPLOAD_SIZE_MB=100

# ─── Frontend ──────────────────────────────────────────
NEXT_PUBLIC_API_URL=https://your-domain.com
NEXTAUTH_SECRET=<generate-nextauth-secret>
NEXTAUTH_URL=https://your-domain.com
```

### Security Notes

- **Never commit `.env` to version control**
- Use strong, randomly generated secrets (32+ characters)
- Rotate secrets regularly in production
- Use environment-specific API keys

## Local Deployment

### Quick Start

```bash
# Start all services
docker-compose up -d

# Run database migrations
docker-compose exec backend alembic upgrade head

# Check service health
docker-compose ps
```

### Access Points

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Nginx Reverse Proxy**: http://localhost

### Development Mode

For hot-reload during development:

```bash
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up
```

### Stopping Services

```bash
docker-compose down
```

To remove volumes (WARNING: deletes data):

```bash
docker-compose down -v
```

## Production Deployment

### 1. Server Setup

#### Ubuntu/Debian

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Add user to docker group
sudo usermod -aG docker $USER
```

#### Firewall Configuration

```bash
# Allow HTTP/HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw allow 22/tcp
sudo ufw enable
```

### 2. SSL/TLS Setup with Let's Encrypt

```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx -y

# Obtain certificate
sudo certbot --nginx -d your-domain.com

# Auto-renewal (configured automatically)
sudo certbot renew --dry-run
```

### 3. Configure Nginx

Update `nginx/nginx.conf` for production:

```nginx
server {
    listen 80;
    server_name your-domain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;

    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    # Frontend
    location / {
        proxy_pass http://frontend:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # Backend API
    location /api/ {
        proxy_pass http://backend:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Health checks
    location /health {
        proxy_pass http://backend:8000;
        access_log off;
    }
}
```

### 4. Deploy with Docker Compose

```bash
# Clone repository
git clone <your-repo-url>
cd analysis-agent

# Configure environment
cp .env.example .env
nano .env  # Edit with production values

# Start services
docker-compose up -d

# Run migrations
docker-compose exec backend alembic upgrade head

# Create admin user
docker-compose exec backend python scripts/create_admin.py
```

### 5. Verify Deployment

```bash
# Check all services are running
docker-compose ps

# Check backend health
curl http://localhost/health/ready

# Check frontend
curl http://localhost/

# View logs
docker-compose logs -f
```

## CI/CD Pipeline

### GitHub Actions Setup

The project includes CI/CD workflows in `.github/workflows/`:

- **ci.yml**: Runs tests on every push/PR
- **deploy.yml**: Deploys to production on main branch pushes

### Required GitHub Secrets

Configure these in your repository settings:

```
DOCKER_USERNAME          # Docker Hub username
DOCKER_PASSWORD          # Docker Hub password/token
PRODUCTION_HOST          # Production server hostname
PRODUCTION_USER          # SSH username for server
SSH_PRIVATE_KEY          # SSH private key for server access
```

### Deployment Workflow

1. **Push to main branch** triggers CI tests
2. **Tests pass** → Build Docker images
3. **Push images** to Docker Hub
4. **SSH to production server**
5. **Pull latest images**
6. **Restart services**
7. **Run database migrations**

### Manual Deployment

```bash
# Build images locally
docker-compose build

# Push to registry
docker push your-username/ai-analyst-backend:latest
docker push your-username/ai-analyst-frontend:latest

# Deploy on server
ssh user@production-server
cd /opt/ai-analyst
docker-compose pull
docker-compose up -d
docker-compose exec backend alembic upgrade head
```

## Monitoring & Health Checks

### Health Endpoints

The backend provides three health endpoints:

- **`/health`**: Basic health check
  ```json
  {"status": "ok", "version": "1.0.0"}
  ```

- **`/health/ready`**: Readiness check (database + Redis)
  ```json
  {"status": "ready", "checks": {"database": "ok", "redis": "ok"}}
  ```

- **`/health/live`**: Liveness check
  ```json
  {"status": "alive", "timestamp": "2024-01-01T00:00:00Z"}
  ```

### Monitoring Logs

```bash
# View all logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f backend
docker-compose logs -f celery_worker

# View last 100 lines
docker-compose logs --tail=100 backend
```

### Log Files

Logs are stored in `backend/logs/`:
- **app.log**: Application logs (JSON format, rotated)
- **Retention**: 30 days with compression

### Metrics Collection

For production monitoring, consider integrating:

- **Prometheus**: For metrics collection
- **Grafana**: For visualization
- **Sentry**: For error tracking
- **Datadog/New Relic**: For APM

Example Prometheus configuration:

```yaml
scrape_configs:
  - job_name: 'ai-analyst'
    static_configs:
      - targets: ['backend:8000']
    metrics_path: '/metrics'
```

## Troubleshooting

### Common Issues

#### 1. Database Connection Failed

```bash
# Check PostgreSQL is running
docker-compose ps postgres

# Check PostgreSQL logs
docker-compose logs postgres

# Restart database
docker-compose restart postgres
```

#### 2. Redis Connection Failed

```bash
# Check Redis is running
docker-compose ps redis

# Check Redis logs
docker-compose logs redis

# Test Redis connection
docker-compose exec redis redis-cli ping
```

#### 3. Celery Worker Not Processing Tasks

```bash
# Check worker status
docker-compose ps celery_worker

# View worker logs
docker-compose logs celery_worker

# Restart worker
docker-compose restart celery_worker
```

#### 4. OpenAI API Errors

```bash
# Verify API key is set
docker-compose exec backend env | grep OPENAI_API_KEY

# Check API quota
# Visit: https://platform.openai.com/usage

# Test API connection
docker-compose exec backend python -c "from openai import OpenAI; client = OpenAI(); print(client.models.list())"
```

#### 5. Nginx 502 Bad Gateway

```bash
# Check backend is running
docker-compose ps backend

# Check backend health
curl http://localhost:8000/health

# Check Nginx configuration
docker-compose exec nginx nginx -t

# Reload Nginx
docker-compose exec nginx nginx -s reload
```

### Database Migrations

```bash
# Check current migration version
docker-compose exec backend alembic current

# Upgrade to latest
docker-compose exec backend alembic upgrade head

# Rollback one step
docker-compose exec backend alembic downgrade -1

# Create new migration
docker-compose exec backend alembic revision --autogenerate -m "description"
```

### Reset Application Data

**WARNING**: This deletes all data

```bash
# Stop services
docker-compose down

# Remove volumes
docker-compose down -v

# Restart
docker-compose up -d
docker-compose exec backend alembic upgrade head
```

## Scaling Considerations

### Horizontal Scaling

For high-traffic deployments, consider:

1. **Multiple Backend Workers**
   ```yaml
   # In docker-compose.yml
   backend:
     deploy:
       replicas: 3
   ```

2. **Load Balancer**
   - Use HAProxy or Nginx as load balancer
   - Configure health checks for backend instances

3. **Database Connection Pooling**
   - Use PgBouncer for PostgreSQL connection pooling
   - Configure appropriate pool sizes in SQLAlchemy

### Vertical Scaling

- Increase CPU cores and RAM for Docker containers
- Use SSD storage for database and uploads
- Increase Celery worker concurrency

### Caching Strategy

- **Redis**: Already configured for caching
- **CDN**: Use Cloudflare or AWS CloudFront for static assets
- **Database Indexing**: Ensure proper indexes on frequently queried columns

### Backup Strategy

```bash
# Database backup
docker-compose exec postgres pg_dump -U analyst_user ai_analyst > backup.sql

# Automated backup script (cron)
0 2 * * * docker-compose exec postgres pg_dump -U analyst_user ai_analyst > /backups/ai_analyst_$(date +\%Y\%m\%d).sql

# Restore backup
docker-compose exec -T postgres psql -U analyst_user ai_analyst < backup.sql
```

## Security Best Practices

1. **Keep dependencies updated**
   ```bash
   docker-compose pull
   docker-compose up -d
   ```

2. **Use secrets management**
   - Docker Secrets for sensitive data
   - Environment variables for configuration
   - Never hardcode credentials

3. **Network isolation**
   - Use Docker networks to isolate services
   - Only expose necessary ports
   - Use internal networks for service communication

4. **Regular security audits**
   - Scan images for vulnerabilities: `docker scan`
   - Review dependency updates
   - Monitor access logs

5. **Rate limiting**
   - Already configured with slowapi
   - Adjust limits based on traffic patterns

## Support

For issues or questions:
- **Documentation**: Check inline code comments
- **Logs**: Review application logs for errors
- **Health Checks**: Use `/health/ready` endpoint
- **GitHub Issues**: Report bugs in the repository
