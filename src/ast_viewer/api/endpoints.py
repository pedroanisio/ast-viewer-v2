"""REST API endpoints for the AST Viewer Code Intelligence Platform."""

import asyncio
import logging
import time
import uuid
from pathlib import Path
from typing import Dict, List, Optional, Any, Union

from fastapi import APIRouter, HTTPException, Query, Depends, BackgroundTasks, status
from fastapi.responses import HTMLResponse, FileResponse

from .models import (
    # Request models
    FileAnalysisRequest, DirectoryAnalysisRequest, ProjectAnalysisRequest,
    SymbolSearchRequest, VisualizationRequest, ImpactAnalysisRequest,
    
    # Response models
    APIResponse, ErrorResponse, FileAnalysisResult, ProjectAnalysisResult,
    VisualizationResult, ImpactAnalysisResult, HealthStatus, PaginatedResponse,
    
    # Data models
    CodeElement, ProjectMetrics, IntelligenceMetrics,
    
    # Enums
    LanguageEnum, ElementTypeEnum, VisualizationTypeEnum, ExportFormatEnum
)
from ..analyzers.universal import UniversalAnalyzer
from ..analyzers.integrated import IntegratedCodeAnalyzer
from ..visualizations.engine import VisualizationEngine
from ..common.converters import convert_nodes_to_graphql
from ..common.git_utils import (
    clone_github_repository, cleanup_repository, validate_github_url,
    GitRepositoryError
)

logger = logging.getLogger(__name__)

# Router setup
router = APIRouter(prefix="/api/v1", tags=["AST Viewer API"])

# Global analyzer instances (will be set by dependency injection)
universal_analyzer = None
integrated_analyzer = None
visualization_engine = None


# Dependency injection
async def get_universal_analyzer() -> UniversalAnalyzer:
    """Get universal analyzer instance."""
    global universal_analyzer
    if universal_analyzer is None:
        universal_analyzer = UniversalAnalyzer()
    return universal_analyzer


async def get_integrated_analyzer() -> IntegratedCodeAnalyzer:
    """Get integrated analyzer instance."""
    global integrated_analyzer
    if integrated_analyzer is None:
        integrated_analyzer = IntegratedCodeAnalyzer()
    return integrated_analyzer


async def get_visualization_engine() -> VisualizationEngine:
    """Get visualization engine instance."""
    global visualization_engine
    if visualization_engine is None:
        visualization_engine = VisualizationEngine()
    return visualization_engine


def generate_request_id() -> str:
    """Generate unique request ID."""
    return str(uuid.uuid4())


def create_success_response(data: Any, message: str = "Success") -> APIResponse:
    """Create standardized success response."""
    return APIResponse(
        success=True,
        message=message,
        data=data,
        request_id=generate_request_id()
    )


def create_error_response(error_type: str, message: str, details: Optional[Dict] = None) -> ErrorResponse:
    """Create standardized error response."""
    return ErrorResponse(
        error_type=error_type,
        message=message,
        details=details,
        request_id=generate_request_id()
    )


# Health and Status Endpoints
@router.get("/health", response_model=APIResponse)
async def health_check(
    analyzer: UniversalAnalyzer = Depends(get_universal_analyzer),
    viz_engine: VisualizationEngine = Depends(get_visualization_engine)
):
    """System health check endpoint."""
    try:
        health_data = HealthStatus(
            status="healthy",
            version="2.0.0",
            uptime="running",
            components={
                "universal_analyzer": "ready" if analyzer else "not_initialized",
                "visualization_engine": "ready" if viz_engine else "not_initialized",
                "supported_languages": str(len(analyzer.get_supported_languages())) if analyzer else "0"
            },
            metrics={
                "memory_usage": "N/A",
                "cpu_usage": "N/A",
                "cache_size": "N/A"
            }
        )
        
        return create_success_response(health_data, "System is healthy")
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Health check failed"
        )


