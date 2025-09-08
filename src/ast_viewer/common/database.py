"""Base database client class to eliminate duplication across database adapters.

This module provides the BaseDataClient abstract class that contains all the common
connection management patterns that were duplicated between Neo4jClient and PostgresClient.

DRY Fix: Eliminates ~200+ lines of duplicated connection management code.
"""

import logging
import os
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, Union
from datetime import datetime

logger = logging.getLogger(__name__)


class BaseDataClient(ABC):
    """Abstract base class for database clients to eliminate connection pattern duplication.
    
    This class contains all the common connection management logic that was previously
    duplicated between Neo4jClient and PostgresClient.
    """
    
    def __init__(self, connection_string: Optional[str] = None, 
                 username: Optional[str] = None, 
                 password: Optional[str] = None,
                 connection_env_var: str = "",
                 username_env_var: str = "",
                 password_env_var: str = "",
                 default_connection: str = ""):
        """Initialize base client with connection parameters.
        
        Args:
            connection_string: Direct connection string
            username: Database username
            password: Database password
            connection_env_var: Environment variable for connection string
            username_env_var: Environment variable for username
            password_env_var: Environment variable for password
            default_connection: Default connection string if none provided
        """
        self.connection_string = connection_string or os.getenv(connection_env_var, default_connection)
        self.username = username or os.getenv(username_env_var, "")
        self.password = password or os.getenv(password_env_var, "")
        
        self._connected = False
        self._connection = None
        self._last_connection_attempt = None
        self._connection_retry_count = 0
        self._max_retries = 3
        
    @abstractmethod
    def _create_connection(self) -> Any:
        """Create the actual database connection. Must be implemented by subclasses."""
        pass
    
    @abstractmethod
    def _test_connection(self) -> bool:
        """Test if the connection is working. Must be implemented by subclasses."""
        pass
    
    @abstractmethod
    def _close_connection(self) -> None:
        """Close the database connection. Must be implemented by subclasses."""
        pass
    
    @property
    @abstractmethod
    def connection_type(self) -> str:
        """Return the type of database connection (e.g., 'Neo4j', 'PostgreSQL')."""
        pass
    
    def connect(self) -> bool:
        """Establish connection to database with retry logic.
        
        This method implements the common connection pattern that was duplicated
        across all database clients.
        """
        if self._connected and self._connection is not None:
            logger.debug(f"Already connected to {self.connection_type}")
            return True
            
        self._last_connection_attempt = datetime.utcnow()
        
        for attempt in range(self._max_retries):
            try:
                logger.info(f"Connecting to {self.connection_type} (attempt {attempt + 1}/{self._max_retries})")
                
                # Create connection using subclass implementation
                self._connection = self._create_connection()
                
                # Test the connection
                if self._test_connection():
                    self._connected = True
                    self._connection_retry_count = 0
                    logger.info(f"Successfully connected to {self.connection_type}")
                    return True
                else:
                    logger.warning(f"Connection test failed for {self.connection_type}")
                    
            except Exception as e:
                logger.error(f"Connection attempt {attempt + 1} failed for {self.connection_type}: {e}")
                self._connection_retry_count += 1
                
                if attempt < self._max_retries - 1:
                    # Wait before retry (exponential backoff)
                    import time
                    wait_time = 2 ** attempt
                    logger.info(f"Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
        
        logger.error(f"Failed to connect to {self.connection_type} after {self._max_retries} attempts")
        self._connected = False
        return False
    
    def disconnect(self) -> None:
        """Disconnect from database.
        
        This method implements the common disconnection pattern.
        """
        if self._connected and self._connection is not None:
            try:
                self._close_connection()
                logger.info(f"Disconnected from {self.connection_type}")
            except Exception as e:
                logger.error(f"Error disconnecting from {self.connection_type}: {e}")
            finally:
                self._connected = False
                self._connection = None
    
    def is_connected(self) -> bool:
        """Check if connected to database.
        
        This method was duplicated across all clients with identical logic.
        """
        return self._connected and self._connection is not None
    
    def ensure_connection(self) -> bool:
        """Ensure we have a valid connection.
        
        This method was duplicated across all clients with identical logic.
        """
        if not self.is_connected():
            return self.connect()
        return True
    
    def get_connection_info(self) -> Dict[str, Any]:
        """Get connection information for debugging."""
        return {
            "type": self.connection_type,
            "connected": self._connected,
            "connection_string": self.connection_string,
            "last_attempt": self._last_connection_attempt,
            "retry_count": self._connection_retry_count,
            "max_retries": self._max_retries
        }
    
    def health_check(self) -> Dict[str, Any]:
        """Perform health check on the database connection."""
        start_time = datetime.utcnow()
        
        try:
            if not self.is_connected():
                return {
                    "status": "disconnected",
                    "type": self.connection_type,
                    "error": "Not connected to database"
                }
            
            # Test the connection
            if self._test_connection():
                duration = (datetime.utcnow() - start_time).total_seconds()
                return {
                    "status": "healthy",
                    "type": self.connection_type,
                    "response_time_ms": duration * 1000,
                    "connected": True
                }
            else:
                return {
                    "status": "unhealthy",
                    "type": self.connection_type,
                    "error": "Connection test failed"
                }
                
        except Exception as e:
            return {
                "status": "error",
                "type": self.connection_type,
                "error": str(e)
            }
    
    def __enter__(self):
        """Context manager entry."""
        if not self.ensure_connection():
            raise ConnectionError(f"Cannot connect to {self.connection_type}")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        # Don't automatically disconnect to allow connection pooling
        pass
    
    def __del__(self):
        """Destructor to ensure cleanup."""
        try:
            self.disconnect()
        except:
            pass  # Ignore errors during cleanup
