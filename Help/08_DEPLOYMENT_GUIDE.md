# SwissKnife AI Scraper - Deployment Guide

## 🚀 **Production Deployment**

This guide covers production deployment strategies, configuration, and best practices for the SwissKnife AI Scraper platform.

---

## 🏗️ **Deployment Architecture**

### **Production Architecture Overview**
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Load Balancer │    │   Web Server    │    │   Application   │
│   (Nginx/HAProxy)│◄──►│   (Nginx)       │◄──►│   (FastAPI)     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   CDN           │    │   Static Files  │    │   Database      │
│   (CloudFlare)  │    │   (S3/MinIO)    │    │   (PostgreSQL)  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### **Service Dependencies**
```mermaid
graph TD
    A[Load Balancer] --> B[Frontend]
    A --> C[Backend API]
    C --> D[PostgreSQL]
    C --> E[Redis]
    C --> F[Crawl4AI]
    C --> G[Ollama]
    F --> H[External Sites]
    C --> I[Jina AI]
```

---

## 🐳 **Docker Production Setup**

### **Production Docker Compose**
Create `docker-compose.prod.yml`:

```yaml
version: '3.8'

services:
  # Frontend with production optimizations
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile.prod
      args:
        - REACT_APP_API_URL=https://api.yourdomain.com
        - REACT_APP_ENV=production
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./ssl:/etc/nginx/ssl:ro
      - ./nginx/nginx.prod.conf:/etc/nginx/nginx.conf:ro
    environment:
      - NODE_ENV=production
    restart: unless-stopped
    networks:
      - swissknife-network

  # Backend with production configuration
  swissknife:
    build:
      context: .
      dockerfile: Dockerfile.prod
    ports:
      - "8601:8601"
    environment:
      - ENVIRONMENT=production
      - DEBUG=false
      - SECRET_KEY=${SECRET_KEY}
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
      - JINA_AI_API_KEY=${JINA_AI_API_KEY}
      - CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
    volumes:
      - swissknife_data:/app/data
      - swissknife_logs:/app/logs
    depends_on:
      - postgres
      - redis
      - crawl4ai
    restart: unless-stopped
    networks:
      - swissknife-network
    deploy:
      resources:
        limits:
          memory: 2G
          cpus: '1.0'

  # Production database with backup
  postgres:
    image: postgres:15-alpine
    ports:
      - "5432:5432"
    environment:
      - POSTGRES_DB=${POSTGRES_DB}
      - POSTGRES_USER=${POSTGRES_USER}
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./backups:/backups
    restart: unless-stopped
    networks:
      - swissknife-network
    deploy:
      resources:
        limits:
          memory: 1G

  # Redis with persistence
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    command: redis-server --appendonly yes --requirepass ${REDIS_PASSWORD}
    restart: unless-stopped
    networks:
      - swissknife-network

  # Crawl4AI with production settings
  crawl4ai:
    image: unclecode/crawl4ai:latest
    ports:
      - "11235:11235"
    environment:
      - MAX_CONCURRENT_SESSIONS=20
      - CRAWL4AI_LOG_LEVEL=WARNING
    volumes:
      - crawl4ai_data:/app/data
    restart: unless-stopped
    networks:
      - swissknife-network
    deploy:
      resources:
        limits:
          memory: 4G
          cpus: '2.0'

volumes:
  postgres_data:
  redis_data:
  crawl4ai_data:
  swissknife_data:
  swissknife_logs:

networks:
  swissknife-network:
    driver: bridge
```

### **Production Dockerfile**
Create `Dockerfile.prod`:

```dockerfile
# Multi-stage build for production
FROM python:3.11-slim as builder

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Production stage
FROM python:3.11-slim

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Create app user
RUN useradd --create-home --shell /bin/bash app
USER app
WORKDIR /app

# Copy application code
COPY --chown=app:app . .

# Expose port
EXPOSE 8601

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8601/health || exit 1

# Start application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8601", "--workers", "4"]
```

