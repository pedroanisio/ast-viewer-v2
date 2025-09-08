"""Universal analyzer for multi-language code analysis."""

import logging
from pathlib import Path
from typing import Dict, List, Optional

from ..adapters.base import LanguageAdapter
from ..adapters.python import PythonAdapter
from ..adapters.tree_sitter import TreeSitterAdapter
from ..models.universal import Language, UniversalFile

logger = logging.getLogger(__name__)


class UniversalAnalyzer:
    """Main analyzer that uses appropriate language adapters."""
    
    def __init__(self, prefer_tree_sitter: bool = True):
        """
        Initialize analyzer with adapter preferences.
        
        Args:
            prefer_tree_sitter: If True, use Tree-sitter when available, 
                               fallback to language-specific adapters
        """
        self.prefer_tree_sitter = prefer_tree_sitter
        self.tree_sitter_adapter = None
        self.language_adapters: Dict[Language, LanguageAdapter] = {}
        self._file_cache: Dict[str, UniversalFile] = {}
        
        # Initialize Tree-sitter adapter
        try:
            self.tree_sitter_adapter = TreeSitterAdapter()
            logger.info("Tree-sitter adapter initialized successfully")
        except Exception as e:
            logger.warning(f"Failed to initialize Tree-sitter adapter: {e}")
        
        # Initialize language-specific adapters
        self.language_adapters[Language.PYTHON] = PythonAdapter()
        
        # Build final adapter mapping
        self.adapters = self._build_adapter_mapping()
    
    def _build_adapter_mapping(self) -> Dict[Language, LanguageAdapter]:
        """Build mapping of languages to their best available adapters."""
        adapters = {}
        
        # For each language, choose the best adapter
        for language in Language:
            if language == Language.UNKNOWN:
                continue
                
            # Check if Tree-sitter supports this language
            if (self.prefer_tree_sitter and 
                self.tree_sitter_adapter and 
                language.tree_sitter_parser is not None):
                adapters[language] = self.tree_sitter_adapter
                logger.debug(f"Using Tree-sitter adapter for {language.value}")
            elif language in self.language_adapters:
                adapters[language] = self.language_adapters[language]
                logger.debug(f"Using specialized adapter for {language.value}")
            else:
                logger.warning(f"No adapter available for {language.value}")
        
        return adapters
    
    def get_supported_languages(self) -> List[Language]:
        """Get list of languages supported by available adapters."""
        return list(self.adapters.keys())
    
    def analyze_file(self, file_path: Path) -> Optional[UniversalFile]:
        """Analyze a single file using the best available adapter."""
        try:
            # Detect language
            language = self._detect_language(file_path)
            if language not in self.adapters:
                logger.warning(f"No adapter available for {language.value} ({file_path})")
                return None
            
            # Read file content
            content = file_path.read_text(encoding='utf-8')
            
            # Get appropriate adapter
            adapter = self.adapters[language]
            adapter_type = "Tree-sitter" if adapter == self.tree_sitter_adapter else "Specialized"
            logger.debug(f"Analyzing {file_path} with {adapter_type} adapter for {language.value}")
            
            # Parse file
            universal_file = adapter.parse_file(file_path, content)
            
            # Add analysis metadata
            universal_file.metadata["analyzer_type"] = adapter_type
            universal_file.metadata["language_detected"] = language.value
            
            # Cache result
            self._file_cache[str(file_path)] = universal_file
            
            return universal_file
            
        except Exception as e:
            logger.error(f"Failed to analyze {file_path}: {e}")
            return None
    
    def analyze_directory(self, directory: Path) -> Dict[str, UniversalFile]:
        """Analyze all files in a directory recursively."""
        results = {}
        
        for file_path in self._discover_files(directory):
            result = self.analyze_file(file_path)
            if result:
                results[str(file_path)] = result
        
        return results
    
    def _detect_language(self, file_path: Path) -> Language:
        """Detect language from file extension."""
        extension_map = {
            '.py': Language.PYTHON,
            '.pyw': Language.PYTHON,
            '.js': Language.JAVASCRIPT,
            '.mjs': Language.JAVASCRIPT,
            '.jsx': Language.JAVASCRIPT,
            '.ts': Language.TYPESCRIPT,
            '.tsx': Language.TYPESCRIPT,
            '.go': Language.GO,
            '.rs': Language.RUST,
            '.c': Language.C,
            '.h': Language.C,
            '.cpp': Language.CPP,
            '.cc': Language.CPP,
            '.cxx': Language.CPP,
            '.hpp': Language.CPP,
            '.java': Language.JAVA,
            '.cs': Language.CSHARP,
            '.rb': Language.RUBY,
            '.php': Language.PHP,
            '.swift': Language.SWIFT,
            '.kt': Language.KOTLIN,
            '.scala': Language.SCALA,
            '.html': Language.HTML,
            '.htm': Language.HTML,
            '.css': Language.CSS,
            '.sql': Language.SQL,
        }
        
        suffix = file_path.suffix.lower()
        return extension_map.get(suffix, Language.UNKNOWN)
    
    def _discover_files(self, directory: Path) -> List[Path]:
        """Discover all analyzable files in directory."""
        excluded_dirs = {'.git', '__pycache__', 'node_modules', '.venv', 'venv', 'dist', 'build'}
        files = []
        
        for file_path in directory.rglob('*'):
            if file_path.is_file():
                # Skip if in excluded directory
                if any(part in excluded_dirs for part in file_path.parts):
                    continue
                
                # Check if file is analyzable
                if self._detect_language(file_path) != Language.UNKNOWN:
                    files.append(file_path)
        
        return files
