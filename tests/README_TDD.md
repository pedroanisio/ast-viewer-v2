# AST Viewer Neo4j Test-Driven Development (TDD) Guide
========================================================

This guide provides comprehensive Test-Driven Development (TDD) implementation for Neo4j operations in the AST Viewer Code Intelligence Platform.

## 🎯 TDD Philosophy

Following the **Red-Green-Refactor** cycle:

1. **🔴 RED**: Write failing tests that define expected behavior
2. **🟢 GREEN**: Write minimal implementation to make tests pass  
3. **🔄 REFACTOR**: Improve code while keeping tests green

## 📁 Test Structure

```
tests/
├── __init__.py                 # Test package init
├── conftest.py                # Shared fixtures and configuration
├── test_neo4j_tdd.py          # Comprehensive Neo4j TDD tests
├── requirements-test.txt       # Testing dependencies
├── README_TDD.md              # This guide
├── reports/                   # Test reports and coverage
│   ├── coverage/              # HTML coverage reports
│   ├── junit.xml              # JUnit test results
│   └── performance/           # Performance test results
├── fixtures/                  # Test data fixtures
├── integration/               # Integration test files
└── unit/                      # Unit test files
```

## 🚀 Quick Start

### 1. Install Test Dependencies
```bash
# Install testing requirements
pip install -r tests/requirements-test.txt

# Or using uv
uv add --dev -r tests/requirements-test.txt
```

### 2. Setup Test Environment
```bash
# Setup test directories and environment
python run_tests.py setup

# Check database connections
python run_tests.py check
```

### 3. Run Tests

#### Unit Tests (Fast, No DB Required)
```bash
# Run all unit tests
python run_tests.py unit

# Or with pytest directly
python -m pytest tests/ -m unit -v
```

#### Neo4j TDD Tests
```bash
# Run Neo4j specific tests
python run_tests.py neo4j

# Or specific test classes
python -m pytest tests/test_neo4j_tdd.py::TestNeo4jConnectionTDD -v
```

#### Integration Tests (Requires Databases)
```bash
# Start databases first
docker compose up neo4j postgres redis -d

# Run integration tests
python run_tests.py integration
```

#### TDD Mode (Watch for Changes)
```bash
# Install pytest-watch
pip install pytest-watch

# Run in TDD mode
python run_tests.py tdd --watch src/
```

#### Coverage Reports
```bash
# Generate coverage report
python run_tests.py coverage --html

# View HTML report
open tests/reports/coverage/index.html
```

## 🧪 Test Categories

### Connection Management Tests
```python
class TestNeo4jConnectionTDD:
    """TDD for Neo4j connection management."""
    
    def test_neo4j_client_initialization_should_set_default_config(self):
        """RED: Test client initialization with default configuration."""
        # Defines expected initialization behavior
        
    def test_connect_should_establish_driver_connection(self):
        """RED: Test successful connection establishment."""
        # Defines expected connection behavior
```

### Project Management Tests
```python
class TestNeo4jProjectManagementTDD:
    """TDD for project management operations."""
    
    def test_create_project_should_store_project_node(self):
        """RED: Test project creation in Neo4j."""
        # Defines expected project storage behavior
        
    def test_get_project_should_retrieve_project_by_id(self):
        """RED: Test project retrieval by ID."""
        # Defines expected project retrieval behavior
```

### Symbol Storage Tests
```python
class TestNeo4jSymbolStorageTDD:
    """TDD for symbol storage and retrieval."""
    
    def test_store_symbol_should_create_symbol_node(self):
        """RED: Test symbol storage in Neo4j."""
        # Defines expected symbol storage behavior
        
    def test_search_symbols_should_find_symbols_by_pattern(self):
        """RED: Test symbol search functionality."""
        # Defines expected search behavior
```

