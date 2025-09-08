# GraphQL Test Payloads for AST Viewer Code Intelligence Platform

This file contains ready-to-use GraphQL payloads for testing the AST Viewer API in the GraphQL playground at http://localhost:8000/graphql

## ✅ Verification Status
- **Field Names**: ✅ Corrected to match camelCase schema
- **Query Structure**: ✅ Verified with actual schema
- **Error Handling**: ✅ Includes proper error types
- **Variables**: ✅ Properly formatted JSON

## 🧪 Quick Verification Tests

### Schema Introspection (Always Works)
```graphql
query TestSchema {
  __schema {
    queryType { name }
    mutationType { name }
    types { name }
  }
}
```

### Basic Symbol Search (Safe Test)
```graphql
query TestSymbolSearch {
  searchSymbols(input: {
    query: "test"
    caseSensitive: false
    limit: 5
  }) {
    id
    name
    type
    language
    displayName
  }
}
```

## 🚀 GitHub Repository Analysis

### 1. Basic GitHub Repository Analysis
```graphql
mutation AnalyzeGitHubRepo {
  analyzeProject(input: {
    githubUrl: "https://github.com/pedroanisio/ast-viewer"
    projectName: "External AST Viewer Analysis"
    includeIntelligence: true
    includeRelationships: true
    includeReferences: true
    includeCallGraph: true
    includeDependencyGraph: true
    recursive: true
    maxFiles: 10
    shallowClone: true
    cloneDepth: 1
  }) {
    ... on AnalysisResult {
      files {
        path
        language
        size
        linesOfCode
        astNodes {
          id
          name
          type
          sourceLocation {
            filePath
            lineNumber
            columnNumber
          }
          cyclomaticComplexity
          cognitiveComplexity
        }
      }
      projectMetrics {
        totalFiles
        totalLines
        totalFunctions
        totalClasses
        averageComplexity
        maxComplexity
        maintainabilityScore
        technicalDebtRatio
      }
      intelligenceData {
        totalSymbols
        totalRelationships
        totalReferences
      }
      analysisTime
      timestamp
      analyzerVersion
    }
    ... on ValidationError {
      message
      field
    }
    ... on AnalysisError {
      message
      filePath
      errorType
    }
    ... on DirectoryNotFoundError {
      message
    }
  }
}
```

### 2. GitHub Repository with Specific Branch
```graphql
mutation AnalyzeGitHubRepoBranch {
  analyzeProject(input: {
    githubUrl: "https://github.com/pedroanisio/ast-viewer"
    branch: "main"
    projectName: "Main Branch Analysis"
    includeIntelligence: true
    maxFiles: 15
    shallowClone: true
    cloneDepth: 1
    fileExtensions: [".py", ".js", ".ts"]
  }) {
    ... on AnalysisResult {
      files {
        path
        language
        linesOfCode
      }
      projectMetrics {
        totalFiles
        totalLines
        totalFunctions
        averageComplexity
      }
      analysisTime
    }
    ... on ValidationError {
      message
      field
    }
    ... on AnalysisError {
      message
      filePath
      errorType
    }
  }
}
```

### 3. Another GitHub Repository Example
```graphql
mutation AnalyzeFlaskRepo {
  analyzeProject(input: {
    githubUrl: "https://github.com/pallets/flask"
    projectName: "Flask Framework Analysis"
    includeIntelligence: true
    includeRelationships: true
    recursive: true
    maxFiles: 20
    shallowClone: true
    cloneDepth: 1
    fileExtensions: [".py"]
    excludePatterns: ["test", "__pycache__", ".git"]
  }) {
    ... on AnalysisResult {
      files {
        path
        language
        linesOfCode
        astNodes {
          name
          type
          cyclomaticComplexity
        }
      }
      projectMetrics {
        totalFiles
        totalLines
        totalFunctions
        totalClasses
        averageComplexity
        maxComplexity
        maintainabilityScore
      }
      intelligenceData {
        totalSymbols
        totalRelationships
        totalReferences
      }
      analysisTime
      timestamp
    }
    ... on AnalysisError {
      message
      filePath
      errorType
    }
  }
}
```

## 📁 Local Directory Analysis

### 4. Local Directory Analysis
```graphql
query AnalyzeLocalDirectory {
  analyzeDirectory(input: {
    directoryPath: "/app/src"
    recursive: true
    includeIntelligence: true
    maxFiles: 50
    fileExtensions: [".py", ".js", ".ts"]
  }) {
    ... on AnalysisResult {
      files {
        path
        language
        size
        linesOfCode
      }
      metrics {
        totalFiles
        totalLines
        totalNodes
        averageComplexity
        maxComplexity
      }
    }
    ... on DirectoryNotFoundError {
      message
    }
    ... on AnalysisError {
      message
    }
  }
}
```

## 📄 Individual File Analysis

### 5. Single File Analysis
```graphql
query AnalyzeSingleFile {
  analyzeFile(input: {
    filePath: "/app/src/ast_viewer/api/main.py"
    includeIntelligence: true
    includeRelationships: true
    includeReferences: true
  }) {
    ... on UniversalFileType {
      path
      language
      size
      linesOfCode
      astNodes {
        id
        name
        type
        sourceLocation {
          filePath
          lineNumber
          columnNumber
        }
        cyclomaticComplexity
        cognitiveComplexity
        docstring
        parameters
        returnType
      }
    }
    ... on FileNotFoundError {
      message
    }
    ... on AnalysisError {
      message
    }
  }
}
```

## 🔍 Symbol Search

### 6. Search for Functions
```graphql
query SearchFunctions {
  searchSymbols(input: {
    query: "analyze"
    symbolTypes: ["function", "method"]
    caseSensitive: false
    limit: 20
  }) {
    id
    name
    type
    language
    displayName
    complexityLevel
    referencesCount
  }
}
```

