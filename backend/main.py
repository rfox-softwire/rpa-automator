from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from pathlib import Path
import os
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

class InstructionRequest(BaseModel):
    content: str
    max_tokens: Optional[int] = Field(200, gt=0, le=2000)
    temperature: Optional[float] = Field(0.7, ge=0.0, le=2.0)
    
class LLMResponse(BaseModel):
    success: bool
    response: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

def save_instruction(instruction: str) -> str:
    """Save instruction to a timestamped file."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = DATA_DIR / f"instruction_{timestamp}.txt"
    
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(instruction)
        return str(filename)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save instruction: {str(e)}")


@app.post("/api/instructions/")
async def create_instruction(instruction: InstructionRequest):
    """
    Process an instruction using the local LLM and save the result.
    """
    try:
        filepath = save_instruction(instruction.content)
        llm_response = await llm_client.generate_text(
            prompt=instruction.content,
            max_tokens=instruction.max_tokens,
            temperature=instruction.temperature
        )


        generated_content = llm_response.get('choices', [{}])[0].get('message', {}).get('content', '')
        
        # Save the LLM response
        response_file = filepath.replace('.txt', '_response.txt')
        with open(response_file, 'w', encoding='utf-8') as f:
            f.write(generated_content)
        
        return {
            "status": "success",
            "message": "Instruction processed successfully",
            "filepath": filepath,
            "response_file": response_file,
            "llm_response": llm_response
        }
    except Exception as e:
        error_msg = f"Error processing instruction: {str(e)}"
        raise HTTPException(status_code=500, detail=error_msg)

@app.post("/api/llm/generate")
async def generate_text(request: Dict[str, Any]):
    """
    Direct endpoint to generate text using the LLM.
    
    Example request body:
    {
        "prompt": "Tell me a joke about programming",
        "max_tokens": 100,
        "temperature": 0.8
    }
    """
    try:
        response = await LLMClient.generate_text(
            prompt=request.get('prompt', ''),
            max_tokens=request.get('max_tokens', 200),
            temperature=request.get('temperature', 0.7),
            **{k: v for k, v in request.items() 
               if k not in ['prompt', 'max_tokens', 'temperature']}
        )
        return {"success": True, "response": response}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok", "message": "Service is running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