---

## ☁️ **Cloud Deployment Options**

### **AWS Deployment**

#### **ECS (Elastic Container Service)**
```yaml
# ecs-task-definition.json
{
  "family": "swissknife-ai-scraper",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "1024",
  "memory": "2048",
  "executionRoleArn": "arn:aws:iam::account:role/ecsTaskExecutionRole",
  "taskRoleArn": "arn:aws:iam::account:role/ecsTaskRole",
  "containerDefinitions": [
    {
      "name": "swissknife-backend",
      "image": "your-account.dkr.ecr.region.amazonaws.com/swissknife:latest",
      "portMappings": [
        {
          "containerPort": 8601,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {
          "name": "ENVIRONMENT",
          "value": "production"
        }
      ],
      "secrets": [
        {
          "name": "SECRET_KEY",
          "valueFrom": "arn:aws:secretsmanager:region:account:secret:swissknife/secret-key"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/swissknife",
          "awslogs-region": "us-west-2",
          "awslogs-stream-prefix": "ecs"
        }
      }
    }
  ]
}
```

#### **EKS (Kubernetes)**
```yaml
# kubernetes/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: swissknife-backend
spec:
  replicas: 3
  selector:
    matchLabels:
      app: swissknife-backend
  template:
    metadata:
      labels:
        app: swissknife-backend
    spec:
      containers:
      - name: swissknife
        image: your-account.dkr.ecr.region.amazonaws.com/swissknife:latest
        ports:
        - containerPort: 8601
        env:
        - name: ENVIRONMENT
          value: "production"
        - name: SECRET_KEY
          valueFrom:
            secretKeyRef:
              name: swissknife-secrets
              key: secret-key
        resources:
          requests:
            memory: "1Gi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "1000m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8601
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8601
          initialDelaySeconds: 5
          periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: swissknife-service
spec:
  selector:
    app: swissknife-backend
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8601
  type: LoadBalancer
```

### **Google Cloud Platform**

#### **Cloud Run**
```yaml
# cloudrun.yaml
apiVersion: serving.knative.dev/v1
kind: Service
metadata:
  name: swissknife-ai-scraper
  annotations:
    run.googleapis.com/ingress: all
spec:
  template:
    metadata:
      annotations:
        autoscaling.knative.dev/maxScale: "10"
        run.googleapis.com/cpu-throttling: "false"
        run.googleapis.com/memory: "2Gi"
        run.googleapis.com/cpu: "1000m"
    spec:
      containerConcurrency: 10
      containers:
      - image: gcr.io/your-project/swissknife:latest
        ports:
        - containerPort: 8601
        env:
        - name: ENVIRONMENT
          value: "production"
        - name: SECRET_KEY
          valueFrom:
            secretKeyRef:
              name: swissknife-secrets
              key: secret-key
        resources:
          limits:
            memory: "2Gi"
            cpu: "1000m"
```

### **Azure Container Instances**
```yaml
# azure-container-group.yaml
apiVersion: 2019-12-01
location: eastus
name: swissknife-container-group
properties:
  containers:
  - name: swissknife-backend
    properties:
      image: your-registry.azurecr.io/swissknife:latest
      resources:
        requests:
          cpu: 1.0
          memoryInGb: 2.0
      ports:
      - port: 8601
        protocol: TCP
      environmentVariables:
      - name: ENVIRONMENT
        value: production
      - name: SECRET_KEY
        secureValue: your-secret-key
  osType: Linux
  restartPolicy: Always
  ipAddress:
    type: Public
    ports:
    - protocol: TCP
      port: 8601
```

---

## 🔒 **Security Configuration**

### **SSL/TLS Setup**

