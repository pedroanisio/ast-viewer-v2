"""Visualization REST API endpoints."""

import logging
import time
import uuid
from pathlib import Path
from typing import Dict, List, Optional, Any

from fastapi import APIRouter, HTTPException, Query, Depends, status
from fastapi.responses import HTMLResponse, FileResponse

from .models import (
    VisualizationRequest, VisualizationResult, APIResponse, ErrorResponse,
    VisualizationTypeEnum, ExportFormatEnum
)
from .endpoints import create_success_response, create_error_response, get_visualization_engine
from ..visualizations.engine import VisualizationEngine, VisualizationType
from ..analyzers.integrated import IntegratedCodeAnalyzer

logger = logging.getLogger(__name__)

# Router setup
viz_router = APIRouter(prefix="/api/v1/visualization", tags=["Visualizations"])


async def get_integrated_analyzer() -> IntegratedCodeAnalyzer:
    """Get integrated analyzer instance."""
    return IntegratedCodeAnalyzer()


@viz_router.get("/types", response_model=APIResponse)
async def get_available_visualizations(
    viz_engine: VisualizationEngine = Depends(get_visualization_engine)
):
    """Get list of available visualization types."""
    try:
        available_types = viz_engine.get_available_visualizations()
        
        visualization_info = {
            "available_types": list(available_types),
            "type_details": {
                "dependency_graph": {
                    "name": "Dependency Graph",
                    "description": "Visualizes dependencies between files and modules",
                    "interactive": True,
                    "export_formats": ["html", "png", "svg", "pdf", "json"]
                },
                "call_graph": {
                    "name": "Call Graph", 
                    "description": "Shows function/method call relationships",
                    "interactive": True,
                    "export_formats": ["html", "png", "svg", "pdf", "json"]
                },
                "complexity_heatmap": {
                    "name": "Complexity Heatmap",
                    "description": "Heat map showing code complexity across files",
                    "interactive": True,
                    "export_formats": ["html", "png", "svg", "pdf"]
                },
                "architecture_map": {
                    "name": "Architecture Map",
                    "description": "High-level architectural overview of the codebase", 
                    "interactive": True,
                    "export_formats": ["html", "png", "svg", "pdf"]
                },
                "reference_network": {
                    "name": "Reference Network",
                    "description": "Network of symbol references and relationships",
                    "interactive": True,
                    "export_formats": ["html", "png", "svg", "pdf", "json"]
                },
                "inheritance_tree": {
                    "name": "Inheritance Tree",
                    "description": "Class inheritance hierarchies",
                    "interactive": True,
                    "export_formats": ["html", "png", "svg", "pdf"]
                },
                "file_interaction_matrix": {
                    "name": "File Interaction Matrix",
                    "description": "Matrix showing interactions between files",
                    "interactive": True,
                    "export_formats": ["html", "png", "svg"]
                },
                "coupling_matrix": {
                    "name": "Coupling Matrix",
                    "description": "Module coupling analysis matrix",
                    "interactive": True,
                    "export_formats": ["html", "png", "svg"]
                },
                "module_overview": {
                    "name": "Module Overview",
                    "description": "Overview of module structure and relationships",
                    "interactive": True,
                    "export_formats": ["html", "png", "svg", "pdf"]
                },
                "layer_diagram": {
                    "name": "Layer Diagram",
                    "description": "Architectural layer visualization",
                    "interactive": True,
                    "export_formats": ["html", "png", "svg", "pdf"]
                },
                "impact_visualization": {
                    "name": "Impact Visualization",
                    "description": "Visualizes impact analysis results",
                    "interactive": True,
                    "export_formats": ["html", "png", "svg", "pdf"]
                },
                "change_propagation": {
                    "name": "Change Propagation",
                    "description": "Shows how changes propagate through the codebase",
                    "interactive": True,
                    "export_formats": ["html", "png", "svg", "pdf"]
                },
                "hotspot_analysis": {
                    "name": "Hotspot Analysis",
                    "description": "Identifies complexity and change hotspots",
                    "interactive": True,
                    "export_formats": ["html", "png", "svg"]
                },
                "evolution_timeline": {
                    "name": "Evolution Timeline",
                    "description": "Timeline of codebase evolution",
                    "interactive": True,
                    "export_formats": ["html", "png", "svg"]
                },
                "growth_analysis": {
                    "name": "Growth Analysis",
                    "description": "Analysis of codebase growth patterns",
                    "interactive": True,
                    "export_formats": ["html", "png", "svg"]
                },
                "project_dashboard": {
                    "name": "Project Dashboard",
                    "description": "Comprehensive project overview dashboard",
                    "interactive": True,
                    "export_formats": ["html", "png", "pdf"]
                },
                "quality_dashboard": {
                    "name": "Quality Dashboard",
                    "description": "Code quality metrics dashboard",
                    "interactive": True,
                    "export_formats": ["html", "png", "pdf"]
                }
            },
            "total_types": len(available_types)
        }
        
        return create_success_response(
            visualization_info, 
            f"Found {len(available_types)} available visualization types"
        )
        
    except Exception as e:
        logger.error(f"Failed to get visualization types: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve visualization types"
        )


