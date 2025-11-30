"""
Application Configuration
Centralized settings management using Pydantic
"""

from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import Field, validator


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # Application
    APP_NAME: str = "AI Student Placement System"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    
    # Database
    DATABASE_URL: str = Field(..., env="DATABASE_URL")
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 10
    
    # Redis
    REDIS_URL: str = Field(..., env="REDIS_URL")
    REDIS_MAX_CONNECTIONS: int = 50
    
    # JWT
    JWT_SECRET_KEY: str = Field(..., env="JWT_SECRET_KEY")
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # OpenAI
    OPENAI_API_KEY: str = Field(..., env="OPENAI_API_KEY")
    OPENAI_MODEL: str = "gpt-4o"
    
    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:3001"]
    ALLOWED_HOSTS: List[str] = ["localhost", "127.0.0.1"]
    
    @validator("CORS_ORIGINS", pre=True)
    def parse_cors_origins(cls, v):
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v
    
    @validator("ALLOWED_HOSTS", pre=True)
    def parse_allowed_hosts(cls, v):
        if isinstance(v, str):
            return [host.strip() for host in v.split(",")]
        return v
    
    # File Upload
    UPLOAD_DIR: str = "/app/uploads"
    MAX_UPLOAD_SIZE: int = 10485760  # 10MB
    ALLOWED_EXTENSIONS: List[str] = ["pdf", "doc", "docx", "jpg", "jpeg", "png"]
    
    # S3 / MinIO
    USE_S3: bool = False
    S3_ENDPOINT: Optional[str] = None
    S3_ACCESS_KEY: Optional[str] = None
    S3_SECRET_KEY: Optional[str] = None
    S3_BUCKET_NAME: str = "placement-resumes"
    S3_REGION: str = "us-east-1"
    
    # Celery
    CELERY_BROKER_URL: str = Field(..., env="REDIS_URL")
    CELERY_RESULT_BACKEND: str = Field(..., env="REDIS_URL")
    CELERY_TASK_ALWAYS_EAGER: bool = False
    
    # Email (Optional)
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: int = 587
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    SMTP_FROM: str = "noreply@placement-system.com"
    
    # Logging
    LOG_LEVEL: str = "INFO"
    SENTRY_DSN: Optional[str] = None
    
    # Rate Limiting
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_PER_MINUTE: int = 60
    
    # AI/ML Models
    SENTENCE_TRANSFORMER_MODEL: str = "all-mpnet-base-v2"
    SPACY_MODEL: str = "en_core_web_sm"
    USE_ML_LEVEL_CLASSIFIER: bool = False
    
    # Interview Configuration
    INTERVIEW_TOTAL_QUESTIONS: int = 10
    INTERVIEW_MCQ_COUNT: int = 4
    INTERVIEW_SCENARIO_COUNT: int = 3
    INTERVIEW_TECHNICAL_COUNT: int = 3
    INTERVIEW_TIME_LIMIT_MINUTES: int = 30
    
    # Matching Weights
    MATCH_WEIGHT_SKILLS: float = 0.60
    MATCH_WEIGHT_EXPERIENCE: float = 0.25
    MATCH_WEIGHT_EDUCATION: float = 0.15
    
    # Security
    ENABLE_HTTPS: bool = False
    SSL_CERT_PATH: Optional[str] = None
    SSL_KEY_PATH: Optional[str] = None
    BCRYPT_ROUNDS: int = 12
    
    # Feature Flags
    ENABLE_VIDEO_INTERVIEWS: bool = False
    ENABLE_BEHAVIOR_TRACKING: bool = False
    ENABLE_EMAIL_NOTIFICATIONS: bool = True
    ENABLE_SMS_NOTIFICATIONS: bool = False
    
    # Third-party Integrations
    LINKEDIN_CLIENT_ID: Optional[str] = None
    LINKEDIN_CLIENT_SECRET: Optional[str] = None
    GOOGLE_CLIENT_ID: Optional[str] = None
    GOOGLE_CLIENT_SECRET: Optional[str] = None
    TWILIO_ACCOUNT_SID: Optional[str] = None
    TWILIO_AUTH_TOKEN: Optional[str] = None
    TWILIO_PHONE_NUMBER: Optional[str] = None
    
    # Development
    RELOAD_ON_CHANGE: bool = True
    SHOW_SQL_QUERIES: bool = False
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Create settings instance
settings = Settings()
