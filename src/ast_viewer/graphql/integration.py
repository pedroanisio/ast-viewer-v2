"""Integration helpers for GraphQL schema with FastAPI and other frameworks."""

from typing import Dict, Any, Optional
import strawberry
from fastapi import FastAPI, Request, Depends
from strawberry.fastapi import GraphQLRouter
import uuid
import time

from .context import create_context, GraphQLContext
from .modern_schema import create_schema
from .extensions import create_extensions


async def get_graphql_context(request: Request) -> GraphQLContext:
    """
    Create GraphQL context for FastAPI integration.
    
    This function implements dependency injection following Strawberry best practices.
    """
    # Generate unique request ID for tracing
    request_id = str(uuid.uuid4())[:8]
    
    # Extract user from request (implement your auth logic here)
    user = await get_current_user(request)  # You'd implement this
    
    # Create context with all dependencies
    context = create_context(
        request_id=request_id,
        user=user
    )
    
    # Add request metadata
    context.start_time = time.time()
    
    return context


async def get_current_user(request: Request) -> Optional[Dict[str, Any]]:
    """
    Extract user information from request.
    
    Implement your authentication logic here.
    """
    # Example implementation - you'd integrate with your auth system
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header[7:]
        # Validate token and return user info
        return {
            "id": "user123",
            "username": "developer",
            "role": "admin"
        }
    return None


def create_fastapi_app() -> FastAPI:
    """
    Create FastAPI app with GraphQL integration following Strawberry best practices.
    """
    # Create FastAPI app
    app = FastAPI(
        title="AST Viewer Code Intelligence API",
        description="GraphQL API for code analysis and intelligence",
        version="1.0.0"
    )
    
    # Create GraphQL schema with extensions
    schema = create_schema()
    
    # Create GraphQL router with context dependency injection
    graphql_app = GraphQLRouter(
        schema,
        context_getter=get_graphql_context,
        graphiql=True  # Enable GraphiQL for development
    )
    
    # Mount GraphQL endpoint
    app.include_router(graphql_app, prefix="/graphql")
    
    # Add health check endpoint
    @app.get("/health")
    async def health_check():
        return {"status": "healthy", "service": "ast-viewer-graphql"}
    
    # Add metrics endpoint
    @app.get("/metrics")
    async def metrics():
        # You could return DataLoader metrics here
        return {"metrics": "Available via GraphQL introspection"}
    
    return app


# Example usage patterns for different scenarios
class GraphQLUsageExamples:
    """
    Examples demonstrating Strawberry best practices implementation.
    """
    
    @staticmethod
    def basic_query_example() -> str:
        """Example of a basic file analysis query."""
        return '''
        query AnalyzeFile($input: FileAnalysisInput!) {
            analyzeFile(input: $input) {
                ... on UniversalFileType {
                    path
                    language
                    totalLines
                    complexity
                    nodes {
                        id
                        type
                        name
                        displayName
                        complexityLevel
                        referencesCount
                    }
                }
                ... on FileNotFoundError {
                    message
                    filePath
                }
                ... on AnalysisError {
                    message
                    filePath
                    errorType
                }
                ... on ValidationError {
                    message
                    field
                }
            }
        }
        '''
    
    @staticmethod
    def complex_query_with_dataloaders() -> str:
        """Example query utilizing DataLoaders for efficient data fetching."""
        return '''
        query ProjectAnalysis($input: ProjectAnalysisInput!) {
            analyzeProject(input: $input) {
                ... on AnalysisResult {
                    files {
                        path
                        nodes {
                            id
                            name
                            type
                            # These fields use DataLoaders for efficient batching
                            relatedSymbols(limit: 5) {
                                id
                                name
                                type
                            }
                            referencesCount
                            complexityLevel
                        }
                    }
                    metrics {
                        totalFiles
                        totalLines
                        averageComplexity
                    }
                }
                ... on DirectoryNotFoundError {
                    message
                    directoryPath
                }
            }
        }
        '''
    
    @staticmethod
    def mutation_example() -> str:
        """Example mutation with proper error handling."""
        return '''
        mutation RefreshAnalysis($projectId: String!) {
            refreshAnalysis(projectId: $projectId)
        }
        '''
    
    @staticmethod
    def introspection_query() -> str:
        """GraphQL introspection query for schema exploration."""
        return '''
        query IntrospectionQuery {
            __schema {
                queryType {
                    name
                    fields {
                        name
                        type {
                            name
                            kind
                        }
                    }
                }
                mutationType {
                    name
                    fields {
                        name
                        type {
                            name
                        }
                    }
                }
            }
        }
        '''


# Testing utilities
class GraphQLTestClient:
    """
    Test client for GraphQL operations using Strawberry test patterns.
    """
    
    def __init__(self, schema):
        from strawberry.test import GraphQLTestClient as BaseClient
        self.client = BaseClient(schema)
    
    async def execute_query(self, query: str, variables: Optional[Dict] = None):
        """Execute GraphQL query with proper error handling."""
        result = self.client.query(query, variables=variables or {})
        
        if result.errors:
            raise Exception(f"GraphQL errors: {result.errors}")
        
        return result.data
    
    def test_file_analysis(self, file_path: str):
        """Test file analysis operation."""
        query = GraphQLUsageExamples.basic_query_example()
        variables = {
            "input": {
                "filePath": file_path,
                "includeIntelligence": True
            }
        }
        return self.execute_query(query, variables)


# Configuration for production deployment
def get_production_schema():
    """
    Create production-ready schema with appropriate extensions.
    """
    from .modern_schema import Query, Mutation
    
    return strawberry.Schema(
        query=Query,
        mutation=Mutation,
        extensions=create_extensions(
            enable_logging=True,
            enable_performance=True,
            enable_validation=True,
            enable_error_tracking=True,
            enable_caching=True,  # Enable caching in production
            slow_query_threshold=1.0,  # Stricter threshold for production
            max_query_depth=10  # Limit depth for security
        )
    )


__all__ = [
    "create_fastapi_app",
    "get_graphql_context", 
    "GraphQLUsageExamples",
    "GraphQLTestClient",
    "get_production_schema"
]
