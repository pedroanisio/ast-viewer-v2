"""GraphQL enum types."""

from enum import Enum
import strawberry


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
    ANNOTATION = "ANNOTATION"
    DECORATOR = "DECORATOR"
    COMMENT = "COMMENT"
    DOCSTRING = "DOCSTRING"
    OTHER = "OTHER"
    UNKNOWN = "UNKNOWN"


@strawberry.enum
class LanguageEnum(Enum):
    """GraphQL enum for programming languages."""
    PYTHON = "python"
    JAVASCRIPT = "javascript"
    TYPESCRIPT = "typescript"
    JAVA = "java"
    CSHARP = "csharp"
    CPP = "cpp"
    C = "c"
    GO = "go"
    RUST = "rust"
    PHP = "php"
    RUBY = "ruby"
    SWIFT = "swift"
    KOTLIN = "kotlin"
    SCALA = "scala"
    SQL = "sql"
    HTML = "html"
    CSS = "css"
    SHELL = "shell"
    YAML = "yaml"
    JSON = "json"
    XML = "xml"
    MARKDOWN = "markdown"
    OTHER = "other"
    UNKNOWN = "unknown"


@strawberry.enum
class AccessLevelEnum(Enum):
    """GraphQL enum for access levels."""
    PUBLIC = "public"
    PRIVATE = "private"
    PROTECTED = "protected"
    INTERNAL = "internal"
    PACKAGE = "package"
    READONLY = "readonly"
    STATIC = "static"
    ABSTRACT = "abstract"
    FINAL = "final"
    OVERRIDE = "override"
    VIRTUAL = "virtual"
    UNKNOWN = "unknown"


@strawberry.enum
class RelationTypeEnum(Enum):
    """GraphQL enum for relationship types."""
    DEPENDS_ON = "depends_on"
    USES = "uses"
    CALLS = "calls"
    INHERITS = "inherits"
    IMPLEMENTS = "implements"
    EXTENDS = "extends"
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


@strawberry.enum
class ComplexityLevelEnum(Enum):
    """GraphQL enum for complexity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"


@strawberry.enum
class AnalysisStatusEnum(Enum):
    """GraphQL enum for analysis status."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@strawberry.enum
class VisualizationTypeEnum(Enum):
    """GraphQL enum for visualization types."""
    DEPENDENCY_GRAPH = "dependency_graph"
    CALL_GRAPH = "call_graph"
    INHERITANCE_TREE = "inheritance_tree"
    COMPLEXITY_HEATMAP = "complexity_heatmap"
    ARCHITECTURE_MAP = "architecture_map"
    METRICS_DASHBOARD = "metrics_dashboard"
    IMPACT_ANALYSIS = "impact_analysis"
