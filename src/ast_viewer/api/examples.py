"""OpenAPI documentation examples for REST API endpoints."""

from .models import (
    FileAnalysisRequest, DirectoryAnalysisRequest, ProjectAnalysisRequest,
    SymbolSearchRequest, VisualizationRequest, ImpactAnalysisRequest,
    VisualizationTypeEnum, ExportFormatEnum, ElementTypeEnum, LanguageEnum
)


# Request examples for OpenAPI documentation
EXAMPLES = {
    "file_analysis_request": {
        "summary": "Analyze a Python file",
        "description": "Example request to analyze a single Python file with full metrics",
        "value": {
            "file_path": "/path/to/your/project/main.py",
            "include_metrics": True,
            "include_elements": True
        }
    },
    
    "directory_analysis_request": {
        "summary": "Analyze a project directory",
        "description": "Example request to analyze a directory with Python files only",
        "value": {
            "directory_path": "/path/to/your/project",
            "file_extensions": [".py", ".pyi"],
            "exclude_patterns": ["__pycache__", ".git", "node_modules"],
            "max_files": 100,
            "include_metrics": True,
            "include_intelligence": True
        }
    },
    
    "project_analysis_local": {
        "summary": "Analyze local project",
        "description": "Example request for comprehensive local project analysis",
        "value": {
            "directory_path": "/path/to/your/project",
            "project_name": "My Awesome Project",
            "file_extensions": [".py", ".js", ".ts"],
            "exclude_patterns": ["node_modules", ".git", "__pycache__", "dist", "build"],
            "max_files": 500,
            "include_intelligence": True,
            "include_visualizations": False,
            "include_dependencies": True
        }
    },
    
    "project_analysis_github": {
        "summary": "Analyze GitHub repository",
        "description": "Example request to analyze a public GitHub repository",
        "value": {
            "github_url": "https://github.com/fastapi/fastapi",
            "branch": "main",
            "project_name": "FastAPI Framework Analysis",
            "file_extensions": [".py"],
            "exclude_patterns": ["tests", "docs", ".github"],
            "max_files": 200,
            "include_intelligence": True,
            "include_visualizations": True,
            "shallow_clone": True,
            "clone_depth": 1
        }
    },
    
    "symbol_search_request": {
        "summary": "Search for functions",
        "description": "Example request to search for function symbols",
        "value": {
            "query": "authenticate",
            "element_types": ["FUNCTION", "METHOD"],
            "languages": ["PYTHON", "JAVASCRIPT"],
            "project_id": "project:my-awesome-project",
            "limit": 20,
            "include_relationships": True
        }
    },
    
    "visualization_dependency_graph": {
        "summary": "Generate dependency graph",
        "description": "Example request to generate an interactive dependency graph",
        "value": {
            "project_id": "project:my-awesome-project",
            "visualization_type": "dependency_graph",
            "width": 1200,
            "height": 800,
            "interactive": True,
            "export_format": "html",
            "include_metadata": True
        }
    },
    
    "visualization_complexity_heatmap": {
        "summary": "Generate complexity heatmap",
        "description": "Example request to generate a complexity heatmap visualization",
        "value": {
            "project_id": "project:my-awesome-project",
            "visualization_type": "complexity_heatmap",
            "complexity_threshold": 5,
            "width": 1000,
            "height": 600,
            "interactive": True,
            "export_format": "png",
            "include_metadata": False
        }
    },
    
    "impact_analysis_request": {
        "summary": "Analyze symbol impact",
        "description": "Example request to analyze the impact of changing a specific symbol",
        "value": {
            "project_id": "project:my-awesome-project",
            "symbol_id": "function:authenticate:auth.py:45",
            "max_depth": 3,
            "include_visualization": True
        }
    }
}

# Response examples
RESPONSE_EXAMPLES = {
    "api_success_response": {
        "summary": "Successful API response",
        "description": "Standard successful API response format",
        "value": {
            "success": True,
            "message": "Operation completed successfully",
            "data": {
                "result": "Sample data here"
            },
            "errors": None,
            "timestamp": "2024-01-15T10:30:00Z",
            "request_id": "550e8400-e29b-41d4-a716-446655440000"
        }
    },
    
    "api_error_response": {
        "summary": "Error API response",
        "description": "Standard error API response format",
        "value": {
            "success": False,
            "error_type": "ValidationError",
            "message": "Invalid input parameters",
            "details": {
                "field": "file_path",
                "issue": "File not found"
            },
            "timestamp": "2024-01-15T10:30:00Z",
            "request_id": "550e8400-e29b-41d4-a716-446655440000"
        }
    },
    
    "file_analysis_response": {
        "summary": "File analysis result",
        "description": "Example response from file analysis",
        "value": {
            "success": True,
            "message": "File analyzed successfully in 0.25s",
            "data": {
                "file": {
                    "path": "/path/to/project/main.py",
                    "language": "PYTHON",
                    "encoding": "utf-8",
                    "size_bytes": 1024,
                    "hash": "abc123def456",
                    "metrics": {
                        "total_lines": 45,
                        "code_lines": 32,
                        "comment_lines": 8,
                        "blank_lines": 5,
                        "complexity": 12.5,
                        "maintainability_index": 78.2
                    },
                    "elements": [
                        {
                            "id": "function:main:main.py:10",
                            "name": "main",
                            "type": "FUNCTION",
                            "language": "PYTHON",
                            "source_location": {
                                "file_path": "/path/to/project/main.py",
                                "line_number": 10,
                                "column_number": 0,
                                "end_line_number": 20,
                                "end_column_number": 0
                            },
                            "cyclomatic_complexity": 3,
                            "cognitive_complexity": 2
                        }
                    ],
                    "imports": ["os", "sys", "argparse"],
                    "exports": ["main"],
                    "created_at": "2024-01-15T10:30:00Z"
                },
                "analysis_time": 0.25,
                "element_count": 5
            }
        }
    },
    
    "visualization_response": {
        "summary": "Visualization generation result",
        "description": "Example response from visualization generation",
        "value": {
            "success": True,
            "message": "Visualization generated successfully in 1.2s",
            "data": {
                "visualization_id": "viz_550e8400-e29b-41d4-a716-446655440000",
                "visualization_type": "dependency_graph",
                "format": "html",
                "content": "<div id='dependency-graph'>Interactive graph here</div>",
                "file_path": None,
                "metadata": {
                    "project_id": "project:my-awesome-project",
                    "config": {
                        "width": 1200,
                        "height": 800,
                        "interactive": True
                    },
                    "nodes": 25,
                    "edges": 42
                },
                "generation_time": 1.2,
                "created_at": "2024-01-15T10:30:00Z"
            }
        }
    },
    
    "health_status_response": {
        "summary": "System health status",
        "description": "Example health check response",
        "value": {
            "success": True,
            "message": "System is healthy",
            "data": {
                "status": "healthy",
                "version": "2.0.0",
                "uptime": "running",
                "components": {
                    "universal_analyzer": "ready (5 languages)",
                    "visualization_engine": "ready (17 types)",
                    "supported_languages": "5"
                },
                "metrics": {
                    "memory_usage": "N/A",
                    "cpu_usage": "N/A",
                    "cache_size": "N/A"
                },
                "timestamp": "2024-01-15T10:30:00Z"
            }
        }
    }
}

