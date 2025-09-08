"""GraphQL context management for dependency injection."""

from typing import Dict, Any, Optional
import strawberry
from dataclasses import dataclass

from ..analyzers.universal import UniversalAnalyzer
from ..analyzers.integrated import IntegratedCodeAnalyzer
from .dataloaders import IntelligenceDataLoaders


@dataclass
class GraphQLContext:
    """Context container for GraphQL operations with dependency injection."""
    
    # Core analyzers
    universal_analyzer: UniversalAnalyzer
    integrated_analyzer: IntegratedCodeAnalyzer
    
    # DataLoaders for efficient batching
    dataloaders: IntelligenceDataLoaders
    
    # Optional user context (for future authentication)
    user: Optional[Dict[str, Any]] = None
    
    # Request metadata
    request_id: Optional[str] = None
    
    # Performance tracking
    start_time: Optional[float] = None


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