@viz_router.post("/generate", response_model=APIResponse)
async def generate_visualization(
    request: VisualizationRequest,
    viz_engine: VisualizationEngine = Depends(get_visualization_engine),
    analyzer: IntegratedCodeAnalyzer = Depends(get_integrated_analyzer)
):
    """Generate a visualization for a project."""
    try:
        start_time = time.time()
        
        # Get project intelligence data
        intelligence = analyzer.get_intelligence(request.project_id)
        if not intelligence:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No analysis data found for project: {request.project_id}"
            )
        
        # Configure visualization
        viz_config = {
            "width": request.width,
            "height": request.height,
            "interactive": request.interactive,
            "format": request.export_format.value
        }
        
        # Apply filters
        if request.file_filter:
            viz_config["file_filter"] = request.file_filter
        if request.element_filter:
            viz_config["element_filter"] = [e.value for e in request.element_filter]
        if request.complexity_threshold:
            viz_config["complexity_threshold"] = request.complexity_threshold
        
        # Generate visualization
        visualization_data = viz_engine.generate_visualization(
            intelligence,
            VisualizationType(request.visualization_type.value),
            **viz_config
        )
        
        generation_time = time.time() - start_time
        
        # Create result
        result = VisualizationResult(
            visualization_id=str(uuid.uuid4()),
            visualization_type=request.visualization_type,
            format=request.export_format,
            content=visualization_data.get("content") if request.export_format in [ExportFormatEnum.HTML, ExportFormatEnum.JSON] else None,
            file_path=visualization_data.get("file_path"),
            metadata={
                "project_id": request.project_id,
                "config": viz_config,
                "data_points": visualization_data.get("data_points", 0),
                "nodes": visualization_data.get("nodes", 0),
                "edges": visualization_data.get("edges", 0)
            } if request.include_metadata else {},
            generation_time=generation_time
        )
        
        return create_success_response(
            result,
            f"Visualization generated successfully in {generation_time:.2f}s"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Visualization generation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Visualization generation failed: {str(e)}"
        )


@viz_router.post("/dashboard", response_model=APIResponse)
async def generate_project_dashboard(
    project_id: str,
    include_all_metrics: bool = Query(default=True, description="Include all available metrics"),
    export_format: ExportFormatEnum = Query(default=ExportFormatEnum.HTML, description="Export format"),
    viz_engine: VisualizationEngine = Depends(get_visualization_engine),
    analyzer: IntegratedCodeAnalyzer = Depends(get_integrated_analyzer)
):
    """Generate a comprehensive project dashboard."""
    try:
        start_time = time.time()
        
        # Get project intelligence data
        intelligence = analyzer.get_intelligence(project_id)
        if not intelligence:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No analysis data found for project: {project_id}"
            )
        
        # Generate dashboard
        dashboard_config = {
            "format": export_format.value,
            "include_all_metrics": include_all_metrics,
            "interactive": True,
            "width": 1400,
            "height": 1000
        }
        
        dashboard_data = viz_engine.generate_visualization(
            intelligence,
            VisualizationType.PROJECT_DASHBOARD,
            **dashboard_config
        )
        
        generation_time = time.time() - start_time
        
        # Create result
        result = VisualizationResult(
            visualization_id=str(uuid.uuid4()),
            visualization_type=VisualizationTypeEnum.PROJECT_DASHBOARD,
            format=export_format,
            content=dashboard_data.get("content") if export_format in [ExportFormatEnum.HTML, ExportFormatEnum.JSON] else None,
            file_path=dashboard_data.get("file_path"),
            metadata={
                "project_id": project_id,
                "dashboard_sections": dashboard_data.get("sections", []),
                "metrics_included": dashboard_data.get("metrics", []),
                "visualizations_count": dashboard_data.get("visualizations_count", 0)
            },
            generation_time=generation_time
        )
        
        return create_success_response(
            result,
            f"Project dashboard generated successfully in {generation_time:.2f}s"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Dashboard generation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Dashboard generation failed: {str(e)}"
        )


