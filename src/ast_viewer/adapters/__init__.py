"""Language-specific adapters for code analysis."""

from .base import LanguageAdapter
from .python import PythonAdapter
from .tree_sitter import TreeSitterAdapter

__all__ = [
    "LanguageAdapter",
    "PythonAdapter", 
    "TreeSitterAdapter",
]
