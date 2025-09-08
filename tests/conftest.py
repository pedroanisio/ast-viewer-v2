"""
Pytest configuration and shared fixtures for AST Viewer tests.
==============================================================

This file provides shared test configuration, fixtures, and utilities
for all test modules in the AST Viewer project.
"""

import pytest
import asyncio
import os
import tempfile
import shutil
from typing import Dict, Any, Generator, Optional
from unittest.mock import Mock, patch
from datetime import datetime
import uuid

# Test environment setup
os.environ["TESTING"] = "true"
os.environ["NEO4J_URI"] = "bolt://localhost:7687"
os.environ["NEO4J_USERNAME"] = "neo4j"
os.environ["NEO4J_PASSWORD"] = "test"
os.environ["POSTGRES_HOST"] = "localhost"
os.environ["POSTGRES_DB"] = "ast_viewer_test"
os.environ["REDIS_URL"] = "redis://localhost:6379/15"  # Test DB


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def test_config():
    """Test configuration settings."""
    return {
        "neo4j": {
            "uri": "bolt://localhost:7687",
            "username": "neo4j",
            "password": "test",
            "database": "ast_viewer_test"
        },
        "postgres": {
            "host": "localhost",
            "port": 5432,
            "database": "ast_viewer_test",
            "username": "test_user",
            "password": "test_pass"
        },
        "redis": {
            "url": "redis://localhost:6379/15"
        },
        "test_data": {
            "max_symbols": 1000,
            "max_files": 100,
            "batch_size": 50
        }
    }


@pytest.fixture
def temp_directory():
    """Create a temporary directory for test files."""
    temp_dir = tempfile.mkdtemp(prefix="ast_viewer_test_")
    yield temp_dir
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def sample_project_id():
    """Generate a unique project ID for testing."""
    return f"test_project_{uuid.uuid4().hex[:8]}"


@pytest.fixture
def sample_symbol_id():
    """Generate a unique symbol ID for testing."""
    return f"test_symbol_{uuid.uuid4().hex[:8]}"


@pytest.fixture
def mock_neo4j_client():
    """Mock Neo4j client for unit testing."""
    from src.ast_viewer.database.neo4j_client import Neo4jClient
    
    client = Neo4jClient()
    client._connected = True
    client.driver = Mock()
    
    # Mock common methods
    client.execute_query = Mock(return_value=[])
    client.execute_transaction = Mock(return_value=True)
    client.test_connection = Mock(return_value=True)
    
    return client


@pytest.fixture
def mock_postgres_client():
    """Mock PostgreSQL client for unit testing."""
    from src.ast_viewer.database.postgres_client import PostgresClient
    
    client = PostgresClient()
    client._connected = True
    client.engine = Mock()
    
    # Mock common async methods
    async def mock_execute(*args, **kwargs):
        return []
    
    client.execute_query = Mock(side_effect=mock_execute)
    client.get_project_by_id = Mock(side_effect=mock_execute)
    
    return client


@pytest.fixture
def neo4j_test_session():
    """
    Real Neo4j session for integration testing.
    
    Requires actual Neo4j instance running for integration tests.
    Use with pytest markers: @pytest.mark.integration
    """
    try:
        from src.ast_viewer.database.neo4j_client import Neo4jClient
        
        client = Neo4jClient(
            uri=os.getenv("NEO4J_URI", "bolt://localhost:7687"),
            username=os.getenv("NEO4J_USERNAME", "neo4j"),
            password=os.getenv("NEO4J_PASSWORD", "test")
        )
        
        if client.connect():
            # Create test database constraints and indexes
            setup_test_database(client)
            yield client
            # Cleanup test data
            cleanup_test_database(client)
            client.disconnect()
        else:
            pytest.skip("Neo4j not available for integration testing")
            
    except ImportError:
        pytest.skip("Neo4j client not available")


def setup_test_database(client):
    """Set up test database with constraints and indexes."""
    setup_queries = [
        # Constraints
        "CREATE CONSTRAINT project_id IF NOT EXISTS FOR (p:Project) REQUIRE p.id IS UNIQUE",
        "CREATE CONSTRAINT symbol_id IF NOT EXISTS FOR (s:Symbol) REQUIRE s.id IS UNIQUE",
        "CREATE CONSTRAINT file_path IF NOT EXISTS FOR (f:File) REQUIRE f.path IS UNIQUE",
        
        # Indexes for performance
        "CREATE INDEX project_name_idx IF NOT EXISTS FOR (p:Project) ON (p.name)",
        "CREATE INDEX symbol_name_idx IF NOT EXISTS FOR (s:Symbol) ON (s.name)",
        "CREATE INDEX symbol_type_idx IF NOT EXISTS FOR (s:Symbol) ON (s.type)",
        "CREATE INDEX file_language_idx IF NOT EXISTS FOR (f:File) ON (f.language)",
    ]
    
    for query in setup_queries:
        try:
            client.execute_query(query)
        except Exception as e:
            # Constraint/index might already exist
            print(f"Setup query warning: {e}")


