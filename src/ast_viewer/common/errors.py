"""Error handling utilities to eliminate repeated try-catch patterns.

This module provides decorators and utilities to eliminate the 30+ repeated 
try-except-log-return patterns identified throughout the codebase.

DRY Fix: Eliminates repeated error handling boilerplate code.
"""

import logging
import functools
from typing import Any, Callable, Optional, Dict, Union, TypeVar, Generic
from contextlib import contextmanager
import traceback
from enum import Enum

logger = logging.getLogger(__name__)

# Type variables for generic error handling
T = TypeVar('T')
F = TypeVar('F', bound=Callable[..., Any])


class ErrorSeverity(Enum):
    """Error severity levels for different handling strategies."""
    DEBUG = "debug"
    INFO = "info" 
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class DatabaseError(Exception):
    """Database-specific error for better error categorization."""
    pass


class AnalysisError(Exception):
    """Code analysis-specific error for better error categorization."""
    pass


class VisualizationError(Exception):
    """Visualization-specific error for better error categorization."""
    pass


def handle_errors(
    default_return: Any = None,
    exception_types: tuple = (Exception,),
    log_level: ErrorSeverity = ErrorSeverity.ERROR,
    custom_message: Optional[str] = None,
    return_error_dict: bool = False,
    raise_on_types: tuple = ()
):
    """Decorator to handle errors with consistent logging and return patterns.
    
    This replaces the repeated pattern:
    ```python
    try:
        # ... some operation
    except Exception as e:
        logger.error(f"Failed to X: {e}")
        return None/False/{"error": str(e)}
    ```
    
    Args:
        default_return: Value to return on error (None, False, {}, etc.)
        exception_types: Tuple of exception types to catch
        log_level: Logging level for errors
        custom_message: Custom error message template
        return_error_dict: If True, return {"error": str(e)} instead of default_return
        raise_on_types: Tuple of exception types that should be re-raised
    
    Usage:
        @handle_errors(default_return=False, custom_message="Database connection failed")
        def connect_to_db():
            # ... connection logic
    """
    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except raise_on_types as e:
                # Re-raise specific exceptions
                raise
            except exception_types as e:
                # Get function name for logging
                func_name = func.__name__
                
                # Create error message
                if custom_message:
                    message = f"{custom_message}: {e}"
                else:
                    message = f"Error in {func_name}: {e}"
                
                # Log based on severity level
                log_func = getattr(logger, log_level.value)
                log_func(message)
                
                # Include traceback for debug level
                if log_level == ErrorSeverity.DEBUG:
                    logger.debug(f"Traceback: {traceback.format_exc()}")
                
                # Return appropriate value
                if return_error_dict:
                    return {"error": str(e)}
                else:
                    return default_return
                    
        return wrapper
    return decorator


def handle_async_errors(
    default_return: Any = None,
    exception_types: tuple = (Exception,),
    log_level: ErrorSeverity = ErrorSeverity.ERROR,
    custom_message: Optional[str] = None,
    return_error_dict: bool = False
):
    """Async version of handle_errors decorator."""
    def decorator(func: F) -> F:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except exception_types as e:
                func_name = func.__name__
                
                if custom_message:
                    message = f"{custom_message}: {e}"
                else:
                    message = f"Error in async {func_name}: {e}"
                
                log_func = getattr(logger, log_level.value)
                log_func(message)
                
                if log_level == ErrorSeverity.DEBUG:
                    logger.debug(f"Traceback: {traceback.format_exc()}")
                
                if return_error_dict:
                    return {"error": str(e)}
                else:
                    return default_return
                    
        return async_wrapper
    return decorator


@contextmanager
def error_context(
    operation_name: str,
    default_return: Any = None,
    log_level: ErrorSeverity = ErrorSeverity.ERROR,
    exception_types: tuple = (Exception,),
    suppress_errors: bool = True
):
    """Context manager for error handling in complex operations.
    
    Usage:
        with error_context("database operation", default_return=False):
            # ... database operations
            return True
    """
    try:
        yield
    except exception_types as e:
        message = f"Error in {operation_name}: {e}"
        log_func = getattr(logger, log_level.value)
        log_func(message)
        
        if log_level == ErrorSeverity.DEBUG:
            logger.debug(f"Traceback: {traceback.format_exc()}")
        
        if not suppress_errors:
            raise
        
        return default_return


