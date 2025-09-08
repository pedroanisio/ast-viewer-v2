"""Modern GraphQL API for AST Viewer with advanced code intelligence."""

from .modern_schema import create_schema
from .integration import create_fastapi_app, get_graphql_context
from .dataloaders import IntelligenceDataLoaders, SimpleDataLoader
from .context import create_context, GraphQLContext
from .errors import (
    FileNotFoundError, DirectoryNotFoundError, AnalysisError, ValidationError
)
from .inputs import (
    FileAnalysisInput, DirectoryAnalysisInput, ProjectAnalysisInput,
    SymbolSearchInput, RelationshipFilterInput
)

# Create default schema instance
schema = create_schema()

__all__ = [
    "schema", 
    "create_schema",
    "create_fastapi_app",
    "get_graphql_context",
    "IntelligenceDataLoaders", 
    "SimpleDataLoader",
    "create_context",
    "GraphQLContext",
    "FileNotFoundError",
    "DirectoryNotFoundError", 
    "AnalysisError",
    "ValidationError",
    "FileAnalysisInput",
    "DirectoryAnalysisInput",
    "ProjectAnalysisInput"
]
