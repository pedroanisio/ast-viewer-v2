"""GraphQL schema for AST Viewer using Strawberry GraphQL."""

from typing import List, Optional
from enum import Enum
import strawberry
from pathlib import Path

from ..models.universal import (
    ElementType, Language, AccessLevel, RelationType,
    Relationship, Reference, DependencyGraph, CallGraphNode
)
from ..analyzers.universal import UniversalAnalyzer
from ..analyzers.integrated import IntegratedCodeAnalyzer


@strawberry.enum
class ElementTypeEnum(Enum):
    """GraphQL enum for code element types."""
    PROJECT = "PROJECT"
    PACKAGE = "PACKAGE"
    MODULE = "MODULE"
    FILE = "FILE"
    CLASS = "CLASS"
    INTERFACE = "INTERFACE"
    TRAIT = "TRAIT"
    ENUM = "ENUM"
    STRUCT = "STRUCT"
    FUNCTION = "FUNCTION"
    METHOD = "METHOD"
    CONSTRUCTOR = "CONSTRUCTOR"
    DESTRUCTOR = "DESTRUCTOR"
    LAMBDA = "LAMBDA"
    GENERATOR = "GENERATOR"
    VARIABLE = "VARIABLE"
    CONSTANT = "CONSTANT"
    PARAMETER = "PARAMETER"
    FIELD = "FIELD"
    PROPERTY = "PROPERTY"
    CONDITIONAL = "CONDITIONAL"
    LOOP = "LOOP"
    EXCEPTION = "EXCEPTION"
    IMPORT = "IMPORT"
    EXPORT = "EXPORT"
    INCLUDE = "INCLUDE"
    COMMENT = "COMMENT"
    DOCSTRING = "DOCSTRING"
    ANNOTATION = "ANNOTATION"


@strawberry.enum
class LanguageEnum(Enum):
    """GraphQL enum for programming languages."""
    PYTHON = "python"
    JAVASCRIPT = "javascript"
    TYPESCRIPT = "typescript"
    GO = "go"
    RUST = "rust"
    C = "c"
    CPP = "cpp"
    JAVA = "java"
    CSHARP = "csharp"
    RUBY = "ruby"
    PHP = "php"
    SWIFT = "swift"
    KOTLIN = "kotlin"
    SCALA = "scala"
    HTML = "html"
    CSS = "css"
    SQL = "sql"
    UNKNOWN = "unknown"


@strawberry.enum
class AccessLevelEnum(Enum):
    """GraphQL enum for access levels."""
    PUBLIC = "public"
    PRIVATE = "private"
    PROTECTED = "protected"
    INTERNAL = "internal"
    PACKAGE = "package"
    FILE = "file"


@strawberry.enum
class RelationTypeEnum(Enum):
    """GraphQL enum for relationship types."""
    EXTENDS = "extends"
    IMPLEMENTS = "implements"
    CALLS = "calls"
    USES = "uses"
    REFERENCES = "references"
    INSTANTIATES = "instantiates"
    IMPORTS = "imports"
    EXPORTS = "exports"
    OVERRIDES = "overrides"
    OVERRIDDEN_BY = "overridden_by"
    RETURNS = "returns"
    ACCEPTS = "accepts"
    THROWS = "throws"
    DECORATES = "decorates"
    ANNOTATES = "annotates"
    CONTAINS = "contains"
    CONTAINED_IN = "contained_in"


@strawberry.type
class SourceLocationType:
    """GraphQL type for source code location."""
    file_path: str
    start_line: int
    end_line: int
    start_column: int
    end_column: int
    offset: Optional[int] = None
    length: Optional[int] = None


@strawberry.type
class UniversalNodeType:
    """GraphQL type for universal code node."""
    id: str
    type: ElementTypeEnum
    name: Optional[str]
    language: LanguageEnum
    location: SourceLocationType
    parent_id: Optional[str] = None
    children_ids: List[str] = strawberry.field(default_factory=list)
    access_level: Optional[AccessLevelEnum] = None
    is_static: bool = False
    is_async: bool = False
    is_abstract: bool = False
    is_final: bool = False
    is_const: bool = False
    data_type: Optional[str] = None
    return_type: Optional[str] = None
    extends: Optional[str] = None
    complexity: float = 1.0
    lines_of_code: int = 0
    lines_of_comments: int = 0
    documentation: Optional[str] = None


