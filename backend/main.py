from fastapi import FastAPI, HTTPException, Request, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from pathlib import Path
import os
import uuid
import subprocess
from datetime import datetime
from typing import Optional, List, Dict, Any
from LLMClient import LLMClient
import uvicorn

llm_client = LLMClient()

app = FastAPI(title="Automator Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)

# Create scripts directory if it doesn't exist
SCRIPTS_DIR = Path("scripts")
SCRIPTS_DIR.mkdir(exist_ok=True)

class InstructionRequest(BaseModel):
    content: str
    
class LLMResponse(BaseModel):
    success: bool
    response: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

@app.post("/api/instructions/")
async def create_instruction(instruction: InstructionRequest):
    """
    Process an instruction using the local LLM and return the result.
    """
    try:
        prompt = f"""
        You are a RPA assistant that generates a Python script based on a user's instruction for interactions with web applications using the Playwright package.
        The user's instructions are: {instruction.content}
        What would be your proposed Python script?
        """

        llm_response = await llm_client.generate_text(
            prompt=prompt,
            max_tokens=-1,  # -1 means use maximum context length
            temperature=0.7  # Default temperature
        )

        generated_content = llm_response.get('choices', [{}])[0].get('message', {}).get('content', '')
        python_script = generated_content.split('```python')[1].split('```')[0]
        
        # Save the generated script to a file
        script_id = str(uuid.uuid4())
        script_filename = f"script_{script_id}.py"
        script_path = SCRIPTS_DIR / script_filename
        
        with open(script_path, 'w', encoding='utf-8') as f:
            f.write(python_script)
        
        return {
            "status": "success",
            "message": "Script created",
            "script_path": str(script_path),
            "script_id": script_id
        }
    except Exception as e:
        error_msg = f"Error processing instruction: {str(e)}"
        raise HTTPException(status_code=500, detail=error_msg)

async def run_script(script_path: str) -> dict:
    """
    Execute a Python script and return the result.
    """
    try:
        # Run the script and capture output
        result = subprocess.run(
            ["python", str(script_path)],
            capture_output=True,
            text=True,
            timeout=300  # 5 minutes timeout
        )
        
        return {
            "success": result.returncode == 0,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode
        }
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "error": "Script execution timed out after 5 minutes"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

@app.post("/api/scripts/{script_id}/run")
async def execute_script(script_id: str):
    """
    Execute a previously generated script by its ID.
    """
    script_path = SCRIPTS_DIR / f"script_{script_id}.py"
    
    if not script_path.exists():
        raise HTTPException(status_code=404, detail="Script not found")
    
    try:
        result = await run_script(script_path)
        return {
            "status": "success" if result["success"] else "error",
            "message": "Script executed successfully" if result["success"] else "Script execution failed",
            "output": result.get("stdout", ""),
            "error": result.get("stderr", result.get("error", "")),
            "returncode": result.get("returncode", -1)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/llm/generate")
async def generate_text(request: Dict[str, Any]):
    """
    Direct endpoint to generate text using the LLM.
    
    Example request body:
    {
        "prompt": "Tell me a joke about programming",
    }
    """
    try:
        response = await LLMClient.generate_text(
            prompt=request.get('prompt', ''),
            max_tokens=request.get('max_tokens', 2000),
            temperature=request.get('temperature', 0.7),
            **{k: v for k, v in request.items() 
               if k not in ['prompt', 'max_tokens', 'temperature']}
        )
        return {"success": True, "response": response}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/api/scripts/{script_id}")
async def get_script(script_id: str):
    """
    Get the content of a script by its ID.
    """
    try:
        script_path = SCRIPTS_DIR / f"script_{script_id}.py"
        if not script_path.exists():
            raise HTTPException(status_code=404, detail="Script not found")
            
        with open(script_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        return {
            "status": "success",
            "content": content,
            "script_id": script_id,
            "script_path": str(script_path)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading script: {str(e)}")

@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok", "message": "Service is running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
