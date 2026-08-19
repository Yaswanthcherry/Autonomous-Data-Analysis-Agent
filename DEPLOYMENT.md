# Deployment Guide - AI Data Analyst Agent

## 📋 Deployment Phases

### Phase 1: Development (COMPLETE ✅)
- SQLite database
- In-memory task execution
- Single process
- Hot reload enabled

### Phase 2: Local Production (READY FOR IMPLEMENTATION)
- Docker containerization
- Docker Compose orchestration
- PostgreSQL database
- Redis cache
- Celery workers
- Nginx reverse proxy

### Phase 3: Cloud Deployment (FUTURE)
- Kubernetes orchestration
- AWS/GCP/Azure integration
- Load balancing
- Auto-scaling
- CDN for static assets

---

## 🚀 Phase 2: Local Production Setup

### Prerequisites
- Docker Desktop installed (Windows/Mac) or Docker Engine (Linux)
- Docker Compose v2.0+
- Git
- 8GB RAM minimum, 4+ CPU cores

### Step 1: Prepare Environment Files

#### Backend `.env` (from `.env.example`)
```bash
# Database
DATABASE_URL=postgresql+psycopg2://analyst:password@postgres:5432/analyst_db

# Redis
REDIS_URL=redis://redis:6379/0

# API Keys
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxx

# JWT
JWT_SECRET_KEY=your-secret-key-at-least-32-characters

# Upload
UPLOAD_DIR=/app/uploads

# Logging
LOG_LEVEL=INFO
```

#### Frontend `.env.local`
```bash
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
```

### Step 2: Create Docker Compose File

**File**: `docker-compose.prod.yml`

```yaml
version: '3.8'

services:
  # PostgreSQL Database
  postgres:
    image: postgres:15-alpine
    container_name: analyst_postgres
    environment:
      POSTGRES_USER: analyst
      POSTGRES_PASSWORD: password
      POSTGRES_DB: analyst_db
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U analyst"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - analyst_network

  # Redis Cache
  redis:
    image: redis:7-alpine
    container_name: analyst_redis
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - analyst_network

  # Backend API
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: analyst_backend
    environment:
      - DATABASE_URL=postgresql+psycopg2://analyst:password@postgres:5432/analyst_db
      - REDIS_URL=redis://redis:6379/0
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - JWT_SECRET_KEY=${JWT_SECRET_KEY}
      - UPLOAD_DIR=/app/uploads
      - LOG_LEVEL=INFO
    volumes:
      - ./backend/uploads:/app/uploads
      - ./backend/logs:/app/logs
    ports:
      - "8000:8000"
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    networks:
      - analyst_network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  # Celery Worker (optional, for production scaling)
  celery_worker:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: analyst_celery
    command: celery -A tasks.celery_app worker --loglevel=info --concurrency=2
    environment:
      - DATABASE_URL=postgresql+psycopg2://analyst:password@postgres:5432/analyst_db
      - REDIS_URL=redis://redis:6379/0
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - JWT_SECRET_KEY=${JWT_SECRET_KEY}
      - UPLOAD_DIR=/app/uploads
      - LOG_LEVEL=INFO
    volumes:
      - ./backend/uploads:/app/uploads
      - ./backend/logs:/app/logs
    depends_on:
      - postgres
      - redis
    networks:
      - analyst_network
    deploy:
      replicas: 1  # Scale this up for high throughput

  # Frontend
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    container_name: analyst_frontend
    environment:
      - NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
    ports:
      - "3000:3000"
    depends_on:
      - backend
    networks:
      - analyst_network

  # Nginx Reverse Proxy
  nginx:
    image: nginx:alpine
    container_name: analyst_nginx
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./ssl:/etc/nginx/ssl:ro  # For HTTPS
    depends_on:
      - backend
      - frontend
    networks:
      - analyst_network

volumes:
  postgres_data:
    driver: local
  redis_data:
    driver: local

networks:
  analyst_network:
    driver: bridge
```

### Step 3: Create Backend Dockerfile

