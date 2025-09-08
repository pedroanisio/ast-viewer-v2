"""Documentation server for GraphQL API with enhanced features."""

from pathlib import Path
from typing import Dict, Any
import json

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from strawberry.fastapi import GraphQLRouter

from ..graphql.modern_schema import create_schema
from ..graphql.docs_generator import GraphQLDocumentationGenerator
from ..graphql.integration import get_graphql_context


class GraphQLDocsServer:
    """Enhanced documentation server for GraphQL API."""
    
    def __init__(self, docs_dir: str = "docs/graphql"):
        self.docs_dir = Path(docs_dir)
        self.docs_dir.mkdir(parents=True, exist_ok=True)
        self.generator = GraphQLDocumentationGenerator(str(self.docs_dir))
        self.app = FastAPI(
            title="AST Viewer GraphQL API Documentation",
            description="Interactive documentation and playground for the AST Viewer Code Intelligence API",
            version="2.0.0"
        )
        self._setup_routes()
        
    def _setup_routes(self):
        """Set up documentation routes."""
        
        @self.app.get("/", response_class=HTMLResponse)
        async def docs_home():
            """Main documentation page."""
            # Generate fresh interactive docs
            docs_file = self.generator.generate_interactive_docs()
            with open(docs_file, 'r') as f:
                return f.read()
        
        @self.app.get("/playground", response_class=HTMLResponse)
        async def graphql_playground():
            """Advanced GraphQL Playground with enhanced features."""
            return """
            <!DOCTYPE html>
            <html>
            <head>
                <title>AST Viewer GraphQL Playground</title>
                <link href="https://cdn.jsdelivr.net/npm/graphql-playground-react@1.7.28/build/static/css/index.css" rel="stylesheet" />
            </head>
            <body>
                <div id="root">
                    <style>
                        body { margin: 0; height: 100vh; overflow: hidden; }
                        #root { height: 100vh; }
                    </style>
                </div>
                <script src="https://cdn.jsdelivr.net/npm/graphql-playground-react@1.7.28/build/static/js/middleware.js"></script>
                <script>
                    window.addEventListener('load', function (event) {
                        GraphQLPlayground.init(document.getElementById('root'), {
                            endpoint: '/graphql',
                            settings: {
                                'request.credentials': 'include',
                            },
                            tabs: [
                                {
                                    endpoint: '/graphql',
                                    query: `# Welcome to AST Viewer GraphQL Playground
# 
# Here are some example queries to get you started:

# 1. Analyze a single file
query AnalyzeFile {
  analyzeFile(input: {
    filePath: "/path/to/your/file.py"
    includeIntelligence: true
  }) {
    ... on UniversalFileType {
      path
      language
      totalLines
      complexity
      nodes {
        id
        name
        type
        displayName
        complexityLevel
        location {
          startLine
          endLine
        }
      }
    }
    ... on FileNotFoundError {
      message
      filePath
    }
  }
}

# 2. Search for symbols
query SearchSymbols {
  searchSymbols(input: {
    query: "class"
    limit: 10
  }) {
    id
    name
    type
    language
    displayName
    filePath: location { filePath }
    relatedSymbols(limit: 3) {
      id
      name
      type
    }
  }
}

# 3. Get schema information
query SchemaInfo {
  __schema {
    queryType { name }
    mutationType { name }
    types {
      name
      kind
      description
    }
  }
}`
                                }
                            ]
                        })
                    })
                </script>
            </body>
            </html>
            """
        
        @self.app.get("/schema.graphql")
        async def get_schema_sdl():
            """Download GraphQL Schema Definition Language."""
            schema_file = self.generator.generate_schema_sdl()
            return FileResponse(schema_file, media_type="text/plain", filename="schema.graphql")
        
        @self.app.get("/schema.json")
        async def get_schema_json():
            """Download GraphQL Schema as JSON."""
            schema_file = self.generator.generate_schema_json()
            return FileResponse(schema_file, media_type="application/json", filename="schema.json")
        
        @self.app.get("/examples.md")
        async def get_examples():
            """Download example queries."""
            examples_file = self.generator.generate_example_queries()
            return FileResponse(examples_file, media_type="text/markdown", filename="examples.md")
        
        @self.app.get("/postman")
        async def get_postman_collection():
            """Download Postman collection."""
            collection_file = self.generator.generate_postman_collection()
            return FileResponse(collection_file, media_type="application/json", filename="ast_viewer_api.postman_collection.json")
        
        @self.app.get("/api/types")
        async def get_type_definitions():
            """Get GraphQL type definitions as JSON."""
            # This is useful for code generators and IDE extensions
            from strawberry.printer import print_schema
            from strawberry.schema.execute import execute_sync
            
            schema = create_schema()
            
            # Get type information
            introspection_query = """
            query {
                __schema {
                    types {
                        name
                        kind
                        description
                        fields {
                            name
                            description
                            type {
                                name
                                kind
                            }
                        }
                        inputFields {
                            name
                            description
                            type {
                                name
                                kind
                            }
                        }
                        enumValues {
                            name
                            description
                        }
                    }
                }
            }
            """
            
            result = execute_sync(schema, introspection_query)
            return JSONResponse(content=result.data)
        
        @self.app.get("/api/queries")
        async def get_available_queries():
            """Get list of available queries with descriptions."""
            schema = create_schema()
            query_type = schema.schema.type_map.get("Query")
            
            queries = []
            if query_type and hasattr(query_type, 'fields'):
                for field_name, field in query_type.fields.items():
                    queries.append({
                        "name": field_name,
                        "description": getattr(field, 'description', None),
                        "args": [
                            {
                                "name": arg_name,
                                "type": str(arg.type),
                                "description": getattr(arg, 'description', None)
                            }
                            for arg_name, arg in getattr(field, 'args', {}).items()
                        ]
                    })
            
            return JSONResponse(content={"queries": queries})
        
        @self.app.get("/health")
        async def docs_health():
            """Health check for documentation server."""
            return {"status": "healthy", "service": "graphql-docs"}
        
        # Mount GraphQL endpoint for testing
        schema = create_schema()
        graphql_app = GraphQLRouter(schema, context_getter=get_graphql_context)
        self.app.include_router(graphql_app, prefix="/graphql")
        
        # Serve static documentation files
        if self.docs_dir.exists():
            self.app.mount("/static", StaticFiles(directory=str(self.docs_dir)), name="static")


def create_docs_app() -> FastAPI:
    """Create FastAPI app for serving GraphQL documentation."""
    docs_server = GraphQLDocsServer()
    return docs_server.app


# CLI for running the docs server standalone
if __name__ == "__main__":
    import uvicorn
    
    docs_app = create_docs_app()
    print("🚀 Starting GraphQL Documentation Server...")
    print("📚 Documentation: http://localhost:8001/")
    print("🛝 GraphQL Playground: http://localhost:8001/playground")
    print("📋 Schema SDL: http://localhost:8001/schema.graphql")
    
    uvicorn.run(docs_app, host="0.0.0.0", port=8001)
