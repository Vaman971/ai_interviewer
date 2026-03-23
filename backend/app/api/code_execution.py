from fastapi import APIRouter, HTTPException, BackgroundTasks
import httpx
from pydantic import BaseModel
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/execute", tags=["code_execution"])

class CodeExecutionRequest(BaseModel):
    language: str
    version: str = "*"
    code: str

class CodeExecutionResponse(BaseModel):
    stdout: str
    stderr: str
    compile_output: str | None = None
    language: str
    version: str

@router.post("", response_model=CodeExecutionResponse)
async def execute_code(request: CodeExecutionRequest):
    """
    Executes the given code securely by proxying to the public Piston API.
    This acts as a remote code sandbox for the technical/DSA rounds.
    """
    url = "https://emkc.org/api/v2/piston/execute"
    payload = {
        "language": request.language,
        "version": request.version,
        "files": [
            {
                "content": request.code
            }
        ]
    }
    
    logger.info(f"Executing {request.language} code via Piston API")
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, json=payload, timeout=15.0)
            response.raise_for_status()
            data = response.json()
            
            run_data = data.get("run", {})
            compile_data = data.get("compile", {})
            
            return CodeExecutionResponse(
                stdout=run_data.get("stdout", ""),
                stderr=run_data.get("stderr", ""),
                compile_output=compile_data.get("stderr", "") if compile_data else None,
                language=data.get("language", request.language),
                version=data.get("version", request.version)
            )
        except httpx.HTTPStatusError as e:
            logger.error(f"Piston API HTTP error: {e.response.text}")
            raise HTTPException(status_code=500, detail="Code execution engine returned an error.")
        except Exception as e:
            logger.error(f"Piston API internal error: {e}")
            raise HTTPException(status_code=500, detail="Failed to reach the code execution sandbox.")