def cleanup_test_database(client):
    """Clean up test data from database."""
    cleanup_queries = [
        "MATCH (n:Project) WHERE n.id STARTS WITH 'test_' DETACH DELETE n",
        "MATCH (n:Symbol) WHERE n.id STARTS WITH 'test_' DETACH DELETE n",
        "MATCH (n:File) WHERE n.path STARTS WITH '/test' DETACH DELETE n",
    ]
    
    for query in cleanup_queries:
        try:
            client.execute_query(query)
        except Exception as e:
            print(f"Cleanup warning: {e}")


# Pytest markers for test categorization
def pytest_configure(config):
    """Configure custom pytest markers."""
    config.addinivalue_line(
        "markers", "unit: mark test as a unit test"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test (requires real database)"
    )
    config.addinivalue_line(
        "markers", "performance: mark test as a performance test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )


# Test data factories
class TestDataFactory:
    """Factory for creating consistent test data."""
    
    @staticmethod
    def create_project_data(project_id: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        """Create sample project data."""
        base_data = {
            "id": project_id or f"test_project_{uuid.uuid4().hex[:8]}",
            "name": "Test Project",
            "description": "A test project for TDD",
            "created_at": datetime.now().isoformat(),
            "language": "python",
            "repository_url": "https://github.com/test/repo",
            "status": "active"
        }
        base_data.update(kwargs)
        return base_data
    
    @staticmethod
    def create_symbol_data(symbol_id: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        """Create sample symbol data."""
        base_data = {
            "id": symbol_id or f"test_symbol_{uuid.uuid4().hex[:8]}",
            "name": "test_function",
            "type": "function",
            "language": "python",
            "file_path": "/test/module.py",
            "start_line": 10,
            "end_line": 20,
            "start_column": 0,
            "end_column": 10,
            "complexity": 3.5,
            "lines_of_code": 10,
            "created_at": datetime.now().isoformat()
        }
        base_data.update(kwargs)
        return base_data
    
    @staticmethod
    def create_relationship_data(rel_id: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        """Create sample relationship data."""
        base_data = {
            "id": rel_id or f"test_rel_{uuid.uuid4().hex[:8]}",
            "from_symbol_id": f"test_symbol_1_{uuid.uuid4().hex[:8]}",
            "to_symbol_id": f"test_symbol_2_{uuid.uuid4().hex[:8]}",
            "type": "CALLS",
            "file_path": "/test/module.py",
            "line": 15,
            "column": 8,
            "context": "function call",
            "created_at": datetime.now().isoformat()
        }
        base_data.update(kwargs)
        return base_data
    
    @staticmethod
    def create_file_data(file_path: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        """Create sample file data."""
        base_data = {
            "path": file_path or f"/test/module_{uuid.uuid4().hex[:8]}.py",
            "language": "python",
            "size": 1024,
            "lines_of_code": 50,
            "complexity": 5.0,
            "last_modified": datetime.now().isoformat(),
            "encoding": "utf-8"
        }
        base_data.update(kwargs)
        return base_data


@pytest.fixture
def test_data_factory():
    """Provide test data factory for creating consistent test data."""
    return TestDataFactory


# Performance testing utilities
@pytest.fixture
def performance_timer():
    """Timer utility for performance testing."""
    import time
    
    class Timer:
        def __init__(self):
            self.start_time = None
            self.end_time = None
        
        def start(self):
            self.start_time = time.time()
        
        def stop(self):
            self.end_time = time.time()
        
        @property
        def elapsed(self):
            if self.start_time and self.end_time:
                return self.end_time - self.start_time
            return None
    
    return Timer()


# Async testing utilities
@pytest.fixture
def async_test_client():
    """Async test client for testing async operations."""
    import asyncio
    
    class AsyncTestClient:
        def __init__(self):
            self.loop = asyncio.get_event_loop()
        
        def run(self, coro):
            """Run async coroutine in test."""
            return self.loop.run_until_complete(coro)
    
    return AsyncTestClient()


# Mock data for complex testing scenarios
@pytest.fixture
def large_dataset():
    """Generate large dataset for performance testing."""
    factory = TestDataFactory()
    
    return {
        "projects": [factory.create_project_data() for _ in range(10)],
        "symbols": [factory.create_symbol_data() for _ in range(1000)],
        "relationships": [factory.create_relationship_data() for _ in range(2000)],
        "files": [factory.create_file_data() for _ in range(100)]
    }


# Error simulation utilities
@pytest.fixture
def error_simulator():
    """Utility for simulating various error conditions."""
    
    class ErrorSimulator:
        @staticmethod
        def connection_error():
            return ConnectionError("Failed to connect to database")
        
        @staticmethod
        def timeout_error():
            return TimeoutError("Operation timed out")
        
        @staticmethod
        def authentication_error():
            return Exception("Authentication failed")
        
        @staticmethod
        def invalid_query_error():
            return Exception("Invalid Cypher syntax")
    
    return ErrorSimulator