**File**: `backend/Dockerfile`

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Create directories
RUN mkdir -p /app/uploads /app/logs

# Expose port
EXPOSE 8000

# Run Uvicorn
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Step 4: Create Frontend Dockerfile

**File**: `frontend/Dockerfile`

```dockerfile
FROM node:20-alpine AS builder

WORKDIR /app

# Install dependencies
COPY package.json package-lock.json ./
RUN npm ci

# Build application
COPY . .
RUN npm run build

# Production stage
FROM node:20-alpine

WORKDIR /app

# Install dependencies for production
COPY package.json package-lock.json ./
RUN npm ci --only=production

# Copy built files from builder
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/public ./public

# Expose port
EXPOSE 3000

# Run Next.js
CMD ["npm", "start"]
```

### Step 5: Create Nginx Configuration

**File**: `nginx.conf`

```nginx
user nginx;
worker_processes auto;
error_log /var/log/nginx/error.log warn;
pid /var/run/nginx.pid;

events {
    worker_connections 1024;
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;

    log_format main '$remote_addr - $remote_user [$time_local] "$request" '
                    '$status $body_bytes_sent "$http_referer" '
                    '"$http_user_agent" "$http_x_forwarded_for"';

    access_log /var/log/nginx/access.log main;

    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;
    keepalive_timeout 65;
    types_hash_max_size 2048;
    client_max_body_size 100M;

    gzip on;
    gzip_vary on;
    gzip_min_length 1000;
    gzip_types text/plain text/css text/xml text/javascript 
               application/x-javascript application/xml+rss 
               application/json application/javascript;

    # Backend upstream
    upstream backend {
        server backend:8000;
    }

    # Frontend upstream
    upstream frontend {
        server frontend:3000;
    }

    server {
        listen 80;
        server_name _;

        # Frontend static files
        location / {
            proxy_pass http://frontend;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection 'upgrade';
            proxy_set_header Host $host;
            proxy_cache_bypass $http_upgrade;
        }

        # API backend
        location /api/ {
            proxy_pass http://backend;
            proxy_http_version 1.1;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            proxy_redirect off;
        }

        # Health check endpoint
        location /health {
            proxy_pass http://backend;
        }

        # API documentation
        location /docs {
            proxy_pass http://backend;
            proxy_set_header Host $host;
        }

        location /redoc {
            proxy_pass http://backend;
            proxy_set_header Host $host;
        }
    }

    # HTTPS configuration (uncomment after SSL setup)
    # server {
    #     listen 443 ssl http2;
    #     server_name your-domain.com;
    #
    #     ssl_certificate /etc/nginx/ssl/cert.pem;
    #     ssl_certificate_key /etc/nginx/ssl/key.pem;
    #
    #     ssl_protocols TLSv1.2 TLSv1.3;
    #     ssl_ciphers HIGH:!aNULL:!MD5;
    #
    #     # ... rest of configuration same as above ...
    # }
    #
    # # Redirect HTTP to HTTPS
    # server {
    #     listen 80;
    #     server_name your-domain.com;
    #     return 301 https://$server_name$request_uri;
    # }
}
```

### Step 6: Run Docker Compose

```bash
# Set environment variables
export OPENAI_API_KEY=sk-xxxxxxxxxxxx
export JWT_SECRET_KEY=your-secret-key-32-chars-min

# Build and start services
docker-compose -f docker-compose.prod.yml up -d

# Check status
docker-compose -f docker-compose.prod.yml ps

# View logs
docker-compose -f docker-compose.prod.yml logs -f backend

# Stop services
docker-compose -f docker-compose.prod.yml down
```

### Step 7: Database Migration

```bash
# Run migrations (automatic on startup)
docker-compose -f docker-compose.prod.yml exec backend \
  alembic upgrade head

# Create admin user
docker-compose -f docker-compose.prod.yml exec backend \
  python scripts/create_admin.py
```

---

## ☁️ Cloud Deployment (AWS Example)

### Option 1: Elastic Container Service (ECS)

