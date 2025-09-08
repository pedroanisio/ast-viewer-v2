"""GraphQL context management for dependency injection."""

from typing import Dict, Any, Optional
import strawberry
from strawberry.types import Info
from strawberry.fastapi import BaseContext

from ..analyzers.universal import UniversalAnalyzer
from ..analyzers.integrated import IntegratedCodeAnalyzer
from .dataloaders import IntelligenceDataLoaders


class GraphQLContext(BaseContext):
    """Context container for GraphQL operations with dependency injection."""
    
    def __init__(
        self,
        universal_analyzer: UniversalAnalyzer,
        integrated_analyzer: IntegratedCodeAnalyzer,
        dataloaders: IntelligenceDataLoaders,
        user: Optional[Dict[str, Any]] = None,
        request_id: Optional[str] = None,
        start_time: Optional[float] = None
    ):
        super().__init__()
        self.universal_analyzer = universal_analyzer
        self.integrated_analyzer = integrated_analyzer
        self.dataloaders = dataloaders
        self.user = user
        self.request_id = request_id
        self.start_time = start_time


def create_context(
    request_id: Optional[str] = None,
    user: Optional[Dict[str, Any]] = None
) -> GraphQLContext:
    """Factory function to create GraphQL context with all dependencies."""
    
    # Initialize analyzers
    universal_analyzer = UniversalAnalyzer()
    integrated_analyzer = IntegratedCodeAnalyzer()
    
    # Create DataLoaders with analyzers
    dataloaders = IntelligenceDataLoaders(integrated_analyzer)
    
    return GraphQLContext(
        universal_analyzer=universal_analyzer,
        integrated_analyzer=integrated_analyzer,
        dataloaders=dataloaders,
        user=user,
        request_id=request_id
    )


# Type alias for easier imports
Context = GraphQLContext


def get_context() -> Context:
    """Get context for dependency injection in resolvers."""
    return create_context()
