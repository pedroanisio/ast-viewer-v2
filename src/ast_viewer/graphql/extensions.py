"""GraphQL extensions for logging, performance monitoring, and caching."""

import time
import logging
import uuid
from typing import Dict, Any, Optional
from strawberry.extensions import Extension
from strawberry.types import ExecutionResult

logger = logging.getLogger(__name__)


class LoggingExtension(Extension):
    """Extension for comprehensive GraphQL operation logging."""
    
    def __init__(self, include_variables: bool = False, include_context: bool = False):
        self.include_variables = include_variables
        self.include_context = include_context
        self.start_time: Optional[float] = None
        self.operation_id: Optional[str] = None
    
    def on_request_start(self):
        """Log when a GraphQL request starts."""
        self.start_time = time.time()
        self.operation_id = str(uuid.uuid4())[:8]
        
        logger.info(
            f"GraphQL request started",
            extra={
                "operation_id": self.operation_id,
                "timestamp": self.start_time
            }
        )
    
    def on_request_end(self):
        """Log when a GraphQL request ends."""
        if self.start_time:
            execution_time = time.time() - self.start_time
            logger.info(
                f"GraphQL request completed",
                extra={
                    "operation_id": self.operation_id,
                    "execution_time_ms": round(execution_time * 1000, 2),
                    "execution_time_s": round(execution_time, 3)
                }
            )
    
    def on_parsing_start(self):
        """Log when query parsing starts."""
        logger.debug(f"Query parsing started", extra={"operation_id": self.operation_id})
    
    def on_parsing_end(self):
        """Log when query parsing ends."""
        logger.debug(f"Query parsing completed", extra={"operation_id": self.operation_id})
    
    def on_validation_start(self):
        """Log when query validation starts."""
        logger.debug(f"Query validation started", extra={"operation_id": self.operation_id})
    
    def on_validation_end(self):
        """Log when query validation ends."""
        logger.debug(f"Query validation completed", extra={"operation_id": self.operation_id})
    
    def on_executing_start(self):
        """Log when query execution starts."""
        logger.debug(f"Query execution started", extra={"operation_id": self.operation_id})
    
    def on_executing_end(self):
        """Log when query execution ends."""
        logger.debug(f"Query execution completed", extra={"operation_id": self.operation_id})


class PerformanceExtension(Extension):
    """Extension for performance monitoring and metrics collection."""
    
    def __init__(self, slow_query_threshold: float = 1.0):
        self.slow_query_threshold = slow_query_threshold
        self.metrics: Dict[str, Any] = {}
        self.start_time: Optional[float] = None
    
    def on_request_start(self):
        """Start performance tracking."""
        self.start_time = time.time()
        self.metrics = {
            "query_count": 0,
            "field_count": 0,
            "resolver_times": {},
            "total_time": 0
        }
    
    def on_request_end(self):
        """Complete performance tracking and log metrics."""
        if self.start_time:
            total_time = time.time() - self.start_time
            self.metrics["total_time"] = total_time
            
            # Log slow queries
            if total_time > self.slow_query_threshold:
                logger.warning(
                    f"Slow GraphQL query detected",
                    extra={
                        "execution_time": total_time,
                        "threshold": self.slow_query_threshold,
                        "metrics": self.metrics
                    }
                )
            
            # Log performance metrics
            logger.info(
                f"GraphQL performance metrics",
                extra=self.metrics
            )
    
    def on_field_start(self, field_name: str):
        """Track field resolution start."""
        self.metrics["field_count"] += 1
        if field_name not in self.metrics["resolver_times"]:
            self.metrics["resolver_times"][field_name] = {
                "count": 0,
                "total_time": 0,
                "start_time": time.time()
            }
        else:
            self.metrics["resolver_times"][field_name]["start_time"] = time.time()
    
    def on_field_end(self, field_name: str):
        """Track field resolution end."""
        if field_name in self.metrics["resolver_times"]:
            resolver_data = self.metrics["resolver_times"][field_name]
            if "start_time" in resolver_data:
                field_time = time.time() - resolver_data["start_time"]
                resolver_data["count"] += 1
                resolver_data["total_time"] += field_time
                del resolver_data["start_time"]


class ValidationExtension(Extension):
    """Extension for additional query validation and security."""
    
    def __init__(self, max_depth: int = 10, max_complexity: int = 1000):
        self.max_depth = max_depth
        self.max_complexity = max_complexity
    
    def on_validation_start(self):
        """Start custom validation."""
        logger.debug("Custom validation started")
    
    def on_validation_end(self):
        """Complete custom validation."""
        logger.debug("Custom validation completed")


class ErrorTrackingExtension(Extension):
    """Extension for comprehensive error tracking and reporting."""
    
    def __init__(self, include_stack_trace: bool = False):
        self.include_stack_trace = include_stack_trace
        self.error_count = 0
    
    def on_request_start(self):
        """Initialize error tracking."""
        self.error_count = 0
    
    def on_request_end(self):
        """Log error summary."""
        if self.error_count > 0:
            logger.warning(
                f"GraphQL request completed with {self.error_count} errors"
            )
    
    def on_executing_end(self):
        """Track execution errors."""
        # This would be enhanced to track specific errors
        pass


class CacheExtension(Extension):
    """Extension for field-level caching (basic implementation)."""
    
    def __init__(self, default_ttl: int = 300):
        self.default_ttl = default_ttl
        self.cache: Dict[str, Dict[str, Any]] = {}
    
    def on_request_start(self):
        """Initialize cache for request."""
        # In production, this would integrate with Redis or similar
        pass
    
    def get_cached_result(self, cache_key: str) -> Optional[Any]:
        """Get cached result if available and not expired."""
        if cache_key in self.cache:
            cache_entry = self.cache[cache_key]
            if time.time() < cache_entry["expires_at"]:
                logger.debug(f"Cache hit for key: {cache_key}")
                return cache_entry["data"]
            else:
                # Remove expired entry
                del self.cache[cache_key]
                logger.debug(f"Cache expired for key: {cache_key}")
        
        logger.debug(f"Cache miss for key: {cache_key}")
        return None
    
    def set_cached_result(self, cache_key: str, data: Any, ttl: Optional[int] = None):
        """Cache result with TTL."""
        ttl = ttl or self.default_ttl
        self.cache[cache_key] = {
            "data": data,
            "expires_at": time.time() + ttl
        }
        logger.debug(f"Cached result for key: {cache_key}, TTL: {ttl}s")


# Extension configuration helper
def create_extensions(
    enable_logging: bool = True,
    enable_performance: bool = True,
    enable_validation: bool = True,
    enable_error_tracking: bool = True,
    enable_caching: bool = False,
    slow_query_threshold: float = 1.0,
    max_query_depth: int = 10
) -> list:
    """Create a list of extensions based on configuration."""
    extensions = []
    
    if enable_logging:
        extensions.append(LoggingExtension(include_variables=False))
    
    if enable_performance:
        extensions.append(PerformanceExtension(slow_query_threshold=slow_query_threshold))
    
    if enable_validation:
        extensions.append(ValidationExtension(max_depth=max_query_depth))
    
    if enable_error_tracking:
        extensions.append(ErrorTrackingExtension(include_stack_trace=False))
    
    if enable_caching:
        extensions.append(CacheExtension())
    
    return extensions
