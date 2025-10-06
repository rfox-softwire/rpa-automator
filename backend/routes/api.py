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
                logger.warning(f"Could not log request body: {str(e)}")
        return await llm_service.generate_script(instruction)
    except Exception as e:
        error_msg = f"Error processing instruction: {str(e)}"
        raise HTTPException(status_code=500, detail=error_msg)

# @router.post("/scripts/validate-urls", response_model=UrlValidationResponse)
# async def validate_urls(request: UrlValidationRequest) -> UrlValidationResponse:
#     """Validate all URLs in a script to ensure they are accessible."""
#     try:
#         result = await script_service.validate_urls(request.script_content)
#         return UrlValidationResponse(**result)
#     except Exception as e:
#         error_msg = f"Error validating URLs: {str(e)}"
#         raise HTTPException(status_code=500, detail=error_msg)

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
            raise HTTPException(status_code=404, detail="Script not found")
        
        result = await script_service.run_script(str(script_path))
        
        if result.success:
            return {
                "status": "success",
                "output": result.stdout,
                "script_id": script_id
            }
        else:
            return {
                "status": "error",
                "error_type": result.error_type,
                "error_details": result.error_details,
                "stderr": result.stderr,
                "script_id": script_id
            }
            
    except HTTPException:
        raise
    except Exception as e:
        error_msg = f"Error executing script: {str(e)}"
        raise HTTPException(status_code=500, detail=error_msg)

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
            max_tokens=request.get("max_tokens", 100),
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
