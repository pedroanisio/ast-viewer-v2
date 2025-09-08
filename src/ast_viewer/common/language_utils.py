"""Centralized language detection utilities to eliminate duplication.

This module consolidates language detection logic that was previously
duplicated in tree_sitter.py and universal.py adapters.

DRY Fix: Eliminates duplicate extension mapping and detection logic.
"""

from pathlib import Path
from typing import Dict, Optional
import mimetypes
import logging

from ..models.universal import Language

logger = logging.getLogger(__name__)


class LanguageDetector:
    """Centralized language detection from file extensions and content."""
    
    # Comprehensive extension mapping (consolidated from both adapters)
    EXTENSION_MAP: Dict[str, Language] = {
        # Python
        '.py': Language.PYTHON,
        '.pyw': Language.PYTHON,
        '.pyi': Language.PYTHON,
        
        # JavaScript/TypeScript
        '.js': Language.JAVASCRIPT,
        '.mjs': Language.JAVASCRIPT,
        '.jsx': Language.JAVASCRIPT,
        '.ts': Language.TYPESCRIPT,
        '.tsx': Language.TYPESCRIPT,
        '.mts': Language.TYPESCRIPT,
        
        # Go
        '.go': Language.GO,
        
        # Rust
        '.rs': Language.RUST,
        
        # C/C++
        '.c': Language.C,
        '.h': Language.C,
        '.cpp': Language.CPP,
        '.cc': Language.CPP,
        '.cxx': Language.CPP,
        '.hpp': Language.CPP,
        '.hxx': Language.CPP,
        
        # Java
        '.java': Language.JAVA,
        
        # C#
        '.cs': Language.CSHARP,
        
        # Web technologies
        '.html': Language.HTML,
        '.htm': Language.HTML,
        '.xhtml': Language.HTML,
        '.css': Language.CSS,
        '.scss': Language.CSS,
        '.sass': Language.CSS,
        
        # Other languages (from original mappers)
        '.rb': Language.RUBY,
        '.php': Language.PHP,
        '.swift': Language.SWIFT,
        '.kt': Language.KOTLIN,
        '.scala': Language.SCALA,
        '.sql': Language.SQL,
        '.xml': Language.XML,
        '.json': Language.JSON,
        '.yaml': Language.YAML,
        '.yml': Language.YAML,
        '.md': Language.MARKDOWN,
        '.sh': Language.SHELL,
        '.bash': Language.SHELL,
        '.zsh': Language.SHELL,
    }
    
    # Content-based detection patterns
    CONTENT_PATTERNS = {
        Language.PYTHON: ['#!/usr/bin/env python', '#!/usr/bin/python', 'import ', 'from '],
        Language.JAVASCRIPT: ['#!/usr/bin/env node', 'require(', 'import ', 'export '],
        Language.SHELL: ['#!/bin/bash', '#!/bin/sh', '#!/usr/bin/env bash'],
        Language.PHP: ['<?php'],
    }
    
    @classmethod
    def detect_from_path(cls, file_path: Path) -> Language:
        """Detect language from file extension.
        
        This replaces the duplicate _detect_language methods in:
        - adapters/tree_sitter.py:690
        - analyzers/universal.py:115
        """
        if not isinstance(file_path, Path):
            file_path = Path(file_path)
        
        # Primary detection by extension
        extension = file_path.suffix.lower()
        if extension in cls.EXTENSION_MAP:
            return cls.EXTENSION_MAP[extension]
        
        # Fallback for common multi-extension files
        full_extension = ''.join(file_path.suffixes).lower()
        if full_extension in cls.EXTENSION_MAP:
            return cls.EXTENSION_MAP[full_extension]
        
        # Special cases
        filename = file_path.name.lower()
        if filename in ['makefile', 'dockerfile', 'rakefile']:
            return Language.OTHER
        
        logger.debug(f"Unknown language for file: {file_path}")
        return Language.UNKNOWN
    
    @classmethod
    def detect_from_content(cls, content: str, file_path: Optional[Path] = None) -> Language:
        """Detect language from file content patterns."""
        if not content.strip():
            return Language.UNKNOWN
        
        # Check first few lines for shebang or common patterns
        first_lines = content[:500].lower()
        
        for language, patterns in cls.CONTENT_PATTERNS.items():
            if any(pattern.lower() in first_lines for pattern in patterns):
                return language
        
        # Fallback to path-based detection
        if file_path:
            return cls.detect_from_path(file_path)
        
        return Language.UNKNOWN
    
    @classmethod
    def detect_with_fallback(cls, file_path: Path, content: Optional[str] = None) -> Language:
        """Comprehensive language detection with multiple fallbacks.
        
        This is the recommended method for new code.
        """
        # Primary: Extension-based detection
        language = cls.detect_from_path(file_path)
        
        # Secondary: Content-based detection if extension is unknown
        if language == Language.UNKNOWN and content:
            language = cls.detect_from_content(content, file_path)
        
        # Tertiary: MIME type detection
        if language == Language.UNKNOWN:
            mime_type, _ = mimetypes.guess_type(str(file_path))
            if mime_type:
                language = cls._language_from_mime_type(mime_type)
        
        return language
    
    @classmethod
    def _language_from_mime_type(cls, mime_type: str) -> Language:
        """Map MIME types to languages."""
        mime_map = {
            'text/x-python': Language.PYTHON,
            'application/javascript': Language.JAVASCRIPT,
            'text/javascript': Language.JAVASCRIPT,
            'text/typescript': Language.TYPESCRIPT,
            'text/x-go': Language.GO,
            'text/x-rust': Language.RUST,
            'text/x-c': Language.C,
            'text/x-c++': Language.CPP,
            'text/x-java-source': Language.JAVA,
            'text/html': Language.HTML,
            'text/css': Language.CSS,
            'application/json': Language.JSON,
            'text/x-yaml': Language.YAML,
            'text/markdown': Language.MARKDOWN,
        }
        return mime_map.get(mime_type, Language.UNKNOWN)
    
    @classmethod
    def get_supported_extensions(cls) -> list[str]:
        """Get list of all supported file extensions."""
        return list(cls.EXTENSION_MAP.keys())
    
    @classmethod
    def get_languages_for_extension(cls, extension: str) -> Optional[Language]:
        """Get language for a specific extension."""
        return cls.EXTENSION_MAP.get(extension.lower())
    
    @classmethod
    def add_extension_mapping(cls, extension: str, language: Language) -> None:
        """Add a new extension mapping (for extensibility)."""
        cls.EXTENSION_MAP[extension.lower()] = language
        logger.info(f"Added extension mapping: {extension} -> {language}")


# Convenience functions for backward compatibility
def detect_language_from_path(file_path: Path) -> Language:
    """Backward compatible function for existing code."""
    return LanguageDetector.detect_from_path(file_path)

def detect_language_from_content(content: str, file_path: Optional[Path] = None) -> Language:
    """Backward compatible function for existing code."""
    return LanguageDetector.detect_from_content(content, file_path)

def detect_language(file_path: Path, content: Optional[str] = None) -> Language:
    """Comprehensive language detection (recommended for new code)."""
    return LanguageDetector.detect_with_fallback(file_path, content)
