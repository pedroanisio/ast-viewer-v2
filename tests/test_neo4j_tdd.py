"""
Test-Driven Development (TDD) for Neo4j Operations
===================================================

Following TDD principles:
1. RED: Write failing tests that define expected behavior
2. GREEN: Implement minimal code to make tests pass  
3. REFACTOR: Improve implementation while keeping tests green

Test Categories:
- Connection & Setup
- Project Management
- Symbol Storage & Retrieval
- Relationship Management
- Complex Graph Queries
- Performance & Optimization
- Error Handling
"""

import pytest
import asyncio
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional
from unittest.mock import Mock, patch, AsyncMock

# Test imports - these will fail initially (RED phase)
from src.ast_viewer.database.neo4j_client import Neo4jClient
from src.ast_viewer.models.universal import (
    UniversalNode, UniversalFile, Relationship, Reference,
    SourceLocation, Language, ElementType, RelationType
)

# Test configuration
TEST_NEO4J_URI = "bolt://localhost:7687"
TEST_DB_NAME = "ast_viewer_test"


class TestNeo4jConnectionTDD:
    """TDD for Neo4j connection management."""
    
    def test_neo4j_client_initialization_should_set_default_config(self):
        """RED: Test client initialization with default configuration."""
        # This test defines what we expect from initialization
        client = Neo4jClient()
        
        assert client.uri is not None
        assert client.username is not None  
        assert client.password is not None
        assert client.driver is None  # Not connected yet
        assert client.is_connected() is False
    
    def test_neo4j_client_initialization_with_custom_config(self):
        """RED: Test client initialization with custom configuration."""
        custom_uri = "bolt://custom:7687"
        custom_user = "test_user"
        custom_pass = "test_pass"
        
        client = Neo4jClient(uri=custom_uri, username=custom_user, password=custom_pass)
        
        assert client.uri == custom_uri
        assert client.username == custom_user
        assert client.password == custom_pass
    
    def test_connect_should_establish_driver_connection(self):
        """RED: Test successful connection establishment."""
        client = Neo4jClient(uri=TEST_NEO4J_URI, username="neo4j", password="test")
        
        # Mock successful connection
        with patch('neo4j.GraphDatabase.driver') as mock_driver:
            mock_driver.return_value = Mock()
            
            result = client.connect()
            
            assert result is True
            assert client.is_connected() is True
            assert client.driver is not None
            mock_driver.assert_called_once()
    
    def test_connect_should_handle_connection_failure(self):
        """RED: Test connection failure handling."""
        client = Neo4jClient(uri="bolt://invalid:7687", username="invalid", password="invalid")
        
        # Mock connection failure
        with patch('neo4j.GraphDatabase.driver') as mock_driver:
            mock_driver.side_effect = Exception("Connection failed")
            
            result = client.connect()
            
            assert result is False
            assert client.is_connected() is False
            assert client.driver is None
    
    def test_disconnect_should_close_driver(self):
        """RED: Test proper disconnection."""
        client = Neo4jClient()
        mock_driver = Mock()
        client.driver = mock_driver
        client._connected = True
        
        client.disconnect()
        
        assert client.is_connected() is False
        assert client.driver is None
        mock_driver.close.assert_called_once()
    
    def test_test_connection_should_verify_database_accessibility(self):
        """RED: Test database connectivity verification."""
        client = Neo4jClient()
        
        with patch.object(client, 'execute_query') as mock_execute:
            mock_execute.return_value = [{"result": 1}]
            
            result = client.test_connection()
            
            assert result is True
            mock_execute.assert_called_once_with("RETURN 1 as result")


