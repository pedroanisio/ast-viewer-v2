"""GraphQL input types for structured operations."""

from typing import Optional, List
import strawberry


@strawberry.input
class FileAnalysisInput:
    """Input for single file analysis."""
    file_path: str
    include_intelligence: bool = False
    include_relationships: bool = False
    include_references: bool = False


@strawberry.input
class DirectoryAnalysisInput:
    """Input for directory analysis."""
    directory_path: str
    recursive: bool = True
    include_intelligence: bool = False
    file_extensions: Optional[List[str]] = None
    exclude_patterns: Optional[List[str]] = None
    max_files: Optional[int] = None


@strawberry.input
class ProjectAnalysisInput:
    """Input for comprehensive project analysis."""
    directory_path: str
    project_name: Optional[str] = None
    include_intelligence: bool = True
    include_relationships: bool = True
    include_references: bool = True
    include_call_graph: bool = True
    include_dependency_graph: bool = True
    recursive: bool = True
    file_extensions: Optional[List[str]] = None
    exclude_patterns: Optional[List[str]] = None
    max_files: Optional[int] = None


@strawberry.input
class SymbolSearchInput:
    """Input for symbol search operations."""
    query: str
    symbol_types: Optional[List[str]] = None
    languages: Optional[List[str]] = None
    case_sensitive: bool = False
    exact_match: bool = False
    limit: Optional[int] = 100
    offset: Optional[int] = 0


@strawberry.input
class RelationshipFilterInput:
    """Input for filtering relationships."""
    source_id: Optional[str] = None
    target_id: Optional[str] = None
    relationship_types: Optional[List[str]] = None
    limit: Optional[int] = None


@strawberry.input
class VisualizationInput:
    """Input for generating code visualizations."""
    project_id: str
    visualization_type: str  # Could be enum: "dependency_graph", "call_graph", "complexity_heatmap", etc.
    format: str = "svg"  # "svg", "png", "html", "json"
    width: Optional[int] = None
    height: Optional[int] = None
    theme: Optional[str] = "default"
    include_labels: bool = True
    max_nodes: Optional[int] = 1000


@strawberry.input
class ImpactAnalysisInput:
    """Input for analyzing impact of code changes."""
    symbol_id: str
    change_type: str  # "modify", "delete", "rename"
    max_depth: int = 5
    include_transitive: bool = True


@strawberry.input
class CodeMetricsInput:
    """Input for code metrics analysis."""
    target_path: str
    metric_types: Optional[List[str]] = None  # "complexity", "maintainability", "coverage", etc.
    aggregation_level: str = "file"  # "file", "class", "function", "project"
    include_history: bool = False


@strawberry.input
class RefactoringAnalysisInput:
    """Input for refactoring opportunity analysis."""
    directory_path: str
    analysis_types: Optional[List[str]] = None  # "duplicate_code", "long_methods", "large_classes", etc.
    severity_threshold: str = "medium"  # "low", "medium", "high"
    max_results: Optional[int] = 100


@strawberry.input
class ArchitectureAnalysisInput:
    """Input for architecture analysis."""
    project_path: str
    analysis_depth: int = 3
    include_external_dependencies: bool = False
    grouping_strategy: str = "package"  # "package", "layer", "component"