@strawberry.type
class UniversalFileType:
    """GraphQL type for universal file representation."""
    path: str
    language: LanguageEnum
    encoding: str
    size_bytes: int
    hash: str
    total_lines: int
    code_lines: int
    comment_lines: int
    blank_lines: int
    nodes: List[UniversalNodeType] = strawberry.field(default_factory=list)
    imports: List[str] = strawberry.field(default_factory=list)
    exports: List[str] = strawberry.field(default_factory=list)
    complexity: float = 1.0
    maintainability_index: Optional[float] = None


@strawberry.type
class RelationshipType:
    """GraphQL type for symbol relationships."""
    id: str
    source_id: str
    target_id: str
    type: RelationTypeEnum
    confidence: float = 1.0
    context: Optional[str] = None


@strawberry.type
class ReferenceType:
    """GraphQL type for symbol references."""
    id: str
    symbol_id: str
    location: SourceLocationType
    kind: str
    is_definition: bool = False
    context: Optional[str] = None


@strawberry.type
class CallGraphNodeType:
    """GraphQL type for call graph nodes."""
    symbol_id: str
    symbol_name: str
    symbol_type: ElementTypeEnum
    file_path: str
    calls: List[str] = strawberry.field(default_factory=list)
    called_by: List[str] = strawberry.field(default_factory=list)
    depth: int = 0
    complexity: float = 1.0


@strawberry.type
class DependencyGraphType:
    """GraphQL type for dependency graphs."""
    total_nodes: int
    total_edges: int
    density: float
    strongly_connected_components: int
    cycles_found: int


@strawberry.type
class ProjectMetrics:
    """GraphQL type for enhanced project-level metrics."""
    # Basic metrics
    total_files: int
    total_lines: int
    total_code_lines: int
    total_nodes: int
    average_complexity: float
    max_complexity: float
    total_imports: int
    
    # Intelligence metrics
    total_symbols: int
    total_relationships: int
    total_references: int
    average_cognitive_complexity: float
    max_cognitive_complexity: float
    
    # Graph metrics
    graph_metrics: Optional[DependencyGraphType] = None


@strawberry.type
class IntelligenceData:
    """GraphQL type for code intelligence information."""
    total_symbols: int
    total_relationships: int
    total_references: int
    call_graph_nodes: int
    dependency_graph: Optional[DependencyGraphType] = None


@strawberry.type
class ImpactAnalysisResult:
    """GraphQL type for impact analysis results."""
    total_impacted_symbols: int
    impacted_files: int
    impacted_symbols: List[str]
    impacted_file_paths: List[str]


@strawberry.type
class CallGraphResult:
    """GraphQL type for call graph results."""
    nodes: List[CallGraphNodeType]
    edges: List[RelationshipType]
    root_symbol: str
    max_depth: int


@strawberry.type
class VisualizationResult:
    """GraphQL type for visualization results."""
    type: str
    title: str
    data: str  # JSON string of visualization data
    metadata: str  # JSON string of metadata
    interactive: bool = True
    format: str = "plotly"
    error: Optional[str] = None


@strawberry.type
class DashboardResult:
    """GraphQL type for dashboard results."""
    type: str = "dashboard"
    title: str
    sections: str  # JSON string of dashboard sections
    metrics: str  # JSON string of metrics
    timestamp: str
    error: Optional[str] = None


@strawberry.type
class AnalysisResult:
    """GraphQL type for complete analysis result."""
    files: List[UniversalFileType]
    metrics: ProjectMetrics
    languages: List[str]
    intelligence: Optional[IntelligenceData] = None


