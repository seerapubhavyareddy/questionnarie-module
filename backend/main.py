"""
Questionnaire Module - FastAPI Application

Main entry point for the Questionnaire Module API.
Provides CRUD operations for questionnaires and questions.

Run:
    uvicorn main:app --reload --port 8003

Or:
    python main.py
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import os
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Import routes
from app.routes.questionnaires import router as questionnaires_router
from app.routes.trial_questionnaires import (
    router as trial_questionnaires_router,
    vendor_router as vendor_trial_questionnaires_router,
)
from app.routes.participant_questionnaires import router as participant_questionnaires_router
from app.database import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.
    Runs on startup and shutdown.
    """
    # Startup
    logger.info("Starting Questionnaire Module API...")
    
    # Initialize database tables
    try:
        init_db()
        logger.info("✅ Database tables initialized")
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Questionnaire Module API...")


# Create FastAPI app
app = FastAPI(
    title="Questionnaire Module API",
    description="""
    API for managing questionnaires in clinical trials.
    
    ## Features
    
    - **CRUD Operations**: Create, read, update, and delete questionnaires
    - **Question Types**: Support for multiple question types (text, choice, scale, etc.)
    - **Version History**: Track changes to questionnaires over time
    - **Bulk Operations**: Update or delete multiple questionnaires at once
    - **Cloning**: Duplicate existing questionnaires
    
    ## Question Types
    
    - Text (single line, multi-line)
    - Number, Email, Phone
    - Date, Time, DateTime
    - Single Choice (radio buttons)
    - Multiple Choice (checkboxes)
    - Dropdown
    - Rating/Scale
    - Yes/No
    - File Upload
    - Section Header
    """,
    version="1.0.0",
    lifespan=lifespan,
)

# CORS Configuration
cors_origins = os.getenv(
    "CORS_ORIGINS", 
    "http://localhost:5173,http://localhost:5174,http://localhost:3000"
)
ALLOWED_ORIGINS = [origin.strip() for origin in cors_origins.split(",") if origin.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Include routers
app.include_router(questionnaires_router)
app.include_router(trial_questionnaires_router)
app.include_router(vendor_trial_questionnaires_router)
app.include_router(participant_questionnaires_router)


# =============================================================================
# Health Check Endpoints
# =============================================================================

@app.get("/health", tags=["Health"])
async def health_check():
    """Basic health check endpoint."""
    return {"status": "ok", "service": "questionnaire-module"}


@app.get("/api/health", tags=["Health"])
async def api_health_check():
    """API health check endpoint."""
    from datetime import datetime
    return {
        "status": "ok",
        "service": "questionnaire-module",
        "timestamp": datetime.now().isoformat()
    }


@app.get("/", tags=["Root"])
async def root():
    """Root endpoint with API information."""
    return {
        "service": "Questionnaire Module API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }


# =============================================================================
# Run with uvicorn
# =============================================================================

if __name__ == "__main__":
    import uvicorn
    
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8003"))
    
    logger.info(f"Starting server at http://{host}:{port}")
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=True,
        log_level="info"
    )
