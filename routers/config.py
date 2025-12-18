"""
Configuration endpoints
"""

from fastapi import APIRouter, HTTPException
import logging

from models import SnowflakeConfig, ConfigResponse
from cortex_processor import CortexProcessor

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["configuration"])

processor: CortexProcessor | None = None


def get_processor() -> CortexProcessor | None:
    """Get the global processor instance"""
    return processor


def set_processor(proc: CortexProcessor):
    """Set the global processor instance"""
    global processor
    processor = proc


@router.get("/configure")
async def get_configuration():
    """
    Get current Snowflake configuration with defaults
    
    Returns:
        Current configuration with default values
    """
    # Return default configuration with alias (schema instead of schema_name)
    return SnowflakeConfig().model_dump(by_alias=True)


@router.post("/configure", response_model=ConfigResponse)
async def configure_connection(config: SnowflakeConfig):
    """
    Configure Snowflake connection

    Args:
        config: Snowflake connection configuration

    Returns:
        Configuration status
    """
    try:
        proc = CortexProcessor(
            account=config.account,
            user=config.user,
            password=config.password,
            warehouse=config.warehouse,
            database=config.database,
            schema_name=config.schema_name,
            semantic_model=config.semantic_model
        )

        if proc.test_connection():
            set_processor(proc)
            return ConfigResponse(
                status="success",
                message="Connection configured successfully"
            )
        else:
            return ConfigResponse(
                status="error",
                message="Failed to connect to Snowflake"
            )

    except Exception as e:
        logger.error(f"Configuration error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