@router.get("/info", response_model=APIResponse)
async def system_info(
    analyzer: UniversalAnalyzer = Depends(get_universal_analyzer),
    viz_engine: VisualizationEngine = Depends(get_visualization_engine)
):
    """Get detailed system information."""
    try:
        info_data = {
            "name": "AST Viewer Code Intelligence Platform",
            "version": "2.0.0",
            "description": "Enterprise-grade code intelligence platform with multi-language support",
            "capabilities": {
                "supported_languages": list(analyzer.get_supported_languages()) if analyzer else [],
                "visualization_types": list(viz_engine.get_available_visualizations()) if viz_engine else [],
                "analysis_features": [
                    "Multi-language parsing",
                    "Code intelligence",
                    "Dependency analysis",
                    "Impact analysis",
                    "Advanced visualizations",
                    "GitHub repository analysis"
                ]
            },
            "api": {
                "version": "v1",
                "documentation": "/docs",
                "endpoints": {
                    "analysis": "/api/v1/analysis/",
                    "visualization": "/api/v1/visualization/",
                    "intelligence": "/api/v1/intelligence/",
                    "projects": "/api/v1/projects/"
                }
            }
        }
        
        return create_success_response(info_data, "System information retrieved")
        
    except Exception as e:
        logger.error(f"System info failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve system information"
        )


# File Analysis Endpoints
@router.post("/analysis/file", response_model=APIResponse)
async def analyze_file(
    request: FileAnalysisRequest,
    analyzer: UniversalAnalyzer = Depends(get_universal_analyzer)
):
    """Analyze a single file."""
    try:
        file_path = Path(request.file_path)
        
        # Validate file exists
        if not file_path.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"File not found: {request.file_path}"
            )
        
        # Perform analysis
        start_time = time.time()
        result = analyzer.analyze_file(file_path)
        analysis_time = time.time() - start_time
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="File analysis failed or returned no results"
            )
        
        # Convert to API response format
        elements = []
        if request.include_elements:
            for node in result.nodes:
                elements.append(CodeElement(
                    id=node.id,
                    name=node.name,
                    type=ElementTypeEnum(node.type.value),
                    language=LanguageEnum(result.language.value),
                    source_location={
                        "file_path": node.source_location.file_path,
                        "line_number": node.source_location.line_number,
                        "column_number": node.source_location.column_number,
                        "end_line_number": node.source_location.end_line_number,
                        "end_column_number": node.source_location.end_column_number
                    },
                    cyclomatic_complexity=getattr(node, 'cyclomatic_complexity', None),
                    cognitive_complexity=getattr(node, 'cognitive_complexity', None)
                ))
        
        file_result = FileAnalysisResult(
            path=str(result.path),
            language=LanguageEnum(result.language.value),
            encoding=result.encoding,
            size_bytes=result.size_bytes,
            hash=result.hash,
            metrics={
                "total_lines": result.total_lines,
                "code_lines": result.code_lines,
                "comment_lines": result.comment_lines,
                "blank_lines": result.blank_lines,
                "complexity": result.complexity,
                "maintainability_index": result.maintainability_index
            },
            elements=elements,
            imports=result.imports,
            exports=result.exports
        )
        
        response_data = {
            "file": file_result,
            "analysis_time": analysis_time,
            "element_count": len(elements)
        }
        
        return create_success_response(response_data, f"File analyzed successfully in {analysis_time:.2f}s")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"File analysis failed for {request.file_path}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"File analysis failed: {str(e)}"
        )