@strawberry.type
class Query:
    """GraphQL query root with advanced code intelligence."""
    
    @strawberry.field
    def analyze_file(self, file_path: str) -> Optional[UniversalFileType]:
        """Analyze a single file and return its universal representation."""
        try:
            analyzer = UniversalAnalyzer()
            path = Path(file_path)
            result = analyzer.analyze_file(path)
            
            if not result:
                return None
                
            # Convert to GraphQL types
            nodes = [
                UniversalNodeType(
                    id=node.id,
                    type=ElementTypeEnum(node.type.name),
                    name=node.name,
                    language=LanguageEnum(node.language.value),
                    location=SourceLocationType(
                        file_path=node.location.file_path,
                        start_line=node.location.start_line,
                        end_line=node.location.end_line,
                        start_column=node.location.start_column,
                        end_column=node.location.end_column,
                        offset=node.location.offset,
                        length=node.location.length
                    ),
                    parent_id=node.parent_id,
                    children_ids=node.children_ids,
                    access_level=AccessLevelEnum(node.access_level.value) if node.access_level else None,
                    is_static=node.is_static,
                    is_async=node.is_async,
                    is_abstract=node.is_abstract,
                    is_final=node.is_final,
                    is_const=node.is_const,
                    data_type=node.data_type,
                    return_type=node.return_type,
                    extends=node.extends,
                    complexity=node.complexity,
                    lines_of_code=node.lines_of_code,
                    lines_of_comments=node.lines_of_comments,
                    documentation=node.documentation
                )
                for node in result.nodes
            ]
            
            return UniversalFileType(
                path=result.path,
                language=LanguageEnum(result.language.value),
                encoding=result.encoding,
                size_bytes=result.size_bytes,
                hash=result.hash,
                total_lines=result.total_lines,
                code_lines=result.code_lines,
                comment_lines=result.comment_lines,
                blank_lines=result.blank_lines,
                nodes=nodes,
                imports=result.imports,
                exports=result.exports,
                complexity=result.complexity,
                maintainability_index=result.maintainability_index
            )
            
        except Exception as e:
            # Log error and return None
            return None
    
    @strawberry.field
    def analyze_directory(self, directory_path: str) -> Optional[AnalysisResult]:
        """Analyze all files in a directory and return aggregated results."""
        try:
            analyzer = UniversalAnalyzer()
            path = Path(directory_path)
            results = analyzer.analyze_directory(path)
            
            if not results:
                return None
            
            # Convert files to GraphQL types
            files = []
            for file_result in results.values():
                nodes = [
                    UniversalNodeType(
                        id=node.id,
                        type=ElementTypeEnum(node.type.name),
                        name=node.name,
                        language=LanguageEnum(node.language.value),
                        location=SourceLocationType(
                            file_path=node.location.file_path,
                            start_line=node.location.start_line,
                            end_line=node.location.end_line,
                            start_column=node.location.start_column,
                            end_column=node.location.end_column,
                            offset=node.location.offset,
                            length=node.location.length
                        ),
                        parent_id=node.parent_id,
                        children_ids=node.children_ids,
                        access_level=AccessLevelEnum(node.access_level.value) if node.access_level else None,
                        is_static=node.is_static,
                        is_async=node.is_async,
                        is_abstract=node.is_abstract,
                        is_final=node.is_final,
                        is_const=node.is_const,
                        data_type=node.data_type,
                        return_type=node.return_type,
                        extends=node.extends,
                        complexity=node.complexity,
                        lines_of_code=node.lines_of_code,
                        lines_of_comments=node.lines_of_comments,
                        documentation=node.documentation
                    )
                    for node in file_result.nodes
                ]
                
                files.append(UniversalFileType(
                    path=file_result.path,
                    language=LanguageEnum(file_result.language.value),
                    encoding=file_result.encoding,
                    size_bytes=file_result.size_bytes,
                    hash=file_result.hash,
                    total_lines=file_result.total_lines,
                    code_lines=file_result.code_lines,
                    comment_lines=file_result.comment_lines,
                    blank_lines=file_result.blank_lines,
                    nodes=nodes,
                    imports=file_result.imports,
                    exports=file_result.exports,
                    complexity=file_result.complexity,
                    maintainability_index=file_result.maintainability_index
                ))
            
            # Calculate metrics
            total_lines = sum(f.total_lines for f in results.values())
            total_code_lines = sum(f.code_lines for f in results.values())
            total_nodes = sum(len(f.nodes) for f in results.values())
            complexities = [f.complexity for f in results.values() if f.complexity > 0]
            
            metrics = ProjectMetrics(
                total_files=len(results),
                total_lines=total_lines,
                total_code_lines=total_code_lines,
                total_nodes=total_nodes,
                average_complexity=sum(complexities) / len(complexities) if complexities else 0,
                max_complexity=max(complexities) if complexities else 0,
                total_imports=sum(len(f.imports) for f in results.values())
            )
            
            # Get language distribution
            language_dist = {}
            for file_result in results.values():
                lang = file_result.language.value
                language_dist[lang] = language_dist.get(lang, 0) + 1
            
            return AnalysisResult(
                files=files,
                metrics=metrics,
                languages=list(language_dist.keys())
            )
            
        except Exception as e:
            # Log error and return None
            return None
    
    @strawberry.field
    def analyze_project_with_intelligence(self, directory_path: str, project_name: Optional[str] = None) -> Optional[AnalysisResult]:
        """Analyze a project with full code intelligence."""
        try:
            analyzer = IntegratedCodeAnalyzer()
            path = Path(directory_path)
            result = analyzer.analyze_project(path, project_name)
            
            if not result:
                return None
            
            # Convert to GraphQL types (simplified for now)
            files = []  # Would convert files like in analyze_directory
            
            metrics = ProjectMetrics(
                # Basic metrics
                total_files=result['metrics']['total_files'],
                total_lines=result['metrics']['total_lines'],
                total_code_lines=result['metrics']['total_code_lines'],
                total_nodes=result['metrics']['total_nodes'],
                average_complexity=result['metrics']['average_complexity'],
                max_complexity=result['metrics']['max_complexity'],
                total_imports=result['metrics']['total_imports'],
                
                # Intelligence metrics
                total_symbols=result['metrics']['total_symbols'],
                total_relationships=result['metrics']['total_relationships'],
                total_references=result['metrics']['total_references'],
                average_cognitive_complexity=result['metrics']['average_cognitive_complexity'],
                max_cognitive_complexity=result['metrics']['max_cognitive_complexity'],
                
                # Graph metrics
                graph_metrics=DependencyGraphType(
                    total_nodes=result['metrics']['graph_metrics'].get('total_nodes', 0),
                    total_edges=result['metrics']['graph_metrics'].get('total_edges', 0),
                    density=result['metrics']['graph_metrics'].get('density', 0.0),
                    strongly_connected_components=result['metrics']['graph_metrics'].get('strongly_connected_components', 0),
                    cycles_found=result['metrics']['graph_metrics'].get('cycles_found', 0)
                ) if result['metrics']['graph_metrics'] else None
            )
            
            intelligence = IntelligenceData(
                total_symbols=result['intelligence']['total_symbols'],
                total_relationships=result['intelligence']['total_relationships'],
                total_references=result['intelligence']['total_references'],
                call_graph_nodes=result['intelligence']['call_graph_nodes'],
                dependency_graph=DependencyGraphType(
                    total_nodes=result['intelligence']['graph_metrics'].get('total_nodes', 0),
                    total_edges=result['intelligence']['graph_metrics'].get('total_edges', 0),
                    density=result['intelligence']['graph_metrics'].get('density', 0.0),
                    strongly_connected_components=result['intelligence']['graph_metrics'].get('strongly_connected_components', 0),
                    cycles_found=result['intelligence']['graph_metrics'].get('cycles_found', 0)
                ) if result['intelligence']['graph_metrics'] else None
            )
            
            return AnalysisResult(
                files=files,
                metrics=metrics,
                languages=result['languages'],
                intelligence=intelligence
            )
            
        except Exception as e:
            return None
    
    @strawberry.field
    def find_symbol_references(self, project_id: str, symbol_id: str) -> List[ReferenceType]:
        """Find all references to a symbol."""
        try:
            analyzer = IntegratedCodeAnalyzer()
            references = analyzer.find_symbol_references(project_id, symbol_id)
            
            return [
                ReferenceType(
                    id=ref['id'],
                    symbol_id=ref['symbol_id'],
                    location=SourceLocationType(
                        file_path=ref['location']['file_path'],
                        start_line=ref['location']['start_line'],
                        end_line=ref['location']['end_line'],
                        start_column=ref['location']['start_column'],
                        end_column=ref['location']['end_column']
                    ),
                    kind=ref['kind'],
                    is_definition=ref['is_definition'],
                    context=ref.get('context')
                )
                for ref in references
            ]
        except Exception as e:
            return []
    
    @strawberry.field
    def get_symbol_relationships(self, project_id: str, symbol_id: str, 
                               relationship_types: Optional[List[RelationTypeEnum]] = None) -> List[RelationshipType]:
        """Get relationships for a symbol."""
        try:
            analyzer = IntegratedCodeAnalyzer()
            rel_types = [rt.value for rt in relationship_types] if relationship_types else None
            relationships = analyzer.get_symbol_relationships(project_id, symbol_id, rel_types)
            
            return [
                RelationshipType(
                    id=rel['id'],
                    source_id=rel['source_id'],
                    target_id=rel['target_id'],
                    type=RelationTypeEnum(rel['type']),
                    confidence=rel['confidence'],
                    context=rel.get('context')
                )
                for rel in relationships
            ]
        except Exception as e:
            return []
    
    @strawberry.field
    def analyze_symbol_impact(self, project_id: str, symbol_id: str, max_depth: int = 5) -> Optional[ImpactAnalysisResult]:
        """Analyze the impact of changing a symbol."""
        try:
            analyzer = IntegratedCodeAnalyzer()
            result = analyzer.analyze_symbol_impact(project_id, symbol_id, max_depth)
            
            if "error" in result:
                return None
            
            return ImpactAnalysisResult(
                total_impacted_symbols=result['total_impacted_symbols'],
                impacted_files=result['impacted_files'],
                impacted_symbols=result['impacted_symbols'],
                impacted_file_paths=result['impacted_file_paths']
            )
        except Exception as e:
            return None
    
    @strawberry.field
    def get_call_graph(self, project_id: str, symbol_id: str, depth: int = 3) -> Optional[CallGraphResult]:
        """Get call graph for a symbol."""
        try:
            analyzer = IntegratedCodeAnalyzer()
            result = analyzer.get_symbol_call_graph(project_id, symbol_id, depth)
            
            if "error" in result:
                return None
            
            nodes = [
                CallGraphNodeType(
                    symbol_id=node['id'],
                    symbol_name=node['name'],
                    symbol_type=ElementTypeEnum(node['type']),
                    file_path=node['file'],
                    complexity=node['complexity'],
                    depth=node['depth']
                )
                for node in result['nodes']
            ]
            
            edges = [
                RelationshipType(
                    id=f"{edge['source']}:{edge['target']}",
                    source_id=edge['source'],
                    target_id=edge['target'],
                    type=RelationTypeEnum.CALLS
                )
                for edge in result['edges']
            ]
            
            return CallGraphResult(
                nodes=nodes,
                edges=edges,
                root_symbol=result['root_symbol'],
                max_depth=result['max_depth']
            )
        except Exception as e:
            return None
    
    @strawberry.field
    def generate_visualization(self, project_id: str, visualization_type: str, **kwargs) -> Optional[VisualizationResult]:
        """Generate a specific visualization for a project."""
        try:
            analyzer = IntegratedCodeAnalyzer()
            result = analyzer.generate_visualization(project_id, visualization_type, **kwargs)
            
            if "error" in result:
                return VisualizationResult(
                    type=visualization_type,
                    title="Error",
                    data="{}",
                    metadata="{}",
                    error=result["error"]
                )
            
            return VisualizationResult(
                type=result.get("type", visualization_type),
                title=result.get("title", "Visualization"),
                data=json.dumps(result.get("data", {})),
                metadata=json.dumps(result.get("metadata", {})),
                interactive=result.get("interactive", True),
                format=result.get("format", "plotly")
            )
        except Exception as e:
            return VisualizationResult(
                type=visualization_type,
                title="Error", 
                data="{}",
                metadata="{}",
                error=str(e)
            )
    
    @strawberry.field
    def generate_project_dashboard(self, project_id: str) -> Optional[DashboardResult]:
        """Generate a comprehensive project dashboard."""
        try:
            analyzer = IntegratedCodeAnalyzer()
            result = analyzer.generate_project_dashboard(project_id)
            
            if "error" in result:
                return DashboardResult(
                    title="Dashboard Error",
                    sections="[]",
                    metrics="{}",
                    timestamp="",
                    error=result["error"]
                )
            
            return DashboardResult(
                title=result.get("title", "Project Dashboard"),
                sections=json.dumps(result.get("sections", [])),
                metrics=json.dumps(result.get("metrics", {})),
                timestamp=result.get("timestamp", "")
            )
        except Exception as e:
            return DashboardResult(
                title="Dashboard Error",
                sections="[]", 
                metrics="{}",
                timestamp="",
                error=str(e)
            )
    
    @strawberry.field
    def get_available_visualizations(self) -> List[str]:
        """Get list of available visualization types."""
        try:
            analyzer = IntegratedCodeAnalyzer()
            return analyzer.get_available_visualizations()
        except Exception as e:
            return []


schema = strawberry.Schema(query=Query)
