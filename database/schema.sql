-- AI-Powered Student Placement System - Database Schema
-- PostgreSQL 15+
-- Author: Ali Ahmed
-- Date: 2025-11-30

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm"; -- For fuzzy text search
CREATE EXTENSION IF NOT EXISTS "btree_gin"; -- For composite indexes

-- ============================================================================
-- USERS & AUTHENTICATION
-- ============================================================================

CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(20) NOT NULL CHECK (role IN ('student', 'company', 'admin')),
    is_active BOOLEAN DEFAULT TRUE,
    is_verified BOOLEAN DEFAULT FALSE,
    verification_token VARCHAR(255),
    reset_token VARCHAR(255),
    reset_token_expires TIMESTAMP,
    last_login TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_role ON users(role);
CREATE INDEX idx_users_created_at ON users(created_at DESC);

-- ============================================================================
-- STUDENTS
-- ============================================================================

CREATE TABLE students (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID UNIQUE NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    full_name VARCHAR(255) NOT NULL,
    phone VARCHAR(20),
    bio TEXT,
    profile_image_url VARCHAR(500),
    resume_url VARCHAR(500),
    resume_parsed_data JSONB, -- Structured resume data
    
    -- Classification
    level VARCHAR(20) CHECK (level IN ('Beginner', 'Intermediate', 'Expert')),
    level_confidence DECIMAL(5,2), -- 0-100
    
    -- Structured data
    education JSONB, -- [{degree, institution, year, gpa, major}]
    experience JSONB, -- [{company, role, start_date, end_date, description}]
    skills JSONB, -- [{name, proficiency, years}]
    certifications JSONB, -- [{name, issuer, date, url}]
    projects JSONB, -- [{title, description, tech_stack, url, date}]
    
    -- Metadata
    total_experience_years DECIMAL(4,2),
    preferred_locations TEXT[],
    expected_salary_min INTEGER,
    expected_salary_max INTEGER,
    availability_date DATE,
    
    -- Search optimization
    skills_text TEXT, -- Denormalized for full-text search
    experience_text TEXT,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_students_user_id ON students(user_id);
CREATE INDEX idx_students_level ON students(level);
CREATE INDEX idx_students_skills_gin ON students USING GIN(skills);
CREATE INDEX idx_students_skills_text ON students USING GIN(skills_text gin_trgm_ops);
CREATE INDEX idx_students_experience_years ON students(total_experience_years);
CREATE INDEX idx_students_created_at ON students(created_at DESC);

-- Full-text search index
CREATE INDEX idx_students_fulltext ON students USING GIN(
    to_tsvector('english', COALESCE(full_name, '') || ' ' || 
                           COALESCE(bio, '') || ' ' || 
                           COALESCE(skills_text, '') || ' ' || 
                           COALESCE(experience_text, ''))
);

-- ============================================================================
-- COMPANIES
-- ============================================================================

CREATE TABLE companies (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID UNIQUE NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    company_name VARCHAR(255) NOT NULL,
    website VARCHAR(500),
    logo_url VARCHAR(500),
    industry VARCHAR(100),
    company_size VARCHAR(50), -- '1-10', '11-50', '51-200', '201-500', '500+'
    address TEXT,
    city VARCHAR(100),
    state VARCHAR(100),
    country VARCHAR(100),
    description TEXT,
    founded_year INTEGER,
    
    -- Contact
    contact_email VARCHAR(255),
    contact_phone VARCHAR(20),
    
    -- Verification
    is_verified BOOLEAN DEFAULT FALSE,
    verification_documents JSONB,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_companies_user_id ON companies(user_id);
CREATE INDEX idx_companies_name ON companies(company_name);
CREATE INDEX idx_companies_industry ON companies(industry);
CREATE INDEX idx_companies_verified ON companies(is_verified);
CREATE INDEX idx_companies_created_at ON companies(created_at DESC);

-- ============================================================================
-- JOBS
-- ============================================================================

CREATE TABLE jobs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_id UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    
    -- Basic info
    title VARCHAR(255) NOT NULL,
    description TEXT NOT NULL,
    job_type VARCHAR(50), -- 'Full-time', 'Part-time', 'Internship', 'Contract'
    work_mode VARCHAR(50), -- 'Remote', 'On-site', 'Hybrid'
    
    -- Requirements
    requirements JSONB NOT NULL, -- {skills: [], experience_years: X, education: [], certifications: []}
    responsibilities TEXT[],
    required_skills TEXT[] NOT NULL,
    preferred_skills TEXT[],
    
    -- Classification
    seniority VARCHAR(50), -- 'Entry', 'Mid', 'Senior', 'Lead', 'Manager'
    department VARCHAR(100),
    
    -- Location & Compensation
    location VARCHAR(255),
    city VARCHAR(100),
    state VARCHAR(100),
    country VARCHAR(100),
    is_remote BOOLEAN DEFAULT FALSE,
    salary_min INTEGER,
    salary_max INTEGER,
    salary_currency VARCHAR(10) DEFAULT 'USD',
    
    -- Benefits
    benefits TEXT[],
    
    -- Status
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('draft', 'active', 'paused', 'closed', 'filled')),
    openings INTEGER DEFAULT 1,
    applications_count INTEGER DEFAULT 0,
    views_count INTEGER DEFAULT 0,
    
    -- Dates
    posted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP,
    filled_at TIMESTAMP,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_jobs_company_id ON jobs(company_id);
CREATE INDEX idx_jobs_status ON jobs(status);
CREATE INDEX idx_jobs_seniority ON jobs(seniority);
CREATE INDEX idx_jobs_job_type ON jobs(job_type);
CREATE INDEX idx_jobs_location ON jobs(location);
CREATE INDEX idx_jobs_required_skills ON jobs USING GIN(required_skills);
CREATE INDEX idx_jobs_posted_at ON jobs(posted_at DESC);
CREATE INDEX idx_jobs_expires_at ON jobs(expires_at);

-- Full-text search for jobs
CREATE INDEX idx_jobs_fulltext ON jobs USING GIN(
    to_tsvector('english', COALESCE(title, '') || ' ' || 
                           COALESCE(description, '') || ' ' || 
                           COALESCE(location, ''))
);

-- ============================================================================
-- APPLICATIONS
-- ============================================================================

CREATE TABLE applications (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    job_id UUID NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
    student_id UUID NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    
    -- Application data
    resume_url VARCHAR(500),
    cover_letter TEXT,
    
    -- Matching & Scoring
    match_score DECIMAL(5,2), -- 0-100
    match_details JSONB, -- {skill_match: X, experience_match: Y, education_match: Z, matched_skills: []}
    
    -- Interview
    interview_status VARCHAR(20) DEFAULT 'pending' CHECK (
        interview_status IN ('pending', 'scheduled', 'in_progress', 'completed', 'skipped')
    ),
    interview_score DECIMAL(5,2), -- 0-100
    interview_completed_at TIMESTAMP,
    
    -- Overall evaluation
    overall_score DECIMAL(5,2), -- Weighted: 60% match + 40% interview
    evaluation_summary JSONB,
    
    -- Status
    status VARCHAR(20) DEFAULT 'submitted' CHECK (
        status IN ('submitted', 'under_review', 'shortlisted', 'interview_scheduled', 
                   'interviewed', 'selected', 'rejected', 'withdrawn')
    ),
    
    -- Company actions
    reviewed_by UUID REFERENCES users(id),
    reviewed_at TIMESTAMP,
    rejection_reason TEXT,
    
    -- Dates
    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(job_id, student_id) -- One application per student per job
);

CREATE INDEX idx_applications_job_id ON applications(job_id);
CREATE INDEX idx_applications_student_id ON applications(student_id);
CREATE INDEX idx_applications_status ON applications(status);
CREATE INDEX idx_applications_match_score ON applications(match_score DESC);
CREATE INDEX idx_applications_overall_score ON applications(overall_score DESC);
CREATE INDEX idx_applications_applied_at ON applications(applied_at DESC);
CREATE INDEX idx_applications_interview_status ON applications(interview_status);

-- Composite index for company dashboard queries
CREATE INDEX idx_applications_job_status_score ON applications(job_id, status, overall_score DESC);

-- ============================================================================
-- INTERVIEWS
-- ============================================================================

CREATE TABLE interviews (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    application_id UUID UNIQUE NOT NULL REFERENCES applications(id) ON DELETE CASCADE,
    
    -- Questions
    questions JSONB NOT NULL, -- [{id, text, type, options, expected_keywords, points, rubric}]
    
    -- Answers
    answers JSONB, -- [{question_id, answer_text, selected_option, audio_url}]
    
    -- Scoring
    per_question_scores JSONB, -- [{question_id, score, max_score, feedback}]
    overall_score DECIMAL(5,2),
    total_points INTEGER,
    earned_points INTEGER,
    
    -- Behavior metrics (optional)
    recorded_video_url VARCHAR(500),
    behavior_metrics JSONB, -- {blink_rate, gaze_offscreen_pct, face_confidence, emotion_scores}
    behavior_score DECIMAL(5,2),
    
    -- Metadata
    started_at TIMESTAMP,
    submitted_at TIMESTAMP,
    duration_seconds INTEGER,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_interviews_application_id ON interviews(application_id);
CREATE INDEX idx_interviews_overall_score ON interviews(overall_score DESC);
CREATE INDEX idx_interviews_submitted_at ON interviews(submitted_at DESC);

-- ============================================================================
-- NOTIFICATIONS
-- ============================================================================

CREATE TABLE notifications (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    type VARCHAR(50) NOT NULL, -- 'application_received', 'interview_ready', 'status_update', etc.
    title VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    
    -- Related entities
    related_job_id UUID REFERENCES jobs(id) ON DELETE SET NULL,
    related_application_id UUID REFERENCES applications(id) ON DELETE SET NULL,
    
    -- Status
    is_read BOOLEAN DEFAULT FALSE,
    read_at TIMESTAMP,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_notifications_user_id ON notifications(user_id);
CREATE INDEX idx_notifications_is_read ON notifications(is_read);
CREATE INDEX idx_notifications_created_at ON notifications(created_at DESC);
CREATE INDEX idx_notifications_user_unread ON notifications(user_id, is_read) WHERE is_read = FALSE;

-- ============================================================================
-- AUDIT LOGS
-- ============================================================================

CREATE TABLE audit_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    
    action VARCHAR(100) NOT NULL, -- 'login', 'create_job', 'apply_job', 'update_profile', etc.
    entity_type VARCHAR(50), -- 'user', 'job', 'application', etc.
    entity_id UUID,
    
    details JSONB,
    ip_address INET,
    user_agent TEXT,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_audit_logs_user_id ON audit_logs(user_id);
CREATE INDEX idx_audit_logs_action ON audit_logs(action);
CREATE INDEX idx_audit_logs_entity ON audit_logs(entity_type, entity_id);
CREATE INDEX idx_audit_logs_created_at ON audit_logs(created_at DESC);

-- ============================================================================
-- SYSTEM SETTINGS
-- ============================================================================

CREATE TABLE system_settings (
    key VARCHAR(100) PRIMARY KEY,
    value JSONB NOT NULL,
    description TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert default settings
INSERT INTO system_settings (key, value, description) VALUES
('matching_weights', '{"skill_match": 0.6, "experience_match": 0.25, "education_match": 0.15}', 'Weights for job matching algorithm'),
('interview_config', '{"num_questions": 10, "mcq_count": 4, "scenario_count": 3, "technical_count": 3}', 'Interview question distribution'),
('level_thresholds', '{"beginner": {"max_years": 2}, "intermediate": {"min_years": 2, "max_years": 5}, "expert": {"min_years": 5}}', 'Student level classification thresholds');

-- ============================================================================
-- TRIGGERS
-- ============================================================================

-- Auto-update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_students_updated_at BEFORE UPDATE ON students
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_companies_updated_at BEFORE UPDATE ON companies
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_jobs_updated_at BEFORE UPDATE ON jobs
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_applications_updated_at BEFORE UPDATE ON applications
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_interviews_updated_at BEFORE UPDATE ON interviews
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Auto-increment applications_count on jobs
CREATE OR REPLACE FUNCTION increment_job_applications()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE jobs SET applications_count = applications_count + 1
    WHERE id = NEW.job_id;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER increment_applications_count AFTER INSERT ON applications
    FOR EACH ROW EXECUTE FUNCTION increment_job_applications();

-- ============================================================================
-- VIEWS
-- ============================================================================

-- Active jobs with company info
CREATE VIEW active_jobs_view AS
SELECT 
    j.*,
    c.company_name,
    c.logo_url,
    c.industry,
    c.company_size,
    c.is_verified as company_verified
FROM jobs j
JOIN companies c ON j.company_id = c.id
WHERE j.status = 'active' AND (j.expires_at IS NULL OR j.expires_at > CURRENT_TIMESTAMP);

-- Student applications with job and company details
CREATE VIEW student_applications_view AS
SELECT 
    a.*,
    j.title as job_title,
    j.location as job_location,
    j.job_type,
    c.company_name,
    c.logo_url as company_logo
FROM applications a
JOIN jobs j ON a.job_id = j.id
JOIN companies c ON j.company_id = c.id;

-- Top candidates per job
CREATE VIEW top_candidates_view AS
SELECT 
    a.job_id,
    a.student_id,
    s.full_name,
    s.level,
    a.match_score,
    a.interview_score,
    a.overall_score,
    a.status,
    ROW_NUMBER() OVER (PARTITION BY a.job_id ORDER BY a.overall_score DESC) as rank
FROM applications a
JOIN students s ON a.student_id = s.id
WHERE a.status NOT IN ('withdrawn', 'rejected');

-- ============================================================================
-- SAMPLE QUERIES
-- ============================================================================

-- Find jobs matching student skills
-- SELECT * FROM jobs WHERE required_skills && (SELECT skills_text FROM students WHERE id = ?);

-- Get top 10 candidates for a job
-- SELECT * FROM top_candidates_view WHERE job_id = ? AND rank <= 10;

-- Full-text search jobs
-- SELECT * FROM jobs WHERE to_tsvector('english', title || ' ' || description) @@ plainto_tsquery('english', 'python developer');

-- Get student application statistics
-- SELECT status, COUNT(*) FROM applications WHERE student_id = ? GROUP BY status;

-- ============================================================================
-- INDEXES FOR PERFORMANCE
-- ============================================================================

-- Composite indexes for common queries
CREATE INDEX idx_jobs_active_posted ON jobs(status, posted_at DESC) WHERE status = 'active';
CREATE INDEX idx_applications_student_status ON applications(student_id, status);
CREATE INDEX idx_applications_job_shortlisted ON applications(job_id, status) WHERE status = 'shortlisted';

-- ============================================================================
-- COMMENTS
-- ============================================================================

COMMENT ON TABLE users IS 'Core user authentication and role management';
COMMENT ON TABLE students IS 'Student profiles with parsed resume data and skills';
COMMENT ON TABLE companies IS 'Company profiles and verification status';
COMMENT ON TABLE jobs IS 'Job postings with requirements and status';
COMMENT ON TABLE applications IS 'Student applications with matching and interview scores';
COMMENT ON TABLE interviews IS 'AI-generated interviews with questions, answers, and scoring';
COMMENT ON TABLE notifications IS 'User notifications for application updates';
COMMENT ON TABLE audit_logs IS 'System audit trail for security and compliance';

-- ============================================================================
-- GRANTS (adjust based on your user setup)
-- ============================================================================

-- GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO placement_app_user;
-- GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO placement_app_user;
