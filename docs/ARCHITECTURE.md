# System Architecture
## AI-Powered Student Placement System

**Version:** 1.0.0  
**Last Updated:** November 30, 2025

---

## Table of Contents

1. [Overview](#overview)
2. [High-Level Architecture](#high-level-architecture)
3. [Component Details](#component-details)
4. [Data Flow](#data-flow)
5. [AI Pipeline](#ai-pipeline)
6. [Security Architecture](#security-architecture)
7. [Scalability & Performance](#scalability--performance)
8. [Technology Stack](#technology-stack)

---

## Overview

The AI-Powered Student Placement System follows a modern microservices-inspired architecture with clear separation of concerns, enabling scalability, maintainability, and independent deployment of components.

### Design Principles

1. **Separation of Concerns** - Clear boundaries between layers
2. **Scalability** - Horizontal scaling capability
3. **Resilience** - Fault tolerance and graceful degradation
4. **Security** - Defense in depth
5. **Observability** - Comprehensive logging and monitoring

---

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                          CLIENT LAYER                                │
├─────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │
│  │  React Web   │  │   Flutter    │  │    Admin     │              │
│  │     App      │  │  Mobile App  │  │  Dashboard   │              │
│  │  (Port 3000) │  │   (Mobile)   │  │  (Port 3001) │              │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘              │
│         │                  │                  │                       │
│         └──────────────────┼──────────────────┘                       │
│                            │                                          │
└────────────────────────────┼──────────────────────────────────────────┘
                             │
                    ┌────────▼────────┐
                    │   Load Balancer │
                    │   (Nginx/ALB)   │
                    └────────┬────────┘
                             │
┌────────────────────────────┼──────────────────────────────────────────┐
│                      API GATEWAY LAYER                                │
├────────────────────────────┼──────────────────────────────────────────┤
│                            │                                          │
│                    ┌───────▼────────┐                                │
│                    │   FastAPI      │                                │
│                    │   Gateway      │                                │
│                    │  (Port 8000)   │                                │
│                    │                │                                │
│                    │ • Auth         │                                │
│                    │ • Validation   │                                │
│                    │ • Rate Limit   │                                │
│                    │ • CORS         │                                │
│                    └───────┬────────┘                                │
│                            │                                          │
└────────────────────────────┼──────────────────────────────────────────┘
                             │
        ┌────────────────────┼────────────────────┐
        │                    │                    │
┌───────▼────────┐  ┌────────▼────────┐  ┌───────▼────────┐
│   Auth Service │  │ Business Logic  │  │  AI Services   │
│                │  │                 │  │                │
│ • JWT          │  │ • Students      │  │ • Parser       │
│ • Sessions     │  │ • Companies     │  │ • Matcher      │
│ • Permissions  │  │ • Jobs          │  │ • Interviewer  │
│                │  │ • Applications  │  │ • Classifier   │
└───────┬────────┘  └────────┬────────┘  └───────┬────────┘
        │                    │                    │
        └────────────────────┼────────────────────┘
                             │
┌────────────────────────────┼──────────────────────────────────────────┐
│                       DATA LAYER                                      │
├────────────────────────────┼──────────────────────────────────────────┤
│                            │                                          │
│  ┌─────────────┐  ┌────────▼────────┐  ┌─────────────┐             │
│  │ PostgreSQL  │  │     Redis       │  │   S3/MinIO  │             │
│  │             │  │                 │  │             │             │
│  │ • Users     │  │ • Cache         │  │ • Resumes   │             │
│  │ • Students  │  │ • Sessions      │  │ • Images    │             │
│  │ • Jobs      │  │ • Queue         │  │ • Documents │             │
│  │ • Apps      │  │ • Pub/Sub       │  │             │             │
│  └─────────────┘  └─────────────────┘  └─────────────┘             │
│                                                                       │
└───────────────────────────────────────────────────────────────────────┘

┌───────────────────────────────────────────────────────────────────────┐
│                    EXTERNAL SERVICES                                  │
├───────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │
│  │   OpenAI     │  │   SendGrid   │  │   Twilio     │              │
│  │   GPT-4      │  │    Email     │  │     SMS      │              │
│  └──────────────┘  └──────────────┘  └──────────────┘              │
│                                                                       │
└───────────────────────────────────────────────────────────────────────┘
```

---

## Component Details

### 1. Client Layer

#### React Web Application
- **Technology:** React 18 + TypeScript
- **UI Framework:** Material-UI v5
- **State Management:** React Context + React Query
- **Routing:** React Router v6
- **Features:**
  - Responsive design
  - Progressive Web App (PWA)
  - Offline support
  - Real-time updates

#### Flutter Mobile App (Optional)
- **Platform:** iOS + Android
- **State Management:** Provider/Riverpod
- **Features:**
  - Native performance
  - Push notifications
  - Camera integration for resume scanning

#### Admin Dashboard
- **Purpose:** Placement officer management
- **Features:**
  - Analytics and reporting
  - User management
  - System configuration

### 2. API Gateway Layer

#### FastAPI Gateway
- **Port:** 8000
- **Responsibilities:**
  - Request routing
  - Authentication (JWT)
  - Input validation (Pydantic)
  - Rate limiting
  - CORS handling
  - API documentation (OpenAPI)

**Middleware Stack:**
```python
Request
  ↓
CORS Middleware
  ↓
Rate Limiting
  ↓
Authentication
  ↓
Request Validation
  ↓
Business Logic
  ↓
Response Formatting
  ↓
Response
```

### 3. Service Layer

#### Authentication Service
- **JWT Token Management**
  - Access tokens (30 min expiry)
  - Refresh tokens (7 day expiry)
  - Token rotation
- **Password Security**
  - bcrypt hashing (12 rounds)
  - Password strength validation
- **Session Management**
  - Redis-backed sessions
  - Multi-device support

#### Business Logic Services

**Student Service:**
- Profile management
- Resume upload and parsing
- Application tracking
- Interview management

**Company Service:**
- Company profile management
- Job posting
- Candidate review
- Hiring analytics

**Job Service:**
- Job CRUD operations
- Search and filtering
- Candidate matching
- Shortlisting

**Application Service:**
- Application submission
- Status tracking
- Interview scheduling
- Evaluation

### 4. AI Services Layer

#### Resume Parser
```
PDF Input
  ↓
Text Extraction (PyPDF2/pdfminer)
  ↓
Text Cleaning
  ↓
┌─────────────┬─────────────┬─────────────┐
│   Regex     │   spaCy     │   GPT-4     │
│  Patterns   │    NER      │   Parser    │
└─────────────┴─────────────┴─────────────┘
  ↓
Result Merging
  ↓
Confidence Scoring
  ↓
Structured JSON Output
```

**Performance:**
- Processing time: 8-12 seconds
- Accuracy: 85%
- Concurrent processing: 10 resumes

#### Level Detector
```
Resume Data
  ↓
Feature Extraction (8 features)
  ↓
┌─────────────────┬─────────────────┐
│   Heuristic     │   ML Classifier │
│     Rules       │  (Random Forest)│
└─────────────────┴─────────────────┘
  ↓
Level Classification
  ↓
Confidence Score
  ↓
{level, confidence, reasoning}
```

#### Job Matcher
```
Student Profile + Job Description
  ↓
Text Preprocessing
  ↓
┌──────────────────────────────────┐
│  Sentence-BERT Embeddings        │
│  (all-mpnet-base-v2)             │
└──────────────────────────────────┘
  ↓
Cosine Similarity
  ↓
┌──────────────────────────────────┐
│  Weighted Scoring                │
│  • Skills: 60%                   │
│  • Experience: 25%               │
│  • Education: 15%                │
└──────────────────────────────────┘
  ↓
Match Score (0-100)
  ↓
Ranking + Recommendations
```

#### Interview Agent
```
Job + Student Profile
  ↓
Context Analysis
  ↓
GPT-4 Question Generation
  ↓
10 Questions (MCQ + Scenario + Technical)
  ↓
Student Answers
  ↓
┌──────────────────────────────────┐
│  Answer Evaluation               │
│  • MCQ: Direct comparison        │
│  • Open: GPT-4 + Rubric          │
└──────────────────────────────────┘
  ↓
Per-Question Scores
  ↓
Overall Score + Grade + Summary
```

### 5. Data Layer

#### PostgreSQL Database
- **Version:** 15+
- **Schema:** See `database/schema.sql`
- **Features:**
  - JSONB for flexible data
  - Full-text search
  - GIN indexes
  - Triggers and views
- **Backup:** Daily automated backups
- **Replication:** Master-slave setup (production)

#### Redis Cache
- **Version:** 7+
- **Use Cases:**
  - Session storage
  - API response caching
  - Celery task queue
  - Pub/Sub for real-time updates
- **Eviction Policy:** LRU
- **Persistence:** RDB + AOF

#### S3/MinIO Storage
- **Purpose:** File storage
- **Contents:**
  - Resume PDFs
  - Profile images
  - Company logos
  - Interview recordings
- **Features:**
  - Versioning enabled
  - Encryption at rest
  - CDN integration

---

## Data Flow

### 1. Student Registration Flow

```
Student → Register Form
  ↓
POST /api/auth/register
  ↓
Validate Input (Pydantic)
  ↓
Hash Password (bcrypt)
  ↓
Create User Record (PostgreSQL)
  ↓
Generate JWT Tokens
  ↓
Return {access_token, refresh_token}
  ↓
Store Session (Redis)
  ↓
Redirect to Profile Setup
```

### 2. Resume Upload & Parsing Flow

```
Student → Upload Resume (PDF)
  ↓
POST /api/students/me/upload-resume
  ↓
Validate File (type, size)
  ↓
Upload to S3
  ↓
Create Celery Task
  ↓
Background Processing:
  ├─ Extract Text
  ├─ Parse with AI
  ├─ Detect Level
  └─ Update Database
  ↓
Notify Student (WebSocket/Email)
  ↓
Display Parsed Data
```

### 3. Job Application Flow

```
Student → Apply to Job
  ↓
POST /api/jobs/:id/apply
  ↓
Check Eligibility
  ↓
Create Application Record
  ↓
Background Processing:
  ├─ Calculate Match Score
  ├─ Generate Interview Questions
  └─ Update Application
  ↓
Notify Student & Company
  ↓
Return Application Details
```

### 4. AI Interview Flow

```
Student → Start Interview
  ↓
POST /api/applications/:id/start-interview
  ↓
Fetch Job + Student Data
  ↓
Generate Questions (GPT-4)
  ↓
Return Questions
  ↓
Student Answers Questions
  ↓
POST /api/applications/:id/submit-interview
  ↓
Background Processing:
  ├─ Evaluate Each Answer
  ├─ Calculate Scores
  ├─ Generate Summary
  └─ Update Application
  ↓
Notify Student & Company
  ↓
Display Results
```

---

## AI Pipeline

### Resume Parsing Pipeline

```
┌─────────────────────────────────────────────────────────────┐
│                    RESUME PARSING PIPELINE                   │
└─────────────────────────────────────────────────────────────┘

Input: PDF File
  ↓
┌─────────────────────────────────────────────────────────────┐
│ Stage 1: Text Extraction                                     │
│ • PyPDF2 (primary)                                           │
│ • pdfminer (fallback)                                        │
│ • OCR (for image-based PDFs)                                 │
└─────────────────────────────────────────────────────────────┘
  ↓
┌─────────────────────────────────────────────────────────────┐
│ Stage 2: Text Cleaning                                       │
│ • Remove extra whitespace                                    │
│ • Normalize characters                                       │
│ • Fix encoding issues                                        │
└─────────────────────────────────────────────────────────────┘
  ↓
┌─────────────────────────────────────────────────────────────┐
│ Stage 3: Multi-Method Extraction                             │
│                                                              │
│ ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│ │    Regex     │  │    spaCy     │  │    GPT-4     │      │
│ │   Patterns   │  │     NER      │  │   Parsing    │      │
│ │              │  │              │  │              │      │
│ │ • Email      │  │ • PERSON     │  │ • Education  │      │
│ │ • Phone      │  │ • ORG        │  │ • Experience │      │
│ │ • URLs       │  │ • DATE       │  │ • Skills     │      │
│ └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
  ↓
┌─────────────────────────────────────────────────────────────┐
│ Stage 4: Result Merging                                      │
│ • Combine results from all methods                           │
│ • Resolve conflicts (GPT-4 takes precedence)                 │
│ • Fill gaps with fallback methods                            │
└─────────────────────────────────────────────────────────────┘
  ↓
┌─────────────────────────────────────────────────────────────┐
│ Stage 5: Confidence Scoring                                  │
│ • Per-field confidence (0-100)                               │
│ • Overall extraction quality                                 │
│ • Flag for manual review if < 70%                            │
└─────────────────────────────────────────────────────────────┘
  ↓
Output: Structured JSON + Confidence Scores
```

### Job Matching Pipeline

```
┌─────────────────────────────────────────────────────────────┐
│                   JOB MATCHING PIPELINE                      │
└─────────────────────────────────────────────────────────────┘

Input: Student Profile + Job Description
  ↓
┌─────────────────────────────────────────────────────────────┐
│ Stage 1: Text Preparation                                    │
│ • Create student text (skills + experience + education)      │
│ • Create job text (requirements + description)               │
└─────────────────────────────────────────────────────────────┘
  ↓
┌─────────────────────────────────────────────────────────────┐
│ Stage 2: Embedding Generation                                │
│ • Model: all-mpnet-base-v2                                   │
│ • Dimension: 768                                             │
│ • Cache embeddings for performance                           │
└─────────────────────────────────────────────────────────────┘
  ↓
┌─────────────────────────────────────────────────────────────┐
│ Stage 3: Multi-Criteria Scoring                              │
│                                                              │
│ ┌──────────────────────────────────────────────────────┐   │
│ │ Skill Match (60% weight)                             │   │
│ │ • Exact keyword matching                             │   │
│ │ • Required vs Preferred                              │   │
│ │ • Score: 0-100                                       │   │
│ └──────────────────────────────────────────────────────┘   │
│                                                              │
│ ┌──────────────────────────────────────────────────────┐   │
│ │ Experience Match (25% weight)                        │   │
│ │ • Years comparison                                   │   │
│ │ • Overqualification penalty                          │   │
│ │ • Score: 0-100                                       │   │
│ └──────────────────────────────────────────────────────┘   │
│                                                              │
│ ┌──────────────────────────────────────────────────────┐   │
│ │ Education Match (15% weight)                         │   │
│ │ • Degree level comparison                            │   │
│ │ • Major relevance                                    │   │
│ │ • Score: 0-100                                       │   │
│ └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
  ↓
┌─────────────────────────────────────────────────────────────┐
│ Stage 4: Semantic Similarity Boost                           │
│ • Cosine similarity of embeddings                            │
│ • Small boost (max +5 points)                                │
└─────────────────────────────────────────────────────────────┘
  ↓
┌─────────────────────────────────────────────────────────────┐
│ Stage 5: Final Score Calculation                             │
│ Match Score = (Skill × 0.6) + (Exp × 0.25) + (Edu × 0.15)  │
│             + (Semantic Boost)                               │
└─────────────────────────────────────────────────────────────┘
  ↓
Output: Match Score (0-100) + Matched Skills + Missing Skills
```

---

## Security Architecture

### Defense in Depth

```
┌─────────────────────────────────────────────────────────────┐
│ Layer 1: Network Security                                    │
│ • Firewall rules                                             │
│ • DDoS protection (CloudFlare/AWS Shield)                    │
│ • VPC isolation                                              │
└─────────────────────────────────────────────────────────────┘
  ↓
┌─────────────────────────────────────────────────────────────┐
│ Layer 2: Application Security                                │
│ • HTTPS/TLS 1.3                                              │
│ • CORS configuration                                         │
│ • Rate limiting                                              │
│ • Input validation                                           │
└─────────────────────────────────────────────────────────────┘
  ↓
┌─────────────────────────────────────────────────────────────┐
│ Layer 3: Authentication & Authorization                      │
│ • JWT with refresh tokens                                    │
│ • Role-based access control (RBAC)                           │
│ • Session management                                         │
└─────────────────────────────────────────────────────────────┘
  ↓
┌─────────────────────────────────────────────────────────────┐
│ Layer 4: Data Security                                       │
│ • Encryption at rest (AES-256)                               │
│ • Encryption in transit (TLS)                                │
│ • Password hashing (bcrypt)                                  │
│ • Secure file storage                                        │
└─────────────────────────────────────────────────────────────┘
  ↓
┌─────────────────────────────────────────────────────────────┐
│ Layer 5: Monitoring & Auditing                               │
│ • Audit logs                                                 │
│ • Security alerts                                            │
│ • Intrusion detection                                        │
└─────────────────────────────────────────────────────────────┘
```

---

## Scalability & Performance

### Horizontal Scaling

```
                    Load Balancer
                         │
        ┌────────────────┼────────────────┐
        │                │                │
   Backend 1        Backend 2        Backend 3
        │                │                │
        └────────────────┼────────────────┘
                         │
                    Shared State
                    (Redis + DB)
```

### Caching Strategy

```
Request
  ↓
Check Redis Cache
  ├─ Hit → Return Cached Response
  └─ Miss → Process Request
              ↓
         Query Database
              ↓
         Cache Result (TTL: 5min)
              ↓
         Return Response
```

### Performance Targets

| Metric | Target | Strategy |
|--------|--------|----------|
| API Response Time (p95) | <500ms | Caching, indexing |
| Resume Parsing | <15s | Async processing |
| Job Matching (1000 candidates) | <5s | Embeddings cache |
| Concurrent Users | 1000+ | Horizontal scaling |
| Database Queries | <100ms | Indexes, connection pooling |

---

## Technology Stack

### Backend
- **Framework:** FastAPI 0.109+
- **Language:** Python 3.11+
- **ORM:** SQLAlchemy 2.0
- **Migrations:** Alembic
- **Task Queue:** Celery + Redis
- **AI/ML:** OpenAI GPT-4, sentence-transformers, spaCy, scikit-learn

### Frontend
- **Framework:** React 18
- **Language:** TypeScript
- **UI:** Material-UI v5
- **State:** React Query + Context
- **Routing:** React Router v6

### Database
- **Primary:** PostgreSQL 15+
- **Cache:** Redis 7+
- **Storage:** S3/MinIO

### DevOps
- **Containers:** Docker + Docker Compose
- **CI/CD:** GitHub Actions
- **Cloud:** AWS ECS / GCP Cloud Run
- **Monitoring:** CloudWatch / Prometheus + Grafana

---

**Last Updated:** November 30, 2025  
**Version:** 1.0.0
