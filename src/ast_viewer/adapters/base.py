"""Base adapter protocol for language-specific parsers."""

from typing import Protocol, List
from pathlib import Path

from ..models.universal import UniversalFile, UniversalNode


class LanguageAdapter(Protocol):
    """Protocol for language-specific adapters."""
    
    def parse_file(self, file_path: Path, content: str) -> UniversalFile:
        """Parse a file and return universal representation."""
        ...
    
    def extract_nodes(self, content: str, file_path: str) -> List[UniversalNode]:
        """Extract nodes from source content."""
        ...
