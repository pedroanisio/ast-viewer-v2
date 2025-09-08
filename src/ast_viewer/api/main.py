"""
AST Viewer Code Intelligence Platform - FastAPI Application

Enterprise-grade code intelligence platform with multi-language support.
"""

import asyncio
import logging
from contextlib import asynccontextmanager
from typing import Dict, Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from strawberry.fastapi import GraphQLRouter

from ..graphql.schema import schema
from ..analyzers.universal import UniversalAnalyzer
from ..visualizations.engine import VisualizationEngine

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global instances
analyzer = None
viz_engine = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management."""
    global analyzer, viz_engine
    
    logger.info("🚀 Starting AST Viewer Code Intelligence Platform...")
    
    # Initialize core components
    try:
        analyzer = UniversalAnalyzer()
        viz_engine = VisualizationEngine()
        
        logger.info(f"✅ Loaded {len(analyzer.get_supported_languages())} language analyzers")
        logger.info(f"✅ Loaded {len(viz_engine.get_available_visualizations())} visualization types")
        
    except Exception as e:
        logger.warning(f"⚠️  Component initialization failed: {e}")
        # Continue without full initialization
        
    logger.info("🎯 AST Viewer API is ready!")
    
    yield
    
    logger.info("🛑 Shutting down AST Viewer...")

# Create FastAPI application
app = FastAPI(
    title="AST Viewer Code Intelligence Platform",
    description="Enterprise-grade code intelligence platform with multi-language support and advanced visualizations",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Add middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(GZipMiddleware, minimum_size=1000)

# GraphQL router
graphql_app = GraphQLRouter(schema, path="/graphql")
app.include_router(graphql_app, prefix="/graphql")

@app.get("/")
async def root():
    """Root endpoint with platform information."""
    return {
        "name": "AST Viewer Code Intelligence Platform",
        "version": "2.0.0",
        "description": "Enterprise-grade code intelligence platform",
        "features": [
            "Multi-language code analysis",
            "Advanced visualizations", 
            "Graph-based intelligence",
            "Interactive dashboards"
        ],
        "endpoints": {
            "health": "/health",
            "graphql": "/graphql",
            "docs": "/docs"
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    global analyzer, viz_engine
    
    status = {
        "status": "healthy",
        "version": "2.0.0",
        "components": {
            "analyzer": "ready" if analyzer else "not_initialized",
            "visualizations": "ready" if viz_engine else "not_initialized"
        }
    }
    
    # Check component health
    if analyzer:
        try:
            languages = analyzer.get_supported_languages()
            status["components"]["analyzer"] = f"ready ({len(languages)} languages)"
        except Exception:
            status["components"]["analyzer"] = "error"
            
    if viz_engine:
        try:
            viz_types = viz_engine.get_available_visualizations()
            status["components"]["visualizations"] = f"ready ({len(viz_types)} types)"
        except Exception:
            status["components"]["visualizations"] = "error"
    
    return status

@app.get("/status")
async def detailed_status():
    """Detailed system status."""
    global analyzer, viz_engine
    
    status = {
        "platform": "AST Viewer Code Intelligence Platform",
        "version": "2.0.0",
        "uptime": "running",
    }
    
    # Analyzer status
    if analyzer:
        try:
            languages = analyzer.get_supported_languages()
            status["analyzer"] = {
                "status": "ready",
                "supported_languages": list(languages),
                "language_count": len(languages)
            }
        except Exception as e:
            status["analyzer"] = {
                "status": "error",
                "error": str(e)
            }
    else:
        status["analyzer"] = {"status": "not_initialized"}
    
    # Visualization engine status  
    if viz_engine:
        try:
            viz_types = viz_engine.get_available_visualizations()
            status["visualizations"] = {
                "status": "ready",
                "available_types": list(viz_types),
                "type_count": len(viz_types)
            }
        except Exception as e:
            status["visualizations"] = {
                "status": "error", 
                "error": str(e)
            }
    else:
        status["visualizations"] = {"status": "not_initialized"}
        
    return status

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler."""
    logger.error(f"Unhandled exception: {exc}")
    return HTTPException(
        status_code=500,
        detail="Internal server error"
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
