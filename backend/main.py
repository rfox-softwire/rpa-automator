from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pathlib import Path
import os
from datetime import datetime

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
    """Endpoint to save a new instruction."""
    try:
        filepath = save_instruction(instruction.content)
        return {"status": "success", "message": "Instruction saved successfully", "filepath": filepath}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok", "message": "Service is running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