@viz_router.get("/export/{visualization_id}")
async def export_visualization(
    visualization_id: str,
    format: ExportFormatEnum = Query(default=ExportFormatEnum.HTML, description="Export format")
):
    """Export a previously generated visualization."""
    try:
        # This would retrieve and export a stored visualization
        # For now, return a placeholder response
        
        # In a real implementation, this would:
        # 1. Look up the visualization by ID
        # 2. Convert to requested format if different
        # 3. Return the file or content
        
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Visualization export endpoint not yet implemented"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Visualization export failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Visualization export failed: {str(e)}"
        )


@viz_router.get("/preview/{visualization_type}")
async def preview_visualization_type(
    visualization_type: VisualizationTypeEnum,
    viz_engine: VisualizationEngine = Depends(get_visualization_engine)
):
    """Get a preview/sample of a visualization type."""
    try:
        # Generate a sample visualization for preview
        preview_data = {
            "type": visualization_type.value,
            "description": f"Preview of {visualization_type.value} visualization",
            "sample_config": {
                "width": 800,
                "height": 600,
                "interactive": True,
                "layout": "force_directed"
            },
            "estimated_generation_time": "1-5 seconds",
            "supported_formats": ["html", "png", "svg", "pdf"],
            "required_data": [
                "project_analysis",
                "code_intelligence",
                "symbol_relationships"
            ]
        }
        
        return create_success_response(
            preview_data,
            f"Preview data for {visualization_type.value} visualization"
        )
        
    except Exception as e:
        logger.error(f"Visualization preview failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Visualization preview failed: {str(e)}"
        )


@viz_router.get("/gallery", response_model=APIResponse)
async def visualization_gallery():
    """Get a gallery of sample visualizations with thumbnails."""
    try:
        gallery_data = {
            "featured_visualizations": [
                {
                    "type": "dependency_graph",
                    "title": "Dependency Graph",
                    "description": "Interactive dependency visualization",
                    "thumbnail": "/static/thumbnails/dependency_graph.png",
                    "complexity": "Medium",
                    "use_cases": ["Architecture review", "Dependency analysis", "Refactoring planning"]
                },
                {
                    "type": "complexity_heatmap", 
                    "title": "Complexity Heatmap",
                    "description": "Code complexity visualization",
                    "thumbnail": "/static/thumbnails/complexity_heatmap.png", 
                    "complexity": "Low",
                    "use_cases": ["Code review", "Technical debt identification", "Quality assessment"]
                },
                {
                    "type": "project_dashboard",
                    "title": "Project Dashboard",
                    "description": "Comprehensive project overview",
                    "thumbnail": "/static/thumbnails/project_dashboard.png",
                    "complexity": "High", 
                    "use_cases": ["Project management", "Team communication", "Executive reporting"]
                }
            ],
            "categories": {
                "graphs": ["dependency_graph", "call_graph", "reference_network", "inheritance_tree"],
                "heatmaps": ["complexity_heatmap", "file_interaction_matrix", "coupling_matrix"],
                "architecture": ["architecture_map", "module_overview", "layer_diagram"],
                "analysis": ["impact_visualization", "change_propagation", "hotspot_analysis"],
                "dashboards": ["project_dashboard", "quality_dashboard"],
                "timeline": ["evolution_timeline", "growth_analysis"]
            },
            "total_visualizations": 17
        }
        
        return create_success_response(
            gallery_data,
            "Visualization gallery loaded successfully"
        )
        
    except Exception as e:
        logger.error(f"Gallery loading failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to load visualization gallery"
        )


# Export router
__all__ = ["viz_router"]