#### Infrastructure as Code (Terraform)
```hcl
# infrastructure/main.tf

provider "aws" {
  region = "us-east-1"
}

# VPC
resource "aws_vpc" "main" {
  cidr_block = "10.0.0.0/16"
}

# RDS PostgreSQL
resource "aws_db_instance" "postgres" {
  allocated_storage    = 20
  engine              = "postgres"
  engine_version      = "15.0"
  instance_class      = "db.t3.micro"
  db_name             = "analyst_db"
  username            = "analyst"
  password            = random_password.db_password.result
  skip_final_snapshot = false
}

# ElastiCache Redis
resource "aws_elasticache_cluster" "redis" {
  cluster_id           = "analyst-redis"
  engine              = "redis"
  node_type           = "cache.t3.micro"
  num_cache_nodes     = 1
  parameter_group_name = "default.redis7"
  engine_version      = "7.0"
}

# ECS Cluster
resource "aws_ecs_cluster" "main" {
  name = "analyst-cluster"
}

# Application Load Balancer
resource "aws_lb" "main" {
  name               = "analyst-alb"
  internal           = false
  load_balancer_type = "application"
  subnets            = aws_subnet.main[*].id
}

# ECS Services, Task Definitions, etc.
```

#### Deploy with AWS CLI
```bash
# Build and push Docker images
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin 123456789.dkr.ecr.us-east-1.amazonaws.com

docker build -t analyst-backend:latest ./backend
docker tag analyst-backend:latest 123456789.dkr.ecr.us-east-1.amazonaws.com/analyst-backend:latest
docker push 123456789.dkr.ecr.us-east-1.amazonaws.com/analyst-backend:latest

# Deploy with ECS
aws ecs create-service \
  --cluster analyst-cluster \
  --service-name analyst-backend \
  --task-definition analyst-backend:1 \
  --desired-count 2 \
  --launch-type FARGATE
```

### Option 2: Kubernetes

#### Helm Chart Structure
```
analyst-helm-chart/
├── Chart.yaml
├── values.yaml
├── templates/
│   ├── backend-deployment.yaml
│   ├── frontend-deployment.yaml
│   ├── postgres-statefulset.yaml
│   ├── redis-deployment.yaml
│   ├── nginx-configmap.yaml
│   ├── service.yaml
│   └── ingress.yaml
```

#### Deploy with Helm
```bash
# Add Helm repository
helm repo add analyst-repo https://charts.example.com

# Install release
helm install analyst analyst-repo/analyst-agent \
  --namespace production \
  --values values-prod.yaml

# Upgrade release
helm upgrade analyst analyst-repo/analyst-agent \
  --namespace production \
  --values values-prod.yaml
```

---

## 🔒 Security Best Practices

### 1. Environment Variables
```bash
# Never commit .env files
echo ".env" >> .gitignore

# Use AWS Secrets Manager or similar
aws secretsmanager create-secret \
  --name analyst/api-keys \
  --secret-string '{"OPENAI_API_KEY":"..."}'
```

### 2. Database Security
```sql
-- Restrict database access
CREATE USER analyst WITH PASSWORD 'strong-random-password';
GRANT CONNECT ON DATABASE analyst_db TO analyst;

-- Enable SSL
ssl = on
ssl_cert_file = '/etc/postgresql/server.crt'
ssl_key_file = '/etc/postgresql/server.key'
```

### 3. API Security
```yaml
# Nginx: Rate limiting
limit_req_zone $binary_remote_addr zone=api_limit:10m rate=10r/s;
location /api/ {
    limit_req zone=api_limit burst=20 nodelay;
}

# Nginx: DDoS protection
limit_conn_zone $binary_remote_addr zone=addr:10m;
limit_conn addr 100;
```

### 4. TLS/SSL
```bash
# Generate self-signed certificate (testing)
openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -days 365

# Use Let's Encrypt (production)
certbot certonly --standalone -d your-domain.com
```

