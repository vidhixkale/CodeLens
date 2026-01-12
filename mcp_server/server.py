from __future__ import annotations

import os
from datetime import datetime, timezone

import requests
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from .tools import read_file as tool_read_file, list_directory as tool_list_directory, review_code as tool_review_code

# Load .env if present
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass


OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "llama3.2:3b")


class ReviewRequest(BaseModel):
    code: str = Field(..., description="Source code to review")
    language: str = Field("python", description="Programming language of the code")


class ReviewResponse(BaseModel):
    review: str
    timestamp: str
    model: str = Field(default_factory=lambda: OLLAMA_MODEL)


class ReadFileRequest(BaseModel):
    file_path: str


class ListDirectoryRequest(BaseModel):
    dir_path: str


app = FastAPI(title="Local Code Reviewer MCP Server", version="0.1.0")

# CORS for local dev (Vite defaults to 5173)
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins + ["*"],  # permissive for local use only
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    ollama_ok = False
    try:
        r = requests.get(f"{OLLAMA_URL}/api/tags", timeout=0.8)
        ollama_ok = r.status_code == 200
    except Exception:
        ollama_ok = False

    return {
        "status": "ok",
        "time": datetime.now(timezone.utc).isoformat(),
        "ollama": {
            "available": ollama_ok,
            "url": OLLAMA_URL,
            "model": OLLAMA_MODEL,
        },
    }


@app.post("/read-file")
def read_file(req: ReadFileRequest):
    try:
        content = tool_read_file(req.file_path)
        return {"path": req.file_path, "content": content}
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="File not found")
    except PermissionError:
        raise HTTPException(status_code=403, detail="Permission denied reading file")
    except IsADirectoryError:
        raise HTTPException(status_code=400, detail="Path is a directory, not a file")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error reading file: {e}")


@app.post("/list-directory")
def list_directory(req: ListDirectoryRequest):
    try:
        entries = tool_list_directory(req.dir_path)
        return {"path": req.dir_path, "entries": entries}
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Directory not found")
    except NotADirectoryError:
        raise HTTPException(status_code=400, detail="Path is not a directory")
    except PermissionError:
        raise HTTPException(status_code=403, detail="Permission denied listing directory")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error listing directory: {e}")


@app.post("/review", response_model=ReviewResponse)
def review(req: ReviewRequest):
    try:
        review_text = tool_review_code(
            code=req.code,
            language=req.language,
            model=OLLAMA_MODEL,
            ollama_url=OLLAMA_URL,
        )
        return ReviewResponse(
            review=review_text,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
    except HTTPException:
        raise
    except requests.RequestException as re:
        raise HTTPException(status_code=502, detail=f"Error contacting Ollama: {re}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error during review: {e}")


if __name__ == "__main__":
    import uvicorn
    host = os.environ.get("HOST", "127.0.0.1")
    try:
        port = int(os.environ.get("PORT", "8000"))
    except ValueError:
        port = 8000
    uvicorn.run("mcp_server.server:app", host=host, port=port, reload=True)