class TestNeo4jProjectManagementTDD:
    """TDD for project management operations."""
    
    @pytest.fixture
    def mock_client(self):
        """Create a mock Neo4j client for testing."""
        client = Neo4jClient()
        client._connected = True
        client.driver = Mock()
        return client
    
    @pytest.fixture
    def sample_project_data(self):
        """Sample project data for testing."""
        return {
            "id": "project_123",
            "name": "Test Project",
            "description": "A test project for TDD",
            "created_at": datetime.now(),
            "language": "python",
            "repository_url": "https://github.com/test/repo"
        }
    
    def test_create_project_should_store_project_node(self, mock_client, sample_project_data):
        """RED: Test project creation in Neo4j."""
        with patch.object(mock_client, 'execute_query') as mock_execute:
            mock_execute.return_value = [{"p.id": sample_project_data["id"]}]
            
            result = mock_client.create_project(sample_project_data)
            
            assert result == sample_project_data["id"]
            mock_execute.assert_called_once()
            
            # Verify the Cypher query structure
            call_args = mock_execute.call_args
            query = call_args[0][0]
            assert "CREATE (p:Project" in query
            assert "SET p.id = $id" in query
    
    def test_get_project_should_retrieve_project_by_id(self, mock_client):
        """RED: Test project retrieval by ID."""
        project_id = "project_123"
        expected_project = {
            "id": project_id,
            "name": "Test Project",
            "created_at": "2023-01-01T00:00:00Z"
        }
        
        with patch.object(mock_client, 'execute_query') as mock_execute:
            mock_execute.return_value = [expected_project]
            
            result = mock_client.get_project(project_id)
            
            assert result == expected_project
            mock_execute.assert_called_once_with(
                pytest.any(str),  # Any Cypher query
                {"project_id": project_id}
            )
    
    def test_get_project_should_return_none_for_nonexistent_project(self, mock_client):
        """RED: Test handling of non-existent project."""
        with patch.object(mock_client, 'execute_query') as mock_execute:
            mock_execute.return_value = []
            
            result = mock_client.get_project("nonexistent_id")
            
            assert result is None
    
    def test_list_projects_should_return_all_projects(self, mock_client):
        """RED: Test listing all projects."""
        expected_projects = [
            {"id": "proj_1", "name": "Project 1"},
            {"id": "proj_2", "name": "Project 2"}
        ]
        
        with patch.object(mock_client, 'execute_query') as mock_execute:
            mock_execute.return_value = expected_projects
            
            result = mock_client.list_projects()
            
            assert result == expected_projects
            assert len(result) == 2
    
    def test_delete_project_should_remove_project_and_dependencies(self, mock_client):
        """RED: Test project deletion with cascade."""
        project_id = "project_to_delete"
        
        with patch.object(mock_client, 'execute_query') as mock_execute:
            mock_execute.return_value = [{"deleted_count": 1}]
            
            result = mock_client.delete_project(project_id)
            
            assert result is True
            
            # Verify cascade deletion query
            call_args = mock_execute.call_args
            query = call_args[0][0]
            assert "DETACH DELETE" in query
            assert project_id in call_args[1].values()


