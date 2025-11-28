from fastapi import APIRouter, HTTPException, Depends, Request, Path, status
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.middleware import Middleware
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.middleware import SlowAPIMiddleware
from typing import Dict, Any, List, Optional, Callable, Awaitable
import json
import asyncio
import datetime
import logging
import traceback
import time
import uuid

# Configure logging
logger = logging.getLogger(__name__)

from backend.models import (
    InstructionRequest,
    UrlValidationRequest,
    UrlValidationResponse,
    LLMResponse,
    ScriptError,
    ScriptResult
)
from backend.models.responses import ErrorResponse, ScriptExecutionResponse
from backend.services.llm_service import LLMService
from backend.services.llm_client import LLMClient
from backend.services.sync_script_service import SyncScriptService

# Create router
router = APIRouter()

# Rate limiting setup
limiter = Limiter(key_func=get_remote_address)

# Configure logging
logger = logging.getLogger(__name__)

# Error responses for common error cases
error_responses = {
    400: {"description": "Bad Request"},
    401: {"description": "Unauthorized"},
    403: {"description": "Forbidden"},
    404: {"description": "Not Found"},
    422: {"description": "Validation Error"},
    500: {"description": "Internal Server Error"}
}

# Create router with common responses
router = APIRouter(
    responses=error_responses,
    default_response_class=JSONResponse
)

# Initialize services
script_service = SyncScriptService()

# Initialize LLM client and service
llm_client = LLMClient()
llm_service = LLMService(llm_client=llm_client)
script_service = SyncScriptService()

# Override the dependency
def get_llm_service():
    return llm_service

