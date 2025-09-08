"""Pydantic models for REST API request/response schemas."""

from typing import Dict, List, Optional, Union, Any
from pathlib import Path
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field, ConfigDict, field_validator


class LanguageEnum(str, Enum):
    """Supported programming languages."""
    PYTHON = "PYTHON"
    JAVASCRIPT = "JAVASCRIPT"
    TYPESCRIPT = "TYPESCRIPT"
    GO = "GO"
    RUST = "RUST"
    JAVA = "JAVA"
    CPP = "CPP"
    CSHARP = "CSHARP"
    UNKNOWN = "UNKNOWN"


class ElementTypeEnum(str, Enum):
    """Types of code elements."""
    FUNCTION = "FUNCTION"
    CLASS = "CLASS"
    METHOD = "METHOD"
    VARIABLE = "VARIABLE"
    CONSTANT = "CONSTANT"
    INTERFACE = "INTERFACE"
    ENUM = "ENUM"
    MODULE = "MODULE"
    IMPORT = "IMPORT"
    EXPORT = "EXPORT"
    NAMESPACE = "NAMESPACE"
    TYPE = "TYPE"
    DECORATOR = "DECORATOR"
    ANNOTATION = "ANNOTATION"
    COMMENT = "COMMENT"
    UNKNOWN = "UNKNOWN"


class VisualizationTypeEnum(str, Enum):
    """Types of visualizations available."""
    DEPENDENCY_GRAPH = "dependency_graph"
    CALL_GRAPH = "call_graph"
    REFERENCE_NETWORK = "reference_network"
    INHERITANCE_TREE = "inheritance_tree"
    COMPLEXITY_HEATMAP = "complexity_heatmap"
    FILE_INTERACTION_MATRIX = "file_interaction_matrix"
    COUPLING_MATRIX = "coupling_matrix"
    ARCHITECTURE_MAP = "architecture_map"
    MODULE_OVERVIEW = "module_overview"
    LAYER_DIAGRAM = "layer_diagram"
    IMPACT_VISUALIZATION = "impact_visualization"
    CHANGE_PROPAGATION = "change_propagation"
    HOTSPOT_ANALYSIS = "hotspot_analysis"
    EVOLUTION_TIMELINE = "evolution_timeline"
    GROWTH_ANALYSIS = "growth_analysis"
    PROJECT_DASHBOARD = "project_dashboard"
    QUALITY_DASHBOARD = "quality_dashboard"


class ExportFormatEnum(str, Enum):
    """Supported export formats."""
    HTML = "html"
    PNG = "png"
    SVG = "svg"
    PDF = "pdf"
    JSON = "json"


# Base models for common structures
class SourceLocation(BaseModel):
    """Source code location information."""
    model_config = ConfigDict(str_strip_whitespace=True)
    
    file_path: str = Field(..., description="Path to the source file")
    line_number: int = Field(..., ge=1, description="Line number (1-based)")
    column_number: int = Field(..., ge=0, description="Column number (0-based)")
    end_line_number: Optional[int] = Field(None, ge=1, description="End line number (1-based)")
    end_column_number: Optional[int] = Field(None, ge=0, description="End column number (0-based)")


class CodeElement(BaseModel):
    """Represents a code element (function, class, variable, etc.)."""
    model_config = ConfigDict(str_strip_whitespace=True)
    
    id: str = Field(..., description="Unique identifier for the element")
    name: Optional[str] = Field(None, description="Name of the element")
    type: ElementTypeEnum = Field(..., description="Type of the element")
    language: LanguageEnum = Field(..., description="Programming language")
    source_location: SourceLocation = Field(..., description="Location in source code")
    cyclomatic_complexity: Optional[int] = Field(None, ge=0, description="Cyclomatic complexity")
    cognitive_complexity: Optional[int] = Field(None, ge=0, description="Cognitive complexity")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional metadata")


class FileAnalysisMetrics(BaseModel):
    """Metrics for a single file analysis."""
    model_config = ConfigDict(str_strip_whitespace=True)
    
    total_lines: int = Field(..., ge=0, description="Total lines in file")
    code_lines: int = Field(..., ge=0, description="Lines of code")
    comment_lines: int = Field(..., ge=0, description="Lines of comments")
    blank_lines: int = Field(..., ge=0, description="Blank lines")
    complexity: Optional[float] = Field(None, ge=0, description="Overall file complexity")
    maintainability_index: Optional[float] = Field(None, ge=0, le=100, description="Maintainability index")


