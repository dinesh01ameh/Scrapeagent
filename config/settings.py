"""
Application Settings and Configuration Management
"""

import os
from functools import lru_cache
from typing import List, Optional
from pydantic import Field, validator
try:
    from pydantic_settings import BaseSettings
except ImportError:
    from pydantic import BaseSettings


class Settings(BaseSettings):
    """Application settings with environment variable support"""
    
    # Application Configuration
    APP_NAME: str = Field(default="SwissKnife AI Scraper", env="APP_NAME")
    APP_VERSION: str = Field(default="1.0.0", env="APP_VERSION")
    DEBUG: bool = Field(default=False, env="DEBUG")
    HOST: str = Field(default="0.0.0.0", env="HOST")
    PORT: int = Field(default=8601, env="PORT")  # Fixed port 8601
    
    # Security
    SECRET_KEY: str = Field(env="SECRET_KEY")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30, env="ACCESS_TOKEN_EXPIRE_MINUTES")
    
    # Database Configuration
    SUPABASE_URL: Optional[str] = Field(default=None, env="SUPABASE_URL")
    SUPABASE_KEY: Optional[str] = Field(default=None, env="SUPABASE_KEY")
    SUPABASE_SERVICE_KEY: Optional[str] = Field(default=None, env="SUPABASE_SERVICE_KEY")
    DATABASE_URL: Optional[str] = Field(default=None, env="DATABASE_URL")
    
    # Redis Configuration
    REDIS_URL: str = Field(default="redis://localhost:6379", env="REDIS_URL")
    REDIS_PASSWORD: Optional[str] = Field(default=None, env="REDIS_PASSWORD")
    REDIS_DB: int = Field(default=0, env="REDIS_DB")
    
    # Local LLM Configuration (Ollama)
    OLLAMA_ENDPOINT: str = Field(default="http://localhost:11434", env="OLLAMA_ENDPOINT")
    DEFAULT_MODEL: str = Field(default="llama3.3", env="DEFAULT_MODEL")
    FALLBACK_MODEL: str = Field(default="mistral", env="FALLBACK_MODEL")
    CODE_MODEL: str = Field(default="codellama", env="CODE_MODEL")
    MAX_CONTEXT_LENGTH: int = Field(default=8192, env="MAX_CONTEXT_LENGTH")
    
    # crawl4ai Configuration (CRITICAL - Core Scraping Engine)
    CRAWL4AI_ENDPOINT: str = Field(default="http://crawl4ai:11235", env="CRAWL4AI_ENDPOINT")
    CRAWL4AI_MAX_SESSIONS: int = Field(default=10, env="CRAWL4AI_MAX_SESSIONS")
    CRAWL4AI_TIMEOUT: int = Field(default=30, env="CRAWL4AI_TIMEOUT")

    # Jina AI Configuration (CRITICAL - Core AI Processing Engine)
    JINA_API_KEY: Optional[str] = Field(default=None, env="JINA_API_KEY")
    JINA_READER_ENDPOINT: str = Field(default="https://r.jina.ai", env="JINA_READER_ENDPOINT")
    JINA_SEARCH_ENDPOINT: str = Field(default="https://s.jina.ai", env="JINA_SEARCH_ENDPOINT")
    JINA_EMBEDDINGS_ENDPOINT: str = Field(default="https://api.jina.ai/v1/embeddings", env="JINA_EMBEDDINGS_ENDPOINT")
    JINA_RERANKER_ENDPOINT: str = Field(default="https://api.jina.ai/v1/rerank", env="JINA_RERANKER_ENDPOINT")
    
    # Proxy Configuration
    PROXY_ROTATION_ENABLED: bool = Field(default=True, env="PROXY_ROTATION_ENABLED")
    PROXY_HEALTH_CHECK_INTERVAL: int = Field(default=300, env="PROXY_HEALTH_CHECK_INTERVAL")
    PROXY_TIMEOUT: int = Field(default=30, env="PROXY_TIMEOUT")
    PROXY_MAX_RETRIES: int = Field(default=3, env="PROXY_MAX_RETRIES")
    
    # Proxy Providers
    BRIGHTDATA_USERNAME: Optional[str] = Field(default=None, env="BRIGHTDATA_USERNAME")
    BRIGHTDATA_PASSWORD: Optional[str] = Field(default=None, env="BRIGHTDATA_PASSWORD")
    SMARTPROXY_USERNAME: Optional[str] = Field(default=None, env="SMARTPROXY_USERNAME")
    SMARTPROXY_PASSWORD: Optional[str] = Field(default=None, env="SMARTPROXY_PASSWORD")
    
    # Crawling Configuration
    DEFAULT_USER_AGENT: str = Field(default="SwissKnife-AI-Scraper/1.0", env="DEFAULT_USER_AGENT")
    MAX_CONCURRENT_REQUESTS: int = Field(default=10, env="MAX_CONCURRENT_REQUESTS")
    REQUEST_DELAY: float = Field(default=1.0, env="REQUEST_DELAY")
    RESPECT_ROBOTS_TXT: bool = Field(default=True, env="RESPECT_ROBOTS_TXT")
    MAX_PAGES_PER_DOMAIN: int = Field(default=1000, env="MAX_PAGES_PER_DOMAIN")
    
    # Content Processing
    MAX_CONTENT_SIZE: int = Field(default=10485760, env="MAX_CONTENT_SIZE")  # 10MB
    ENABLE_OCR: bool = Field(default=True, env="ENABLE_OCR")
    ENABLE_PDF_PROCESSING: bool = Field(default=True, env="ENABLE_PDF_PROCESSING")
    ENABLE_IMAGE_ANALYSIS: bool = Field(default=True, env="ENABLE_IMAGE_ANALYSIS")
    
    # Storage Configuration
    DATA_STORAGE_PATH: str = Field(default="./data", env="DATA_STORAGE_PATH")
    CACHE_STORAGE_PATH: str = Field(default="./cache", env="CACHE_STORAGE_PATH")
    LOG_STORAGE_PATH: str = Field(default="./logs", env="LOG_STORAGE_PATH")
    MODEL_STORAGE_PATH: str = Field(default="./models", env="MODEL_STORAGE_PATH")
    
    # Monitoring & Logging
    LOG_LEVEL: str = Field(default="INFO", env="LOG_LEVEL")
    ENABLE_METRICS: bool = Field(default=True, env="ENABLE_METRICS")
    METRICS_PORT: int = Field(default=9090, env="METRICS_PORT")
    ENABLE_STRUCTURED_LOGGING: bool = Field(default=True, env="ENABLE_STRUCTURED_LOGGING")
    
    # Rate Limiting
    RATE_LIMIT_REQUESTS_PER_MINUTE: int = Field(default=60, env="RATE_LIMIT_REQUESTS_PER_MINUTE")
    RATE_LIMIT_BURST: int = Field(default=10, env="RATE_LIMIT_BURST")
    
    # Session Management
    SESSION_TIMEOUT: int = Field(default=3600, env="SESSION_TIMEOUT")
    MAX_SESSIONS_PER_USER: int = Field(default=5, env="MAX_SESSIONS_PER_USER")
    
    # Feature Flags
    ENABLE_NATURAL_LANGUAGE_INTERFACE: bool = Field(default=True, env="ENABLE_NATURAL_LANGUAGE_INTERFACE")
    ENABLE_MULTIMODAL_PROCESSING: bool = Field(default=True, env="ENABLE_MULTIMODAL_PROCESSING")
    ENABLE_ADAPTIVE_EXTRACTION: bool = Field(default=True, env="ENABLE_ADAPTIVE_EXTRACTION")
    ENABLE_PROXY_ROTATION: bool = Field(default=True, env="ENABLE_PROXY_ROTATION")
    ENABLE_CONTENT_INTELLIGENCE: bool = Field(default=True, env="ENABLE_CONTENT_INTELLIGENCE")
    
    # Development Settings
    RELOAD_ON_CHANGE: bool = Field(default=True, env="RELOAD_ON_CHANGE")
    ENABLE_CORS: bool = Field(default=True, env="ENABLE_CORS")
    # Temporarily disabled due to parsing issues
    # CORS_ORIGINS: List[str] = Field(
    #     default=["http://localhost:3000", "http://localhost:8080"],
    #     env="CORS_ORIGINS"
    # )
    
    # Testing Configuration
    TEST_DATABASE_URL: Optional[str] = Field(default=None, env="TEST_DATABASE_URL")
    TEST_REDIS_URL: str = Field(default="redis://localhost:6379/1", env="TEST_REDIS_URL")
    
    @validator("SECRET_KEY")
    def validate_secret_key(cls, v):
        if not v or len(v) < 32:
            raise ValueError("SECRET_KEY must be at least 32 characters long")
        return v
    
    @validator("LOG_LEVEL")
    def validate_log_level(cls, v):
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"LOG_LEVEL must be one of {valid_levels}")
        return v.upper()
    
    # Temporarily disabled due to parsing issues
    # @validator("CORS_ORIGINS", pre=True, always=True)
    # def parse_cors_origins(cls, v):
    #     if v is None:
    #         return ["http://localhost:3000", "http://localhost:8080"]
    #     if isinstance(v, str):
    #         return [origin.strip() for origin in v.split(",")]
    #     return v
    
    def create_directories(self):
        """Create necessary directories if they don't exist"""
        directories = [
            self.DATA_STORAGE_PATH,
            self.CACHE_STORAGE_PATH,
            self.LOG_STORAGE_PATH,
            self.MODEL_STORAGE_PATH,
        ]
        
        for directory in directories:
            os.makedirs(directory, exist_ok=True)
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    settings = Settings()
    settings.create_directories()
    return settings
