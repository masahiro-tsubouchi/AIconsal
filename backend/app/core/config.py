"""Configuration management for Manufacturing AI Assistant"""
from functools import lru_cache
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings with environment variable support"""
    
    # API Configuration
    api_v1_str: str = "/api/v1"
    project_name: str = "Manufacturing AI Assistant"
    version: str = "1.0.0"
    debug: bool = False
    
    # Server Configuration
    host: str = "0.0.0.0"
    port: int = 8002
    reload: bool = False
    
    # AI Configuration
    gemini_api_key: str = ""
    gemini_model: str = "gemini-1.5-pro"
    gemini_fallback_model: Optional[str] = "gemini-1.5-flash"
    gemini_max_retries: int = 3
    gemini_retry_backoff_seconds: float = 2.0
    langsmith_api_key: Optional[str] = None
    langsmith_project: str = "manufacturing-ai-assistant"
    
    # File Processing
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    upload_dir: str = "/tmp/uploads"
    supported_file_types: list[str] = [".pdf", ".docx", ".txt", ".csv", ".xlsx"]
    
    # Session Management
    session_timeout: int = 3600  # 1 hour in seconds
    
    # CORS Configuration
    cors_origins: str = "http://localhost:3002,http://frontend:3002,http://localhost:5175"
    
    def get_cors_origins_list(self) -> list[str]:
        """Parse CORS origins string into list"""
        if isinstance(self.cors_origins, str):
            return [origin.strip() for origin in self.cors_origins.split(",")]
        return self.cors_origins
    
    # Logging
    log_level: str = "INFO"
    
    # Docker Specific Settings
    environment: str = "development"
    docker_internal_host: str = "backend"
    docker_network: str = "app-network"
    
    # Monitoring
    enable_metrics: bool = False
    metrics_port: int = 9090
    
    # Security
    secret_key: str = "your-secret-key-for-jwt-tokens"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    # LangGraph Durable Execution (optional)
    enable_checkpointer: bool = False
    
    # Debug/Streaming (development-only flags)
    # Enable WebSocket debug event streaming when true (can be toggled per-request via query param)
    debug_streaming: bool = False
    # Placeholder for Phase B (breakpoints). Not used yet.
    debug_breakpoints: bool = False
    
    # Timeouts
    llm_generate_timeout_seconds: float = 30.0
    workflow_invoke_timeout_seconds: float = 60.0
    
    model_config = {
        "env_file": ["/app/.env"],
        "case_sensitive": False,
        "extra": "allow"
    }


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()