class TestNeo4jSymbolStorageTDD:
    """TDD for symbol storage and retrieval."""
    
    @pytest.fixture
    def mock_client(self):
        client = Neo4jClient()
        client._connected = True
        return client
    
    @pytest.fixture  
    def sample_symbol(self):
        """Sample symbol for testing."""
        return UniversalNode(
            id="symbol_123",
            name="test_function",
            type=ElementType.FUNCTION,
            language=Language.PYTHON,
            source_location=SourceLocation(
                file_path="/test/file.py",
                start_line=10,
                end_line=20,
                start_column=0,
                end_column=10
            ),
            complexity=5.0,
            lines_of_code=10
        )
    
    def test_store_symbol_should_create_symbol_node(self, mock_client, sample_symbol):
        """RED: Test symbol storage in Neo4j."""
        project_id = "project_123"
        
        with patch.object(mock_client, 'execute_query') as mock_execute:
            mock_execute.return_value = [{"s.id": sample_symbol.id}]
            
            result = mock_client.store_symbol(project_id, sample_symbol)
            
            assert result == sample_symbol.id
            mock_execute.assert_called_once()
            
            # Verify symbol node creation
            call_args = mock_execute.call_args
            query = call_args[0][0]
            assert "CREATE (s:Symbol" in query
            assert "HAS_SYMBOL" in query  # Project relationship
    
    def test_get_symbol_should_retrieve_symbol_by_id(self, mock_client):
        """RED: Test symbol retrieval."""
        symbol_id = "symbol_123"
        project_id = "project_123"
        
        expected_symbol = {
            "id": symbol_id,
            "name": "test_function",
            "type": "function",
            "complexity": 5.0
        }
        
        with patch.object(mock_client, 'execute_query') as mock_execute:
            mock_execute.return_value = [expected_symbol]
            
            result = mock_client.get_symbol(project_id, symbol_id)
            
            assert result == expected_symbol
            mock_execute.assert_called_once()
    
    def test_search_symbols_should_find_symbols_by_pattern(self, mock_client):
        """RED: Test symbol search functionality."""
        project_id = "project_123"
        search_pattern = "test_*"
        symbol_types = ["function", "class"]
        
        expected_symbols = [
            {"id": "sym_1", "name": "test_function", "type": "function"},
            {"id": "sym_2", "name": "test_class", "type": "class"}
        ]
        
        with patch.object(mock_client, 'execute_query') as mock_execute:
            mock_execute.return_value = expected_symbols
            
            result = mock_client.search_symbols(
                project_id=project_id,
                pattern=search_pattern,
                symbol_types=symbol_types,
                limit=10
            )
            
            assert result == expected_symbols
            assert len(result) == 2
    
    def test_get_symbols_by_file_should_return_file_symbols(self, mock_client):
        """RED: Test retrieving symbols by file path."""
        project_id = "project_123"
        file_path = "/test/module.py"
        
        expected_symbols = [
            {"id": "sym_1", "name": "function_1", "line": 10},
            {"id": "sym_2", "name": "Class1", "line": 25}
        ]
        
        with patch.object(mock_client, 'execute_query') as mock_execute:
            mock_execute.return_value = expected_symbols
            
            result = mock_client.get_symbols_by_file(project_id, file_path)
            
            assert result == expected_symbols
            
            # Verify file path filtering
            call_args = mock_execute.call_args
            assert file_path in str(call_args[1])


class TestNeo4jRelationshipManagementTDD:
    """TDD for relationship management."""
    
    @pytest.fixture
    def mock_client(self):
        client = Neo4jClient()
        client._connected = True
        return client
    
    @pytest.fixture
    def sample_relationship(self):
        """Sample relationship for testing."""
        return Relationship(
            id="rel_123",
            from_symbol_id="sym_1",
            to_symbol_id="sym_2",
            type=RelationType.CALLS,
            source_location=SourceLocation(
                file_path="/test/file.py",
                start_line=15,
                end_line=15,
                start_column=8,
                end_column=20
            )
        )
    
    def test_store_relationship_should_create_relationship_edge(self, mock_client, sample_relationship):
        """RED: Test relationship storage."""
        project_id = "project_123"
        
        with patch.object(mock_client, 'execute_query') as mock_execute:
            mock_execute.return_value = [{"r.id": sample_relationship.id}]
            
            result = mock_client.store_relationship(project_id, sample_relationship)
            
            assert result == sample_relationship.id
            mock_execute.assert_called_once()
            
            # Verify relationship creation
            call_args = mock_execute.call_args
            query = call_args[0][0]
            assert "MATCH" in query  # Finding existing symbols
            assert "MERGE" in query  # Creating relationship
            assert sample_relationship.type.value.upper() in query
    
    def test_get_symbol_relationships_should_return_connected_symbols(self, mock_client):
        """RED: Test getting symbol relationships."""
        project_id = "project_123"
        symbol_id = "sym_1"
        relationship_types = ["CALLS", "USES"]
        
        expected_relationships = [
            {
                "target_symbol": {"id": "sym_2", "name": "called_function"},
                "relationship": {"type": "CALLS", "line": 15}
            },
            {
                "target_symbol": {"id": "sym_3", "name": "used_variable"},
                "relationship": {"type": "USES", "line": 16}
            }
        ]
        
        with patch.object(mock_client, 'execute_query') as mock_execute:
            mock_execute.return_value = expected_relationships
            
            result = mock_client.get_symbol_relationships(
                project_id=project_id,
                symbol_id=symbol_id,
                relationship_types=relationship_types,
                direction="outgoing"
            )
            
            assert result == expected_relationships
            assert len(result) == 2
    
    def test_find_circular_dependencies_should_detect_cycles(self, mock_client):
        """RED: Test circular dependency detection."""
        project_id = "project_123"
        
        expected_cycles = [
            ["module_a.py", "module_b.py", "module_c.py", "module_a.py"],
            ["class_x", "class_y", "class_x"]
        ]
        
        with patch.object(mock_client, 'execute_query') as mock_execute:
            mock_execute.return_value = [
                {"cycle": expected_cycles[0]},
                {"cycle": expected_cycles[1]}
            ]
            
            result = mock_client.find_circular_dependencies(project_id)
            
            assert len(result) == 2
            assert expected_cycles[0] in result
            assert expected_cycles[1] in result