#### **Nginx SSL Configuration**
```nginx
# nginx/nginx.prod.conf
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com www.yourdomain.com;

    # SSL Configuration
    ssl_certificate /etc/nginx/ssl/fullchain.pem;
    ssl_certificate_key /etc/nginx/ssl/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;

    # Security Headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Content-Type-Options nosniff;
    add_header X-Frame-Options DENY;
    add_header X-XSS-Protection "1; mode=block";
    add_header Referrer-Policy "strict-origin-when-cross-origin";

    # Frontend
    location / {
        root /usr/share/nginx/html;
        index index.html index.htm;
        try_files $uri $uri/ /index.html;
        
        # Cache static assets
        location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
            expires 1y;
            add_header Cache-Control "public, immutable";
        }
    }

    # API Proxy
    location /api/ {
        proxy_pass http://swissknife:8601/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
}
```

### **Environment Variables Security**
```bash
# Use secrets management
# AWS Secrets Manager
aws secretsmanager create-secret \
    --name "swissknife/production" \
    --description "SwissKnife AI Scraper production secrets" \
    --secret-string '{
        "SECRET_KEY": "your-super-secret-key",
        "DATABASE_URL": "postgresql://user:pass@host:5432/db",
        "JINA_AI_API_KEY": "your-jina-api-key"
    }'

# Google Secret Manager
gcloud secrets create swissknife-secret-key --data-file=secret-key.txt

# Azure Key Vault
az keyvault secret set \
    --vault-name "swissknife-keyvault" \
    --name "secret-key" \
    --value "your-super-secret-key"
```

---

## 📊 **Monitoring & Logging**

### **Application Monitoring**

#### **Prometheus Configuration**
```yaml
# prometheus/prometheus.yml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

rule_files:
  - "alert_rules.yml"

scrape_configs:
  - job_name: 'swissknife-backend'
    static_configs:
      - targets: ['swissknife:8601']
    metrics_path: '/metrics'
    scrape_interval: 30s

  - job_name: 'postgres'
    static_configs:
      - targets: ['postgres-exporter:9187']

  - job_name: 'redis'
    static_configs:
      - targets: ['redis-exporter:9121']

alerting:
  alertmanagers:
    - static_configs:
        - targets:
          - alertmanager:9093
```

#### **Grafana Dashboard**
```json
{
  "dashboard": {
    "title": "SwissKnife AI Scraper",
    "panels": [
      {
        "title": "Request Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(http_requests_total[5m])",
            "legendFormat": "{{method}} {{endpoint}}"
          }
        ]
      },
      {
        "title": "Response Time",
        "type": "graph",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))",
            "legendFormat": "95th percentile"
          }
        ]
      },
      {
        "title": "Error Rate",
        "type": "singlestat",
        "targets": [
          {
            "expr": "rate(http_requests_total{status=~\"5..\"}[5m]) / rate(http_requests_total[5m]) * 100",
            "legendFormat": "Error Rate %"
          }
        ]
      }
    ]
  }
}
```

### **Centralized Logging**

#### **ELK Stack Configuration**
```yaml
# docker-compose.logging.yml
version: '3.8'

services:
  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:8.5.0
    environment:
      - discovery.type=single-node
      - "ES_JAVA_OPTS=-Xms512m -Xmx512m"
    volumes:
      - elasticsearch_data:/usr/share/elasticsearch/data
    ports:
      - "9200:9200"

  logstash:
    image: docker.elastic.co/logstash/logstash:8.5.0
    volumes:
      - ./logstash/pipeline:/usr/share/logstash/pipeline
    ports:
      - "5044:5044"
    depends_on:
      - elasticsearch

  kibana:
    image: docker.elastic.co/kibana/kibana:8.5.0
    ports:
      - "5601:5601"
    environment:
      - ELASTICSEARCH_HOSTS=http://elasticsearch:9200
    depends_on:
      - elasticsearch

volumes:
  elasticsearch_data:
```

---

## 🔄 **CI/CD Pipeline**