### Relationship Management Tests
```python
class TestNeo4jRelationshipManagementTDD:
    """TDD for relationship management."""
    
    def test_store_relationship_should_create_relationship_edge(self):
        """RED: Test relationship storage."""
        # Defines expected relationship behavior
        
    def test_find_circular_dependencies_should_detect_cycles(self):
        """RED: Test circular dependency detection."""
        # Defines expected cycle detection behavior
```

### Complex Query Tests
```python
class TestNeo4jComplexQueriesTDD:
    """TDD for complex graph queries."""
    
    def test_get_call_graph_should_build_symbol_call_hierarchy(self):
        """RED: Test call graph generation."""
        # Defines expected call graph behavior
        
    def test_get_dependency_graph_should_build_module_dependencies(self):
        """RED: Test dependency graph generation."""
        # Defines expected dependency analysis behavior
```

## 🔄 TDD Workflow

### Step 1: Write Failing Test (RED)
```python
def test_create_project_should_return_project_id(self):
    """RED: Define expected project creation behavior."""
    client = Neo4jClient()
    project_data = {"name": "Test Project", "language": "python"}
    
    # This will fail initially - no implementation yet
    result = client.create_project(project_data)
    
    assert result is not None
    assert isinstance(result, str)
    assert result.startswith("project_")
```

### Step 2: Make Test Pass (GREEN)
```python
# In Neo4jClient class
def create_project(self, project_data):
    """Minimal implementation to make test pass."""
    project_id = f"project_{uuid.uuid4().hex[:8]}"
    
    query = """
    CREATE (p:Project {
        id: $project_id,
        name: $name,
        language: $language,
        created_at: datetime()
    })
    RETURN p.id as project_id
    """
    
    result = self.execute_query(query, {
        "project_id": project_id,
        **project_data
    })
    
    return result[0]["project_id"] if result else None
```

### Step 3: Refactor (REFACTOR)
```python
def create_project(self, project_data):
    """Improved implementation with better error handling."""
    # Add validation
    if not project_data.get("name"):
        raise ValueError("Project name is required")
    
    project_id = self._generate_project_id()
    
    # More robust query with error handling
    query = self._build_create_project_query()
    
    try:
        result = self.execute_query(query, {
            "project_id": project_id,
            **self._sanitize_project_data(project_data)
        })
        
        return result[0]["project_id"] if result else None
        
    except Exception as e:
        self.logger.error(f"Failed to create project: {e}")
        raise ProjectCreationError(f"Could not create project: {e}")
```

## 📊 Testing Best Practices

### 1. Test Naming Convention
- Use descriptive test names that explain the expected behavior
- Format: `test_[method]_should_[expected_behavior]_[conditions]`
- Example: `test_get_symbol_should_return_none_for_nonexistent_symbol`

### 2. Test Structure (AAA Pattern)
```python
def test_method_should_behavior(self):
    # ARRANGE: Set up test data and mocks
    client = Neo4jClient()
    test_data = {"id": "test_123"}
    
    # ACT: Execute the method being tested
    result = client.method_under_test(test_data)
    
    # ASSERT: Verify expected behavior
    assert result == expected_value
```

### 3. Use Fixtures for Common Setup
```python
@pytest.fixture
def neo4j_client():
    """Provide configured Neo4j client for testing."""
    client = Neo4jClient(uri="bolt://localhost:7687")
    yield client
    client.disconnect()

def test_with_fixture(neo4j_client):
    """Test using shared fixture."""
    result = neo4j_client.test_connection()
    assert result is True
```

### 4. Mock External Dependencies
```python
def test_with_mocked_driver(self, mock_neo4j_client):
    """Test with mocked Neo4j driver."""
    with patch.object(mock_neo4j_client, 'execute_query') as mock_execute:
        mock_execute.return_value = [{"id": "test_123"}]
        
        result = mock_neo4j_client.get_project("test_123")
        
        assert result["id"] == "test_123"
        mock_execute.assert_called_once()
```

## 🏷️ Test Markers