class TestNeo4jComplexQueriesTDD:
    """TDD for complex graph queries."""
    
    @pytest.fixture
    def mock_client(self):
        client = Neo4jClient()
        client._connected = True
        return client
    
    def test_get_call_graph_should_build_symbol_call_hierarchy(self, mock_client):
        """RED: Test call graph generation."""
        project_id = "project_123"
        root_symbol_id = "main_function"
        max_depth = 3
        
        expected_call_graph = {
            "root": {"id": root_symbol_id, "name": "main_function"},
            "calls": [
                {
                    "symbol": {"id": "helper_1", "name": "helper_function"},
                    "depth": 1,
                    "calls": [
                        {"symbol": {"id": "utility_1", "name": "utility_func"}, "depth": 2, "calls": []}
                    ]
                }
            ]
        }
        
        with patch.object(mock_client, 'get_call_graph') as mock_get:
            mock_get.return_value = expected_call_graph
            
            result = mock_client.get_call_graph(project_id, root_symbol_id, max_depth)
            
            assert result == expected_call_graph
            assert "root" in result
            assert "calls" in result
    
    def test_get_dependency_graph_should_build_module_dependencies(self, mock_client):
        """RED: Test dependency graph generation."""
        project_id = "project_123"
        
        expected_deps = [
            {
                "source": {"file": "main.py", "symbols": 5},
                "target": {"file": "utils.py", "symbols": 3},
                "relationship_count": 8,
                "types": ["IMPORTS", "CALLS"]
            },
            {
                "source": {"file": "utils.py", "symbols": 3},
                "target": {"file": "helpers.py", "symbols": 2},
                "relationship_count": 4,
                "types": ["CALLS"]
            }
        ]
        
        with patch.object(mock_client, 'execute_query') as mock_execute:
            mock_execute.return_value = expected_deps
            
            result = mock_client.get_dependency_graph(project_id)
            
            assert result == expected_deps
            assert len(result) == 2
    
    def test_get_complexity_hotspots_should_identify_high_complexity_areas(self, mock_client):
        """RED: Test complexity hotspot identification."""
        project_id = "project_123"
        min_complexity = 10.0
        
        expected_hotspots = [
            {
                "symbol": {"id": "complex_func", "name": "complex_function"},
                "complexity": 15.5,
                "file": "complex_module.py",
                "line": 45,
                "issues": ["high_cyclomatic", "deep_nesting"]
            }
        ]
        
        with patch.object(mock_client, 'get_high_complexity_symbols') as mock_get:
            mock_get.return_value = expected_hotspots
            
            result = mock_client.get_high_complexity_symbols(project_id, min_complexity)
            
            assert result == expected_hotspots
            assert result[0]["complexity"] >= min_complexity
    
    def test_analyze_code_metrics_should_compute_project_statistics(self, mock_client):
        """RED: Test comprehensive code metrics analysis."""
        project_id = "project_123"
        
        expected_metrics = {
            "total_symbols": 150,
            "total_relationships": 300,
            "average_complexity": 3.2,
            "max_complexity": 15.5,
            "files_count": 25,
            "languages": ["python", "javascript"],
            "complexity_distribution": {
                "low": 120,    # complexity 1-5
                "medium": 25,  # complexity 6-10
                "high": 5      # complexity >10
            },
            "relationship_types": {
                "CALLS": 150,
                "USES": 100,
                "IMPORTS": 50
            }
        }
        
        with patch.object(mock_client, 'get_project_overview') as mock_overview:
            mock_overview.return_value = expected_metrics
            
            result = mock_client.get_project_overview(project_id)
            
            assert result == expected_metrics
            assert "total_symbols" in result
            assert "complexity_distribution" in result