### 5. Backup Strategy
```bash
# Automated PostgreSQL backups
pg_dump analyst_db > backup_$(date +%Y%m%d).sql

# S3 backup with lifecycle
aws s3 cp backup_*.sql s3://analyst-backups/
aws s3api put-bucket-lifecycle-configuration \
  --bucket analyst-backups \
  --lifecycle-configuration file://lifecycle.json
```

---

## 📊 Monitoring & Logging

### Application Monitoring
```yaml
# prometheus.yml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'analyst-backend'
    static_configs:
      - targets: ['localhost:8000']

  - job_name: 'postgres'
    static_configs:
      - targets: ['localhost:5432']
```

### Log Aggregation
```bash
# ElasticSearch + Kibana setup
docker-compose up -d elasticsearch kibana

# Filebeat configuration
filebeat.inputs:
- type: log
  enabled: true
  paths:
    - ./backend/logs/*.log
  json.message_key: msg
  json.keys_under_root: true

output.elasticsearch:
  hosts: ["localhost:9200"]
```

### Alerting
```yaml
# AlertManager rules
groups:
  - name: analyst_alerts
    rules:
      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.05
        for: 5m
        labels:
          severity: critical

      - alert: LowDiskSpace
        expr: node_filesystem_avail_bytes / node_filesystem_size_bytes < 0.1
        for: 10m
        labels:
          severity: warning
```

---

## 📈 Scaling Strategy

### Horizontal Scaling
```bash
# Scale backend workers
docker-compose -f docker-compose.prod.yml up -d --scale backend=3

# Scale Celery workers
docker-compose -f docker-compose.prod.yml up -d --scale celery_worker=5
```

### Database Scaling
```sql
-- Replication setup
ALTER SYSTEM SET wal_level = replica;
ALTER SYSTEM SET max_wal_senders = 10;
SELECT pg_ctl_restart();

-- On replica server
pg_basebackup -h primary-host -D /var/lib/postgresql/data -U replication -v -P
```

### Cache Optimization
```python
# Redis clustering for high availability
redis-cli --cluster create \
  node1:6379 node2:6379 node3:6379 \
  node4:6379 node5:6379 node6:6379 \
  --cluster-replicas 1
```

---

## 🚨 Troubleshooting

### Container Won't Start
```bash
# Check logs
docker-compose logs backend

# Inspect container
docker exec -it analyst_backend bash

# Check environment variables
docker exec analyst_backend printenv
```

### Database Connection Error
```bash
# Test PostgreSQL
docker exec analyst_postgres psql -U analyst -d analyst_db -c "SELECT 1"

# Check PostgreSQL logs
docker logs analyst_postgres
```

### Out of Memory
```bash
# Monitor Docker resource usage
docker stats

# Increase container limits
# In docker-compose.yml:
services:
  backend:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 4G
```

### Slow API Response
```bash
# Check Nginx logs
docker logs analyst_nginx

# Profile backend with pprof
curl http://localhost:8000/debug/pprof/

# Enable query logging in PostgreSQL
ALTER SYSTEM SET log_statement = 'all';
SELECT pg_ctl_restart();
```

---

## ✅ Deployment Checklist

- [ ] All environment variables configured
- [ ] Database migrations run successfully
- [ ] Admin user created
- [ ] SSL/TLS certificates obtained
- [ ] Nginx configuration tested
- [ ] Docker images built and tested locally
- [ ] Health checks passing
- [ ] Logs aggregated and monitored
- [ ] Backups configured
- [ ] Load testing completed
- [ ] Security audit passed
- [ ] Documentation updated
- [ ] Team trained on deployment

---

## 📞 Post-Deployment

### First Week
- Monitor error rates and response times
- Test all critical user workflows
- Verify backups are working
- Collect performance metrics
- Address any issues

### Monthly Tasks
- Review and rotate API keys
- Update dependencies
- Analyze usage patterns
- Plan capacity upgrades
- Security patching

### Quarterly Tasks
- Full security audit
- Database optimization
- Infrastructure review
- Disaster recovery drill
- Performance benchmarking

---

**Deployment Guide v1.0** | Last Updated: 2026-08-09
