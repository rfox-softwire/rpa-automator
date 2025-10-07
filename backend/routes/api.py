from fastapi import APIRouter, HTTPException, Depends, Request
from typing import Dict, Any, List, Optional
import json
import asyncio
import datetime
import logging

# Configure logging
logger = logging.getLogger(__name__)

from backend.models import (
    InstructionRequest,
    UrlValidationRequest,
    UrlValidationResponse,
    LLMResponse,
    ScriptError
)
from backend.services.llm_service import LLMService
from backend.services.llm_client import LLMClient
from backend.services.script_service import ScriptService

# Configure logging
logger = logging.getLogger(__name__)

router = APIRouter()
script_service = ScriptService()

# Initialize LLM client and service
llm_client = LLMClient()
llm_service = LLMService(llm_client=llm_client)

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

@router.post("/scripts/{script_id}/run", response_model=Dict[str, Any])
async def execute_script(script_id: str) -> Dict[str, Any]:
    """Execute a previously generated script by its ID."""
    try:
        script_path = script_service.scripts_dir / f"script_{script_id}.py"
        if not script_path.exists():
            raise HTTPException(
                status_code=404, 
                detail={
                    "error_type": "ScriptNotFoundError",
                    "message": f"Script with ID {script_id} not found",
                    "script_id": script_id,
                    "suggestions": [
                        "Check if the script ID is correct",
                        "The script may have been deleted or never created"
                    ]
                }
            )
        
        logger.info(f"Executing script: {script_path}")
        result = await script_service.run_script(str(script_path))
        
        if result.success:
            return {
                "status": "success",
                "output": result.stdout,
                "script_id": script_id,
                "execution_time": getattr(result, 'execution_time', None)
            }
        else:
            # Format a more detailed error response
            error_details = {
                "error_type": result.error_type or "ScriptExecutionError",
                "message": result.error_details.get("message", "Script execution failed") if result.error_details else "Script execution failed",
                "script_id": script_id,
                "suggestions": []
            }
            
            # Add specific suggestions based on error type
            if "ModuleNotFoundError" in str(result.error_type):
                error_details["suggestions"] = [
                    "The script is trying to use a Python module that is not installed",
                    f"Try installing the missing module with: pip install {result.error_details.get('message', '').split()[-1]}"
                ]
            elif "TimeoutError" in str(result.error_type):
                error_details["suggestions"] = [
                    "The script took too long to execute (timeout after 5 minutes)",
                    "Check for infinite loops or long-running operations in your script",
                    "Consider optimizing your script or increasing the timeout if needed"
                ]
            elif "FileNotFoundError" in str(result.error_type):
                error_details["suggestions"] = [
                    "The script is trying to access a file that doesn't exist",
                    f"Check if the file path is correct: {result.error_details.get('message', '')}",
                    "Make sure all required files are in the correct location"
                ]
            
            # Include the full error details if available
            if hasattr(result, 'error_details') and result.error_details:
                error_details["details"] = result.error_details
            
            # Include stderr if available
            if hasattr(result, 'stderr') and result.stderr:
                error_details["stderr"] = result.stderr
                
            return {
                "status": "error",
                **error_details
            }
            
    except HTTPException as http_exc:
        # Re-raise HTTP exceptions as is
        raise http_exc
    except Exception as e:
        logger.error(f"Unexpected error executing script {script_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "error_type": "InternalServerError",
                "message": f"An unexpected error occurred while executing the script: {str(e)}",
                "script_id": script_id,
                "suggestions": [
                    "Check the server logs for more detailed error information",
                    "Contact support if the issue persists"
                ]
            }
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
