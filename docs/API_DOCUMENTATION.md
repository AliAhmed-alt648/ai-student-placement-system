# API Documentation
## AI Student Placement System REST API

**Base URL:** `http://localhost:8000/api`  
**Version:** 1.0.0  
**Authentication:** JWT Bearer Token

---

## Table of Contents

1. [Authentication](#authentication)
2. [Students](#students)
3. [Companies](#companies)
4. [Jobs](#jobs)
5. [Applications](#applications)
6. [Interviews](#interviews)
7. [Error Handling](#error-handling)
8. [Rate Limiting](#rate-limiting)

---

## Authentication

### Register User

**Endpoint:** `POST /auth/register`

**Description:** Register a new user (student, company, or admin)

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "SecurePassword123!",
  "role": "student",
  "full_name": "John Doe"
}
```

**Response:** `201 Created`
```json
{
  "success": true,
  "data": {
    "user_id": "uuid",
    "email": "user@example.com",
    "role": "student",
    "created_at": "2025-11-30T12:00:00Z"
  }
}
```

---

### Login

**Endpoint:** `POST /auth/login`

**Description:** Authenticate user and receive JWT tokens

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "SecurePassword123!"
}
```

**Response:** `200 OK`
```json
{
  "success": true,
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer",
    "expires_in": 1800,
    "user": {
      "id": "uuid",
      "email": "user@example.com",
      "role": "student"
    }
  }
}
```

---

### Refresh Token

**Endpoint:** `POST /auth/refresh`

**Description:** Get new access token using refresh token

**Request Body:**
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Response:** `200 OK`
```json
{
  "success": true,
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer",
    "expires_in": 1800
  }
}
```

---

## Students

### Get Current Student Profile

**Endpoint:** `GET /students/me`

**Headers:** `Authorization: Bearer {access_token}`

**Response:** `200 OK`
```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "user_id": "uuid",
    "full_name": "John Doe",
    "email": "john@example.com",
    "phone": "+1-555-0123",
    "bio": "Passionate developer...",
    "level": "Intermediate",
    "level_confidence": 85.5,
    "education": [...],
    "experience": [...],
    "skills": [...],
    "projects": [...],
    "certifications": [...],
    "total_experience_years": 3.5,
    "resume_url": "https://...",
    "created_at": "2025-01-01T00:00:00Z",
    "updated_at": "2025-11-30T12:00:00Z"
  }
}
```

---

### Update Student Profile

**Endpoint:** `PUT /students/me`

**Headers:** `Authorization: Bearer {access_token}`

**Request Body:**
```json
{
  "full_name": "John Doe",
  "phone": "+1-555-0123",
  "bio": "Updated bio...",
  "skills": [
    {"name": "Python", "proficiency": "Advanced", "years": 4}
  ],
  "education": [...],
  "experience": [...],
  "projects": [...]
}
```

**Response:** `200 OK`

---

### Upload Resume

**Endpoint:** `POST /students/me/upload-resume`

**Headers:** 
- `Authorization: Bearer {access_token}`
- `Content-Type: multipart/form-data`

**Request Body:** (multipart/form-data)
- `file`: PDF/DOCX file (max 10MB)

**Response:** `200 OK`
```json
{
  "success": true,
  "data": {
    "resume_url": "https://storage.../resume.pdf",
    "parsed_data": {
      "name": "John Doe",
      "email": "john@example.com",
      "phone": "+1-555-0123",
      "education": [...],
      "experience": [...],
      "skills": [...],
      "confidence_scores": {
        "overall": 85,
        "name": 95,
        "email": 100,
        "skills": 80
      }
    },
    "level_detection": {
      "level": "Intermediate",
      "confidence": 85.5,
      "method": "heuristic",
      "reasoning": "..."
    }
  }
}
```

---

### Get Parsed Resume

**Endpoint:** `GET /students/:id/resume-parse`

**Headers:** `Authorization: Bearer {access_token}`

**Response:** `200 OK`
```json
{
  "success": true,
  "data": {
    "parsed_data": {...},
    "level_detection": {...}
  }
}
```

---

## Companies

### Create Company Profile

**Endpoint:** `POST /companies`

**Headers:** `Authorization: Bearer {access_token}`

**Request Body:**
```json
{
  "company_name": "TechCorp Inc",
  "website": "https://techcorp.com",
  "industry": "Technology",
  "company_size": "51-200",
  "address": "123 Tech Street",
  "city": "San Francisco",
  "state": "CA",
  "country": "USA",
  "description": "Leading tech company...",
  "contact_email": "hr@techcorp.com",
  "contact_phone": "+1-555-9999"
}
```

**Response:** `201 Created`

---

### Get Company Details

**Endpoint:** `GET /companies/:id`

**Response:** `200 OK`
```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "company_name": "TechCorp Inc",
    "website": "https://techcorp.com",
    "logo_url": "https://...",
    "industry": "Technology",
    "company_size": "51-200",
    "description": "...",
    "is_verified": true,
    "created_at": "2025-01-01T00:00:00Z"
  }
}
```

---

### List Company Jobs

**Endpoint:** `GET /companies/:id/jobs`

**Query Parameters:**
- `status`: Filter by status (active, closed, all)
- `page`: Page number (default: 1)
- `per_page`: Items per page (default: 10)

**Response:** `200 OK`
```json
{
  "success": true,
  "data": {
    "jobs": [...],
    "pagination": {
      "page": 1,
      "per_page": 10,
      "total": 25,
      "pages": 3
    }
  }
}
```

---

## Jobs

### List All Jobs

**Endpoint:** `GET /jobs`

**Query Parameters:**
- `search`: Search in title and description
- `location`: Filter by location
- `job_type`: Filter by type (Full-time, Part-time, Internship)
- `seniority`: Filter by seniority (Entry, Mid, Senior)
- `skills`: Comma-separated skills
- `remote`: Filter remote jobs (true/false)
- `page`: Page number
- `per_page`: Items per page

**Response:** `200 OK`
```json
{
  "success": true,
  "data": {
    "jobs": [
      {
        "id": "uuid",
        "company_id": "uuid",
        "company_name": "TechCorp Inc",
        "company_logo": "https://...",
        "title": "Senior Full Stack Developer",
        "description": "...",
        "job_type": "Full-time",
        "work_mode": "Hybrid",
        "seniority": "Senior",
        "required_skills": ["React", "Node.js", "AWS"],
        "location": "San Francisco, CA",
        "is_remote": false,
        "salary_min": 120000,
        "salary_max": 180000,
        "posted_at": "2025-11-01T00:00:00Z",
        "applications_count": 45
      }
    ],
    "pagination": {...}
  }
}
```

---

### Get Job Details

**Endpoint:** `GET /jobs/:id`

**Response:** `200 OK`
```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "company": {...},
    "title": "Senior Full Stack Developer",
    "description": "...",
    "requirements": {
      "experience_years": 5,
      "education": ["Bachelor's in CS"],
      "skills": ["React", "Node.js"]
    },
    "responsibilities": [...],
    "required_skills": [...],
    "preferred_skills": [...],
    "benefits": [...],
    "salary_range": "120k-180k USD",
    "posted_at": "2025-11-01T00:00:00Z",
    "expires_at": "2025-12-31T23:59:59Z"
  }
}
```

---

### Create Job Posting

**Endpoint:** `POST /companies/:id/jobs`

**Headers:** `Authorization: Bearer {access_token}`

**Request Body:**
```json
{
  "title": "Senior Full Stack Developer",
  "description": "We are seeking...",
  "job_type": "Full-time",
  "work_mode": "Hybrid",
  "seniority": "Senior",
  "department": "Engineering",
  "required_skills": ["React", "Node.js", "AWS"],
  "preferred_skills": ["TypeScript", "Kubernetes"],
  "requirements": {
    "experience_years": 5,
    "education": ["Bachelor's in Computer Science"],
    "certifications": []
  },
  "responsibilities": [...],
  "location": "San Francisco, CA",
  "is_remote": false,
  "salary_min": 120000,
  "salary_max": 180000,
  "benefits": [...],
  "openings": 2,
  "expires_at": "2025-12-31T23:59:59Z"
}
```

**Response:** `201 Created`

---

### Get Matched Candidates

**Endpoint:** `GET /jobs/:id/match`

**Headers:** `Authorization: Bearer {access_token}`

**Query Parameters:**
- `min_score`: Minimum match score (0-100)
- `top_k`: Return top K candidates
- `level`: Filter by student level

**Response:** `200 OK`
```json
{
  "success": true,
  "data": {
    "job_id": "uuid",
    "job_title": "Senior Full Stack Developer",
    "total_candidates": 150,
    "matched_candidates": [
      {
        "student_id": "uuid",
        "student_name": "John Doe",
        "student_level": "Intermediate",
        "match_score": 87.5,
        "skill_match_score": 90.0,
        "experience_match_score": 85.0,
        "education_match_score": 100.0,
        "matched_skills": ["React", "Node.js", "AWS"],
        "missing_skills": ["Kubernetes"],
        "recommendation": "Excellent Match",
        "resume_url": "https://...",
        "profile_url": "/students/uuid"
      }
    ]
  }
}
```

---

### Shortlist Candidates

**Endpoint:** `POST /jobs/:id/shortlist`

**Headers:** `Authorization: Bearer {access_token}`

**Request Body:**
```json
{
  "threshold": 75,
  "top_k": 10
}
```

**Response:** `200 OK`
```json
{
  "success": true,
  "data": {
    "shortlisted_count": 10,
    "candidates": [...]
  }
}
```

---

## Applications

### Apply to Job

**Endpoint:** `POST /jobs/:id/apply`

**Headers:** `Authorization: Bearer {access_token}`

**Request Body:**
```json
{
  "cover_letter": "I am excited to apply..."
}
```

**Response:** `201 Created`
```json
{
  "success": true,
  "data": {
    "application_id": "uuid",
    "job_id": "uuid",
    "student_id": "uuid",
    "status": "submitted",
    "match_score": 85.5,
    "match_details": {
      "skill_match": 90.0,
      "experience_match": 80.0,
      "matched_skills": [...]
    },
    "interview_status": "pending",
    "applied_at": "2025-11-30T12:00:00Z"
  }
}
```

---

### Get Application Details

**Endpoint:** `GET /applications/:id`

**Headers:** `Authorization: Bearer {access_token}`

**Response:** `200 OK`
```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "job": {...},
    "student": {...},
    "status": "interviewed",
    "match_score": 85.5,
    "interview_score": 78.0,
    "overall_score": 82.5,
    "evaluation_summary": {...},
    "applied_at": "2025-11-30T12:00:00Z",
    "updated_at": "2025-11-30T14:00:00Z"
  }
}
```

---

## Interviews

### Start Interview

**Endpoint:** `POST /applications/:id/start-interview`

**Headers:** `Authorization: Bearer {access_token}`

**Response:** `200 OK`
```json
{
  "success": true,
  "data": {
    "interview_id": "uuid",
    "application_id": "uuid",
    "questions": [
      {
        "id": "Q1",
        "type": "MCQ",
        "text": "What is the time complexity of binary search?",
        "options": ["A) O(n)", "B) O(log n)", "C) O(n²)", "D) O(1)"],
        "points": 10,
        "difficulty": "Easy",
        "skill_tested": "Algorithms"
      },
      {
        "id": "Q2",
        "type": "Scenario",
        "text": "Design a system to handle 1M concurrent users...",
        "points": 15,
        "difficulty": "Hard",
        "skill_tested": "System Design"
      }
    ],
    "total_points": 100,
    "estimated_duration_minutes": 30,
    "started_at": "2025-11-30T12:00:00Z"
  }
}
```

---

### Submit Interview

**Endpoint:** `POST /applications/:id/submit-interview`

**Headers:** `Authorization: Bearer {access_token}`

**Request Body:**
```json
{
  "answers": [
    {
      "question_id": "Q1",
      "answer_text": "B"
    },
    {
      "question_id": "Q2",
      "answer_text": "I would use a microservices architecture with load balancers..."
    }
  ]
}
```

**Response:** `200 OK`
```json
{
  "success": true,
  "data": {
    "interview_id": "uuid",
    "status": "completed",
    "submitted_at": "2025-11-30T12:30:00Z",
    "message": "Interview submitted successfully. Results will be available shortly."
  }
}
```

---

### Get Interview Results

**Endpoint:** `GET /applications/:id/result`

**Headers:** `Authorization: Bearer {access_token}`

**Response:** `200 OK`
```json
{
  "success": true,
  "data": {
    "interview_id": "uuid",
    "application_id": "uuid",
    "overall_score": 78.5,
    "grade": "B",
    "total_points": 100,
    "earned_points": 78.5,
    "percentage": 78.5,
    "per_question_scores": [
      {
        "question_id": "Q1",
        "question_text": "...",
        "student_answer": "B",
        "score": 10,
        "max_score": 10,
        "feedback": "Correct!",
        "key_points_covered": ["B"],
        "key_points_missed": []
      }
    ],
    "summary": "Interview Performance: B (78.5%)\n\nAnswered 7 out of 10 questions well.\n\nStrengths: Algorithms, Data Structures\nAreas for Improvement: System Design\n\nGood performance with room for improvement in some areas.",
    "submitted_at": "2025-11-30T12:30:00Z",
    "evaluated_at": "2025-11-30T12:31:00Z"
  }
}
```

---

## Error Handling

All errors follow this format:

```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error message",
    "details": {...}
  }
}
```

### Common Error Codes

| Code | Status | Description |
|------|--------|-------------|
| `VALIDATION_ERROR` | 422 | Request validation failed |
| `UNAUTHORIZED` | 401 | Authentication required |
| `FORBIDDEN` | 403 | Insufficient permissions |
| `NOT_FOUND` | 404 | Resource not found |
| `CONFLICT` | 409 | Resource already exists |
| `RATE_LIMIT_EXCEEDED` | 429 | Too many requests |
| `INTERNAL_SERVER_ERROR` | 500 | Server error |

---

## Rate Limiting

**Default Limits:**
- Authentication endpoints: 5 requests/minute
- General endpoints: 60 requests/minute
- File uploads: 10 requests/hour

**Headers:**
- `X-RateLimit-Limit`: Maximum requests allowed
- `X-RateLimit-Remaining`: Remaining requests
- `X-RateLimit-Reset`: Time when limit resets (Unix timestamp)

---

## Pagination

All list endpoints support pagination:

**Query Parameters:**
- `page`: Page number (default: 1)
- `per_page`: Items per page (default: 10, max: 100)

**Response:**
```json
{
  "data": [...],
  "pagination": {
    "page": 1,
    "per_page": 10,
    "total": 150,
    "pages": 15,
    "has_next": true,
    "has_prev": false
  }
}
```

---

## Postman Collection

Import the Postman collection for easy API testing:

**File:** `postman/AI_Placement_System.postman_collection.json`

**Environment Variables:**
- `base_url`: http://localhost:8000/api
- `access_token`: Your JWT token

---

## OpenAPI Specification

Interactive API documentation available at:
- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc
- **OpenAPI JSON:** http://localhost:8000/openapi.json

---

**Last Updated:** November 30, 2025  
**Version:** 1.0.0