### **GitHub Actions**
```yaml
# .github/workflows/deploy.yml
name: Deploy to Production

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install -r requirements-dev.txt
    
    - name: Run tests
      run: |
        pytest tests/ -v --cov=.
    
    - name: Run linting
      run: |
        flake8 .
        black --check .

  build:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Configure AWS credentials
      uses: aws-actions/configure-aws-credentials@v2
      with:
        aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
        aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
        aws-region: us-west-2
    
    - name: Login to Amazon ECR
      id: login-ecr
      uses: aws-actions/amazon-ecr-login@v1
    
    - name: Build and push Docker image
      env:
        ECR_REGISTRY: ${{ steps.login-ecr.outputs.registry }}
        ECR_REPOSITORY: swissknife-ai-scraper
        IMAGE_TAG: ${{ github.sha }}
      run: |
        docker build -f Dockerfile.prod -t $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG .
        docker push $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG
        docker tag $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG $ECR_REGISTRY/$ECR_REPOSITORY:latest
        docker push $ECR_REGISTRY/$ECR_REPOSITORY:latest

  deploy:
    needs: build
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    
    steps:
    - name: Deploy to ECS
      run: |
        aws ecs update-service \
          --cluster swissknife-cluster \
          --service swissknife-service \
          --force-new-deployment
```

### **GitLab CI/CD**
```yaml
# .gitlab-ci.yml
stages:
  - test
  - build
  - deploy

variables:
  DOCKER_DRIVER: overlay2
  DOCKER_TLS_CERTDIR: "/certs"

test:
  stage: test
  image: python:3.11
  script:
    - pip install -r requirements.txt -r requirements-dev.txt
    - pytest tests/ -v --cov=.
    - flake8 .
    - black --check .

build:
  stage: build
  image: docker:20.10.16
  services:
    - docker:20.10.16-dind
  script:
    - docker build -f Dockerfile.prod -t $CI_REGISTRY_IMAGE:$CI_COMMIT_SHA .
    - docker push $CI_REGISTRY_IMAGE:$CI_COMMIT_SHA
  only:
    - main

deploy:
  stage: deploy
  image: alpine:latest
  script:
    - apk add --no-cache curl
    - curl -X POST "$WEBHOOK_URL" -H "Content-Type: application/json" -d '{"image":"'$CI_REGISTRY_IMAGE:$CI_COMMIT_SHA'"}'
  only:
    - main
```

---

## 📈 **Performance Optimization**

### **Database Optimization**
```sql
-- Create indexes for better performance
CREATE INDEX CONCURRENTLY idx_users_email ON users(email);
CREATE INDEX CONCURRENTLY idx_jobs_status ON scraping_jobs(status);
CREATE INDEX CONCURRENTLY idx_jobs_created_at ON scraping_jobs(created_at);
CREATE INDEX CONCURRENTLY idx_content_url_hash ON scraped_content(url_hash);

-- Optimize PostgreSQL configuration
-- postgresql.conf
shared_buffers = 256MB
effective_cache_size = 1GB
maintenance_work_mem = 64MB
checkpoint_completion_target = 0.9
wal_buffers = 16MB
default_statistics_target = 100
random_page_cost = 1.1
effective_io_concurrency = 200
```

### **Redis Configuration**
```conf
# redis.conf
maxmemory 512mb
maxmemory-policy allkeys-lru
save 900 1
save 300 10
save 60 10000
appendonly yes
appendfsync everysec
```

### **Application Performance**
```python
# Production settings
PRODUCTION_SETTINGS = {
    "MAX_CONCURRENT_REQUESTS": 50,
    "CONNECTION_POOL_SIZE": 20,
    "CACHE_TTL": 3600,
    "BATCH_SIZE": 100,
    "WORKER_PROCESSES": 4,
    "KEEP_ALIVE_TIMEOUT": 5,
    "MAX_REQUEST_SIZE": 10 * 1024 * 1024,  # 10MB
}
```

---

## 🔧 **Maintenance & Updates**