@router.post("/analysis/directory", response_model=APIResponse)
async def analyze_directory(
    request: DirectoryAnalysisRequest,
    analyzer: UniversalAnalyzer = Depends(get_universal_analyzer),
    integrated_analyzer: IntegratedCodeAnalyzer = Depends(get_integrated_analyzer)
):
    """Analyze all files in a directory."""
    try:
        directory_path = Path(request.directory_path)
        
        # Validate directory exists
        if not directory_path.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Directory not found: {request.directory_path}"
            )
        
        if not directory_path.is_dir():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Path is not a directory: {request.directory_path}"
            )
        
        # Perform analysis
        start_time = time.time()
        results = analyzer.analyze_directory(directory_path)
        
        if not results:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="No files found to analyze in directory"
            )
        
        # Convert results
        files = []
        total_elements = 0
        
        for file_path, file_result in results.items():
            # Apply filters
            if request.file_extensions and not any(file_path.endswith(ext) for ext in request.file_extensions):
                continue
            
            if request.exclude_patterns and any(pattern in file_path for pattern in request.exclude_patterns):
                continue
            
            if request.max_files and len(files) >= request.max_files:
                break
            
            # Convert elements
            elements = []
            if request.include_metrics:
                for node in file_result.nodes:
                    elements.append(CodeElement(
                        id=node.id,
                        name=node.name,
                        type=ElementTypeEnum(node.type.value),
                        language=LanguageEnum(file_result.language.value),
                        source_location={
                            "file_path": node.source_location.file_path,
                            "line_number": node.source_location.line_number,
                            "column_number": node.source_location.column_number,
                            "end_line_number": node.source_location.end_line_number,
                            "end_column_number": node.source_location.end_column_number
                        },
                        cyclomatic_complexity=getattr(node, 'cyclomatic_complexity', None),
                        cognitive_complexity=getattr(node, 'cognitive_complexity', None)
                    ))
            
            files.append(FileAnalysisResult(
                path=file_path,
                language=LanguageEnum(file_result.language.value),
                encoding=file_result.encoding,
                size_bytes=file_result.size_bytes,
                hash=file_result.hash,
                metrics={
                    "total_lines": file_result.total_lines,
                    "code_lines": file_result.code_lines,
                    "comment_lines": file_result.comment_lines,
                    "blank_lines": file_result.blank_lines,
                    "complexity": file_result.complexity,
                    "maintainability_index": file_result.maintainability_index
                },
                elements=elements,
                imports=file_result.imports,
                exports=file_result.exports
            ))
            
            total_elements += len(elements)
        
        # Calculate directory metrics
        total_lines = sum(f.metrics["total_lines"] for f in files)
        total_code_lines = sum(f.metrics["code_lines"] for f in files)
        complexities = [f.metrics["complexity"] for f in files if f.metrics["complexity"] and f.metrics["complexity"] > 0]
        
        metrics = ProjectMetrics(
            total_files=len(files),
            total_lines=total_lines,
            total_code_lines=total_code_lines,
            total_elements=total_elements,
            total_functions=sum(len([e for e in f.elements if e.type == ElementTypeEnum.FUNCTION]) for f in files),
            total_classes=sum(len([e for e in f.elements if e.type == ElementTypeEnum.CLASS]) for f in files),
            total_imports=sum(len(f.imports) for f in files),
            average_complexity=sum(complexities) / len(complexities) if complexities else 0,
            max_complexity=max(complexities) if complexities else 0
        )
        
        # Language distribution
        language_dist = {}
        for file in files:
            lang = file.language.value
            language_dist[lang] = language_dist.get(lang, 0) + 1
        
        analysis_time = time.time() - start_time
        
        # Enhanced intelligence analysis if requested
        intelligence = None
        if request.include_intelligence:
            try:
                intelligence_result = integrated_analyzer.analyze_project(directory_path)
                intelligence = IntelligenceMetrics(
                    total_symbols=intelligence_result.get('intelligence', {}).get('total_symbols', 0),
                    total_relationships=intelligence_result.get('intelligence', {}).get('total_relationships', 0),
                    total_references=intelligence_result.get('intelligence', {}).get('total_references', 0),
                    call_graph_nodes=intelligence_result.get('intelligence', {}).get('call_graph_nodes', 0),
                    dependency_cycles=0,  # Would be calculated from dependency graph
                    graph_density=None
                )
            except Exception as e:
                logger.warning(f"Intelligence analysis failed: {e}")
        
        result = ProjectAnalysisResult(
            project_name=directory_path.name,
            project_path=str(directory_path),
            files=files,
            metrics=metrics,
            intelligence=intelligence,
            languages=language_dist,
            dependencies={},  # Would be extracted from intelligence analysis
            analysis_time=analysis_time
        )
        
        return create_success_response(result, f"Directory analyzed successfully in {analysis_time:.2f}s")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Directory analysis failed for {request.directory_path}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Directory analysis failed: {str(e)}"
        )


