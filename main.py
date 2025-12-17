"""
Cortex Analyst UI - FastAPI Application
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import logging

from config import settings, create_directories
from routers import config, jobs
from cortex_processor import CortexProcessor


logging.basicConfig(
    level=settings.log_level,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler"""
    create_directories()
    
    # Initialize CortexProcessor with default values
    try:
        default_processor = CortexProcessor()
        if default_processor.test_connection():
            config.set_processor(default_processor)
            logger.info("Default Snowflake connection established successfully")
        else:
            logger.warning("Default Snowflake connection failed - configuration required")
    except Exception as e:
        logger.error(f"Failed to initialize default connection: {e}")
    
    logger.info("Application startup complete")
    yield
    logger.info("Application shutdown")


app = FastAPI(
    title=settings.app_name,
    description="Upload CSV questions and process them through Snowflake Cortex Analyst",
    version=settings.app_version,
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(config.router)
app.include_router(jobs.router)


@app.get("/", response_class=HTMLResponse)
async def read_root():
    """Serve the main UI"""
    index_path = settings.static_dir / "index.html"
    with open(index_path, "r") as f:
        return f.read()


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "version": settings.app_version}


app.mount("/static", StaticFiles(directory=str(settings.static_dir)), name="static")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host=settings.host,
        port=settings.port,
        log_level=settings.log_level.lower()
    )
