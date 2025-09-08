"""Middleware for REST API including rate limiting, logging, and validation."""

import asyncio
import logging
import time
import uuid
from typing import Dict, Any, Optional
from collections import defaultdict, deque
from datetime import datetime, timedelta

from fastapi import Request, Response, HTTPException, status
from fastapi.middleware.base import BaseHTTPMiddleware
from starlette.middleware.base import RequestResponseEndpoint

logger = logging.getLogger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for comprehensive request logging."""
    
    def __init__(self, app):
        super().__init__(app)
        self.request_count = 0
        self.total_time = 0.0
    
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        # Generate request ID
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        
        # Start timing
        start_time = time.time()
        
        # Log request
        logger.info(
            f"[{request_id}] {request.method} {request.url.path} "
            f"from {request.client.host if request.client else 'unknown'}"
        )
        
        # Add request ID to headers
        response = await call_next(request)
        
        # Calculate timing
        process_time = time.time() - start_time
        self.request_count += 1
        self.total_time += process_time
        
        # Add response headers
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Process-Time"] = str(round(process_time, 4))
        
        # Log response
        logger.info(
            f"[{request_id}] Response: {response.status_code} "
            f"({process_time:.4f}s)"
        )
        
        # Log slow requests
        if process_time > 2.0:
            logger.warning(
                f"[{request_id}] Slow request: {request.method} {request.url.path} "
                f"took {process_time:.4f}s"
            )
        
        return response


class RateLimitingMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware with token bucket algorithm."""
    
    def __init__(self, app, requests_per_minute: int = 100, requests_per_hour: int = 1000):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.requests_per_hour = requests_per_hour
        
        # Track requests per IP
        self.minute_buckets: Dict[str, deque] = defaultdict(deque)
        self.hour_buckets: Dict[str, deque] = defaultdict(deque)
        
        # Cleanup old entries periodically
        self.last_cleanup = time.time()
        self.cleanup_interval = 300  # 5 minutes
    
    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP address."""
        # Check for forwarded header first (for proxy scenarios)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        # Check for real IP header
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        # Fall back to direct client IP
        return request.client.host if request.client else "unknown"
    
    def _cleanup_old_entries(self):
        """Remove old entries from buckets."""
        current_time = time.time()
        
        # Only cleanup periodically to avoid overhead
        if current_time - self.last_cleanup < self.cleanup_interval:
            return
        
        minute_cutoff = current_time - 60
        hour_cutoff = current_time - 3600
        
        # Cleanup minute buckets
        for ip, bucket in list(self.minute_buckets.items()):
            while bucket and bucket[0] < minute_cutoff:
                bucket.popleft()
            if not bucket:
                del self.minute_buckets[ip]
        
        # Cleanup hour buckets
        for ip, bucket in list(self.hour_buckets.items()):
            while bucket and bucket[0] < hour_cutoff:
                bucket.popleft()
            if not bucket:
                del self.hour_buckets[ip]
        
        self.last_cleanup = current_time
    
    def _is_rate_limited(self, ip: str) -> tuple[bool, Optional[str]]:
        """Check if IP is rate limited."""
        current_time = time.time()
        
        # Clean up old entries
        self._cleanup_old_entries()
        
        # Check minute limit
        minute_bucket = self.minute_buckets[ip]
        minute_cutoff = current_time - 60
        
        # Remove old entries from minute bucket
        while minute_bucket and minute_bucket[0] < minute_cutoff:
            minute_bucket.popleft()
        
        if len(minute_bucket) >= self.requests_per_minute:
            return True, "Rate limit exceeded: too many requests per minute"
        
        # Check hour limit
        hour_bucket = self.hour_buckets[ip]
        hour_cutoff = current_time - 3600
        
        # Remove old entries from hour bucket
        while hour_bucket and hour_bucket[0] < hour_cutoff:
            hour_bucket.popleft()
        
        if len(hour_bucket) >= self.requests_per_hour:
            return True, "Rate limit exceeded: too many requests per hour"
        
        return False, None
    
    def _record_request(self, ip: str):
        """Record a request for rate limiting."""
        current_time = time.time()
        self.minute_buckets[ip].append(current_time)
        self.hour_buckets[ip].append(current_time)
    
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        # Skip rate limiting for health checks
        if request.url.path in ["/health", "/api/v1/health"]:
            return await call_next(request)
        
        # Get client IP
        client_ip = self._get_client_ip(request)
        
        # Check rate limits
        is_limited, limit_message = self._is_rate_limited(client_ip)
        
        if is_limited:
            logger.warning(f"Rate limit exceeded for IP {client_ip}: {limit_message}")
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={
                    "error": "Rate limit exceeded",
                    "message": limit_message,
                    "retry_after": 60,  # seconds
                    "limits": {
                        "per_minute": self.requests_per_minute,
                        "per_hour": self.requests_per_hour
                    }
                }
            )
        
        # Record the request
        self._record_request(client_ip)
        
        # Add rate limit headers to response
        response = await call_next(request)
        
        # Add rate limit info to headers
        minute_remaining = max(0, self.requests_per_minute - len(self.minute_buckets[client_ip]))
        hour_remaining = max(0, self.requests_per_hour - len(self.hour_buckets[client_ip]))
        
        response.headers["X-RateLimit-Limit-Minute"] = str(self.requests_per_minute)
        response.headers["X-RateLimit-Remaining-Minute"] = str(minute_remaining)
        response.headers["X-RateLimit-Limit-Hour"] = str(self.requests_per_hour)
        response.headers["X-RateLimit-Remaining-Hour"] = str(hour_remaining)
        
        return response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Middleware for adding security headers."""
    
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        response = await call_next(request)
        
        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        
        # Add CSP header for HTML responses
        if "text/html" in response.headers.get("content-type", ""):
            response.headers["Content-Security-Policy"] = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' 'unsafe-eval' cdn.plot.ly; "
                "style-src 'self' 'unsafe-inline'; "
                "img-src 'self' data:; "
                "connect-src 'self'"
            )
        
        return response