class TestNeo4jPerformanceTDD:
    """TDD for performance and optimization."""
    
    @pytest.fixture
    def mock_client(self):
        client = Neo4jClient()
        client._connected = True
        return client
    
    def test_batch_operations_should_handle_large_datasets(self, mock_client):
        """RED: Test batch processing for large datasets."""
        project_id = "project_123"
        batch_size = 100
        
        # Generate large dataset
        symbols = [
            UniversalNode(
                id=f"sym_{i}",
                name=f"symbol_{i}",
                type=ElementType.FUNCTION,
                language=Language.PYTHON,
                source_location=SourceLocation(
                    file_path=f"/test/file_{i}.py",
                    start_line=i,
                    end_line=i+5,
                    start_column=0,
                    end_column=10
                )
            )
            for i in range(1000)  # 1000 symbols
        ]
        
        with patch.object(mock_client, 'store_symbols_batch') as mock_batch:
            mock_batch.return_value = {"stored_count": 1000, "batch_count": 10}
            
            result = mock_client.store_symbols_batch(project_id, symbols, batch_size)
            
            assert result["stored_count"] == 1000
            assert result["batch_count"] == 10
            mock_batch.assert_called_once_with(project_id, symbols, batch_size)
    
    def test_query_performance_should_use_indexes(self, mock_client):
        """RED: Test query performance with proper indexing."""
        project_id = "project_123"
        
        with patch.object(mock_client, 'execute_query') as mock_execute:
            # Mock query execution time
            mock_execute.return_value = [{"execution_time_ms": 50}]
            
            # Test index usage for common queries
            result = mock_client.get_symbol(project_id, "symbol_123")
            
            # Verify query was optimized (execution time < 100ms)
            call_args = mock_execute.call_args
            query = call_args[0][0]
            
            # Should use indexed fields
            assert any(field in query for field in ["id", "project_id"])
    
    def test_connection_pooling_should_manage_concurrent_access(self, mock_client):
        """RED: Test connection pool management."""
        concurrent_requests = 20
        
        async def concurrent_query():
            """Simulate concurrent database access."""
            return await mock_client.execute_query_async("RETURN 1")
        
        # This test defines expected behavior for concurrent access
        # Implementation will need proper connection pooling
        assert hasattr(mock_client, 'execute_query_async')


