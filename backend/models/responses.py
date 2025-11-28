from pydantic import BaseModel
from typing import Dict, Any, List, Optional

class ErrorResponse(BaseModel):
    """Standard error response model"""
    error_type: str
    message: str
    details: Optional[Dict[str, Any]] = None
    suggestions: Optional[List[str]] = None

class ScriptExecutionResponse(BaseModel):
    """Response model for script execution"""
    type: str  # 'output', 'error', or 'complete'
    success: Optional[bool] = None
    content: Optional[str] = None
    is_error: Optional[bool] = None
    message: Optional[str] = None
    stdout: Optional[str] = None
    stderr: Optional[str] = None
    error: Optional[str] = None
    error_type: Optional[str] = None
    error_details: Optional[Dict[str, Any]] = None
    returncode: Optional[int] = None
    script_content: Optional[str] = None
    page_history: Optional[List[Dict[str, Any]]] = None
    details: Optional[Dict[str, Any]] = None
    suggestions: Optional[List[str]] = None
    possible_causes: Optional[List[str]] = None