### 7. Search for Classes
```graphql
query SearchClasses {
  searchSymbols(input: {
    query: "Analyzer"
    symbolTypes: ["class"]
    exactMatch: false
    limit: 10
  }) {
    id
    name
    type
    language
    displayName
    complexityLevel
    relatedSymbols(limit: 5) {
      id
      name
      type
    }
  }
}
```

## 🔧 Utility Operations

### 8. Get Symbol Details
```graphql
query GetSymbolDetails {
  getSymbol(symbolId: "example-symbol-id-123") {
    ... on UniversalNodeTypeEnhanced {
      id
      name
      type
      language
      displayName
      complexityLevel
      referencesCount
      relatedSymbols(limit: 5) {
        id
        name
        type
        displayName
      }
    }
    ... on ValidationError {
      message
      field
    }
    ... on InternalError {
      message
    }
  }
}
```

### 9. Refresh Analysis Cache
```graphql
mutation RefreshCache {
  refreshAnalysis(projectId: "example-project-id") 
}
```

## 🧪 Test Scenarios

### 10. Small Repository Test
```graphql
mutation TestSmallRepo {
  analyzeProject(input: {
    githubUrl: "https://github.com/requests/requests"
    projectName: "Requests Library Test"
    includeIntelligence: false
    includeRelationships: false
    includeReferences: false
    includeCallGraph: false
    includeDependencyGraph: false
    recursive: true
    maxFiles: 5
    shallowClone: true
    cloneDepth: 1
    fileExtensions: [".py"]
  }) {
    ... on AnalysisResult {
      files {
        path
        language
        linesOfCode
      }
      projectMetrics {
        totalFiles
        totalLines
        totalFunctions
      }
      analysisTime
    }
    ... on AnalysisError {
      message
      errorType
    }
  }
}
```

### 11. Error Testing - Invalid URL
```graphql
mutation TestInvalidUrl {
  analyzeProject(input: {
    githubUrl: "https://invalid-url.com/repo"
    projectName: "Error Test"
    includeIntelligence: true
    maxFiles: 10
    shallowClone: true
  }) {
    ... on AnalysisResult {
      analysisTime
    }
    ... on ValidationError {
      message
      field
    }
    ... on AnalysisError {
      message
      filePath
      errorType
    }
  }
}
```

### 12. Error Testing - Both Inputs Provided
```graphql
mutation TestBothInputs {
  analyzeProject(input: {
    directoryPath: "/app/src"
    githubUrl: "https://github.com/pedroanisio/ast-viewer"
    projectName: "Error Test"
    includeIntelligence: true
    maxFiles: 10
  }) {
    ... on AnalysisResult {
      analysisTime
    }
    ... on ValidationError {
      message
      field
    }
    ... on AnalysisError {
      message
      filePath
      errorType
    }
  }
}
```

## 📊 Variables Examples

You can also use variables in the GraphQL playground. Here are some example variables:

### Variables for GitHub Analysis:
```json
{
  "input": {
    "githubUrl": "https://github.com/pedroanisio/ast-viewer",
    "projectName": "Variable-based Analysis",
    "includeIntelligence": true,
    "includeRelationships": true,
    "includeReferences": true,
    "includeCallGraph": true,
    "includeDependencyGraph": true,
    "recursive": true,
    "maxFiles": 15,
    "shallowClone": true,
    "cloneDepth": 1,
    "fileExtensions": [".py", ".js", ".ts"],
    "excludePatterns": ["test", "tests", "__pycache__", ".git"]
  }
}
```

### Variables for File Analysis:
```json
{
  "input": {
    "filePath": "/app/src/ast_viewer/api/main.py",
    "includeIntelligence": true,
    "includeRelationships": true,
    "includeReferences": true
  }
}
```

### Variables for Symbol Search:
```json
{
  "input": {
    "query": "GraphQL",
    "symbolTypes": ["class", "function"],
    "caseSensitive": false,
    "exactMatch": false,
    "limit": 25,
    "offset": 0
  }
}
```

## 🎯 Usage Tips

1. **Start Small**: Begin with `maxFiles: 5-10` to test quickly
2. **Use Shallow Clone**: Always use `shallowClone: true` for faster GitHub analysis
3. **Filter Files**: Use `fileExtensions` to focus on specific languages
4. **Exclude Patterns**: Use `excludePatterns` to skip test files, cache directories, etc.
5. **Error Handling**: Always include error union types in your selection sets
6. **Variables**: Use GraphQL variables for reusable queries

## 🔧 Troubleshooting

### Common Field Name Errors
- Use **camelCase** for all field names (e.g., `totalFiles`, not `total_files`)
- Use **caseSensitive** instead of `caseInsensitive` in search inputs
- Available fields for `UniversalNodeTypeEnhanced`: `id`, `name`, `type`, `language`, `displayName`, `complexityLevel`, `referencesCount`, `relatedSymbols`

### GitHub Clone Issues
If you get git clone errors:
1. Try a different repository (e.g., `https://github.com/octocat/Hello-World`)
2. Reduce `maxFiles` to 2-3 for testing
3. Ensure `shallowClone: true` and `cloneDepth: 1`

### Schema Verification
Run this query to check available fields:
```graphql
query IntrospectTypes {
  __type(name: "ProjectMetrics") {
    fields { name type { name } }
  }
}
```

## 🔗 Endpoints

- **GraphQL Playground**: http://localhost:8000/graphql
- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

Copy any of these payloads into the GraphQL playground and click the play button to test the AST Viewer's capabilities! 🚀
