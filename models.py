"""
Pydantic models for request/response validation
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class SnowflakeConfig(BaseModel):
    """Snowflake connection configuration"""
    
    model_config = ConfigDict(populate_by_name=True)

    account: str = Field(default="AYFRZOA-QLIK", description="Snowflake account identifier")
    user: str = Field(default="JRP", description="Snowflake username")
    password: str = Field(default="qlik123!", description="Snowflake password")
    warehouse: str = Field(default="CORTEX_ANALYST_WH", description="Snowflake warehouse name")
    database: str = Field(default="CORTEX_ANALYST_DEMO", description="Database name")
    schema_name: str = Field(default="OMNICHEM", alias="schema", serialization_alias="schema", description="Schema name")
    semantic_model: str = Field(
        default="@CORTEX_ANALYST_DEMO.OMNICHEM.RAW_DATA/OMNICHEM_V2_1.yaml",
        description="Semantic model path"
    )


class ConfigResponse(BaseModel):
    """Response for configuration endpoint"""

    status: str
    message: str


class UploadResponse(BaseModel):
    """Response for file upload"""

    job_id: str
    filename: str
    num_questions: int
    status: str
    message: str


class JobStatus(BaseModel):
    """Job processing status"""

    job_id: str
    status: str
    total: int
    processed: int
    successful: int
    failed: int
    error_392708: int
    progress_percent: float
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error: Optional[str] = None


class JobSummary(BaseModel):
    """Summary of a processing job"""

    job_id: str
    status: str
    total: int
    processed: int
    successful: int
    failed: int
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class JobsList(BaseModel):
    """List of jobs"""

    jobs: list[JobSummary]


class QuestionResult(BaseModel):
    """Result of processing a single question"""

    question_id: int | str
    question: str
    interpretation: str
    sql: str
    query_results: str
    full_response: str
    api_start: str
    api_end: str
    api_duration_ms: int
    sql_duration_ms: int
    total_duration_ms: int
    status: str
    error: Optional[str] = None