class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """Middleware for standardized error handling."""
    
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        try:
            response = await call_next(request)
            return response
            
        except HTTPException:
            # Re-raise HTTP exceptions (they're handled by FastAPI)
            raise
            
        except asyncio.TimeoutError:
            logger.error(f"Request timeout for {request.url.path}")
            raise HTTPException(
                status_code=status.HTTP_408_REQUEST_TIMEOUT,
                detail={
                    "error": "Request timeout",
                    "message": "The request took too long to process"
                }
            )
            
        except Exception as e:
            # Log unexpected errors
            request_id = getattr(request.state, 'request_id', 'unknown')
            logger.exception(f"[{request_id}] Unexpected error: {e}")
            
            # Return generic error response
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "error": "Internal server error",
                    "message": "An unexpected error occurred",
                    "request_id": request_id
                }
            )


class MetricsMiddleware(BaseHTTPMiddleware):
    """Middleware for collecting API metrics."""
    
    def __init__(self, app):
        super().__init__(app)
        self.metrics = {
            "total_requests": 0,
            "total_errors": 0,
            "endpoint_stats": defaultdict(lambda: {
                "count": 0,
                "total_time": 0.0,
                "errors": 0
            }),
            "status_codes": defaultdict(int),
            "start_time": datetime.now()
        }
    
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        start_time = time.time()
        
        # Extract endpoint path (normalize with path parameters)
        endpoint = request.url.path
        for route in request.app.routes:
            match, _ = route.matches({"type": "http", "path": endpoint, "method": request.method})
            if match.name in ["full_match", "partial_match"]:
                endpoint = route.path
                break
        
        try:
            response = await call_next(request)
            
            # Record metrics
            process_time = time.time() - start_time
            self.metrics["total_requests"] += 1
            self.metrics["status_codes"][response.status_code] += 1
            
            endpoint_stats = self.metrics["endpoint_stats"][f"{request.method} {endpoint}"]
            endpoint_stats["count"] += 1
            endpoint_stats["total_time"] += process_time
            
            if response.status_code >= 400:
                self.metrics["total_errors"] += 1
                endpoint_stats["errors"] += 1
            
            return response
            
        except Exception as e:
            # Record error metrics
            self.metrics["total_requests"] += 1
            self.metrics["total_errors"] += 1
            self.metrics["status_codes"][500] += 1
            
            endpoint_stats = self.metrics["endpoint_stats"][f"{request.method} {endpoint}"]
            endpoint_stats["count"] += 1
            endpoint_stats["errors"] += 1
            
            raise
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get current metrics."""
        uptime = datetime.now() - self.metrics["start_time"]
        
        # Calculate averages
        endpoint_metrics = {}
        for endpoint, stats in self.metrics["endpoint_stats"].items():
            avg_time = stats["total_time"] / stats["count"] if stats["count"] > 0 else 0
            error_rate = stats["errors"] / stats["count"] if stats["count"] > 0 else 0
            
            endpoint_metrics[endpoint] = {
                "requests": stats["count"],
                "average_time": round(avg_time, 4),
                "error_rate": round(error_rate, 4),
                "total_errors": stats["errors"]
            }
        
        return {
            "uptime_seconds": int(uptime.total_seconds()),
            "total_requests": self.metrics["total_requests"],
            "total_errors": self.metrics["total_errors"],
            "error_rate": round(self.metrics["total_errors"] / max(1, self.metrics["total_requests"]), 4),
            "status_codes": dict(self.metrics["status_codes"]),
            "endpoints": endpoint_metrics
        }


# Global metrics instance for access
metrics_middleware_instance = None


def get_metrics() -> Dict[str, Any]:
    """Get current API metrics."""
    if metrics_middleware_instance:
        return metrics_middleware_instance.get_metrics()
    return {"error": "Metrics not available"}


# Export all middleware classes
__all__ = [
    "RequestLoggingMiddleware",
    "RateLimitingMiddleware", 
    "SecurityHeadersMiddleware",
    "ErrorHandlingMiddleware",
    "MetricsMiddleware",
    "get_metrics"
]
