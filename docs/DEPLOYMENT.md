# Deployment Guide
## AI Student Placement System

This guide covers deployment strategies for development, staging, and production environments.

---

## Table of Contents

1. [Local Development](#local-development)
2. [Docker Deployment](#docker-deployment)
3. [AWS Deployment](#aws-deployment)
4. [GCP Deployment](#gcp-deployment)
5. [Azure Deployment](#azure-deployment)
6. [CI/CD Pipeline](#cicd-pipeline)
7. [Monitoring & Logging](#monitoring--logging)
8. [Backup & Recovery](#backup--recovery)

---

## Local Development

### Prerequisites
- Docker & Docker Compose
- Node.js 18+
- Python 3.11+
- PostgreSQL 15+ (optional if using Docker)

### Setup Steps

1. **Clone Repository**
```bash
git clone https://github.com/AliAhmed-alt648/ai-student-placement-system.git
cd ai-student-placement-system
```

2. **Environment Configuration**
```bash
cp .env.example .env
# Edit .env with your values
nano .env
```

3. **Start Services**
```bash
docker-compose up -d
```

4. **Initialize Database**
```bash
docker-compose exec backend alembic upgrade head
docker-compose exec backend python scripts/load_sample_data.py
```

5. **Access Application**
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

---

## Docker Deployment

### Production Build

1. **Build Images**
```bash
# Backend
docker build -t placement-backend:latest ./backend

# Frontend
docker build -t placement-frontend:latest ./frontend
```

2. **Run with Docker Compose**
```bash
docker-compose -f docker-compose.prod.yml up -d
```

3. **Health Checks**
```bash
docker-compose ps
docker-compose logs -f backend
```

### Docker Compose Production

Create `docker-compose.prod.yml`:

```yaml
version: '3.8'

services:
  db:
    image: postgres:15-alpine
    environment:
      POSTGRES_USER: ${DB_USER}
      POSTGRES_PASSWORD: ${DB_PASSWORD}
      POSTGRES_DB: ${DB_NAME}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: always

  redis:
    image: redis:7-alpine
    restart: always

  backend:
    image: placement-backend:latest
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - JWT_SECRET_KEY=${JWT_SECRET_KEY}
      - ENVIRONMENT=production
      - DEBUG=false
    ports:
      - "8000:8000"
    depends_on:
      - db
      - redis
    restart: always

  frontend:
    image: placement-frontend:latest
    environment:
      - REACT_APP_API_URL=${API_URL}
    ports:
      - "80:80"
    depends_on:
      - backend
    restart: always

  nginx:
    image: nginx:alpine
    ports:
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf
      - ./nginx/ssl:/etc/nginx/ssl
    depends_on:
      - backend
      - frontend
    restart: always

volumes:
  postgres_data:
```

---

## AWS Deployment

### Architecture

```
Internet → Route 53 → CloudFront → ALB → ECS (Fargate)
                                      ↓
                                    RDS (PostgreSQL)
                                    ElastiCache (Redis)
                                    S3 (File Storage)
```

### Step-by-Step Deployment

#### 1. Setup AWS CLI
```bash
aws configure
# Enter AWS Access Key ID
# Enter AWS Secret Access Key
# Default region: us-east-1
```

#### 2. Create ECR Repositories
```bash
# Backend repository
aws ecr create-repository --repository-name placement-backend

# Frontend repository
aws ecr create-repository --repository-name placement-frontend

# Get login command
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <account-id>.dkr.ecr.us-east-1.amazonaws.com
```

#### 3. Build and Push Images
```bash
# Backend
docker build -t placement-backend:latest ./backend
docker tag placement-backend:latest <account-id>.dkr.ecr.us-east-1.amazonaws.com/placement-backend:latest
docker push <account-id>.dkr.ecr.us-east-1.amazonaws.com/placement-backend:latest

# Frontend
docker build -t placement-frontend:latest ./frontend
docker tag placement-frontend:latest <account-id>.dkr.ecr.us-east-1.amazonaws.com/placement-frontend:latest
docker push <account-id>.dkr.ecr.us-east-1.amazonaws.com/placement-frontend:latest
```

#### 4. Create RDS Database
```bash
aws rds create-db-instance \
  --db-instance-identifier placement-db \
  --db-instance-class db.t3.medium \
  --engine postgres \
  --engine-version 15.3 \
  --master-username admin \
  --master-user-password <secure-password> \
  --allocated-storage 100 \
  --vpc-security-group-ids sg-xxxxx \
  --db-subnet-group-name default \
  --backup-retention-period 7 \
  --multi-az
```

#### 5. Create ElastiCache Redis
```bash
aws elasticache create-cache-cluster \
  --cache-cluster-id placement-redis \
  --cache-node-type cache.t3.medium \
  --engine redis \
  --num-cache-nodes 1 \
  --security-group-ids sg-xxxxx
```

#### 6. Create S3 Bucket
```bash
aws s3 mb s3://placement-resumes-prod
aws s3api put-bucket-encryption \
  --bucket placement-resumes-prod \
  --server-side-encryption-configuration '{
    "Rules": [{
      "ApplyServerSideEncryptionByDefault": {
        "SSEAlgorithm": "AES256"
      }
    }]
  }'
```

#### 7. Create ECS Cluster
```bash
aws ecs create-cluster --cluster-name placement-cluster
```

#### 8. Create Task Definitions

**Backend Task Definition** (`backend-task-def.json`):
```json
{
  "family": "placement-backend",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "1024",
  "memory": "2048",
  "containerDefinitions": [
    {
      "name": "backend",
      "image": "<account-id>.dkr.ecr.us-east-1.amazonaws.com/placement-backend:latest",
      "portMappings": [
        {
          "containerPort": 8000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {"name": "ENVIRONMENT", "value": "production"},
        {"name": "DEBUG", "value": "false"}
      ],
      "secrets": [
        {"name": "DATABASE_URL", "valueFrom": "arn:aws:secretsmanager:..."},
        {"name": "OPENAI_API_KEY", "valueFrom": "arn:aws:secretsmanager:..."},
        {"name": "JWT_SECRET_KEY", "valueFrom": "arn:aws:secretsmanager:..."}
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/placement-backend",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "ecs"
        }
      }
    }
  ]
}
```

Register task definition:
```bash
aws ecs register-task-definition --cli-input-json file://backend-task-def.json
```

#### 9. Create Application Load Balancer
```bash
aws elbv2 create-load-balancer \
  --name placement-alb \
  --subnets subnet-xxxxx subnet-yyyyy \
  --security-groups sg-xxxxx \
  --scheme internet-facing \
  --type application
```

#### 10. Create ECS Service
```bash
aws ecs create-service \
  --cluster placement-cluster \
  --service-name placement-backend-service \
  --task-definition placement-backend \
  --desired-count 2 \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[subnet-xxxxx],securityGroups=[sg-xxxxx],assignPublicIp=ENABLED}" \
  --load-balancers "targetGroupArn=arn:aws:elasticloadbalancing:...,containerName=backend,containerPort=8000"
```

#### 11. Setup Auto Scaling
```bash
aws application-autoscaling register-scalable-target \
  --service-namespace ecs \
  --resource-id service/placement-cluster/placement-backend-service \
  --scalable-dimension ecs:service:DesiredCount \
  --min-capacity 2 \
  --max-capacity 10

aws application-autoscaling put-scaling-policy \
  --service-namespace ecs \
  --resource-id service/placement-cluster/placement-backend-service \
  --scalable-dimension ecs:service:DesiredCount \
  --policy-name cpu-scaling \
  --policy-type TargetTrackingScaling \
  --target-tracking-scaling-policy-configuration file://scaling-policy.json
```

#### 12. Configure Secrets Manager
```bash
aws secretsmanager create-secret \
  --name placement/database-url \
  --secret-string "postgresql://admin:password@placement-db.xxxxx.us-east-1.rds.amazonaws.com:5432/placement_db"

aws secretsmanager create-secret \
  --name placement/openai-api-key \
  --secret-string "sk-your-openai-key"

aws secretsmanager create-secret \
  --name placement/jwt-secret \
  --secret-string "your-jwt-secret-key"
```

### Cost Estimation (Monthly)

| Service | Configuration | Cost |
|---------|--------------|------|
| ECS Fargate | 2 tasks (1 vCPU, 2GB) | ~$60 |
| RDS PostgreSQL | db.t3.medium | ~$70 |
| ElastiCache Redis | cache.t3.medium | ~$50 |
| ALB | Standard | ~$20 |
| S3 | 100GB storage | ~$3 |
| Data Transfer | 1TB | ~$90 |
| **Total** | | **~$293/month** |

---

## GCP Deployment

### Architecture

```
Internet → Cloud Load Balancing → Cloud Run
                                    ↓
                                  Cloud SQL (PostgreSQL)
                                  Memorystore (Redis)
                                  Cloud Storage
```

### Step-by-Step Deployment

#### 1. Setup GCP CLI
```bash
gcloud init
gcloud config set project <project-id>
```

#### 2. Enable Required APIs
```bash
gcloud services enable \
  run.googleapis.com \
  sql-component.googleapis.com \
  redis.googleapis.com \
  storage-api.googleapis.com \
  cloudbuild.googleapis.com
```

#### 3. Create Cloud SQL Instance
```bash
gcloud sql instances create placement-db \
  --database-version=POSTGRES_15 \
  --tier=db-custom-2-7680 \
  --region=us-central1 \
  --backup \
  --backup-start-time=03:00

gcloud sql databases create placement_db --instance=placement-db

gcloud sql users create admin \
  --instance=placement-db \
  --password=<secure-password>
```

#### 4. Create Memorystore Redis
```bash
gcloud redis instances create placement-redis \
  --size=2 \
  --region=us-central1 \
  --redis-version=redis_7_0
```

#### 5. Create Cloud Storage Bucket
```bash
gsutil mb -l us-central1 gs://placement-resumes-prod
gsutil versioning set on gs://placement-resumes-prod
```

#### 6. Build and Deploy to Cloud Run

**Backend:**
```bash
gcloud builds submit --tag gcr.io/<project-id>/placement-backend ./backend

gcloud run deploy placement-backend \
  --image gcr.io/<project-id>/placement-backend \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --memory 2Gi \
  --cpu 2 \
  --min-instances 1 \
  --max-instances 10 \
  --set-env-vars ENVIRONMENT=production \
  --set-secrets DATABASE_URL=placement-database-url:latest,OPENAI_API_KEY=placement-openai-key:latest
```

**Frontend:**
```bash
gcloud builds submit --tag gcr.io/<project-id>/placement-frontend ./frontend

gcloud run deploy placement-frontend \
  --image gcr.io/<project-id>/placement-frontend \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated
```

#### 7. Setup Cloud Load Balancer
```bash
gcloud compute backend-services create placement-backend-service \
  --global \
  --load-balancing-scheme=EXTERNAL

gcloud compute url-maps create placement-lb \
  --default-service placement-backend-service

gcloud compute target-http-proxies create placement-http-proxy \
  --url-map placement-lb

gcloud compute forwarding-rules create placement-http-rule \
  --global \
  --target-http-proxy placement-http-proxy \
  --ports 80
```

### Cost Estimation (Monthly)

| Service | Configuration | Cost |
|---------|--------------|------|
| Cloud Run | 2 instances (2 vCPU, 2GB) | ~$50 |
| Cloud SQL | db-custom-2-7680 | ~$80 |
| Memorystore | 2GB Redis | ~$40 |
| Cloud Storage | 100GB | ~$2 |
| Load Balancing | Standard | ~$20 |
| **Total** | | **~$192/month** |

---

## Azure Deployment

### Quick Deploy

1. **Create Resource Group**
```bash
az group create --name placement-rg --location eastus
```

2. **Deploy Container Instances**
```bash
az container create \
  --resource-group placement-rg \
  --name placement-backend \
  --image <registry>/placement-backend:latest \
  --cpu 2 \
  --memory 4 \
  --ports 8000 \
  --environment-variables \
    ENVIRONMENT=production \
    DATABASE_URL=<connection-string>
```

3. **Create Azure Database for PostgreSQL**
```bash
az postgres flexible-server create \
  --resource-group placement-rg \
  --name placement-db \
  --location eastus \
  --admin-user admin \
  --admin-password <password> \
  --sku-name Standard_D2s_v3 \
  --version 15
```

---

## CI/CD Pipeline

### GitHub Actions Workflow

See `.github/workflows/ci-cd.yml` for complete pipeline.

**Pipeline Stages:**
1. **Lint & Test** - Run tests and code quality checks
2. **Build** - Build Docker images
3. **Push** - Push to container registry
4. **Deploy** - Deploy to staging/production

**Secrets Required:**
- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`
- `OPENAI_API_KEY`
- `JWT_SECRET_KEY`
- `DATABASE_URL`

---

## Monitoring & Logging

### AWS CloudWatch

1. **Create Log Groups**
```bash
aws logs create-log-group --log-group-name /ecs/placement-backend
aws logs create-log-group --log-group-name /ecs/placement-frontend
```

2. **Create Alarms**
```bash
aws cloudwatch put-metric-alarm \
  --alarm-name high-cpu \
  --alarm-description "Alert when CPU exceeds 80%" \
  --metric-name CPUUtilization \
  --namespace AWS/ECS \
  --statistic Average \
  --period 300 \
  --threshold 80 \
  --comparison-operator GreaterThanThreshold
```

### Sentry Integration

Add to `.env`:
```
SENTRY_DSN=https://xxxxx@sentry.io/xxxxx
```

### Prometheus + Grafana

Deploy monitoring stack:
```bash
docker-compose -f docker-compose.monitoring.yml up -d
```

---

## Backup & Recovery

### Database Backups

**Automated Backups (AWS RDS):**
```bash
aws rds modify-db-instance \
  --db-instance-identifier placement-db \
  --backup-retention-period 30 \
  --preferred-backup-window "03:00-04:00"
```

**Manual Backup:**
```bash
pg_dump -h <host> -U admin placement_db > backup_$(date +%Y%m%d).sql
```

**Restore:**
```bash
psql -h <host> -U admin placement_db < backup_20251130.sql
```

### File Storage Backups

**S3 Versioning:**
```bash
aws s3api put-bucket-versioning \
  --bucket placement-resumes-prod \
  --versioning-configuration Status=Enabled
```

---

## Security Checklist

- [ ] Enable HTTPS/TLS
- [ ] Configure WAF rules
- [ ] Enable DDoS protection
- [ ] Rotate secrets regularly
- [ ] Enable audit logging
- [ ] Configure VPC/firewall rules
- [ ] Enable encryption at rest
- [ ] Setup backup strategy
- [ ] Configure monitoring alerts
- [ ] Implement rate limiting

---

## Troubleshooting

### Common Issues

**1. Database Connection Failed**
```bash
# Check security group rules
# Verify connection string
# Test connection
psql -h <host> -U admin -d placement_db
```

**2. High Memory Usage**
```bash
# Check container logs
docker logs placement-backend

# Increase memory allocation
# Optimize queries
```

**3. Slow API Response**
```bash
# Enable query logging
# Check Redis cache
# Review CloudWatch metrics
```

---

**Last Updated:** November 30, 2025  
**Maintained By:** Ali Ahmed
