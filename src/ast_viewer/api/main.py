"""
AST Viewer Code Intelligence Platform - FastAPI Application

Enterprise-grade code intelligence platform with multi-language support.
Provides both GraphQL and REST API endpoints.
"""

import asyncio
import logging
from contextlib import asynccontextmanager
from typing import Dict, Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from strawberry.fastapi import GraphQLRouter

from ..graphql.integration import create_fastapi_app, get_graphql_context
from ..graphql.modern_schema import create_schema
from .docs_server import GraphQLDocsServer
from ..analyzers.universal import UniversalAnalyzer
from ..analyzers.integrated import IntegratedCodeAnalyzer
from ..visualizations.engine import VisualizationEngine

# Import REST API components
from .endpoints import router as api_router
from .visualization_endpoints import viz_router
from .middleware import (
    RequestLoggingMiddleware,
    RateLimitingMiddleware,
    SecurityHeadersMiddleware,
    ErrorHandlingMiddleware,
    MetricsMiddleware,
    get_metrics,
    metrics_middleware_instance
)
from .models import APIResponse

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global instances
analyzer = None
integrated_analyzer = None
viz_engine = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management."""
    global analyzer, integrated_analyzer, viz_engine
    
    logger.info("🚀 Starting AST Viewer Code Intelligence Platform...")
    
    # Initialize core components
    try:
        analyzer = UniversalAnalyzer()
        integrated_analyzer = IntegratedCodeAnalyzer()
        viz_engine = VisualizationEngine()
        
        logger.info(f"✅ Loaded {len(analyzer.get_supported_languages())} language analyzers")
        logger.info(f"✅ Loaded {len(viz_engine.get_available_visualizations())} visualization types")
        logger.info("✅ Integrated analyzer with intelligence engine ready")
        
    except Exception as e:
        logger.warning(f"⚠️  Component initialization failed: {e}")
        # Continue without full initialization
        
    logger.info("🎯 AST Viewer API is ready!")
    logger.info("📡 GraphQL endpoint: /graphql")
    logger.info("🔄 REST API endpoints: /api/v1/")
    logger.info("📚 API Documentation: /docs")
    
    yield
    
    logger.info("🛑 Shutting down AST Viewer...")

# Create FastAPI application
app = FastAPI(
    title="AST Viewer Code Intelligence Platform",
    description="Enterprise-grade code intelligence platform with multi-language support and advanced visualizations. Provides both GraphQL and REST API endpoints for comprehensive code analysis.",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
    openapi_tags=[
        {"name": "Health", "description": "System health and status endpoints"},
        {"name": "Analysis", "description": "Code analysis endpoints"},
        {"name": "Intelligence", "description": "Code intelligence and symbol analysis"},
        {"name": "Visualizations", "description": "Visualization generation and export"},
        {"name": "Projects", "description": "Project-level analysis and management"},
        {"name": "GraphQL", "description": "GraphQL endpoint for advanced queries"}
    ]
)

# Add custom middleware stack (order matters!)
global metrics_middleware_instance
metrics_middleware_instance = MetricsMiddleware(app)

app.add_middleware(ErrorHandlingMiddleware)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RateLimitingMiddleware, requests_per_minute=100, requests_per_hour=1000)
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(metrics_middleware_instance.__class__, app=app)

# Add CORS middleware (should be last in the stack)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add compression middleware
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Include REST API routers
app.include_router(api_router, tags=["Analysis", "Intelligence", "Projects"])
app.include_router(viz_router, tags=["Visualizations"])

# GraphQL router with modern schema and context injection
schema = create_schema()
graphql_app = GraphQLRouter(schema, context_getter=get_graphql_context)
app.include_router(graphql_app, prefix="/graphql", tags=["GraphQL"])

# Mount GraphQL documentation server
docs_server = GraphQLDocsServer()
app.mount("/graphql-docs", docs_server.app)

@app.get("/", response_model=APIResponse, tags=["Health"])
async def root():
    """Root endpoint with platform information."""
    platform_info = {
        "name": "AST Viewer Code Intelligence Platform",
        "version": "2.0.0",
        "description": "Enterprise-grade code intelligence platform with multi-language support and advanced visualizations",
        "features": [
            "Multi-language code analysis (Python, JavaScript, TypeScript, Go, Rust)",
            "Advanced visualizations (17+ types)",
            "Graph-based code intelligence",
            "Interactive dashboards",
            "GitHub repository analysis",
            "Impact analysis",
            "Dependency visualization",
            "Real-time metrics"
        ],
        "apis": {
            "rest": {
                "base_url": "/api/v1",
                "documentation": "/docs",
                "endpoints": {
                    "health": "/api/v1/health",
                    "file_analysis": "/api/v1/analysis/file",
                    "directory_analysis": "/api/v1/analysis/directory", 
                    "project_analysis": "/api/v1/analysis/project",
                    "symbol_search": "/api/v1/intelligence/symbols/search",
                    "impact_analysis": "/api/v1/intelligence/impact",
                    "visualizations": "/api/v1/visualization/generate",
                    "dashboard": "/api/v1/visualization/dashboard"
                }
            },
            "graphql": {
                "endpoint": "/graphql",
                "documentation": "/graphql-docs",
                "playground": "/graphql-docs/playground",
                "schema": "/graphql-docs/schema.graphql",
                "examples": "/graphql-docs/examples.md"
            }
        },
        "capabilities": {
            "supported_languages": list(analyzer.get_supported_languages()) if analyzer else [],
            "visualization_types": list(viz_engine.get_available_visualizations()) if viz_engine else [],
            "intelligence_features": [
                "Symbol relationship analysis",
                "Call graph generation",
                "Dependency tracking",
                "Impact assessment",
                "Complexity analysis",
                "Reference tracking"
            ]
        }
    }
    
    return APIResponse(
        success=True,
        message="AST Viewer Code Intelligence Platform - Ready to analyze your code!",
        data=platform_info
    )

@app.get("/metrics", response_model=APIResponse, tags=["Health"])
async def api_metrics():
    """Get API usage metrics."""
    try:
        metrics_data = get_metrics()
        return APIResponse(
            success=True,
            message="API metrics retrieved successfully",
            data=metrics_data
        )
    except Exception as e:
        logger.error(f"Failed to get metrics: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve metrics"
        )

# Legacy health endpoints (maintained for backward compatibility)
@app.get("/health", tags=["Health"])
async def health_check():
    """Legacy health check endpoint."""
    global analyzer, integrated_analyzer, viz_engine
    
    status = {
        "status": "healthy",
        "version": "2.0.0",
        "components": {
            "universal_analyzer": "ready" if analyzer else "not_initialized",
            "integrated_analyzer": "ready" if integrated_analyzer else "not_initialized",
            "visualizations": "ready" if viz_engine else "not_initialized"
        }
    }
    
    # Check component health
    if analyzer:
        try:
            languages = analyzer.get_supported_languages()
            status["components"]["universal_analyzer"] = f"ready ({len(languages)} languages)"
        except Exception:
            status["components"]["universal_analyzer"] = "error"
            
    if viz_engine:
        try:
            viz_types = viz_engine.get_available_visualizations()
            status["components"]["visualizations"] = f"ready ({len(viz_types)} types)"
        except Exception:
            status["components"]["visualizations"] = "error"
    
    return status

@app.get("/status", tags=["Health"])
async def detailed_status():
    """Legacy detailed system status."""
    global analyzer, integrated_analyzer, viz_engine
    
    status = {
        "platform": "AST Viewer Code Intelligence Platform",
        "version": "2.0.0",
        "uptime": "running",
    }
    
    # Universal analyzer status
    if analyzer:
        try:
            languages = analyzer.get_supported_languages()
            status["universal_analyzer"] = {
                "status": "ready",
                "supported_languages": list(languages),
                "language_count": len(languages)
            }
        except Exception as e:
            status["universal_analyzer"] = {
                "status": "error",
                "error": str(e)
            }
    else:
        status["universal_analyzer"] = {"status": "not_initialized"}
    
    # Integrated analyzer status
    if integrated_analyzer:
        status["integrated_analyzer"] = {"status": "ready"}
    else:
        status["integrated_analyzer"] = {"status": "not_initialized"}
    
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
