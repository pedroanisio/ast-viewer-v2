"""
AST Viewer - Universal Code Analysis Model

A unified implementation for multi-language code analysis that bridges 
AST analyzer (Python-specific) with ProjectBuilder (multi-language).
"""

from .models.universal import (
    ElementType,
    Language,
    AccessLevel,
    SourceLocation,
    UniversalNode,
    UniversalFile,
    RelationType,
    Relationship,
    Reference,
    CodeIntelligence,
    DependencyGraph,
    CallGraphNode,
)

from .analyzers.universal import UniversalAnalyzer
from .analyzers.integrated import IntegratedCodeAnalyzer
from .analyzers.intelligence import IntelligenceEngine

__version__ = "0.2.0"  # Upgraded to v0.2.0 with intelligence features
__all__ = [
    # Core Models
    "ElementType",
    "Language", 
    "AccessLevel",
    "SourceLocation",
    "UniversalNode",
    "UniversalFile",
    
    # Intelligence Models
    "RelationType",
    "Relationship", 
    "Reference",
    "CodeIntelligence",
    "DependencyGraph",
    "CallGraphNode",
    
    # Analyzers
    "UniversalAnalyzer",
    "IntegratedCodeAnalyzer",
    "IntelligenceEngine",
]
