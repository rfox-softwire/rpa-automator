from pydantic import BaseModel
from typing import Dict, List, Optional, Any, Union
import json

class InstructionRequest(BaseModel):
    content: str
    error_context: Optional[Dict[str, Any]] = None
    original_script: Optional[str] = None
    
    class Config:
        json_encoders = {
            dict: lambda v: v,  # Handle dictionary serialization
            object: lambda v: str(v)  # Fallback for any other non-serializable objects
        }

class UrlValidationRequest(BaseModel):
    script_content: str

class UrlValidationResponse(BaseModel):
    accessible: bool
    inaccessible_urls: List[str]
    all_urls: List[str]

class LLMResponse(BaseModel):
    success: bool
    response: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

class ScriptError(BaseModel):
    error_type: str
    error: str
    stderr: Optional[str] = None
    traceback: Optional[str] = None
    script_content: Optional[str] = None

class ScriptResult(BaseModel):
    success: bool
    stdout: str = ""
    stderr: str = ""
    returncode: int = 0
    script_content: str = ""
    error_type: Optional[str] = None
    error_details: Dict[str, Any] = {}
    script_id: Optional[str] = None
    script_path: Optional[str] = None
