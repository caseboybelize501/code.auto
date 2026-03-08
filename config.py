import os
from pydantic import BaseModel
from typing import Optional


class Config(BaseModel):
    """Application configuration"""
    
    # LLM Settings
    # Providers: "openai", "anthropic", "llama-cpp" (local)
    llm_provider: str = "llama-cpp"  # Default to local llama.cpp
    
    # Commercial API Keys (for customer deployments)
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    openai_model: str = "gpt-4o-mini"
    anthropic_model: str = "claude-3-5-sonnet-20241022"
    
    # Local llama.cpp Settings (owner use - no API key needed)
    local_llm_enabled: bool = True
    local_llm_base_url: str = "http://localhost:8080"  # llama.cpp default
    local_llm_model: str = "local-model"
    local_llm_context_length: int = 8192
    
    # ChromaDB Settings (Optional - falls back to in-memory)
    chroma_host: str = "localhost"
    chroma_port: int = 8000
    chroma_collection_name: str = "code_auto_memory"
    
    # Neo4j Settings (Optional)
    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = "password"
    
    # Redis Settings (Optional)
    redis_host: str = "localhost"
    redis_port: int = 6379
    
    # Build Settings
    build_timeout: int = 300  # seconds
    test_timeout: int = 600  # seconds
    
    # Deployment Settings
    docker_registry: str = "localhost:5000"
    deployment_timeout: int = 120
    
    # Working directories
    work_dir: str = "./workspace"
    logs_dir: str = "./logs"

    class Config:
        env_prefix = "CODE_AUTO_"
        env_file = ".env"


def load_config() -> Config:
    """Load configuration from environment"""
    return Config(
        llm_provider=os.getenv("CODE_AUTO_LLM_PROVIDER", "llama-cpp"),
        openai_api_key=os.getenv("CODE_AUTO_OPENAI_API_KEY"),
        anthropic_api_key=os.getenv("CODE_AUTO_ANTHROPIC_API_KEY"),
        openai_model=os.getenv("CODE_AUTO_OPENAI_MODEL", "gpt-4o-mini"),
        anthropic_model=os.getenv("CODE_AUTO_ANTHROPIC_MODEL", "claude-3-5-sonnet-20241022"),
        local_llm_enabled=os.getenv("CODE_AUTO_LOCAL_LLM_ENABLED", "true").lower() == "true",
        local_llm_base_url=os.getenv("CODE_AUTO_LOCAL_LLM_URL", "http://localhost:8080"),
        local_llm_model=os.getenv("CODE_AUTO_LOCAL_LLM_MODEL", "local-model"),
        local_llm_context_length=int(os.getenv("CODE_AUTO_LOCAL_LLM_CONTEXT", "8192")),
        chroma_host=os.getenv("CODE_AUTO_CHROMA_HOST", "localhost"),
        chroma_port=int(os.getenv("CODE_AUTO_CHROMA_PORT", "8000")),
        chroma_collection_name=os.getenv("CODE_AUTO_CHROMA_COLLECTION", "code_auto_memory"),
        neo4j_uri=os.getenv("CODE_AUTO_NEO4J_URI", "bolt://localhost:7687"),
        neo4j_user=os.getenv("CODE_AUTO_NEO4J_USER", "neo4j"),
        neo4j_password=os.getenv("CODE_AUTO_NEO4J_PASSWORD", "password"),
        redis_host=os.getenv("CODE_AUTO_REDIS_HOST", "localhost"),
        redis_port=int(os.getenv("CODE_AUTO_REDIS_PORT", "6379")),
        build_timeout=int(os.getenv("CODE_AUTO_BUILD_TIMEOUT", "300")),
        test_timeout=int(os.getenv("CODE_AUTO_TEST_TIMEOUT", "600")),
        docker_registry=os.getenv("CODE_AUTO_DOCKER_REGISTRY", "localhost:5000"),
        deployment_timeout=int(os.getenv("CODE_AUTO_DEPLOYMENT_TIMEOUT", "120")),
        work_dir=os.getenv("CODE_AUTO_WORK_DIR", "./workspace"),
        logs_dir=os.getenv("CODE_AUTO_LOGS_DIR", "./logs"),
    )


# Global config instance
config = load_config()