class FileAnalysisResult(BaseModel):
    """Result of analyzing a single file."""
    model_config = ConfigDict(str_strip_whitespace=True)
    
    path: str = Field(..., description="File path")
    language: LanguageEnum = Field(..., description="Detected language")
    encoding: str = Field(default="utf-8", description="File encoding")
    size_bytes: int = Field(..., ge=0, description="File size in bytes")
    hash: Optional[str] = Field(None, description="File content hash")
    metrics: FileAnalysisMetrics = Field(..., description="File metrics")
    elements: List[CodeElement] = Field(default_factory=list, description="Code elements found")
    imports: List[str] = Field(default_factory=list, description="Import statements")
    exports: List[str] = Field(default_factory=list, description="Export statements")
    created_at: datetime = Field(default_factory=datetime.now, description="Analysis timestamp")


class ProjectMetrics(BaseModel):
    """Comprehensive project metrics."""
    model_config = ConfigDict(str_strip_whitespace=True)
    
    total_files: int = Field(..., ge=0, description="Total number of files")
    total_lines: int = Field(..., ge=0, description="Total lines of code")
    total_code_lines: int = Field(..., ge=0, description="Total non-empty lines")
    total_elements: int = Field(..., ge=0, description="Total code elements")
    total_functions: int = Field(..., ge=0, description="Total functions")
    total_classes: int = Field(..., ge=0, description="Total classes")
    total_imports: int = Field(..., ge=0, description="Total import statements")
    average_complexity: float = Field(..., ge=0, description="Average complexity")
    max_complexity: float = Field(..., ge=0, description="Maximum complexity")
    maintainability_score: Optional[float] = Field(None, ge=0, le=100, description="Overall maintainability")
    technical_debt_ratio: Optional[float] = Field(None, ge=0, le=1, description="Technical debt ratio")


class IntelligenceMetrics(BaseModel):
    """Code intelligence analysis metrics."""
    model_config = ConfigDict(str_strip_whitespace=True)
    
    total_symbols: int = Field(..., ge=0, description="Total symbols found")
    total_relationships: int = Field(..., ge=0, description="Total relationships")
    total_references: int = Field(..., ge=0, description="Total references")
    call_graph_nodes: int = Field(..., ge=0, description="Call graph nodes")
    dependency_cycles: int = Field(..., ge=0, description="Number of dependency cycles")
    graph_density: Optional[float] = Field(None, ge=0, le=1, description="Graph density")


class ProjectAnalysisResult(BaseModel):
    """Result of comprehensive project analysis."""
    model_config = ConfigDict(str_strip_whitespace=True)
    
    project_name: str = Field(..., description="Project name")
    project_path: str = Field(..., description="Project path")
    files: List[FileAnalysisResult] = Field(default_factory=list, description="File analysis results")
    metrics: ProjectMetrics = Field(..., description="Project metrics")
    intelligence: Optional[IntelligenceMetrics] = Field(None, description="Intelligence analysis")
    languages: Dict[str, int] = Field(default_factory=dict, description="Language distribution")
    dependencies: Dict[str, List[str]] = Field(default_factory=dict, description="File dependencies")
    analysis_time: float = Field(..., ge=0, description="Analysis time in seconds")
    analyzer_version: str = Field(default="2.0.0", description="Analyzer version")
    created_at: datetime = Field(default_factory=datetime.now, description="Analysis timestamp")


# Request models
class FileAnalysisRequest(BaseModel):
    """Request to analyze a single file."""
    model_config = ConfigDict(str_strip_whitespace=True)
    
    file_path: str = Field(..., description="Path to the file to analyze")
    include_metrics: bool = Field(default=True, description="Include detailed metrics")
    include_elements: bool = Field(default=True, description="Include code elements")
    
    @field_validator('file_path')
    @classmethod
    def validate_file_path(cls, v: str) -> str:
        """Validate file path."""
        if not v or not v.strip():
            raise ValueError("File path cannot be empty")
        return v.strip()


