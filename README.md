# AI-Powered Student Placement System

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![React 18](https://img.shields.io/badge/react-18-blue.svg)](https://reactjs.org/)

A production-ready, LinkedIn-style placement platform with AI-powered resume parsing, intelligent job matching, automated interviews, and candidate evaluation.

## 🎯 Features

### For Students
- **Smart Profile Creation**: Upload CV (PDF/Image), auto-parse education, skills, experience
- **AI Level Detection**: Automatic classification (Beginner/Intermediate/Expert)
- **Intelligent Job Matching**: AI-powered recommendations based on skills and experience
- **AI Interview System**: Automated 10-question interviews tailored to job and skill level
- **Real-time Feedback**: Instant scoring and evaluation reports

### For Companies
- **Job Posting**: Create detailed job listings with requirements
- **Smart Candidate Matching**: AI ranks candidates by fit score (0-100)
- **Automated Shortlisting**: Top candidates auto-selected based on match + interview scores
- **Candidate Analytics**: Detailed evaluation reports with skill breakdowns

### AI Capabilities
- **Resume Parsing**: NLP-powered extraction of structured data from PDFs
- **Semantic Matching**: Sentence embeddings + cosine similarity for job-candidate matching
- **Interview Generation**: Context-aware question generation (MCQ, scenario, technical)
- **Auto-Evaluation**: LLM-based answer scoring with rubrics
- **Behavior Analysis**: Optional face/gaze tracking integration (MediaPipe)

## 🏗️ Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  React Frontend │────▶│  FastAPI Backend│────▶│   PostgreSQL    │
│   (Port 3000)   │     │   (Port 8000)   │     │   (Port 5432)   │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                               │
                               ├──────▶ Redis (Cache/Queue)
                               │
                               ├──────▶ Celery Workers (Async Tasks)
                               │
                               ├──────▶ OpenAI GPT-4/5 (NLP)
                               │
                               └──────▶ S3/MinIO (File Storage)
```

## 📋 Tech Stack

**Frontend**
- React 18 + TypeScript
- Material-UI (MUI) v5
- React Router v6
- Axios + React Query
- Formik + Yup validation

**Backend**
- Python 3.11+
- FastAPI + Uvicorn
- SQLAlchemy 2.0 (ORM)
- Alembic (migrations)
- Celery + Redis (async tasks)
- JWT authentication

**AI/ML**
- OpenAI GPT-4o/GPT-5 (parsing, interview, scoring)
- sentence-transformers (embeddings)
- spaCy (NER)
- scikit-learn (level classifier)
- PyPDF2/pdfminer (PDF extraction)

**Database**
- PostgreSQL 15+
- Redis 7+

**DevOps**
- Docker + Docker Compose
- GitHub Actions (CI/CD)
- AWS ECS / GCP Cloud Run ready

## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose
- Node.js 18+ (for local frontend dev)
- Python 3.11+ (for local backend dev)
- OpenAI API Key

### 1. Clone Repository
```bash
git clone https://github.com/AliAhmed-alt648/ai-student-placement-system.git
cd ai-student-placement-system
```

### 2. Environment Setup
```bash
# Copy environment template
cp .env.example .env

# Edit .env and add your keys
nano .env
```

Required environment variables:
```env
# OpenAI
OPENAI_API_KEY=sk-...

# Database
DATABASE_URL=postgresql://postgres:postgres@db:5432/placement_db

# JWT
JWT_SECRET_KEY=your-secret-key-change-in-production
JWT_ALGORITHM=HS256

# Redis
REDIS_URL=redis://redis:6379/0

# File Storage
UPLOAD_DIR=/app/uploads
MAX_UPLOAD_SIZE=10485760
```

### 3. Run with Docker Compose
```bash
# Build and start all services
docker-compose up --build

# Run in detached mode
docker-compose up -d

# View logs
docker-compose logs -f
```

Services will be available at:
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **PostgreSQL**: localhost:5432
- **Redis**: localhost:6379

### 4. Initialize Database
```bash
# Run migrations
docker-compose exec backend alembic upgrade head

# Load sample data
docker-compose exec backend python scripts/load_sample_data.py
```

### 5. Run Tests
```bash
# Backend tests
docker-compose exec backend pytest -v

# Frontend tests
docker-compose exec frontend npm test

# Integration tests
docker-compose exec backend pytest tests/integration/ -v
```

## 📁 Project Structure

```
ai-student-placement-system/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── auth.py          # Authentication endpoints
│   │   │   ├── students.py      # Student endpoints
│   │   │   ├── companies.py     # Company endpoints
│   │   │   ├── jobs.py          # Job endpoints
│   │   │   └── applications.py  # Application/Interview endpoints
│   │   ├── models/              # SQLAlchemy models
│   │   ├── schemas/             # Pydantic schemas
│   │   ├── services/            # Business logic
│   │   ├── ai_modules/          # AI/ML modules
│   │   │   ├── resume_parser.py
│   │   │   ├── level_detector.py
│   │   │   ├── job_matcher.py
│   │   │   └── interview_agent.py
│   │   ├── core/                # Config, security, database
│   │   └── main.py              # FastAPI app
│   ├── tests/                   # Backend tests
│   ├── alembic/                 # Database migrations
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── components/          # React components
│   │   ├── pages/               # Page components
│   │   ├── services/            # API services
│   │   ├── contexts/            # React contexts
│   │   ├── hooks/               # Custom hooks
│   │   └── App.tsx
│   ├── public/
│   ├── package.json
│   └── Dockerfile
├── mobile/                      # Flutter app (optional)
├── docs/
│   ├── FYP_REPORT.md           # Complete FYP documentation
│   ├── API_DOCUMENTATION.md    # API reference
│   ├── ARCHITECTURE.md         # System architecture
│   └── DEPLOYMENT.md           # Deployment guide
├── sample_data/                # Sample datasets
│   ├── students.json
│   ├── jobs.json
│   └── resumes/
├── scripts/                    # Utility scripts
├── .github/
│   └── workflows/
│       └── ci-cd.yml          # GitHub Actions
├── docker-compose.yml
├── .env.example
└── README.md
```

## 🔑 API Endpoints

### Authentication
- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - Login and get JWT token
- `POST /api/auth/refresh` - Refresh access token

### Students
- `GET /api/students/me` - Get current student profile
- `PUT /api/students/me` - Update profile
- `POST /api/students/me/upload-resume` - Upload and parse resume
- `GET /api/students/:id/resume-parse` - Get parsed resume data

### Companies
- `POST /api/companies` - Create company profile
- `GET /api/companies/:id` - Get company details
- `GET /api/companies/:id/jobs` - List company jobs
- `POST /api/companies/:id/jobs` - Create job posting

### Jobs & Matching
- `GET /api/jobs` - List all jobs (with filters)
- `GET /api/jobs/:id` - Get job details
- `GET /api/jobs/:id/match` - Get matched candidates with scores
- `POST /api/jobs/:id/shortlist` - Auto-shortlist top candidates

### Applications & Interviews
- `POST /api/jobs/:id/apply` - Apply to job
- `GET /api/applications/:id` - Get application details
- `POST /api/applications/:id/start-interview` - Generate interview questions
- `POST /api/applications/:id/submit-interview` - Submit answers
- `GET /api/applications/:id/result` - Get evaluation report

Full API documentation: http://localhost:8000/docs

## 🧪 Testing

### Unit Tests
```bash
# Backend
pytest tests/unit/ -v --cov=app

# Frontend
npm test -- --coverage
```

### Integration Tests
```bash
pytest tests/integration/ -v
```

### Load Testing
```bash
locust -f tests/load/locustfile.py --host=http://localhost:8000
```

## 📊 Sample Data

The system includes sample data for testing:
- **10 Student Profiles**: Varied skills and experience levels
- **8 Job Postings**: Different roles and requirements
- **5 Sample Resumes**: PDF format with diverse formats

Load sample data:
```bash
docker-compose exec backend python scripts/load_sample_data.py
```

## 🔒 Security Features

- **Authentication**: JWT with refresh tokens
- **Password Hashing**: bcrypt with salt
- **Input Validation**: Pydantic schemas
- **SQL Injection Protection**: SQLAlchemy ORM
- **File Upload Security**: Type validation, size limits, malware scanning
- **Rate Limiting**: Per-endpoint throttling
- **CORS**: Configurable origins
- **HTTPS**: TLS/SSL in production
- **Data Encryption**: At-rest encryption for sensitive data

## 🚢 Deployment

### Docker Compose (Development)
```bash
docker-compose up -d
```

### AWS ECS (Production)
See [DEPLOYMENT.md](docs/DEPLOYMENT.md) for detailed steps:
1. Build and push Docker images to ECR
2. Create ECS cluster and task definitions
3. Configure RDS PostgreSQL and ElastiCache Redis
4. Set up Application Load Balancer
5. Configure secrets in AWS Secrets Manager
6. Deploy with CloudFormation/Terraform

### GCP Cloud Run
```bash
# Build and push
gcloud builds submit --tag gcr.io/PROJECT_ID/placement-backend
gcloud builds submit --tag gcr.io/PROJECT_ID/placement-frontend

# Deploy
gcloud run deploy placement-backend --image gcr.io/PROJECT_ID/placement-backend
gcloud run deploy placement-frontend --image gcr.io/PROJECT_ID/placement-frontend
```

## 📈 Performance

**Expected Performance (Production)**
- API Response Time: < 200ms (p95)
- Resume Parsing: < 10s (async)
- Job Matching: < 5s for 1000 candidates
- Interview Generation: < 3s
- Concurrent Users: 1000+ (with horizontal scaling)

**Resource Requirements**
- Backend: 2 vCPU, 4GB RAM (per instance)
- Database: 2 vCPU, 8GB RAM
- Redis: 1 vCPU, 2GB RAM
- Storage: 100GB+ for resumes

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open Pull Request

## 📄 License

This project is licensed under the MIT License - see [LICENSE](LICENSE) file.

## 👥 Authors

- **Ali Ahmed** - Initial work - [AliAhmed-alt648](https://github.com/AliAhmed-alt648)

## 🙏 Acknowledgments

- OpenAI for GPT models
- Hugging Face for sentence-transformers
- FastAPI and React communities

## 📞 Support

For issues and questions:
- GitHub Issues: [Create Issue](https://github.com/AliAhmed-alt648/ai-student-placement-system/issues)
- Email: aalliiahmed0099@gmail.com

## 🗺️ Roadmap

- [ ] Mobile app (Flutter)
- [ ] Video interview recording
- [ ] Advanced behavior analytics
- [ ] Multi-language support
- [ ] Integration with LinkedIn API
- [ ] Blockchain-verified certificates
- [ ] AI-powered career counseling

---

**Built with ❤️ for students and companies**
