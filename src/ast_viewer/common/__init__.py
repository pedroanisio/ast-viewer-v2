"""Common utilities and base classes to eliminate code duplication."""

from .database import BaseDataClient
from .converters import convert_to_graphql_node, GraphQLConverters
from .errors import handle_errors, DatabaseError, AnalysisError
from .metrics import ComplexityCalculator, MetricsCollector
from .language_utils import LanguageDetector, detect_language
from .identifiers import IDGenerator, generate_node_id, generate_file_hash

__all__ = [
    # Database utilities
    "BaseDataClient",
    
    # GraphQL conversion utilities
    "convert_to_graphql_node", 
    "GraphQLConverters",
    
    # Error handling utilities
    "handle_errors",
    "DatabaseError", 
    "AnalysisError",
    
    # Metrics and complexity utilities
    "ComplexityCalculator",
    "MetricsCollector",
    
    # Language detection utilities  
    "LanguageDetector",
    "detect_language",
    
    # ID generation utilities
    "IDGenerator",
    "generate_node_id",
    "generate_file_hash"
]