class DirectoryAnalysisRequest(BaseModel):
    """Request to analyze a directory."""
    model_config = ConfigDict(str_strip_whitespace=True)
    
    directory_path: str = Field(..., description="Path to the directory to analyze")
    file_extensions: Optional[List[str]] = Field(None, description="File extensions to include")
    exclude_patterns: Optional[List[str]] = Field(None, description="Patterns to exclude")
    max_files: Optional[int] = Field(None, ge=1, description="Maximum number of files to analyze")
    include_metrics: bool = Field(default=True, description="Include detailed metrics")
    include_intelligence: bool = Field(default=False, description="Include intelligence analysis")
    
    @field_validator('directory_path')
    @classmethod
    def validate_directory_path(cls, v: str) -> str:
        """Validate directory path."""
        if not v or not v.strip():
            raise ValueError("Directory path cannot be empty")
        return v.strip()


class ProjectAnalysisRequest(BaseModel):
    """Request for comprehensive project analysis."""
    model_config = ConfigDict(str_strip_whitespace=True)
    
    # Source specification (either local directory or GitHub repo)
    directory_path: Optional[str] = Field(None, description="Local directory path")
    github_url: Optional[str] = Field(None, description="GitHub repository URL")
    branch: Optional[str] = Field(default="main", description="Git branch to analyze")
    
    # Analysis options
    project_name: Optional[str] = Field(None, description="Project name (auto-detected if not provided)")
    file_extensions: Optional[List[str]] = Field(None, description="File extensions to include")
    exclude_patterns: Optional[List[str]] = Field(None, description="Patterns to exclude")
    max_files: Optional[int] = Field(None, ge=1, description="Maximum number of files to analyze")
    
    # Feature flags
    include_intelligence: bool = Field(default=True, description="Include intelligence analysis")
    include_visualizations: bool = Field(default=False, description="Generate visualizations")
    include_dependencies: bool = Field(default=True, description="Analyze dependencies")
    
    # GitHub-specific options
    shallow_clone: bool = Field(default=True, description="Use shallow clone for GitHub repos")
    clone_depth: int = Field(default=1, ge=1, description="Clone depth for shallow clones")
    
    @field_validator('github_url')
    @classmethod
    def validate_github_url(cls, v: Optional[str]) -> Optional[str]:
        """Validate GitHub URL format."""
        if v and not v.startswith(('https://github.com/', 'git@github.com:')):
            raise ValueError("Invalid GitHub URL format")
        return v


class SymbolSearchRequest(BaseModel):
    """Request to search for symbols."""
    model_config = ConfigDict(str_strip_whitespace=True)
    
    query: str = Field(..., min_length=1, description="Search query")
    element_types: Optional[List[ElementTypeEnum]] = Field(None, description="Element types to search")
    languages: Optional[List[LanguageEnum]] = Field(None, description="Languages to search")
    project_id: Optional[str] = Field(None, description="Project ID to search within")
    limit: int = Field(default=50, ge=1, le=1000, description="Maximum results to return")
    include_relationships: bool = Field(default=False, description="Include symbol relationships")


class VisualizationRequest(BaseModel):
    """Request to generate a visualization."""
    model_config = ConfigDict(str_strip_whitespace=True)
    
    project_id: str = Field(..., description="Project identifier")
    visualization_type: VisualizationTypeEnum = Field(..., description="Type of visualization")
    
    # Filtering options
    file_filter: Optional[List[str]] = Field(None, description="Filter by file paths")
    element_filter: Optional[List[ElementTypeEnum]] = Field(None, description="Filter by element types")
    complexity_threshold: Optional[int] = Field(None, ge=1, description="Minimum complexity threshold")
    
    # Layout options
    width: int = Field(default=1200, ge=400, le=4000, description="Visualization width")
    height: int = Field(default=800, ge=300, le=3000, description="Visualization height")
    interactive: bool = Field(default=True, description="Generate interactive visualization")
    
    # Export options
    export_format: ExportFormatEnum = Field(default=ExportFormatEnum.HTML, description="Export format")
    include_metadata: bool = Field(default=True, description="Include metadata in export")