@router.post("/scripts/repair", response_model=Dict[str, Any])
async def repair_script(
    instruction: InstructionRequest,
    request: Request = None
) -> Dict[str, Any]:
    """Repair a script based on error context and original script."""
    try:
        # Log the incoming request
        logger.info(f"Received repair request: {instruction.dict()}")
        if request:
            logger.info(f"Request headers: {dict(request.headers)}")
            try:
                body = await request.body()
                logger.info(f"Request body: {body.decode()}")
            except Exception as e:
                logger.warning(f"Could not log request body: {e}")

        # Ensure we have the required error context and original script for repair
        if instruction.error_context is not None and not instruction.original_script:
            raise HTTPException(
                status_code=400,
                detail="original_script is required when error_context is provided"
            )
            
        # Log the error context if present
        if instruction.error_context:
            logger.info(f"Error context: {instruction.error_context}")
            if instruction.original_script:
                logger.info(f"Original script length: {len(instruction.original_script)} characters")

        # Return the result directly as the response
        result = await llm_service.generate_script(instruction)
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error repairing script: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/instructions/", response_model=Dict[str, Any])
async def create_instruction(
    instruction: InstructionRequest,
    llm_service: LLMService = Depends(get_llm_service),
    request: Request = None
) -> Dict[str, Any]:
    """Process an instruction using the LLM and return the result."""
    try:
        # Log the incoming request
        logger.info(f"Received instruction request: {instruction.dict()}")
        if request:
            logger.info(f"Request headers: {dict(request.headers)}")
            try:
                body = await request.body()
                logger.info(f"Request body: {body.decode()}")
            except Exception as e:
                logger.warning(f"Could not log request body: {e}")

        # Return the result directly as the response
        result = await llm_service.generate_script(instruction)
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing instruction: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/scripts/{script_id}", response_model=Dict[str, Any])
async def get_script(script_id: str) -> Dict[str, Any]:
    """Get the content of a script by its ID."""
    try:
        script_path = script_service.scripts_dir / f"script_{script_id}.py"
        if not script_path.exists():
            raise HTTPException(status_code=404, detail="Script not found")
        
        with open(script_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        return {
            "script_id": script_id,
            "content": content,
            "path": str(script_path)
        }
    except HTTPException:
        raise
    except Exception as e:
        error_msg = f"Error retrieving script: {str(e)}"
        raise HTTPException(status_code=500, detail=error_msg)

# Error responses for OpenAPI documentation
error_responses = {
    404: {"model": ErrorResponse, "description": "Script not found"},
    408: {"model": ErrorResponse, "description": "Request timeout"},
    422: {"model": ErrorResponse, "description": "Validation error"},
    429: {"model": ErrorResponse, "description": "Too many requests"},
    500: {"model": ErrorResponse, "description": "Internal server error"}
}

@router.post(
    "/scripts/{script_id}/run",
    response_model=ScriptExecutionResponse,
    responses={
        200: {"description": "Script execution result"},
        **error_responses
    }
)
@limiter.limit("10/minute")  # Rate limiting
async def execute_script(
    request: Request,
    script_id: str = Path(..., 
        regex=r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$',
        description="UUID of the script to execute"
    )
):
    """
    Execute a previously generated script by its ID.
    
    - **script_id**: UUID of the script to execute
    
    Returns the script execution result after completion.
    """
    try:
        script_path = script_service.scripts_dir / f"script_{script_id}.py"
        
        if not script_path.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=ErrorResponse(
                    error_type="ScriptNotFoundError",
                    message=f"Script with ID {script_id} not found",
                    suggestions=[
                        "Check if the script ID is correct",
                        "The script may have been deleted or never created"
                    ]
                ).dict()
            )
        
        logger.info(f"Executing script: {script_path}")
        
        try:
            # Run the script and get the result
            result = await asyncio.to_thread(script_service.run_script, str(script_path))
            
            # Prepare the response
            response_data = {
                'type': 'complete',
                'success': result.success,
                'stdout': result.stdout or "",
                'stderr': result.stderr or "",
                'content': result.stdout or "",
                'is_error': not result.success,
                'message': 'Script executed successfully' if result.success else getattr(result, 'error', 'Script execution failed'),
                'error': None if result.success else getattr(result, 'error', 'Script execution failed'),
                'error_type': None if result.success else str(getattr(result, 'error_type', 'ExecutionError')),
                'error_details': getattr(result, 'error_details', None),
                'returncode': getattr(result, 'returncode', 0 if result.success else 1),
                'page_history': getattr(result, 'page_history', []),
                'details': getattr(result, 'details', None),
                'suggestions': [],
                'possible_causes': []
            }
            
            # Add script content if available
            if hasattr(result, 'script_content'):
                response_data['script_content'] = result.script_content
            
            # Add error-specific suggestions
            if not result.success:
                error_type = str(getattr(result, 'error_type', '')).lower()
                
                if "modulenotfound" in error_type:
                    module_name = getattr(result, 'error_details', {}).get('message', '').split()[-1]
                    response_data['suggestions'] = [
                        "The script is trying to use a Python module that is not installed",
                        f"Try installing the missing module with: pip install {module_name}" if module_name else "Check your imports"
                    ]
                    response_data['possible_causes'] = [
                        "Missing Python package",
                        "Virtual environment not activated",
                        "Incorrect Python environment"
                    ]
                elif "timeout" in error_type:
                    response_data['suggestions'] = [
                        "The script took too long to execute (timeout after 5 minutes)",
                        "Check for infinite loops or long-running operations in your script"
                    ]
                    response_data['possible_causes'] = [
                        "Infinite loop in the script",
                        "Network requests taking too long",
                        "Resource-intensive operations"
                    ]
                elif "filenotfound" in error_type:
                    file_path = getattr(result, 'error_details', {}).get('message', 'unknown path')
                    response_data['suggestions'] = [
                        "The script is trying to access a file that doesn't exist",
                        f"Check the file path: {file_path}"
                    ]
                    response_data['possible_causes'] = [
                        "Incorrect file path",
                        "File permissions issue",
                        "File deleted or moved"
                    ]
                else:
                    # Default error suggestions
                    response_data['suggestions'] = [
                        "Check the script for syntax errors",
                        "Verify all required dependencies are installed",
                        "Review the error message and traceback"
                    ]
            
            return ScriptExecutionResponse(**response_data)
                
        except asyncio.TimeoutError:
            logger.error("Script execution timed out")
            return ScriptExecutionResponse(
                type='error',
                success=False,
                is_error=True,
                message='Script execution timed out',
                error='Script execution timed out',
                error_type='TimeoutError',
                returncode=-1,
                suggestions=[
                    'The script took too long to execute',
                    'Check for infinite loops or long-running operations',
                    'Consider optimizing the script or increasing the timeout'
                ],
                possible_causes=[
                    'Infinite loop in the script',
                    'Network requests taking too long',
                    'Resource-intensive operations'
                ]
            )
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Error in script execution: {error_msg}", exc_info=True)
            return ScriptExecutionResponse(
                type='error',
                success=False,
                is_error=True,
                message=error_msg,
                error=error_msg,
                error_type=type(e).__name__,
                returncode=-1,
                details={"traceback": traceback.format_exc()},
                suggestions=[
                    'An unexpected error occurred while executing the script',
                    'Check the server logs for more details',
                    'Verify the script syntax and dependencies'
                ],
                possible_causes=[
                    'Syntax error in the script',
                    'Missing dependencies',
                    'Environment configuration issue'
                ]
            )
        
    except HTTPException:
        raise
    except Exception as e:
        error_msg = f"An unexpected error occurred: {str(e)}"
        logger.error(error_msg, exc_info=True)
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponse(
                error_type="InternalServerError",
                message=error_msg,
                details={"traceback": traceback.format_exc()},
                suggestions=[
                    "Check the server logs for more detailed error information",
                    "Contact support if the issue persists"
                ]
            ).dict()
        )

@router.post("/generate-text", response_model=LLMResponse)
async def generate_text(request: Dict[str, Any], llm_service: LLMService = Depends()) -> LLMResponse:
    """
    Direct endpoint to generate text using the LLM.
    Example request body:
    {
        "prompt": "Tell me a joke about programming",
    }
    """
    try:
        prompt = request.get("prompt", "")
        if not prompt:
            raise HTTPException(status_code=400, detail="Prompt is required")
            
        response = await llm_service.llm_client.generate_text(
            prompt=prompt,
            max_tokens=request.get("max_tokens", -1),
            temperature=request.get("temperature", 0.7)
        )
        
        return LLMResponse(
            success=True,
            response=response
        )
    except HTTPException:
        raise
    except Exception as e:
        error_msg = f"Error generating text: {str(e)}"
        return LLMResponse(success=False, error=error_msg)

@router.get("/health")
async def health_check() -> Dict[str, str]:
    """Health check endpoint."""
    return {"status": "ok", "timestamp": datetime.datetime.utcnow().isoformat()}