@router.post("/analysis/project", response_model=APIResponse)
async def analyze_project(
    request: ProjectAnalysisRequest,
    background_tasks: BackgroundTasks,
    integrated_analyzer: IntegratedCodeAnalyzer = Depends(get_integrated_analyzer)
):
    """Comprehensive project analysis - supports local directories and GitHub repositories."""
    try:
        # Validate input
        if not request.directory_path and not request.github_url:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Either directory_path or github_url must be provided"
            )
        
        if request.directory_path and request.github_url:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Provide either directory_path or github_url, not both"
            )
        
        cloned_path = None
        
        # Handle GitHub repository
        if request.github_url:
            logger.info(f"Analyzing GitHub repository: {request.github_url}")
            
            # Validate GitHub URL
            if not validate_github_url(request.github_url):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid GitHub URL: {request.github_url}"
                )
            
            try:
                # Clone repository
                cloned_path = await asyncio.get_event_loop().run_in_executor(
                    None,
                    clone_github_repository,
                    request.github_url,
                    request.branch,
                    request.shallow_clone,
                    request.clone_depth
                )
                
                project_path = Path(cloned_path)
                project_name = request.project_name or project_path.name
                
                # Schedule cleanup
                background_tasks.add_task(cleanup_repository, cloned_path)
                
            except GitRepositoryError as e:
                logger.error(f"Failed to clone repository {request.github_url}: {e}")
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=f"Failed to clone repository: {str(e)}"
                )
        else:
            # Handle local directory
            project_path = Path(request.directory_path)
            project_name = request.project_name or project_path.name
            
            if not project_path.exists():
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Directory not found: {request.directory_path}"
                )
            
            if not project_path.is_dir():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Path is not a directory: {request.directory_path}"
                )
        
        # Perform comprehensive analysis
        start_time = time.time()
        logger.info(f"Starting comprehensive analysis of: {project_path}")
        
        analysis_result = integrated_analyzer.analyze_project(project_path, project_name)
        analysis_time = time.time() - start_time
        
        # Convert to API response format
        files = []
        for file_path, file_data in analysis_result['files'].items():
            # Apply filters
            if request.file_extensions:
                if not any(file_path.endswith(ext) for ext in request.file_extensions):
                    continue
            
            if request.exclude_patterns:
                if any(pattern in file_path for pattern in request.exclude_patterns):
                    continue
            
            if request.max_files and len(files) >= request.max_files:
                break
            
            # Convert file data
            file_result = FileAnalysisResult(
                path=file_path,
                language=LanguageEnum(file_data.get('language', 'UNKNOWN')),
                encoding=file_data.get('encoding', 'utf-8'),
                size_bytes=file_data.get('size_bytes', 0),
                hash=file_data.get('hash', ''),
                metrics={
                    "total_lines": file_data.get('total_lines', 0),
                    "code_lines": file_data.get('code_lines', 0),
                    "comment_lines": file_data.get('comment_lines', 0),
                    "blank_lines": file_data.get('blank_lines', 0),
                    "complexity": file_data.get('complexity', 0),
                    "maintainability_index": file_data.get('maintainability_index', 0)
                },
                elements=[],  # Would be populated from node data
                imports=file_data.get('imports', []),
                exports=file_data.get('exports', [])
            )
            files.append(file_result)
        
        # Extract metrics
        metrics_data = analysis_result.get('metrics', {})
        metrics = ProjectMetrics(
            total_files=metrics_data.get('total_files', len(files)),
            total_lines=metrics_data.get('total_lines', 0),
            total_code_lines=metrics_data.get('total_code_lines', 0),
            total_elements=metrics_data.get('total_nodes', 0),
            total_functions=metrics_data.get('total_functions', 0),
            total_classes=metrics_data.get('total_classes', 0),
            total_imports=metrics_data.get('total_imports', 0),
            average_complexity=metrics_data.get('average_complexity', 0),
            max_complexity=metrics_data.get('max_complexity', 0),
            maintainability_score=metrics_data.get('maintainability_score', 75.0),
            technical_debt_ratio=metrics_data.get('technical_debt_ratio', 0.15)
        )
        
        # Extract intelligence data
        intelligence_data = analysis_result.get('intelligence', {})
        intelligence = IntelligenceMetrics(
            total_symbols=intelligence_data.get('total_symbols', 0),
            total_relationships=intelligence_data.get('total_relationships', 0),
            total_references=intelligence_data.get('total_references', 0),
            call_graph_nodes=intelligence_data.get('call_graph_nodes', 0),
            dependency_cycles=0,  # Would be calculated
            graph_density=None
        ) if request.include_intelligence else None
        
        result = ProjectAnalysisResult(
            project_name=project_name,
            project_path=str(project_path),
            files=files,
            metrics=metrics,
            intelligence=intelligence,
            languages=analysis_result.get('languages', {}),
            dependencies=analysis_result.get('dependencies', {}),
            analysis_time=analysis_time
        )
        
        logger.info(f"Project analysis completed in {analysis_time:.2f}s - {len(files)} files")
        
        return create_success_response(
            result, 
            f"Project '{project_name}' analyzed successfully in {analysis_time:.2f}s"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Project analysis failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Project analysis failed: {str(e)}"
        )


