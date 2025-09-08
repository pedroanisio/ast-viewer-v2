"""Centralized ID generation utilities to eliminate duplication.

This module provides consistent ID generation methods that were previously
duplicated across multiple adapters and analyzers.

DRY Fix: Eliminates repeated hashlib.md5(...).hexdigest()[:16] patterns.
"""

import hashlib
import uuid
from typing import Any, List, Union, Optional
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class IDGenerator:
    """Centralized ID generation for consistent identifiers across the system."""
    
    @staticmethod
    def generate_node_id(*parts: Any) -> str:
        """Generate consistent node IDs across all adapters.
        
        This replaces the duplicate patterns found in:
        - adapters/python.py:206-208
        - adapters/tree_sitter.py:723-725
        - analyzers/intelligence.py:439
        """
        # Convert all parts to strings and join
        id_parts = [str(part) for part in parts if part is not None]
        id_string = ':'.join(id_parts)
        
        # Generate consistent 16-character hash
        return hashlib.md5(id_string.encode('utf-8')).hexdigest()[:16]
    
    @staticmethod
    def generate_file_hash(content: Union[str, bytes]) -> str:
        """Generate consistent file content hash.
        
        This replaces the duplicate patterns found in:
        - adapters/tree_sitter.py:70
        - adapters/python.py:33
        """
        if isinstance(content, str):
            content_bytes = content.encode('utf-8')
        else:
            content_bytes = content
        
        return hashlib.md5(content_bytes).hexdigest()
    
    @staticmethod
    def generate_relationship_id(source_id: str, target_id: str, rel_type: str) -> str:
        """Generate consistent relationship IDs.
        
        This replaces the pattern in intelligence.py:439.
        """
        return IDGenerator.generate_node_id(source_id, target_id, rel_type)
    
    @staticmethod
    def generate_reference_id(symbol_id: str, file_path: Union[str, Path], 
                            line: int, column: int) -> str:
        """Generate consistent reference IDs.
        
        This replaces the pattern in intelligence.py:452.
        """
        if isinstance(file_path, Path):
            file_path = str(file_path)
        
        return IDGenerator.generate_node_id(symbol_id, file_path, line, column)
    
    @staticmethod
    def generate_project_id(project_name: str, owner: Optional[str] = None) -> str:
        """Generate consistent project IDs."""
        parts = [project_name]
        if owner:
            parts.append(owner)
        return IDGenerator.generate_node_id(*parts)
    
    @staticmethod
    def generate_uuid() -> str:
        """Generate a UUID4 for unique identifiers."""
        return str(uuid.uuid4())
    
    @staticmethod
    def generate_short_uuid() -> str:
        """Generate a short UUID (8 characters) for less critical IDs."""
        return str(uuid.uuid4())[:8]
    
    @staticmethod
    def generate_symbol_id(file_path: Union[str, Path], symbol_name: str, 
                          symbol_type: str, line: Optional[int] = None) -> str:
        """Generate consistent symbol IDs across analyzers."""
        if isinstance(file_path, Path):
            file_path = str(file_path)
        
        parts = [file_path, symbol_type, symbol_name]
        if line is not None:
            parts.append(line)
        
        return IDGenerator.generate_node_id(*parts)
    
    @staticmethod
    def generate_analysis_id(project_id: str, timestamp: Optional[str] = None) -> str:
        """Generate analysis run IDs."""
        import datetime
        
        if timestamp is None:
            timestamp = datetime.datetime.utcnow().isoformat()
        
        return IDGenerator.generate_node_id(project_id, "analysis", timestamp)
    
    @staticmethod
    def normalize_path_for_id(file_path: Union[str, Path]) -> str:
        """Normalize file paths for consistent ID generation."""
        if isinstance(file_path, Path):
            file_path = str(file_path)
        
        # Normalize separators and remove leading/trailing slashes
        normalized = file_path.replace('\\', '/').strip('/')
        return normalized
    
    @staticmethod
    def validate_id(id_value: str) -> bool:
        """Validate that an ID is properly formatted."""
        if not id_value or not isinstance(id_value, str):
            return False
        
        # Check if it's a valid hex string of appropriate length
        if len(id_value) == 16:
            try:
                int(id_value, 16)
                return True
            except ValueError:
                return False
        
        # Check if it's a UUID
        try:
            uuid.UUID(id_value)
            return True
        except ValueError:
            return False
    
    @classmethod
    def create_deterministic_id(cls, seed: str) -> str:
        """Create a deterministic ID from a seed string.
        
        Useful for testing or when you need reproducible IDs.
        """
        return cls.generate_node_id(seed, "deterministic")


# Convenience functions for backward compatibility and common usage
def generate_node_id(*parts: Any) -> str:
    """Convenience function for node ID generation."""
    return IDGenerator.generate_node_id(*parts)

def generate_file_hash(content: Union[str, bytes]) -> str:
    """Convenience function for file hashing."""
    return IDGenerator.generate_file_hash(content)

def generate_relationship_id(source_id: str, target_id: str, rel_type: str) -> str:
    """Convenience function for relationship ID generation."""
    return IDGenerator.generate_relationship_id(source_id, target_id, rel_type)

def generate_reference_id(symbol_id: str, file_path: Union[str, Path], 
                         line: int, column: int) -> str:
    """Convenience function for reference ID generation."""
    return IDGenerator.generate_reference_id(symbol_id, file_path, line, column)

def generate_symbol_id(file_path: Union[str, Path], symbol_name: str, 
                      symbol_type: str, line: Optional[int] = None) -> str:
    """Convenience function for symbol ID generation."""
    return IDGenerator.generate_symbol_id(file_path, symbol_name, symbol_type, line)
