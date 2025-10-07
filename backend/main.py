import os
import sys
import time
import logging
import uvicorn
import platform
import asyncio
from pathlib import Path
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime

# Set Windows event loop policy if on Windows
if platform.system() == 'Windows':
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

# Add the parent directory to the Python path
sys.path.append(str(Path(__file__).parent.parent))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Import routes
from backend.routes import router

# Create FastAPI app
app = FastAPI(title="Automator Backend")

# Middleware for request logging
@app.middleware("http")
async def log_requests(request: Request, call_next):
    # Log request details
    start_time = time.time()
    request_id = f"{time.time():.3f}"
    
    # Log request
    logger.info(f"[Request {request_id}] {request.method} {request.url}")
    logger.debug(f"[Request {request_id}] Headers: {dict(request.headers)}")
    
    # Process the request
    try:
        response = await call_next(request)
    except Exception as e:
        logger.error(f"[Request {request_id}] Error processing request: {str(e)}", exc_info=True)
        raise
    
    # Calculate process time
    process_time = (time.time() - start_time) * 1000
    process_time_str = f"{process_time:.2f}ms"
    
    # Log response
    logger.info(
        f"[Request {request_id}] Completed {request.method} {request.url} "
        f"Status: {response.status_code} Time: {process_time_str}"
    )
    
    return response

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(router)

if __name__ == "__main__":
    logger.info("Starting Automator Backend...")
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
