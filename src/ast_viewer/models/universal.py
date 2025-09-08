"""
Universal data models for multi-language code analysis.

This module defines the core data structures used across all language adapters
to provide a unified representation of code elements using Pydantic models.
"""

from typing import Dict, List, Optional, Set, Any, Tuple
from enum import Enum, auto
import ast

from pydantic import BaseModel, Field


class ElementType(Enum):
    """Universal code element types across all languages."""
    # Structural
    PROJECT = auto()
    PACKAGE = auto()
    MODULE = auto()
    FILE = auto()
    
    # Object-Oriented
    CLASS = auto()
    INTERFACE = auto()
    TRAIT = auto()
    ENUM = auto()
    STRUCT = auto()
    
    # Functions
    FUNCTION = auto()
    METHOD = auto()
    CONSTRUCTOR = auto()
    DESTRUCTOR = auto()
    LAMBDA = auto()
    GENERATOR = auto()
    
    # Variables
    VARIABLE = auto()
    CONSTANT = auto()
    PARAMETER = auto()
    FIELD = auto()
    PROPERTY = auto()
    
    # Control Flow
    CONDITIONAL = auto()
    LOOP = auto()
    EXCEPTION = auto()
    
    # Dependencies
    IMPORT = auto()
    EXPORT = auto()
    INCLUDE = auto()
    
    # Documentation
    COMMENT = auto()
    DOCSTRING = auto()
    ANNOTATION = auto()


class Language(Enum):
    """Supported programming languages."""
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
    
    @property
    def tree_sitter_parser(self):
        """Get Tree-sitter Language object for language if available."""
        try:
            import tree_sitter
            
            if self == Language.PYTHON:
                import tree_sitter_python
                return tree_sitter.Language(tree_sitter_python.language())
            elif self == Language.JAVASCRIPT:
                import tree_sitter_javascript
                return tree_sitter.Language(tree_sitter_javascript.language())
            elif self == Language.TYPESCRIPT:
                import tree_sitter_typescript
                return tree_sitter.Language(tree_sitter_typescript.language_tsx())
            elif self == Language.GO:
                import tree_sitter_go
                return tree_sitter.Language(tree_sitter_go.language())
            elif self == Language.RUST:
                import tree_sitter_rust
                return tree_sitter.Language(tree_sitter_rust.language())
        except ImportError:
            pass
        return None


class AccessLevel(Enum):
    """Universal access/visibility levels."""
    PUBLIC = "public"
    PRIVATE = "private"
    PROTECTED = "protected"
    INTERNAL = "internal"
    PACKAGE = "package"
    FILE = "file"


class SourceLocation(BaseModel):
    """Universal source code location."""
    file_path: str
    start_line: int
    end_line: int
    start_column: int = 0
    end_column: int = 0
    offset: Optional[int] = None
    length: Optional[int] = None
    
    # Tree-sitter specific byte positions
    start_byte: Optional[int] = None
    end_byte: Optional[int] = None
    
    @classmethod
    def from_ast_node(cls, node: ast.AST, file_path: str) -> 'SourceLocation':
        """Create from Python AST node."""
        return cls(
            file_path=file_path,
            start_line=getattr(node, 'lineno', 1),
            end_line=getattr(node, 'end_lineno', node.lineno) if hasattr(node, 'lineno') else 1,
            start_column=getattr(node, 'col_offset', 0),
            end_column=getattr(node, 'end_col_offset', 0)
        )
    
    @classmethod
    def from_tree_sitter_node(cls, node: Any, file_path: str) -> 'SourceLocation':
        """Create from Tree-sitter node."""
        return cls(
            file_path=file_path,
            start_line=node.start_point[0] + 1,  # Tree-sitter is 0-based
            end_line=node.end_point[0] + 1,
            start_column=node.start_point[1],
            end_column=node.end_point[1],
            start_byte=node.start_byte,
            end_byte=node.end_byte
        )
    
    def contains(self, other: 'SourceLocation') -> bool:
        """Check if this location contains another."""
        return (self.file_path == other.file_path and
                self.start_line <= other.start_line and
                self.end_line >= other.end_line)