# Intelligence and Symbol Endpoints
@router.post("/intelligence/symbols/search", response_model=APIResponse)
async def search_symbols(
    request: SymbolSearchRequest,
    analyzer: IntegratedCodeAnalyzer = Depends(get_integrated_analyzer)
):
    """Search for symbols across the codebase."""
    try:
        # This would implement comprehensive symbol search
        # For now, return a placeholder response
        symbols = []
        
        # In a real implementation, this would:
        # 1. Search through cached intelligence data
        # 2. Apply filters (element_types, languages, project_id)
        # 3. Rank results by relevance
        # 4. Include relationships if requested
        
        response_data = {
            "query": request.query,
            "symbols": symbols,
            "total_results": len(symbols),
            "filters_applied": {
                "element_types": request.element_types,
                "languages": request.languages,
                "project_id": request.project_id
            }
        }
        
        return create_success_response(response_data, f"Found {len(symbols)} symbols matching query")
        
    except Exception as e:
        logger.error(f"Symbol search failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Symbol search failed: {str(e)}"
        )


@router.get("/intelligence/symbols/{symbol_id}", response_model=APIResponse)
async def get_symbol(
    symbol_id: str,
    include_relationships: bool = Query(default=False, description="Include symbol relationships"),
    analyzer: IntegratedCodeAnalyzer = Depends(get_integrated_analyzer)
):
    """Get detailed information about a specific symbol."""
    try:
        # This would fetch symbol details from the intelligence cache
        # For now, return a placeholder response
        
        symbol_data = {
            "id": symbol_id,
            "name": "placeholder_symbol",
            "type": "FUNCTION",
            "language": "PYTHON",
            "source_location": {
                "file_path": "/placeholder/file.py",
                "line_number": 1,
                "column_number": 0
            },
            "relationships": [] if include_relationships else None,
            "metadata": {}
        }
        
        return create_success_response(symbol_data, "Symbol details retrieved")
        
    except Exception as e:
        logger.error(f"Symbol lookup failed for {symbol_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Symbol lookup failed: {str(e)}"
        )


@router.post("/intelligence/impact", response_model=APIResponse)
async def analyze_impact(
    request: ImpactAnalysisRequest,
    analyzer: IntegratedCodeAnalyzer = Depends(get_integrated_analyzer),
    viz_engine: VisualizationEngine = Depends(get_visualization_engine)
):
    """Analyze the impact of changes to a specific symbol."""
    try:
        # Perform impact analysis
        start_time = time.time()
        
        # This would use the integrated analyzer's impact analysis
        # For now, return a placeholder response
        impact_result = ImpactAnalysisResult(
            symbol_id=request.symbol_id,
            impact_score=0.0,
            affected_files=[],
            affected_symbols=[],
            dependency_chain=[],
            risk_level="LOW",
            recommendations=[]
        )
        
        # Generate visualization if requested
        if request.include_visualization:
            try:
                # This would generate an impact visualization
                visualization = VisualizationResult(
                    visualization_id=str(uuid.uuid4()),
                    visualization_type=VisualizationTypeEnum.IMPACT_VISUALIZATION,
                    format=ExportFormatEnum.HTML,
                    content="<div>Impact visualization placeholder</div>",
                    metadata={"symbol_id": request.symbol_id},
                    generation_time=0.1
                )
                impact_result.visualization = visualization
            except Exception as e:
                logger.warning(f"Impact visualization failed: {e}")
        
        analysis_time = time.time() - start_time
        
        response_data = {
            "impact_analysis": impact_result,
            "analysis_time": analysis_time
        }
        
        return create_success_response(
            response_data, 
            f"Impact analysis completed for symbol {request.symbol_id}"
        )
        
    except Exception as e:
        logger.error(f"Impact analysis failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Impact analysis failed: {str(e)}"
        )


# Add the router to be imported by main.py
__all__ = ["router"]