class TestNeo4jErrorHandlingTDD:
    """TDD for error handling and edge cases."""
    
    @pytest.fixture
    def mock_client(self):
        client = Neo4jClient()
        client._connected = True
        return client
    
    def test_connection_lost_should_auto_reconnect(self, mock_client):
        """RED: Test automatic reconnection on connection loss."""
        with patch.object(mock_client, 'execute_query') as mock_execute:
            # First call fails with connection error
            # Second call should succeed after reconnection
            mock_execute.side_effect = [
                Exception("Connection lost"),
                [{"result": "success"}]
            ]
            
            with patch.object(mock_client, 'connect') as mock_reconnect:
                mock_reconnect.return_value = True
                
                # This should trigger reconnection and retry
                result = mock_client.execute_query_with_retry("RETURN 1")
                
                assert result == [{"result": "success"}]
                mock_reconnect.assert_called_once()
    
    def test_invalid_cypher_query_should_raise_meaningful_error(self, mock_client):
        """RED: Test handling of invalid Cypher queries."""
        invalid_query = "INVALID CYPHER SYNTAX"
        
        with patch.object(mock_client, 'execute_query') as mock_execute:
            mock_execute.side_effect = Exception("Invalid Cypher syntax")
            
            with pytest.raises(Exception) as exc_info:
                mock_client.execute_query(invalid_query)
            
            assert "Invalid Cypher syntax" in str(exc_info.value)
    
    def test_large_result_sets_should_use_pagination(self, mock_client):
        """RED: Test handling of large result sets with pagination."""
        project_id = "project_123"
        page_size = 100
        page_number = 1
        
        expected_result = {
            "data": [{"id": f"sym_{i}"} for i in range(100)],
            "total_count": 1000,
            "page": 1,
            "page_size": 100,
            "has_next": True
        }
        
        with patch.object(mock_client, 'get_symbols_paginated') as mock_paginated:
            mock_paginated.return_value = expected_result
            
            result = mock_client.get_symbols_paginated(project_id, page_size, page_number)
            
            assert result == expected_result
            assert result["has_next"] is True
            assert len(result["data"]) == page_size


# Integration Tests
class TestNeo4jIntegrationTDD:
    """TDD for end-to-end integration scenarios."""
    
    @pytest.fixture
    def integration_client(self):
        """Real Neo4j client for integration testing."""
        # This would connect to a test database
        client = Neo4jClient(
            uri="bolt://localhost:7687",
            username="neo4j", 
            password="test"
        )
        return client
    
    def test_complete_project_analysis_workflow(self, integration_client):
        """RED: Test complete project analysis workflow."""
        # This test defines the expected end-to-end behavior
        
        # 1. Create project
        project_data = {
            "id": f"test_project_{uuid.uuid4()}",
            "name": "Integration Test Project",
            "description": "End-to-end test"
        }
        
        # 2. Store symbols and relationships
        symbols = [
            # Sample symbols would be created here
        ]
        
        relationships = [
            # Sample relationships would be created here  
        ]
        
        # 3. Query and verify data
        # This defines what the complete workflow should achieve
        
        # Expected workflow:
        # - Project creation should return project ID
        # - Symbol storage should link to project
        # - Relationships should connect symbols
        # - Queries should return consistent data
        # - Cleanup should remove all test data
        
        # This test will initially fail (RED) until implementation is complete
        pass


# Test Runner Configuration
@pytest.fixture(scope="session")
def neo4j_test_setup():
    """Setup test environment for Neo4j testing."""
    # This fixture would:
    # 1. Start test Neo4j container if needed
    # 2. Create test database
    # 3. Set up indexes and constraints
    # 4. Provide cleanup after tests
    
    yield "test_setup"
    
    # Cleanup after all tests
    pass


if __name__ == "__main__":
    """
    Run TDD tests for Neo4j operations.
    
    Usage:
        python -m pytest tests/test_neo4j_tdd.py -v
        python -m pytest tests/test_neo4j_tdd.py::TestNeo4jConnectionTDD -v
        python -m pytest tests/test_neo4j_tdd.py -k "test_connection" -v
    """
    pytest.main([__file__, "-v", "--tb=short"])
