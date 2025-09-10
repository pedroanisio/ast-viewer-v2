"""GraphQL result types for AST Viewer."""

from typing import List, Optional
import strawberry


@strawberry.type
class SourceLocationType:
    """GraphQL type for source code location."""
    file_path: str
    line_number: int
    column_number: int
    end_line_number: Optional[int] = None
    end_column_number: Optional[int] = None


@strawberry.type
class UniversalNodeType:
    """GraphQL type for universal code node."""
    id: str
    name: str
    type: str
    source_location: SourceLocationType
    children: List["UniversalNodeType"] = strawberry.field(default_factory=list)
    
    # Complexity metrics
    cyclomatic_complexity: Optional[int] = None
    cognitive_complexity: Optional[int] = None
    halstead_difficulty: Optional[float] = None
    maintainability_index: Optional[float] = None
    
    # Additional metadata
    docstring: Optional[str] = None
    decorators: List[str] = strawberry.field(default_factory=list)
    parameters: List[str] = strawberry.field(default_factory=list)
    return_type: Optional[str] = None


@strawberry.type
class UniversalFileType:
    """GraphQL type for universal file representation."""
    path: str
    language: str
    size: int
    lines_of_code: int
    ast_nodes: List[UniversalNodeType] = strawberry.field(default_factory=list)
    
    # File-level metrics
    cyclomatic_complexity: Optional[int] = None
    cognitive_complexity: Optional[int] = None
    maintainability_index: Optional[float] = None
    
    # Additional metadata
    encoding: Optional[str] = None
    last_modified: Optional[str] = None
    imports: List[str] = strawberry.field(default_factory=list)


@strawberry.type
class RelationshipType:
    """GraphQL type for symbol relationships."""
    id: str
    from_symbol_id: str
    to_symbol_id: str
    type: str
    source_location: Optional[SourceLocationType] = None


@strawberry.type
class ReferenceType:
    """GraphQL type for symbol references."""
    id: str
    symbol_id: str
    source_location: SourceLocationType
    context: Optional[str] = None


@strawberry.type
class ProjectMetrics:
    """GraphQL type for enhanced project-level metrics."""
    # Basic metrics
    total_files: int
    total_lines: int
    total_functions: int
    total_classes: int
    
    # Advanced metrics
    average_complexity: float
    max_complexity: int
    maintainability_score: float
    technical_debt_ratio: float
    
    # Language breakdown
    language_distribution: List[str] = strawberry.field(default_factory=list)


@strawberry.type
class IntelligenceData:
    """GraphQL type for code intelligence information."""
    total_symbols: int
    total_relationships: int
    total_references: int


@strawberry.type
class AnalysisResult:
    """GraphQL type for complete analysis result."""
    files: List[UniversalFileType]
    project_metrics: ProjectMetrics
    intelligence_data: IntelligenceData
    
    # Analysis metadata
    analysis_time: float
    timestamp: str
    analyzer_version: str