Use pytest markers to categorize tests:

```python
@pytest.mark.unit
def test_unit_functionality():
    """Fast unit test with no external dependencies."""
    pass

@pytest.mark.integration
def test_integration_with_database():
    """Integration test requiring real database."""
    pass

@pytest.mark.performance
def test_performance_benchmark():
    """Performance test with benchmarking."""
    pass

@pytest.mark.slow
def test_long_running_operation():
    """Test that takes significant time to run."""
    pass
```

Run specific markers:
```bash
# Run only unit tests
python -m pytest -m unit

# Run integration tests
python -m pytest -m integration

# Exclude slow tests
python -m pytest -m "not slow"
```

## 📈 Coverage Goals

- **Minimum Coverage**: 85% for all Neo4j operations
- **Target Coverage**: 95% for critical paths
- **100% Coverage**: Connection management, error handling

### Check Coverage
```bash
# Generate coverage report
python run_tests.py coverage --html

# Check specific files
python -m pytest --cov=src/ast_viewer/database/neo4j_client.py --cov-report=term-missing
```

## 🔧 Debugging Tests

### Run Single Test with Debug
```bash
# Run single test with verbose output
python -m pytest tests/test_neo4j_tdd.py::test_specific_test -v -s

# Run with pdb debugger
python -m pytest tests/test_neo4j_tdd.py::test_specific_test --pdb
```

### Debug Fixtures
```python
def test_debug_fixture(neo4j_client, caplog):
    """Debug test with logging and fixtures."""
    with caplog.at_level(logging.DEBUG):
        result = neo4j_client.test_connection()
        
    # Check logs
    assert "Connected to Neo4j" in caplog.text
    assert result is True
```

## 🚨 Common Issues & Solutions

### 1. Connection Errors
```python
# Problem: Tests fail with connection errors
# Solution: Check database is running
docker compose up neo4j -d

# Or mock the connection for unit tests
@patch('neo4j.GraphDatabase.driver')
def test_with_mocked_connection(mock_driver):
    mock_driver.return_value = Mock()
    # Test continues with mocked connection
```

### 2. Test Data Cleanup
```python
# Problem: Tests interfere with each other
# Solution: Use fixtures with cleanup
@pytest.fixture
def clean_database(neo4j_client):
    """Ensure clean database state."""
    yield neo4j_client
    # Cleanup after test
    neo4j_client.execute_query("MATCH (n:Test) DETACH DELETE n")
```

### 3. Slow Tests
```python
# Problem: Tests run too slowly
# Solution: Use unit tests with mocks
def test_fast_unit_test(mock_neo4j_client):
    """Fast test with mocked dependencies."""
    # No real database connection needed
    pass

# Mark slow tests
@pytest.mark.slow
def test_integration_full_workflow():
    """Complete workflow test - marked as slow."""
    pass
```

## 📚 Further Reading

- [pytest Documentation](https://docs.pytest.org/)
- [Neo4j Testing Best Practices](https://neo4j.com/docs/operations-manual/current/testing/)
- [TDD with Python](https://www.obeythetestinggoat.com/)
- [Testing GraphQL APIs](https://graphql.org/learn/testing/)

## 🤝 Contributing

When adding new Neo4j functionality:

1. **Write the test first** (RED)
2. **Implement minimal functionality** (GREEN)  
3. **Refactor and improve** (REFACTOR)
4. **Ensure >85% coverage**
5. **Add appropriate markers**
6. **Update this documentation**

## 🎯 Next Steps

1. **Run the existing tests** to see them fail (RED phase)
2. **Implement the missing methods** in `Neo4jClient` (GREEN phase)
3. **Refactor and optimize** the implementation (REFACTOR phase)
4. **Add more test cases** for edge cases and error conditions
5. **Integrate with GraphQL layer** for complete functionality

---

**Happy Testing! 🧪✨**

Remember: *"The best time to write tests was yesterday. The second best time is now."*
