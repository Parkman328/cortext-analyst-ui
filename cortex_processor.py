"""
Cortex Processor - Handles Snowflake Cortex Analyst API interactions
"""

import json
import time
from datetime import datetime
from dataclasses import dataclass, field
from typing import Optional, Callable
import pandas as pd
from pathlib import Path
import logging

import snowflake.snowpark as snowpark
from snowflake.snowpark import Session

logger = logging.getLogger(__name__)


@dataclass
class ProcessingStatus:
    """Track processing status"""
    job_id: str
    status: str  # queued, processing, completed, failed
    total: int = 0
    processed: int = 0
    successful: int = 0
    failed: int = 0
    error_392708: int = 0
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error: Optional[str] = None
    output_json: Optional[str] = None
    output_csv: Optional[str] = None


class CortexProcessor:
    """Process questions through Cortex Analyst API"""
    
    def __init__(
        self,
        account: str = 'AYFRZOA-QLIK',
        user: str = 'JRP',
        password: str = 'qlik123!',
        warehouse: str = 'CORTEX_ANALYST_WH',
        database: str = "CORTEX_ANALYST_DEMO",
        schema_name: str = "OMNICHEM",
        semantic_model: str = "@CORTEX_ANALYST_DEMO.OMNICHEM.RAW_DATA/OMNICHEM_V2_1_ENHANCED.yaml"
    ):
        """Initialize processor with Snowflake connection"""
        self.connection_params = {
            "account": account,
            "user": user,
            "password": password,
            "warehouse": warehouse,
            "database": database,
            "schema": schema_name
        }
        
        self.semantic_model = semantic_model
        self.session = None
        
        # Processing configuration
        self.api_endpoint = "/api/v2/cortex/analyst/message"
        self.api_timeout = 600000  # 10 minutes
        self.max_retries = 3
        self.delay_between_requests = 5  # seconds

    def call_cortex_analyst(self, question: str) -> dict:
        """Call Cortex Analyst for a single question.

        This method is intended to be implemented using a Snowflake-accessible
        interface that works outside the in-database Python runtime, for
        example by issuing SQL against functions or procedures that wrap
        Cortex Analyst via the Snowflake connector/Snowpark Session.

        The returned dictionary is expected to be compatible with the
        structure previously produced by the internal _snowflake API, i.e.
        containing top-level keys such as "error_code" (optional) and a
        "message" object with a "content" list of items where each item has
        a "type" (e.g. "text" or "sql").
        """
        raise RuntimeError(
            "call_cortex_analyst is not implemented. Implement this method "
            "to call Snowflake Cortex Analyst using an external interface "
            "(e.g. via SQL through the Snowpark Session)."
        )
    
    def test_connection(self) -> bool:
        """Test Snowflake connection"""
        try:
            self.session = Session.builder.configs(self.connection_params).create()
            # Test query
            self.session.sql("SELECT 1").collect()
            logger.info("Successfully connected to Snowflake")
            return True
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False
    
    def row_to_dict(self, row):
        """Safely convert Snowpark Row to dictionary"""
        try:
            if hasattr(row, 'asDict'):
                return row.asDict()
            elif hasattr(row, 'as_dict'):
                return row.as_dict()
            else:
                return {field: row[field] for field in row.__fields__}
        except Exception as e:
            logger.error(f"Row conversion error: {e}")
            return {"error": f"Could not convert row: {str(e)}"}
    
    def process_csv(
        self,
        csv_path: Path,
        job_id: str,
        status_callback: Optional[Callable[[ProcessingStatus], None]] = None
    ) -> list:
        """
        Process questions from CSV file
        
        Args:
            csv_path: Path to CSV file with Id, Question columns
            job_id: Unique job identifier
            status_callback: Optional callback for status updates
            
        Returns:
            List of result dictionaries
        """
        if not self.session:
            raise Exception("Not connected to Snowflake. Call test_connection() first.")
        
        # Load questions
        df = pd.read_csv(csv_path)
        questions = df.to_dict('records')
        
        # Initialize status
        status = ProcessingStatus(
            job_id=job_id,
            status="processing",
            total=len(questions),
            started_at=datetime.now()
        )
        
        results = []
        consecutive_errors = 0
        
        logger.info(f"Processing {len(questions)} questions for job {job_id}")
        
        for idx, row in enumerate(questions, 1):
            qid = row.get('Id') or row.get('id') or idx
            question = row.get('Question') or row.get('question', '')
            
            if not question:
                logger.warning(f"Skipping row {idx}: no question found")
                continue
            
            logger.info(f"[{idx}/{len(questions)}] Processing question {qid}")
            
            # Throttle after consecutive errors
            if consecutive_errors >= 3:
                logger.warning(f"Throttling: pausing 30s after {consecutive_errors} errors")
                time.sleep(30)
                consecutive_errors = 0
            
            success = False
            last_error = None
            total_start = time.time()
            
            # Retry loop
            for retry in range(self.max_retries):
                if retry > 0:
                    wait = 5 * (2 ** (retry - 1))
                    logger.info(f"Retry {retry}/{self.max_retries} after {wait}s")
                    time.sleep(wait)
                
                try:
                    api_start = datetime.utcnow()
                    t0 = time.time()
                    
                    # Call Cortex Analyst API via pluggable method
                    parsed = self.call_cortex_analyst(question)
                    api_duration_ms = int((time.time() - t0) * 1000)
                    api_end = datetime.utcnow()
                    
                    # Check for error 392708
                    if parsed.get("error_code") == "392708":
                        last_error = f"Error 392708: {parsed.get('message', 'Unknown')}"
                        logger.warning(last_error)
                        status.error_392708 += 1
                        consecutive_errors += 1
                        break  # Don't retry semantic errors
                    
                    # Extract response
                    interpretation = ""
                    sql_statement = ""
                    
                    for item in parsed.get("message", {}).get("content", []):
                        if item.get("type") == "text":
                            interpretation = item.get("text", "")
                        elif item.get("type") == "sql":
                            sql_statement = item.get("statement", "")
                    
                    # Execute SQL if generated
                    query_results = ""
                    sql_duration_ms = 0
                    
                    if sql_statement:
                        t1 = time.time()
                        try:
                            qr = self.session.sql(sql_statement).collect()
                            
                            if len(qr) > 100:
                                qr = qr[:100]
                            
                            # Convert rows to dicts
                            query_results_list = [self.row_to_dict(r) for r in qr]
                            query_results = json.dumps(query_results_list, default=str)
                            
                            sql_duration_ms = int((time.time() - t1) * 1000)
                            logger.info(f"SQL executed: {len(qr)} rows in {sql_duration_ms}ms")
                            
                        except Exception as e:
                            query_results = f"SQL error: {str(e)}"
                            sql_duration_ms = int((time.time() - t1) * 1000)
                            logger.error(f"SQL execution failed: {e}")
                    
                    # Store result
                    results.append({
                        "question_id": qid,
                        "question": question,
                        "interpretation": interpretation,
                        "sql": sql_statement,
                        "query_results": query_results,
                        "full_response": json.dumps(parsed, default=str),
                        "api_start": api_start.isoformat(),
                        "api_end": api_end.isoformat(),
                        "api_duration_ms": api_duration_ms,
                        "sql_duration_ms": sql_duration_ms,
                        "total_duration_ms": int((time.time() - total_start) * 1000),
                        "status": "success"
                    })
                    
                    success = True
                    consecutive_errors = 0
                    status.successful += 1
                    break
                    
                except Exception as e:
                    last_error = str(e)
                    logger.error(f"Error processing question {qid}: {e}")
                    consecutive_errors += 1
            
            # Handle failure
            if not success:
                logger.error(f"Question {qid} failed after {self.max_retries} attempts")
                status.failed += 1
                
                results.append({
                    "question_id": qid,
                    "question": question,
                    "interpretation": "",
                    "sql": "",
                    "query_results": "",
                    "full_response": json.dumps({"error": last_error}),
                    "api_start": datetime.utcnow().isoformat(),
                    "api_end": datetime.utcnow().isoformat(),
                    "api_duration_ms": 0,
                    "sql_duration_ms": 0,
                    "total_duration_ms": int((time.time() - total_start) * 1000),
                    "status": "failed",
                    "error": last_error
                })
            
            # Update status
            status.processed += 1
            
            if status_callback:
                status_callback(status)
            
            # Rate limiting
            if idx < len(questions):
                time.sleep(self.delay_between_requests)
        
        # Final status
        status.completed_at = datetime.now()
        
        if status_callback:
            status_callback(status)
        
        logger.info(
            f"Job {job_id} completed: "
            f"{status.successful} successful, "
            f"{status.failed} failed, "
            f"{status.error_392708} error 392708"
        )
        
        return results
    
    def close(self):
        """Close Snowflake session"""
        if self.session:
            self.session.close()
            logger.info("Snowflake session closed")
