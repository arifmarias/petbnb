# setup_project.py
import os

def create_directory_structure():
    # Define the directory structure
    directories = [
        "app",
        "app/core",
        "app/api",
        "app/api/v1",
        "app/api/v1/endpoints",
        "app/models",
        "app/schemas",
        "app/utils",
        "tests",
        "tests/test_api"
    ]
    
    # Create directories
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        # Create __init__.py in each directory
        with open(os.path.join(directory, "__init__.py"), "w") as f:
            pass
    
    # Create core configuration files
    core_files = {
        "app/core/config.py": """
from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import List

class Settings(BaseSettings):
    PROJECT_NAME: str = "PetBnB"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # Database
    DATABASE_URL: str = "postgresql://postgres:password@localhost:5432/petbnb"
    
    # JWT
    SECRET_KEY: str = "your-super-secret-key-here"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours
    
    # CORS
    BACKEND_CORS_ORIGINS: List[str] = ["*"]
    
    class Config:
        case_sensitive = True

@lru_cache()
def get_settings():
    return Settings()

settings = get_settings()
""",
        "app/core/database.py": """
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from .config import settings

engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
""",
        "app/main.py": """
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# Set up CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"message": "Welcome to PetBnB API"}
"""
    }
    
    # Create core files
    for file_path, content in core_files.items():
        with open(file_path, "w") as f:
            f.write(content.lstrip())

if __name__ == "__main__":
    create_directory_structure()
    print("Project structure created successfully!")