# OpenAPI tags for better organization
OPENAPI_TAGS = [
    {
        "name": "Health",
        "description": "System health, status, and metrics endpoints",
    },
    {
        "name": "Analysis",
        "description": "Code analysis endpoints for files, directories, and projects",
        "externalDocs": {
            "description": "Analysis documentation",
            "url": "https://docs.astviewer.com/analysis"
        }
    },
    {
        "name": "Intelligence",
        "description": "Code intelligence endpoints for symbols, relationships, and impact analysis",
        "externalDocs": {
            "description": "Intelligence documentation", 
            "url": "https://docs.astviewer.com/intelligence"
        }
    },
    {
        "name": "Visualizations",
        "description": "Visualization generation and export endpoints",
        "externalDocs": {
            "description": "Visualization documentation",
            "url": "https://docs.astviewer.com/visualizations"
        }
    },
    {
        "name": "Projects",
        "description": "Project-level analysis and management endpoints"
    },
    {
        "name": "GraphQL",
        "description": "GraphQL endpoint for advanced queries and mutations",
        "externalDocs": {
            "description": "GraphQL documentation",
            "url": "/graphql-docs"
        }
    }
]

# Usage examples for the documentation
USAGE_EXAMPLES = {
    "curl": {
        "file_analysis": """
# Analyze a single file
curl -X POST "http://localhost:8000/api/v1/analysis/file" \\
     -H "Content-Type: application/json" \\
     -d '{
       "file_path": "/path/to/your/file.py",
       "include_metrics": true,
       "include_elements": true
     }'
        """,
        
        "project_analysis": """
# Analyze a GitHub repository
curl -X POST "http://localhost:8000/api/v1/analysis/project" \\
     -H "Content-Type: application/json" \\
     -d '{
       "github_url": "https://github.com/fastapi/fastapi",
       "project_name": "FastAPI Analysis",
       "include_intelligence": true,
       "max_files": 100
     }'
        """,
        
        "visualization": """
# Generate a dependency graph visualization
curl -X POST "http://localhost:8000/api/v1/visualization/generate" \\
     -H "Content-Type: application/json" \\
     -d '{
       "project_id": "project:fastapi",
       "visualization_type": "dependency_graph",
       "width": 1200,
       "height": 800,
       "export_format": "html"
     }'
        """
    },
    
    "python": {
        "file_analysis": """
import requests

# Analyze a single file
response = requests.post(
    "http://localhost:8000/api/v1/analysis/file",
    json={
        "file_path": "/path/to/your/file.py",
        "include_metrics": True,
        "include_elements": True
    }
)

result = response.json()
print(f"Analysis completed: {result['success']}")
print(f"Found {result['data']['element_count']} code elements")
        """,
        
        "project_analysis": """
import requests

# Analyze a GitHub repository
response = requests.post(
    "http://localhost:8000/api/v1/analysis/project", 
    json={
        "github_url": "https://github.com/fastapi/fastapi",
        "project_name": "FastAPI Analysis",
        "include_intelligence": True,
        "max_files": 100
    }
)

result = response.json()
if result['success']:
    project = result['data']
    print(f"Analyzed {project['metrics']['total_files']} files")
    print(f"Found {project['metrics']['total_functions']} functions")
    print(f"Languages: {list(project['languages'].keys())}")
        """
    },
    
    "javascript": {
        "file_analysis": """
// Analyze a single file using fetch
const response = await fetch('http://localhost:8000/api/v1/analysis/file', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    file_path: '/path/to/your/file.py',
    include_metrics: true,
    include_elements: true
  })
});

const result = await response.json();
console.log(`Analysis completed: ${result.success}`);
console.log(`Found ${result.data.element_count} code elements`);
        """
    }
}

__all__ = ["EXAMPLES", "RESPONSE_EXAMPLES", "OPENAPI_TAGS", "USAGE_EXAMPLES"]
