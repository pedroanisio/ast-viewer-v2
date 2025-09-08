"""GraphQL schema for AST Viewer - Modern Implementation.

This module provides the default GraphQL schema using modern Strawberry best practices.
"""

# Re-export the modern schema as the default
from .modern_schema import create_schema, Query, Mutation
from .types import (
    UniversalFileType, AnalysisResult, ProjectMetrics, 
    IntelligenceData, UniversalNodeType, SourceLocationType, 
    RelationshipType, ReferenceType
)

# Create default schema instance
schema = create_schema()

__all__ = [
    "schema",
    "create_schema", 
    "Query",
    "Mutation",
    # Type exports
    "UniversalFileType",
    "AnalysisResult", 
    "ProjectMetrics",
    "IntelligenceData",
    "UniversalNodeType",
    "SourceLocationType",
    "RelationshipType", 
    "ReferenceType"
]