### **Zero-Downtime Deployment**
```bash
#!/bin/bash
# deploy.sh - Zero-downtime deployment script

# Build new image
docker build -f Dockerfile.prod -t swissknife:new .

# Start new container
docker run -d --name swissknife-new \
  --network swissknife-network \
  -e ENVIRONMENT=production \
  swissknife:new

# Health check
for i in {1..30}; do
  if curl -f http://swissknife-new:8601/health; then
    echo "New container is healthy"
    break
  fi
  sleep 2
done

# Update load balancer
# Switch traffic to new container
docker exec nginx nginx -s reload

# Stop old container
docker stop swissknife-old
docker rm swissknife-old

# Tag new container
docker tag swissknife:new swissknife:latest
```

### **Database Migrations**
```python
# alembic/versions/001_initial_migration.py
from alembic import op
import sqlalchemy as sa

def upgrade():
    # Create tables
    op.create_table(
        'users',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('email', sa.String(), unique=True, nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )

def downgrade():
    op.drop_table('users')
```

### **Backup Strategy**
```bash
#!/bin/bash
# backup.sh - Automated backup script

# Database backup
pg_dump -h $DB_HOST -U $DB_USER -d $DB_NAME > backup_$(date +%Y%m%d_%H%M%S).sql

# Upload to S3
aws s3 cp backup_*.sql s3://swissknife-backups/database/

# Clean old backups (keep last 30 days)
find . -name "backup_*.sql" -mtime +30 -delete

# Volume backup
docker run --rm -v swissknife_data:/data -v $(pwd):/backup alpine \
  tar czf /backup/data_backup_$(date +%Y%m%d_%H%M%S).tar.gz /data
```

---

## 🚨 **Disaster Recovery**

### **Backup & Restore Procedures**
```bash
# Full system backup
docker-compose down
docker run --rm -v swissknife_postgres_data:/data -v $(pwd):/backup alpine \
  tar czf /backup/postgres_backup.tar.gz /data
docker run --rm -v swissknife_redis_data:/data -v $(pwd):/backup alpine \
  tar czf /backup/redis_backup.tar.gz /data

# Restore from backup
docker volume create swissknife_postgres_data
docker run --rm -v swissknife_postgres_data:/data -v $(pwd):/backup alpine \
  tar xzf /backup/postgres_backup.tar.gz -C /
```

### **High Availability Setup**
```yaml
# docker-compose.ha.yml
version: '3.8'

services:
  # Multiple backend instances
  swissknife-1:
    <<: *swissknife-service
    container_name: swissknife-1
  
  swissknife-2:
    <<: *swissknife-service
    container_name: swissknife-2
  
  # Load balancer
  haproxy:
    image: haproxy:2.4
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./haproxy/haproxy.cfg:/usr/local/etc/haproxy/haproxy.cfg
    depends_on:
      - swissknife-1
      - swissknife-2
```

---

## 📋 **Deployment Checklist**

### **Pre-Deployment**
- [ ] All tests passing
- [ ] Security scan completed
- [ ] Performance testing done
- [ ] Database migrations prepared
- [ ] Environment variables configured
- [ ] SSL certificates ready
- [ ] Monitoring configured
- [ ] Backup strategy in place

### **Deployment**
- [ ] Build and push Docker images
- [ ] Update environment configuration
- [ ] Run database migrations
- [ ] Deploy application containers
- [ ] Update load balancer configuration
- [ ] Verify health checks
- [ ] Test critical functionality
- [ ] Monitor error rates and performance

### **Post-Deployment**
- [ ] Verify all services running
- [ ] Check application logs
- [ ] Monitor performance metrics
- [ ] Test user authentication
- [ ] Verify scraping functionality
- [ ] Check external API integrations
- [ ] Update documentation
- [ ] Notify stakeholders

---

**This deployment guide ensures reliable, secure, and scalable production deployment of the SwissKnife AI Scraper platform.**

---

**Last Updated**: August 6, 2025  
**Version**: 2.2.0