class UniversalNode(BaseModel):
    """Universal code node representation."""
    id: str
    type: ElementType
    name: Optional[str]
    language: Language
    location: SourceLocation
    
    # Hierarchy
    parent_id: Optional[str] = None
    children_ids: List[str] = Field(default_factory=list)
    
    # Properties
    access_level: Optional[AccessLevel] = None
    is_static: bool = False
    is_async: bool = False
    is_abstract: bool = False
    is_final: bool = False
    is_const: bool = False
    
    # Type information
    data_type: Optional[str] = None
    return_type: Optional[str] = None
    parameters: List[Dict[str, Any]] = Field(default_factory=list)
    generics: List[str] = Field(default_factory=list)
    
    # Relationships
    dependencies: Set[str] = Field(default_factory=set)
    references: Set[str] = Field(default_factory=set)
    implements: Set[str] = Field(default_factory=set)
    extends: Optional[str] = None
    
    # Metrics
    complexity: float = 1.0
    lines_of_code: int = 0
    lines_of_comments: int = 0
    
    # Documentation
    documentation: Optional[str] = None
    annotations: Dict[str, Any] = Field(default_factory=dict)
    
    # Raw data for language-specific processing
    raw_node: Optional[Any] = Field(default=None, exclude=True)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    # Tree-sitter specific fields
    tree_sitter_type: Optional[str] = None
    cognitive_complexity: int = 1
    
    model_config = {"arbitrary_types_allowed": True}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary, handling enums and complex types."""
        return self.model_dump(
            mode='python',
            exclude={'raw_node'},
            by_alias=True
        )


class UniversalFile(BaseModel):
    """Universal file representation."""
    path: str
    language: Language
    encoding: str = 'utf-8'
    size_bytes: int = 0
    hash: str = ''
    
    # Content metrics
    total_lines: int = 0
    code_lines: int = 0
    comment_lines: int = 0
    blank_lines: int = 0
    
    # Elements in file
    nodes: List[UniversalNode] = Field(default_factory=list)
    imports: List[str] = Field(default_factory=list)
    exports: List[str] = Field(default_factory=list)
    
    # File-level metrics
    complexity: float = 1.0
    maintainability_index: Optional[float] = None
    
    # Analysis metadata
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    def add_node(self, node: UniversalNode) -> None:
        """Add a node to this file."""
        self.nodes.append(node)
        # Update metrics
        if node.location.end_line > self.total_lines:
            self.total_lines = node.location.end_line


class RelationType(Enum):
    """Types of relationships between code symbols."""
    # Inheritance relationships
    EXTENDS = "extends"
    IMPLEMENTS = "implements"
    
    # Usage relationships
    CALLS = "calls"
    USES = "uses"
    REFERENCES = "references"
    INSTANTIATES = "instantiates"
    
    # Import/export relationships
    IMPORTS = "imports"
    EXPORTS = "exports"
    
    # Override relationships
    OVERRIDES = "overrides"
    OVERRIDDEN_BY = "overridden_by"
    
    # Type relationships
    RETURNS = "returns"
    ACCEPTS = "accepts"
    THROWS = "throws"
    
    # Annotation relationships
    DECORATES = "decorates"
    ANNOTATES = "annotates"
    
    # Containment relationships
    CONTAINS = "contains"
    CONTAINED_IN = "contained_in"


class Relationship(BaseModel):
    """Represents a relationship between two code symbols."""
    id: str
    source_id: str
    target_id: str
    type: RelationType
    location: Optional[SourceLocation] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    # Confidence and context
    confidence: float = 1.0  # 0.0 to 1.0
    context: Optional[str] = None  # Additional context about the relationship


class Reference(BaseModel):
    """Represents a reference to a symbol at a specific location."""
    id: str
    symbol_id: str
    location: SourceLocation
    kind: str  # "read", "write", "call", "definition", "declaration"
    is_definition: bool = False
    context: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class CallGraphNode(BaseModel):
    """Node in a call graph."""
    symbol_id: str
    symbol_name: str
    symbol_type: ElementType
    file_path: str
    calls: List[str] = Field(default_factory=list)  # Symbol IDs this node calls
    called_by: List[str] = Field(default_factory=list)  # Symbol IDs that call this node
    depth: int = 0  # Depth in call graph
    complexity: float = 1.0


class DependencyGraph(BaseModel):
    """Represents project dependency relationships."""
    nodes: List[str]  # Symbol or file IDs
    edges: List[Tuple[str, str, RelationType]]  # (source, target, relation_type)
    files: Set[str] = Field(default_factory=set)  # File paths involved
    cycles: List[List[str]] = Field(default_factory=list)  # Circular dependencies
    
    # Graph statistics
    total_nodes: int = 0
    total_edges: int = 0
    density: float = 0.0
    strongly_connected_components: int = 0
    
    def add_relationship(self, source: str, target: str, relation_type: RelationType):
        """Add a relationship to the graph."""
        if source not in self.nodes:
            self.nodes.append(source)
        if target not in self.nodes:
            self.nodes.append(target)
        
        edge = (source, target, relation_type)
        if edge not in self.edges:
            self.edges.append(edge)


class CodeIntelligence(BaseModel):
    """Comprehensive code intelligence data for a project."""
    project_id: str
    
    # Core data
    symbols: Dict[str, UniversalNode] = Field(default_factory=dict)
    files: Dict[str, UniversalFile] = Field(default_factory=dict)
    relationships: List[Relationship] = Field(default_factory=list)
    references: Dict[str, List[Reference]] = Field(default_factory=dict)  # symbol_id -> references
    
    # Graph representations
    dependency_graph: Optional[DependencyGraph] = None
    call_graph: Dict[str, CallGraphNode] = Field(default_factory=dict)  # symbol_id -> node
    
    # Computed intelligence
    metrics: Dict[str, Any] = Field(default_factory=dict)
    
    def add_symbol(self, symbol: UniversalNode):
        """Add a symbol to the intelligence store."""
        self.symbols[symbol.id] = symbol
        
    def add_relationship(self, relationship: Relationship):
        """Add a relationship between symbols."""
        self.relationships.append(relationship)
        
        # Update dependency graph
        if not self.dependency_graph:
            self.dependency_graph = DependencyGraph(nodes=[], edges=[])
        self.dependency_graph.add_relationship(
            relationship.source_id, 
            relationship.target_id, 
            relationship.type
        )
    
    def add_reference(self, reference: Reference):
        """Add a reference to a symbol."""
        if reference.symbol_id not in self.references:
            self.references[reference.symbol_id] = []
        self.references[reference.symbol_id].append(reference)
    
    def get_symbol_references(self, symbol_id: str) -> List[Reference]:
        """Get all references to a symbol."""
        return self.references.get(symbol_id, [])
    
    def get_symbol_relationships(self, symbol_id: str, 
                               relationship_types: Optional[List[RelationType]] = None) -> List[Relationship]:
        """Get relationships involving a symbol."""
        results = []
        for rel in self.relationships:
            if rel.source_id == symbol_id or rel.target_id == symbol_id:
                if not relationship_types or rel.type in relationship_types:
                    results.append(rel)
        return results
    
    def get_dependencies(self, symbol_id: str) -> List[str]:
        """Get symbols that this symbol depends on."""
        dependencies = []
        for rel in self.relationships:
            if rel.source_id == symbol_id and rel.type in [
                RelationType.CALLS, RelationType.USES, RelationType.IMPORTS, 
                RelationType.EXTENDS, RelationType.IMPLEMENTS
            ]:
                dependencies.append(rel.target_id)
        return dependencies
    
    def get_dependents(self, symbol_id: str) -> List[str]:
        """Get symbols that depend on this symbol."""
        dependents = []
        for rel in self.relationships:
            if rel.target_id == symbol_id and rel.type in [
                RelationType.CALLS, RelationType.USES, RelationType.IMPORTS,
                RelationType.EXTENDS, RelationType.IMPLEMENTS
            ]:
                dependents.append(rel.source_id)
        return dependents
