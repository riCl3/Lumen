import os
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

from scanner import ScannerPipeline

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("mcp-dashboard")

app = FastAPI(title="MCP Scanner Dashboard")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Pipeline
pipeline = ScannerPipeline()

# Models
class ScanRequest(BaseModel):
    path: str
    model: Optional[str] = None

# API Endpoints
@app.get("/api/models")
async def get_models():
    """Returns a list of available models."""
    # In a real scenario, we could query OpenRouter's API
    return [
        {"id": "openai/gpt-3.5-turbo", "name": "GPT-3.5 Turbo"},
        {"id": "openai/gpt-4-turbo", "name": "GPT-4 Turbo"},
        {"id": "anthropic/claude-3-opus", "name": "Claude 3 Opus"},
        {"id": "anthropic/claude-3-sonnet", "name": "Claude 3 Sonnet"},
        {"id": "mistralai/mistral-large", "name": "Mistral Large"},
    ]

@app.post("/api/scan")
async def run_scan(request: ScanRequest):
    """Runs the scan on the specified directory."""
    directory = request.path
    if not os.path.isdir(directory):
        raise HTTPException(status_code=400, detail="Invalid directory path")
    
    # Update model in env if provided (hacky but works for simple singleton usage)
    if request.model:
        os.environ["OPENROUTER_MODEL"] = request.model
        # Re-init analyzer to pick up new model
        pipeline.llm_analyzer.__init__()

    output_file = "scan_results.json"
    
    output_file = "scan_results.json"
    
    try:
        print(f"DEBUG: Processing scan for {directory}") # Force output to stdout
        from fastapi.concurrency import run_in_threadpool
        print("DEBUG: Threadpool starting")
        summary = await run_in_threadpool(pipeline.run_scan, directory, output_file)
        print("DEBUG: Threadpool finished")
        
        # Read the generated results
        if os.path.exists(output_file):
            with open(output_file, "r", encoding="utf-8") as f:
                results = json.load(f)
            return results
        else:
            return {"error": "Scan failed to generate results file."}
            
    except Exception as e:
        logger.exception("Scan failed")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/results")
async def get_results():
    """Returns the latest scan results."""
    output_file = "scan_results.json"
    if os.path.exists(output_file):
        with open(output_file, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

@app.get("/api/browse")
async def browse_files(path: str = ""):
    """List directories for file browser."""
    try:
        if not path:
            # List drives on Windows
            if os.name == 'nt':
                drives = []
                import string
                from ctypes import windll
                bitmask = windll.kernel32.GetLogicalDrives()
                for letter in string.ascii_uppercase:
                    if bitmask & 1:
                        drives.append({
                            "name": f"{letter}:\\",
                            "path": f"{letter}:\\",
                            "type": "drive"
                        })
                    bitmask >>= 1
                return drives
            else:
                # Root for Unix
                return [{"name": "/", "path": "/", "type": "drive"}]
        
        # List directory
        p = Path(path)
        if not p.exists() or not p.is_dir():
            raise HTTPException(status_code=400, detail="Invalid directory")
            
        items = []
        # Add parent directory option if we are not at a root
        if p.parent != p:
             items.append({
                 "name": "..",
                 "path": str(p.parent),
                 "type": "parent"
             })

        for item in p.iterdir():
            try:
                if item.is_dir():
                    items.append({
                        "name": item.name,
                        "path": str(item),
                        "type": "dir"
                    })
            except PermissionError:
                continue
                
        return sorted(items, key=lambda x: x["name"])
        
    except Exception as e:
        logger.error(f"Browse error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/test-llm")
async def test_llm():
    """Test OpenRouter connectivity."""
    try:
        logger.info("Starting LLM connectivity test...")
        pipeline.llm_analyzer.__init__() # Reload env vars
        
        if not pipeline.llm_analyzer.client:
             logger.error("LLM Client not initialized. Check API Key.")
             return JSONResponse(status_code=400, content={"detail": "API Key missing"})

        logger.info(f"Sending test ping to model: {pipeline.llm_analyzer.model}")
        
        # Simple test
        completion = pipeline.llm_analyzer.client.chat.completions.create(
            model=pipeline.llm_analyzer.model,
            messages=[{"role": "user", "content": "Say 'OK' if you can hear me."}],
            max_tokens=10
        )
        
        response = completion.choices[0].message.content
        logger.info(f"LLM Test Success. Response: {response}")
        return {"status": "success", "response": response}
        
    except Exception as e:
        logger.error(f"LLM Test Failed: {e}")
        return JSONResponse(status_code=500, content={"detail": str(e)})

@app.post("/api/test-logs")
async def test_logs():
    """Add test logs to verify polling works."""
    logger.info("Test log 1: Logger is working!")
    logger.info("Test log 2: Logs are being captured")
    logger.info("Test log 3: Frontend should display this")
    return {"status": "ok", "message": "Added 3 test logs"}

# Log Buffer for frontend
log_buffer = []

class BufferHandler(logging.Handler):
    def emit(self, record):
        msg = self.format(record)
        log_buffer.append(msg)
        if len(log_buffer) > 100: # Keep last 100 logs
            log_buffer.pop(0)

# Add handler to root logger
buffer_handler = BufferHandler()
buffer_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
buffer_handler.setLevel(logging.INFO)

# Add to root logger to catch everything
root_logger = logging.getLogger()
root_logger.addHandler(buffer_handler)
root_logger.setLevel(logging.INFO)

# Ensure specific loggers also use INFO level
logging.getLogger("mcp-dashboard").setLevel(logging.INFO)
logging.getLogger("scanner").setLevel(logging.INFO)
logging.getLogger("scanner.llm").setLevel(logging.INFO)

# Add an initial test log
logger.info("MCP Scanner server started - logging initialized")

@app.get("/api/logs")
async def get_logs():
    """Returns the latest logs."""
    return {"logs": log_buffer}

@app.delete("/api/logs")
async def clear_logs():
    """Clears the log buffer."""
    log_buffer.clear()
    return {"status": "cleared"}

# Serve Static Files
static_dir = Path(__file__).parent / "static"
frontend_dir = Path(__file__).parent / "frontend"

static_dir.mkdir(exist_ok=True)
if frontend_dir.exists():
    app.mount("/frontend", StaticFiles(directory=frontend_dir), name="frontend")
app.mount("/static", StaticFiles(directory=static_dir), name="static")

@app.get("/", response_class=HTMLResponse)
async def read_root():
    # Prefer new dashboard if exists
    dashboard_path = frontend_dir / "dashboard.html"
    if dashboard_path.exists():
         return dashboard_path.read_text(encoding="utf-8")
         
    index_path = static_dir / "index.html"
    if index_path.exists():
        return index_path.read_text(encoding="utf-8")
    return "<h1>MCP Scanner Dashboard</h1><p>Please create frontend/dashboard.html or static/index.html</p>"

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)
