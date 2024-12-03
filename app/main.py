from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.websockets import WebSocket
from app.core.config import settings
from app.api.v1.api import api_router
from app.models import *  # This will import all models
import logging
import time
from typing import Callable
import json

# Configure detailed logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# Debug middleware to log request details
@app.middleware("http")
async def log_requests(request: Request, call_next: Callable):
    # Generate request ID
    request_id = str(time.time())
    
    # Log request details
    logger.info(f"=== Incoming Request [{request_id}] ===")
    logger.info(f"Method: {request.method}")
    logger.info(f"URL: {request.url}")
    logger.info(f"Client Host: {request.client.host}")
    
    # Log headers (excluding sensitive data)
    safe_headers = dict(request.headers)
    if 'authorization' in safe_headers:
        safe_headers['authorization'] = 'Bearer <token omitted>'
    logger.info(f"Headers: {json.dumps(safe_headers, indent=2)}")

    # Process request and time it
    start_time = time.time()
    try:
        response = await call_next(request)
        
        # Log response details
        process_time = time.time() - start_time
        logger.info(f"=== Response [{request_id}] ===")
        logger.info(f"Status Code: {response.status_code}")
        logger.info(f"Process Time: {process_time:.3f}s")
        
        return response
    except Exception as e:
        logger.error(f"=== Request Failed [{request_id}] ===")
        logger.error(f"Error: {str(e)}")
        raise
    finally:
        logger.info(f"=== Request Complete [{request_id}] ===")

# CORS middleware with detailed configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],  # Added to ensure all headers are exposed
)

# API router
app.include_router(api_router, prefix=settings.API_V1_STR)

# Enhanced health check endpoint
@app.get("/health")
async def health_check(request: Request):
    logger.info(f"Health check from {request.client.host}")
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "api_version": settings.VERSION,
        "cors_origins": settings.cors_origins
    }

if __name__ == "__main__":
    import uvicorn
    
    # Log startup configuration
    logger.info("=== Starting PetBnB API Server ===")
    logger.info(f"API Version: {settings.VERSION}")
    logger.info(f"CORS Origins: {settings.cors_origins}")
    logger.info(f"API Base Path: {settings.API_V1_STR}")
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        ws_ping_interval=30,
        ws_ping_timeout=30,
        log_level="info"
    )