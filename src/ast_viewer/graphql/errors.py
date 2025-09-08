"""GraphQL error types using Union patterns for explicit error handling."""

from typing import Union
import strawberry


@strawberry.type
class FileNotFoundError:
    """Error when a requested file cannot be found."""
    message: str = "File not found"
    file_path: str
    
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.message = f"File not found: {file_path}"


@strawberry.type
class DirectoryNotFoundError:
    """Error when a requested directory cannot be found."""
    message: str = "Directory not found"
    directory_path: str
    
    def __init__(self, directory_path: str):
        self.directory_path = directory_path
        self.message = f"Directory not found: {directory_path}"


@strawberry.type
class AnalysisError:
    """Error during code analysis."""
    message: str
    file_path: str
    error_type: str
    
    def __init__(self, file_path: str, error: Exception):
        self.file_path = file_path
        self.error_type = type(error).__name__
        self.message = f"Analysis failed for {file_path}: {str(error)}"


@strawberry.type
class ValidationError:
    """Input validation error."""
    message: str
    field: str
    
    def __init__(self, field: str, message: str):
        self.field = field
        self.message = message


@strawberry.type
class PermissionError:
    """Permission denied error."""
    message: str = "Permission denied"
    resource: str
    
    def __init__(self, resource: str):
        self.resource = resource
        self.message = f"Permission denied for resource: {resource}"


@strawberry.type
class InternalError:
    """Internal server error."""
    message: str = "Internal server error"
    error_id: str
    
    def __init__(self, error_id: str, details: str = ""):
        self.error_id = error_id
        self.message = f"Internal error ({error_id}): {details}"


# Union types for operation results
# Note: These will be defined in modern_schema.py where all types are available
# to avoid circular import issues

# Type aliases for now - unions will be created in schema
FileAnalysisResult = "FileAnalysisResult"
DirectoryAnalysisResult = "DirectoryAnalysisResult" 
ProjectAnalysisResult = "ProjectAnalysisResult"
SymbolLookupResult = "SymbolLookupResult"

# Generic result types
GenericError = Union[
    FileNotFoundError, DirectoryNotFoundError, AnalysisError, 
    ValidationError, PermissionError, InternalError
]
