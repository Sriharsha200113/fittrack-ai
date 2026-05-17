from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str
    OPENAI_API_KEY: str
    COHERE_API_KEY: str = ""
    REDIS_URL: str = "redis://localhost:6379/0"
    BACKEND_URL: str = "http://localhost:8000"
    BRIDGE_URL: str = "http://localhost:3000"
    BRIDGE_PORT: int = 3000
    BACKEND_PORT: int = 8000
    CHROMA_HOST: str = "localhost"
    CHROMA_PORT: int = 8001
    LANGCHAIN_TRACING_V2: bool = False
    LANGCHAIN_API_KEY: str = ""
    LANGCHAIN_PROJECT: str = "fitsquad"
    # JWT
    JWT_SECRET_KEY: str = "change-me-in-production"
    # APNs (Apple Push Notifications)
    APNS_KEY_ID: str = ""
    APNS_TEAM_ID: str = ""
    APNS_BUNDLE_ID: str = "com.yourname.fitsquad"
    APNS_PRIVATE_KEY: str = ""
    APNS_SANDBOX: bool = True

    class Config:
        env_file = ".env"

settings = Settings()
