"""GraphQL Documentation Generator for AST Viewer API.

This module provides comprehensive documentation generation capabilities for the GraphQL API,
including schema introspection, example queries, and interactive documentation.
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Any, Optional
import strawberry
from strawberry.printer import print_schema
from strawberry.schema.config import StrawberryConfig

from .modern_schema import create_schema
from .integration import GraphQLUsageExamples


class GraphQLDocumentationGenerator:
    """Generate comprehensive GraphQL API documentation."""
    
    def __init__(self, output_dir: str = "docs/graphql"):
        self.schema = create_schema()
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
    def generate_all_docs(self) -> Dict[str, str]:
        """Generate all documentation formats."""
        generated_files = {}
        
        # Generate Schema Definition Language (SDL)
        generated_files["schema.graphql"] = self.generate_schema_sdl()
        
        # Generate JSON Schema
        generated_files["schema.json"] = self.generate_schema_json()
        
        # Generate Introspection Query Result
        generated_files["introspection.json"] = self.generate_introspection()
        
        # Generate Example Queries
        generated_files["examples.md"] = self.generate_example_queries()
        
        # Generate API Reference
        generated_files["api-reference.md"] = self.generate_api_reference()
        
        # Generate Interactive HTML Documentation
        generated_files["interactive.html"] = self.generate_interactive_docs()
        
        # Generate Postman Collection
        generated_files["postman_collection.json"] = self.generate_postman_collection()
        
        return generated_files
    
    def generate_schema_sdl(self) -> str:
        """Generate Schema Definition Language file."""
        schema_sdl = print_schema(self.schema)
        
        output_file = self.output_dir / "schema.graphql"
        with open(output_file, 'w') as f:
            f.write(schema_sdl)
            
        return str(output_file)
    
    def generate_schema_json(self) -> str:
        """Generate JSON representation of the schema."""
        from strawberry.schema.execute import execute_sync
        
        introspection_query = """
        query IntrospectionQuery {
            __schema {
                queryType { name }
                mutationType { name }
                subscriptionType { name }
                types {
                    ...FullType
                }
                directives {
                    name
                    description
                    locations
                    args {
                        ...InputValue
                    }
                }
            }
        }
        
        fragment FullType on __Type {
            kind
            name
            description
            fields(includeDeprecated: true) {
                name
                description
                args {
                    ...InputValue
                }
                type {
                    ...TypeRef
                }
                isDeprecated
                deprecationReason
            }
            inputFields {
                ...InputValue
            }
            interfaces {
                ...TypeRef
            }
            enumValues(includeDeprecated: true) {
                name
                description
                isDeprecated
                deprecationReason
            }
            possibleTypes {
                ...TypeRef
            }
        }
        
        fragment InputValue on __InputValue {
            name
            description
            type { ...TypeRef }
            defaultValue
        }
        
        fragment TypeRef on __Type {
            kind
            name
            ofType {
                kind
                name
                ofType {
                    kind
                    name
                    ofType {
                        kind
                        name
                        ofType {
                            kind
                            name
                            ofType {
                                kind
                                name
                                ofType {
                                    kind
                                    name
                                    ofType {
                                        kind
                                        name
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
        """
        
        result = execute_sync(self.schema, introspection_query)
        
        output_file = self.output_dir / "schema.json"
        with open(output_file, 'w') as f:
            json.dump(result.data, f, indent=2)
            
        return str(output_file)
    
    def generate_introspection(self) -> str:
        """Generate full introspection query result."""
        # This is useful for tools like GraphQL Code Generator
        return self.generate_schema_json()
    
    def generate_example_queries(self) -> str:
        """Generate comprehensive example queries documentation."""
        examples = GraphQLUsageExamples()
        
        markdown_content = """# GraphQL API Examples

This document provides comprehensive examples for using the AST Viewer Code Intelligence GraphQL API.

## Table of Contents
- [Basic File Analysis](#basic-file-analysis)
- [Project Analysis](#project-analysis)
- [Symbol Search](#symbol-search)
- [Relationship Queries](#relationship-queries)
- [Visualization Generation](#visualization-generation)
- [Mutations](#mutations)

## Basic File Analysis

Analyze a single file to extract code intelligence:

```graphql
""" + examples.basic_query_example() + """
```

### Variables Example:
```json
{
  "input": {
    "filePath": "/path/to/your/file.py",
    "includeIntelligence": true,
    "includeRelationships": true,
    "maxDepth": 5
  }
}
```

## Project Analysis

Analyze an entire project or directory:

```graphql
""" + examples.complex_query_with_dataloaders() + """
```

### Variables Example:
```json
{
  "input": {
    "directoryPath": "/path/to/your/project",
    "includeHidden": false,
    "recursive": true,
    "fileExtensions": [".py", ".js", ".ts"],
    "maxFiles": 1000
  }
}
```

## Symbol Search

Search for specific symbols across your codebase:

```graphql
query SearchSymbols($input: SymbolSearchInput!) {
    searchSymbols(input: $input) {
        id
        name
        type
        language
        displayName
        filePath
        complexityLevel
        location {
            startLine
            endLine
            filePath
        }
        relatedSymbols(limit: 5) {
            id
            name
            type
        }
    }
}
```

### Variables Example:
```json
{
  "input": {
    "query": "DatabaseManager",
    "types": ["CLASS", "INTERFACE"],
    "languages": ["PYTHON", "TYPESCRIPT"],
    "limit": 20
  }
}
```

## Relationship Queries

Query relationships between code elements:

```graphql
query GetSymbolRelationships($symbolId: String!) {
    getSymbol(id: $symbolId) {
        ... on UniversalNodeTypeEnhanced {
            id
            name
            type
            relatedSymbols(limit: 10) {
                id
                name
                type
                relationshipType
            }
            dependencies: relatedSymbols(relationshipTypes: ["CALLS", "USES", "IMPORTS"]) {
                id
                name
                filePath
            }
            dependents: relatedSymbols(relationshipTypes: ["CALLED_BY", "USED_BY"]) {
                id
                name
                filePath
            }
        }
    }
}
```

## Visualization Generation

Generate interactive visualizations:

```graphql
query GenerateVisualization($input: VisualizationInput!) {
    generateVisualization(input: $input) {
        ... on VisualizationResult {
            type
            htmlContent
            metadata {
                nodeCount
                edgeCount
                generationTime
            }
            exportUrl
        }
        ... on ValidationError {
            message
            field
        }
    }
}
```

### Variables Example:
```json
{
  "input": {
    "type": "DEPENDENCY_GRAPH",
    "projectPath": "/path/to/project",
    "config": {
      "includeExternal": false,
      "maxNodes": 100,
      "layout": "force-directed",
      "theme": "dark"
    },
    "exportFormat": "HTML"
  }
}
```

## Mutations

Refresh analysis and manage cache:

```graphql
""" + examples.mutation_example() + """
```

## Error Handling

All queries return union types with proper error handling:

```graphql
query ExampleWithErrorHandling($input: FileAnalysisInput!) {
    analyzeFile(input: $input) {
        ... on UniversalFileType {
            path
            language
            nodes { id name type }
        }
        ... on FileNotFoundError {
            message
            filePath
            suggestions
        }
        ... on AnalysisError {
            message
            errorType
            filePath
            context
        }
        ... on ValidationError {
            message
            field
            validationRules
        }
    }
}
```

## Performance Tips

1. **Use DataLoaders**: The API automatically batches related queries
2. **Limit Results**: Use `limit` parameters to control response size
3. **Selective Fields**: Only request the fields you need
4. **Fragment Usage**: Use fragments for reusable field sets
5. **Caching**: Results are cached for improved performance

## Authentication

Currently, the API supports optional authentication via Bearer tokens:

```http
Authorization: Bearer your_jwt_token_here
```

For public analysis, authentication is optional.
"""

        output_file = self.output_dir / "examples.md"
        with open(output_file, 'w') as f:
            f.write(markdown_content)
            
        return str(output_file)
    
    def generate_api_reference(self) -> str:
        """Generate comprehensive API reference documentation."""
        content = """# AST Viewer GraphQL API Reference

## Overview

The AST Viewer Code Intelligence Platform provides a powerful GraphQL API for analyzing code across multiple programming languages. This API enables you to extract deep insights about code structure, relationships, and metrics.

## Schema Information

- **API Version**: 2.0.0
- **GraphQL Spec**: June 2018
- **Supported Languages**: Python, JavaScript, TypeScript, Go, Rust
- **Visualization Types**: 17 different visualization types available

## Core Types

### UniversalNodeType
Represents any code element (class, function, variable, etc.)

**Fields:**
- `id: String!` - Unique identifier
- `type: ElementTypeEnum!` - Type of code element
- `name: String` - Element name
- `language: LanguageEnum!` - Programming language
- `displayName: String!` - Formatted display name
- `filePath: String!` - File path
- `complexityLevel: ComplexityLevel!` - Complexity rating
- `location: SourceLocationType!` - Source code location

### UniversalFileType
Represents a source code file with analysis results

**Fields:**
- `path: String!` - File path
- `language: LanguageEnum!` - Programming language
- `totalLines: Int!` - Total lines of code
- `complexity: Float!` - File complexity score
- `nodes: [UniversalNodeType!]!` - Code elements in file

### AnalysisResult
Container for analysis results

**Fields:**
- `files: [UniversalFileType!]!` - Analyzed files
- `metrics: ProjectMetrics!` - Project-level metrics
- `intelligence: IntelligenceData` - Advanced intelligence data

## Enums

### ElementTypeEnum
```graphql
enum ElementTypeEnum {
    CLASS
    FUNCTION
    METHOD
    VARIABLE
    CONSTANT
    INTERFACE
    ENUM
    STRUCT
    MODULE
    PACKAGE
    # ... and more
}
```

### LanguageEnum
```graphql
enum LanguageEnum {
    PYTHON
    JAVASCRIPT
    TYPESCRIPT
    GO
    RUST
    # ... and more
}
```

## Input Types

### FileAnalysisInput
```graphql
input FileAnalysisInput {
    filePath: String!
    includeIntelligence: Boolean = true
    includeRelationships: Boolean = true
    maxDepth: Int = 5
}
```

### ProjectAnalysisInput
```graphql
input ProjectAnalysisInput {
    directoryPath: String!
    includeHidden: Boolean = false
    recursive: Boolean = true
    fileExtensions: [String!]
    maxFiles: Int = 1000
}
```

## Query Operations

### analyzeFile
Analyze a single source code file

**Arguments:**
- `input: FileAnalysisInput!`

**Returns:** `Union of UniversalFileType | FileNotFoundError | AnalysisError | ValidationError`

### analyzeProject
Analyze an entire project or directory

**Arguments:**
- `input: ProjectAnalysisInput!`

**Returns:** `Union of AnalysisResult | DirectoryNotFoundError | AnalysisError | ValidationError`

### searchSymbols
Search for symbols across the codebase

**Arguments:**
- `input: SymbolSearchInput!`

**Returns:** `[UniversalNodeTypeEnhanced!]!`

## Mutation Operations

### refreshAnalysis
Refresh analysis cache for a project

**Arguments:**
- `projectId: String!`

**Returns:** `Boolean!`

## Error Types

All operations use union types for comprehensive error handling:

- `FileNotFoundError` - File not found
- `DirectoryNotFoundError` - Directory not found
- `AnalysisError` - Analysis failed
- `ValidationError` - Input validation failed
- `InternalError` - Internal server error

## Rate Limiting

- **Default Limit**: 100 requests per minute
- **Burst Limit**: 20 requests per second
- **Complex Query Limit**: 10 requests per minute

## Caching

- Query results are cached for 1 hour
- Analysis results are cached until files change
- Use `refreshAnalysis` mutation to invalidate cache

## WebSocket Subscriptions

Currently not supported, but planned for future releases.
"""

        output_file = self.output_dir / "api-reference.md"
        with open(output_file, 'w') as f:
            f.write(content)
            
        return str(output_file)
    
    def generate_interactive_docs(self) -> str:
        """Generate interactive HTML documentation with embedded GraphiQL."""
        html_content = """<!DOCTYPE html>
<html>
<head>
    <title>AST Viewer GraphQL API Documentation</title>
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; margin: 0; padding: 20px; }
        .container { max-width: 1200px; margin: 0 auto; }
        .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 40px; border-radius: 10px; margin-bottom: 30px; }
        .section { background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); margin-bottom: 20px; }
        .graphiql-container { height: 600px; border: 1px solid #ddd; border-radius: 5px; }
        pre { background: #f8f9fa; padding: 15px; border-radius: 5px; overflow-x: auto; }
        .example-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; }
        .example-card { border: 1px solid #e1e5e9; border-radius: 8px; padding: 20px; }
        .tag { background: #e3f2fd; color: #1976d2; padding: 4px 8px; border-radius: 4px; font-size: 12px; }
    </style>
    <script src="https://unpkg.com/react@17/umd/react.development.js"></script>
    <script src="https://unpkg.com/react-dom@17/umd/react-dom.development.js"></script>
    <script src="https://unpkg.com/graphiql@1.8.7/graphiql.min.js"></script>
    <link rel="stylesheet" href="https://unpkg.com/graphiql@1.8.7/graphiql.min.css" />
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🧠 AST Viewer GraphQL API</h1>
            <p>Enterprise-grade code intelligence platform with multi-language support and advanced visualizations</p>
            <p><strong>Version:</strong> 2.0.0 | <strong>Endpoint:</strong> <code>/graphql</code></p>
        </div>

        <div class="section">
            <h2>🚀 Quick Start</h2>
            <p>The GraphQL API provides powerful code analysis capabilities. Use the interactive explorer below to test queries.</p>
            
            <div class="example-grid">
                <div class="example-card">
                    <h4>🔍 File Analysis</h4>
                    <span class="tag">QUERY</span>
                    <p>Analyze individual source files</p>
                    <pre><code>query {
  analyzeFile(input: {
    filePath: "/src/main.py"
  }) {
    ... on UniversalFileType {
      path
      language
      totalLines
    }
  }
}</code></pre>
                </div>
                
                <div class="example-card">
                    <h4>🏗️ Project Analysis</h4>
                    <span class="tag">QUERY</span>
                    <p>Comprehensive project analysis</p>
                    <pre><code>query {
  analyzeProject(input: {
    directoryPath: "/src"
  }) {
    ... on AnalysisResult {
      metrics {
        totalFiles
        totalLines
      }
    }
  }
}</code></pre>
                </div>
                
                <div class="example-card">
                    <h4>🎨 Visualizations</h4>
                    <span class="tag">QUERY</span>
                    <p>Generate interactive visualizations</p>
                    <pre><code>query {
  generateVisualization(input: {
    type: DEPENDENCY_GRAPH
    projectPath: "/src"
  }) {
    ... on VisualizationResult {
      htmlContent
    }
  }
}</code></pre>
                </div>
            </div>
        </div>

        <div class="section">
            <h2>🛠️ Interactive GraphQL Explorer</h2>
            <p>Test queries directly against the API. The explorer includes schema introspection and autocomplete.</p>
            <div id="graphiql" class="graphiql-container">Loading GraphiQL...</div>
        </div>

        <div class="section">
            <h2>📚 Documentation Links</h2>
            <ul>
                <li><a href="schema.graphql">📋 Schema Definition (SDL)</a></li>
                <li><a href="examples.md">💡 Query Examples</a></li>
                <li><a href="api-reference.md">📖 API Reference</a></li>
                <li><a href="postman_collection.json">📮 Postman Collection</a></li>
            </ul>
        </div>

        <div class="section">
            <h2>🔧 Development Tools</h2>
            <p>Integrate with your development workflow:</p>
            <ul>
                <li><strong>GraphQL Code Generator:</strong> Use <code>schema.json</code> for type generation</li>
                <li><strong>Apollo Studio:</strong> Import schema for collaborative development</li>
                <li><strong>Insomnia/Postman:</strong> Import the provided collection</li>
                <li><strong>VS Code:</strong> Use GraphQL extension with schema introspection</li>
            </ul>
        </div>
    </div>

    <script>
        const fetcher = GraphiQL.createFetcher({
            url: '/graphql',
        });

        const defaultQuery = `# Welcome to AST Viewer GraphQL API
# Try these example queries:

query ExampleFileAnalysis {
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
        complexityLevel
      }
    }
    ... on FileNotFoundError {
      message
      filePath
    }
  }
}

# Uncomment to try project analysis:
# query ExampleProjectAnalysis {
#   analyzeProject(input: {
#     directoryPath: "/path/to/your/project"
#     recursive: true
#   }) {
#     ... on AnalysisResult {
#       metrics {
#         totalFiles
#         totalLines
#         averageComplexity
#       }
#       files {
#         path
#         language
#         totalLines
#       }
#     }
#   }
# }`;

        ReactDOM.render(
            React.createElement(GraphiQL, {
                fetcher,
                defaultQuery,
                headerEditorEnabled: true,
                shouldPersistHeaders: true,
            }),
            document.getElementById('graphiql'),
        );
    </script>
</body>
</html>"""

        output_file = self.output_dir / "interactive.html"
        with open(output_file, 'w') as f:
            f.write(html_content)
            
        return str(output_file)
    
    def generate_postman_collection(self) -> str:
        """Generate Postman collection for GraphQL API testing."""
        collection = {
            "info": {
                "name": "AST Viewer GraphQL API",
                "description": "Complete collection for testing AST Viewer Code Intelligence API",
                "version": "2.0.0",
                "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
            },
            "variable": [
                {
                    "key": "baseUrl",
                    "value": "http://localhost:8000",
                    "type": "string"
                },
                {
                    "key": "authToken",
                    "value": "",
                    "type": "string"
                }
            ],
            "item": [
                {
                    "name": "File Analysis",
                    "request": {
                        "method": "POST",
                        "header": [
                            {
                                "key": "Content-Type",
                                "value": "application/json"
                            }
                        ],
                        "body": {
                            "mode": "graphql",
                            "graphql": {
                                "query": GraphQLUsageExamples.basic_query_example(),
                                "variables": json.dumps({
                                    "input": {
                                        "filePath": "/path/to/your/file.py",
                                        "includeIntelligence": True
                                    }
                                }, indent=2)
                            }
                        },
                        "url": {
                            "raw": "{{baseUrl}}/graphql",
                            "host": ["{{baseUrl}}"],
                            "path": ["graphql"]
                        }
                    }
                },
                {
                    "name": "Project Analysis",
                    "request": {
                        "method": "POST",
                        "header": [
                            {
                                "key": "Content-Type",
                                "value": "application/json"
                            }
                        ],
                        "body": {
                            "mode": "graphql",
                            "graphql": {
                                "query": GraphQLUsageExamples.complex_query_with_dataloaders(),
                                "variables": json.dumps({
                                    "input": {
                                        "directoryPath": "/path/to/your/project",
                                        "recursive": True
                                    }
                                }, indent=2)
                            }
                        },
                        "url": {
                            "raw": "{{baseUrl}}/graphql",
                            "host": ["{{baseUrl}}"],
                            "path": ["graphql"]
                        }
                    }
                },
                {
                    "name": "Schema Introspection",
                    "request": {
                        "method": "POST",
                        "header": [
                            {
                                "key": "Content-Type",
                                "value": "application/json"
                            }
                        ],
                        "body": {
                            "mode": "graphql",
                            "graphql": {
                                "query": GraphQLUsageExamples.introspection_query()
                            }
                        },
                        "url": {
                            "raw": "{{baseUrl}}/graphql",
                            "host": ["{{baseUrl}}"],
                            "path": ["graphql"]
                        }
                    }
                }
            ]
        }
        
        output_file = self.output_dir / "postman_collection.json"
        with open(output_file, 'w') as f:
            json.dump(collection, f, indent=2)
            
        return str(output_file)


def generate_docs_cli():
    """Command-line interface for generating documentation."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate GraphQL API documentation")
    parser.add_argument("--output-dir", default="docs/graphql", help="Output directory for docs")
    parser.add_argument("--format", choices=["all", "sdl", "json", "examples", "interactive"], 
                       default="all", help="Documentation format to generate")
    
    args = parser.parse_args()
    
    generator = GraphQLDocumentationGenerator(args.output_dir)
    
    if args.format == "all":
        files = generator.generate_all_docs()
        print("Generated documentation files:")
        for name, path in files.items():
            print(f"  - {name}: {path}")
    elif args.format == "sdl":
        path = generator.generate_schema_sdl()
        print(f"Generated SDL: {path}")
    elif args.format == "json":
        path = generator.generate_schema_json()
        print(f"Generated JSON schema: {path}")
    elif args.format == "examples":
        path = generator.generate_example_queries()
        print(f"Generated examples: {path}")
    elif args.format == "interactive":
        path = generator.generate_interactive_docs()
        print(f"Generated interactive docs: {path}")


if __name__ == "__main__":
    generate_docs_cli()
