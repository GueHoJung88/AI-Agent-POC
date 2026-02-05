import os
from pydantic import BaseModel

class Settings(BaseModel):
    database_host: str = os.getenv("DATABASE_HOST", "127.0.0.1")
    database_port: int = int(os.getenv("DATABASE_PORT", "5432"))
    database_name: str = os.getenv("DATABASE_NAME", "ragdb")
    database_user: str = os.getenv("DATABASE_USER", "raguser")
    database_password: str = os.getenv("DATABASE_PASSWORD", "")

    default_doc_group: str = os.getenv("DEFAULT_DOC_GROUP", "guide")

    azure_endpoint: str = os.getenv("AZURE_OPENAI_ENDPOINT", "")
    azure_api_key: str = os.getenv("AZURE_OPENAI_API_KEY", "")
    azure_deployment: str = os.getenv("AZURE_OPENAI_DEPLOYMENT", "")
    azure_api_version: str = os.getenv("AZURE_OPENAI_API_VERSION", "2024-06-01")

    embedding_model_name: str = os.getenv("EMBEDDING_MODEL_NAME", "BAAI/bge-small-en-v1.5")

settings = Settings()