class SafeOperations:
    """Utility class for safe operations with consistent error handling."""
    
    @staticmethod
    def safe_get(dictionary: Dict, key: str, default: Any = None, log_missing: bool = False) -> Any:
        """Safely get a value from dictionary with optional logging."""
        try:
            return dictionary.get(key, default)
        except Exception as e:
            if log_missing:
                logger.warning(f"Failed to get key '{key}' from dictionary: {e}")
            return default
    
    @staticmethod
    def safe_call(func: Callable, *args, default: Any = None, log_errors: bool = True, **kwargs) -> Any:
        """Safely call a function with error handling."""
        try:
            return func(*args, **kwargs)
        except Exception as e:
            if log_errors:
                logger.error(f"Error calling {func.__name__}: {e}")
            return default
    
    @staticmethod
    async def safe_async_call(func: Callable, *args, default: Any = None, log_errors: bool = True, **kwargs) -> Any:
        """Safely call an async function with error handling."""
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            if log_errors:
                logger.error(f"Error calling async {func.__name__}: {e}")
            return default
    
    @staticmethod
    def safe_convert(value: Any, target_type: type, default: Any = None) -> Any:
        """Safely convert a value to target type."""
        try:
            return target_type(value)
        except (ValueError, TypeError) as e:
            logger.warning(f"Failed to convert {value} to {target_type}: {e}")
            return default
    
    @staticmethod
    def safe_list_operation(items: list, operation: Callable, default_item: Any = None) -> list:
        """Safely apply operation to list items, skipping failures."""
        results = []
        failed_count = 0
        
        for item in items:
            try:
                result = operation(item)
                if result is not None:
                    results.append(result)
                else:
                    results.append(default_item)
            except Exception as e:
                failed_count += 1
                logger.warning(f"Failed operation on item {item}: {e}")
                if default_item is not None:
                    results.append(default_item)
        
        if failed_count > 0:
            logger.info(f"List operation completed: {len(results)} successful, {failed_count} failed")
        
        return results


# Specific decorators for common patterns in the codebase
def database_operation(default_return: Any = False):
    """Decorator specifically for database operations."""
    return handle_errors(
        default_return=default_return,
        exception_types=(DatabaseError, ConnectionError, Exception),
        custom_message="Database operation failed",
        log_level=ErrorSeverity.ERROR
    )


def analysis_operation(default_return: Any = None):
    """Decorator specifically for code analysis operations."""
    return handle_errors(
        default_return=default_return,
        exception_types=(AnalysisError, Exception),
        custom_message="Analysis operation failed",
        log_level=ErrorSeverity.WARNING
    )


def visualization_operation(default_return: Any = None):
    """Decorator specifically for visualization operations."""
    return handle_errors(
        default_return=default_return,
        exception_types=(VisualizationError, ImportError, Exception),
        custom_message="Visualization operation failed",
        log_level=ErrorSeverity.WARNING,
        return_error_dict=True
    )


def api_endpoint(return_error_dict: bool = True):
    """Decorator specifically for API endpoints."""
    return handle_errors(
        default_return={"error": "Internal server error"},
        exception_types=(Exception,),
        custom_message="API endpoint error",
        log_level=ErrorSeverity.ERROR,
        return_error_dict=return_error_dict
    )


# Error aggregation utilities
class ErrorCollector:
    """Collect and aggregate errors during batch operations."""
    
    def __init__(self):
        self.errors: List[Dict[str, Any]] = []
        self.success_count = 0
        self.failure_count = 0
    
    def add_error(self, operation: str, error: Exception, context: Dict = None):
        """Add an error to the collection."""
        self.errors.append({
            "operation": operation,
            "error": str(error),
            "type": type(error).__name__,
            "context": context or {}
        })
        self.failure_count += 1
    
    def add_success(self):
        """Mark a successful operation."""
        self.success_count += 1
    
    def has_errors(self) -> bool:
        """Check if any errors were collected."""
        return len(self.errors) > 0
    
    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of all operations."""
        return {
            "total_operations": self.success_count + self.failure_count,
            "successful": self.success_count,
            "failed": self.failure_count,
            "success_rate": self.success_count / max(1, self.success_count + self.failure_count),
            "errors": self.errors
        }
    
    def log_summary(self, operation_type: str = "batch operation"):
        """Log a summary of the collected errors."""
        summary = self.get_summary()
        
        if self.has_errors():
            logger.warning(
                f"{operation_type} completed with errors: "
                f"{summary['successful']}/{summary['total_operations']} successful "
                f"({summary['success_rate']:.1%} success rate)"
            )
            for error in self.errors[:5]:  # Log first 5 errors
                logger.warning(f"  - {error['operation']}: {error['error']}")
            
            if len(self.errors) > 5:
                logger.warning(f"  ... and {len(self.errors) - 5} more errors")
        else:
            logger.info(f"{operation_type} completed successfully: {summary['successful']} operations")