class ImpactAnalysisRequest(BaseModel):
    """Request for impact analysis."""
    model_config = ConfigDict(str_strip_whitespace=True)
    
    project_id: str = Field(..., description="Project identifier")
    symbol_id: str = Field(..., description="Symbol to analyze impact for")
    max_depth: int = Field(default=5, ge=1, le=10, description="Maximum analysis depth")
    include_visualization: bool = Field(default=False, description="Include impact visualization")


# Response models
class APIResponse(BaseModel):
    """Standard API response wrapper."""
    model_config = ConfigDict(str_strip_whitespace=True)
    
    success: bool = Field(..., description="Whether the request was successful")
    message: str = Field(..., description="Response message")
    data: Optional[Any] = Field(None, description="Response data")
    errors: Optional[List[str]] = Field(None, description="Error messages if any")
    timestamp: datetime = Field(default_factory=datetime.now, description="Response timestamp")
    request_id: Optional[str] = Field(None, description="Request tracking ID")


class ErrorResponse(BaseModel):
    """Error response model."""
    model_config = ConfigDict(str_strip_whitespace=True)
    
    success: bool = Field(default=False, description="Success flag (always false for errors)")
    error_type: str = Field(..., description="Type of error")
    message: str = Field(..., description="Error message")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")
    timestamp: datetime = Field(default_factory=datetime.now, description="Error timestamp")
    request_id: Optional[str] = Field(None, description="Request tracking ID")


class VisualizationResult(BaseModel):
    """Visualization generation result."""
    model_config = ConfigDict(str_strip_whitespace=True)
    
    visualization_id: str = Field(..., description="Unique visualization identifier")
    visualization_type: VisualizationTypeEnum = Field(..., description="Type of visualization")
    format: ExportFormatEnum = Field(..., description="Export format")
    content: Optional[str] = Field(None, description="Visualization content (for HTML/JSON)")
    file_path: Optional[str] = Field(None, description="Path to exported file")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Visualization metadata")
    generation_time: float = Field(..., ge=0, description="Generation time in seconds")
    created_at: datetime = Field(default_factory=datetime.now, description="Generation timestamp")


class ImpactAnalysisResult(BaseModel):
    """Impact analysis result."""
    model_config = ConfigDict(str_strip_whitespace=True)
    
    symbol_id: str = Field(..., description="Analyzed symbol ID")
    impact_score: float = Field(..., ge=0, description="Overall impact score")
    affected_files: List[str] = Field(default_factory=list, description="Files that would be affected")
    affected_symbols: List[str] = Field(default_factory=list, description="Symbols that would be affected")
    dependency_chain: List[str] = Field(default_factory=list, description="Dependency chain")
    risk_level: str = Field(..., description="Risk level (LOW, MEDIUM, HIGH, CRITICAL)")
    recommendations: List[str] = Field(default_factory=list, description="Recommended actions")
    visualization: Optional[VisualizationResult] = Field(None, description="Impact visualization")


class HealthStatus(BaseModel):
    """System health status."""
    model_config = ConfigDict(str_strip_whitespace=True)
    
    status: str = Field(..., description="Overall status")
    version: str = Field(..., description="System version")
    uptime: str = Field(..., description="System uptime")
    components: Dict[str, str] = Field(default_factory=dict, description="Component status")
    metrics: Dict[str, Any] = Field(default_factory=dict, description="System metrics")
    timestamp: datetime = Field(default_factory=datetime.now, description="Status timestamp")


# Pagination models
class PaginationMeta(BaseModel):
    """Pagination metadata."""
    model_config = ConfigDict(str_strip_whitespace=True)
    
    page: int = Field(..., ge=1, description="Current page number")
    per_page: int = Field(..., ge=1, le=1000, description="Items per page")
    total: int = Field(..., ge=0, description="Total number of items")
    pages: int = Field(..., ge=0, description="Total number of pages")
    has_next: bool = Field(..., description="Has next page")
    has_prev: bool = Field(..., description="Has previous page")


class PaginatedResponse(BaseModel):
    """Paginated API response."""
    model_config = ConfigDict(str_strip_whitespace=True)
    
    success: bool = Field(default=True, description="Success flag")
    data: List[Any] = Field(default_factory=list, description="Response data")
    pagination: PaginationMeta = Field(..., description="Pagination metadata")
    timestamp: datetime = Field(default_factory=datetime.now, description="Response timestamp")
