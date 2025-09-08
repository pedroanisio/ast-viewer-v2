#!/usr/bin/env python3
"""
Local development server for AST Viewer Code Intelligence Platform
Run this to test the app locally before Docker deployment.
"""

import os
import sys
import logging
from pathlib import Path

# Add src to Python path
project_root = Path(__file__).parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

# Set environment variables for local development
os.environ.setdefault("DEBUG", "true")
os.environ.setdefault("LOG_LEVEL", "DEBUG")
os.environ.setdefault("PYTHONPATH", str(src_path))

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def check_dependencies():
    """Check if required dependencies are available."""
    missing_deps = []
    
    try:
        import fastapi
        logger.info("✅ FastAPI available")
    except ImportError:
        missing_deps.append("fastapi")
    
    try:
        import uvicorn
        logger.info("✅ Uvicorn available")
    except ImportError:
        missing_deps.append("uvicorn")
    
    try:
        import strawberry
        logger.info("✅ Strawberry GraphQL available")
    except ImportError:
        missing_deps.append("strawberry-graphql")
    
    try:
        import pydantic
        logger.info("✅ Pydantic available")
    except ImportError:
        missing_deps.append("pydantic")
    
    if missing_deps:
        logger.error(f"❌ Missing dependencies: {', '.join(missing_deps)}")
        logger.info("Install them with: pip install " + " ".join(missing_deps))
        return False
    
    return True

def run_app():
    """Run the FastAPI application locally."""
    logger.info("🚀 Starting AST Viewer locally...")
    
    if not check_dependencies():
        logger.error("❌ Cannot start - missing dependencies")
        return 1
    
    try:
        # Import the app
        from ast_viewer.api.main import app
        logger.info("✅ FastAPI app imported successfully")
        
        # Start with uvicorn
        import uvicorn
        logger.info("🎯 Starting development server on http://localhost:8001")
        logger.info("📚 API docs will be available at http://localhost:8001/docs")
        logger.info("🔍 GraphQL playground at http://localhost:8001/graphql")
        
        uvicorn.run(
            app,
            host="127.0.0.1",
            port=8001,
            reload=True,
            log_level="debug"
        )
        
    except ImportError as e:
        logger.error(f"❌ Import error: {e}")
        logger.info("💡 This is expected if some components aren't fully implemented yet")
        
        # Try with a minimal app
        logger.info("🔄 Trying with minimal FastAPI app...")
        from fastapi import FastAPI
        
        minimal_app = FastAPI(title="AST Viewer (Minimal)", version="2.0.0")
        
        @minimal_app.get("/")
        def root():
            return {
                "name": "AST Viewer Code Intelligence Platform",
                "version": "2.0.0",
                "status": "running locally",
                "message": "Minimal mode - some features may not be available"
            }
        
        @minimal_app.get("/health")
        def health():
            return {"status": "healthy", "mode": "minimal"}
        
        uvicorn.run(minimal_app, host="127.0.0.1", port=8001, reload=True)
        
    except Exception as e:
        logger.error(f"❌ Failed to start: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(run_app())
