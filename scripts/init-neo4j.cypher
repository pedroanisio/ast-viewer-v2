// AST Viewer Code Intelligence Platform - Neo4j Database Initialization
// This script sets up the graph schema for code intelligence data

// =============================================================================
// CONSTRAINTS AND INDEXES
// =============================================================================

// Symbol constraints
CREATE CONSTRAINT symbol_id_unique IF NOT EXISTS FOR (s:Symbol) REQUIRE s.id IS UNIQUE;
CREATE CONSTRAINT file_path_unique IF NOT EXISTS FOR (f:File) REQUIRE f.path IS UNIQUE;
CREATE CONSTRAINT project_id_unique IF NOT EXISTS FOR (p:Project) REQUIRE p.id IS UNIQUE;

// Performance indexes
CREATE INDEX symbol_name_index IF NOT EXISTS FOR (s:Symbol) ON (s.name);
CREATE INDEX symbol_type_index IF NOT EXISTS FOR (s:Symbol) ON (s.type);
CREATE INDEX file_language_index IF NOT EXISTS FOR (f:File) ON (f.language);
CREATE INDEX symbol_complexity_index IF NOT EXISTS FOR (s:Symbol) ON (s.complexity);
CREATE INDEX relationship_type_index IF NOT EXISTS FOR ()-[r:RELATES_TO]-() ON (r.type);

// Composite indexes for common queries
CREATE INDEX symbol_file_type_index IF NOT EXISTS FOR (s:Symbol) ON (s.file_path, s.type);
CREATE INDEX symbol_name_type_index IF NOT EXISTS FOR (s:Symbol) ON (s.name, s.type);

// =============================================================================
// NODE LABELS AND PROPERTIES
// =============================================================================

// Symbol nodes represent code elements (classes, functions, variables, etc.)
// Properties:
// - id: unique identifier
// - name: symbol name
// - type: ElementType (CLASS, FUNCTION, METHOD, VARIABLE, etc.)
// - language: programming language
// - file_path: source file path
// - start_line, end_line: location in file
// - start_column, end_column: precise location
// - complexity: cyclomatic complexity
// - cognitive_complexity: cognitive complexity
// - lines_of_code: number of lines
// - access_level: PUBLIC, PRIVATE, PROTECTED, etc.
// - is_abstract: boolean for abstract symbols
// - is_static: boolean for static symbols
// - is_async: boolean for async functions
// - docstring: documentation string
// - metadata: additional properties as JSON

// File nodes represent source code files
// Properties:
// - path: file path
// - language: programming language
// - total_lines: total lines in file
// - code_lines: lines containing code
// - imports: list of imports
// - exports: list of exports
// - complexity: file complexity
// - maintainability_index: maintainability score

// Project nodes represent analyzed projects
// Properties:
// - id: project identifier
// - name: project name
// - version: project version
// - created_at: analysis timestamp
// - updated_at: last update timestamp
// - total_files: number of files
// - total_symbols: number of symbols
// - languages: supported languages

// =============================================================================
// RELATIONSHIP TYPES
// =============================================================================

// Code relationship types
// EXTENDS - inheritance relationship
// IMPLEMENTS - interface implementation
// CALLS - function/method calls
// USES - variable/symbol usage
// REFERENCES - symbol references
// INSTANTIATES - object instantiation
// IMPORTS - import statements
// EXPORTS - export statements
// OVERRIDES - method overriding
// OVERRIDDEN_BY - reverse override relationship
// RETURNS - return type relationships
// ACCEPTS - parameter type relationships
// THROWS - exception relationships
// DECORATES - decorator relationships
// ANNOTATES - annotation relationships
// CONTAINS - parent-child relationships
// CONTAINED_IN - reverse containment

// =============================================================================
// EXAMPLE DATA STRUCTURE
// =============================================================================

// Create example project
MERGE (p:Project {
    id: "example-project",
    name: "Example Project",
    version: "1.0.0",
    created_at: datetime(),
    total_files: 0,
    total_symbols: 0,
    languages: ["python", "javascript"]
});

// Create example file
MERGE (f:File {
    path: "src/example.py",
    language: "python",
    total_lines: 50,
    code_lines: 35,
    imports: ["os", "sys"],
    exports: ["ExampleClass"],
    complexity: 5.2
});

// Create example symbols
MERGE (c:Symbol {
    id: "example-class-1",
    name: "ExampleClass",
    type: "CLASS",
    language: "python",
    file_path: "src/example.py",
    start_line: 10,
    end_line: 30,
    start_column: 0,
    end_column: 4,
    complexity: 3,
    cognitive_complexity: 2,
    lines_of_code: 20,
    access_level: "PUBLIC",
    is_abstract: false,
    docstring: "An example class for demonstration"
});

MERGE (m:Symbol {
    id: "example-method-1",
    name: "__init__",
    type: "METHOD",
    language: "python",
    file_path: "src/example.py",
    start_line: 12,
    end_line: 15,
    start_column: 4,
    end_column: 8,
    complexity: 1,
    cognitive_complexity: 1,
    lines_of_code: 3,
    access_level: "PUBLIC",
    is_abstract: false,
    is_static: false,
    is_async: false,
    docstring: "Initialize the example class"
});

// Create relationships
MERGE (p)-[:CONTAINS]->(f);
MERGE (f)-[:CONTAINS]->(c);
MERGE (c)-[:CONTAINS]->(m);

// =============================================================================
// USEFUL QUERIES FOR CODE INTELLIGENCE
// =============================================================================

// Find all classes in a project
// MATCH (p:Project {id: "project-id"})-[:CONTAINS*]->(s:Symbol {type: "CLASS"})
// RETURN s.name, s.file_path, s.complexity;

// Find all methods of a class
// MATCH (c:Symbol {type: "CLASS", name: "ClassName"})-[:CONTAINS]->(m:Symbol {type: "METHOD"})
// RETURN m.name, m.complexity, m.lines_of_code;

// Find call relationships
// MATCH (s1:Symbol)-[r:RELATES_TO {type: "CALLS"}]->(s2:Symbol)
// RETURN s1.name, s2.name, r.confidence;

// Find inheritance hierarchy
// MATCH path = (s:Symbol {type: "CLASS"})-[:RELATES_TO* {type: "EXTENDS"}]->(parent:Symbol)
// RETURN path;

// Find symbols with high complexity
// MATCH (s:Symbol)
// WHERE s.complexity > 10
// RETURN s.name, s.type, s.complexity, s.file_path
// ORDER BY s.complexity DESC;

// Find most referenced symbols
// MATCH (s:Symbol)<-[r:RELATES_TO {type: "REFERENCES"}]-()
// RETURN s.name, s.type, count(r) as reference_count
// ORDER BY reference_count DESC
// LIMIT 10;

// Find circular dependencies
// MATCH path = (s1:Symbol)-[:RELATES_TO* {type: "USES"}]->(s1)
// WHERE length(path) > 1
// RETURN path;

// =============================================================================
// PERFORMANCE RECOMMENDATIONS
// =============================================================================

// 1. Use periodic commits for large data loads:
// USING PERIODIC COMMIT 1000
// LOAD CSV WITH HEADERS FROM 'file:///symbols.csv' AS row
// CREATE (s:Symbol {id: row.id, name: row.name, type: row.type});

// 2. Use parameters for frequent queries:
// MATCH (s:Symbol {type: $symbolType})
// WHERE s.complexity > $minComplexity
// RETURN s;

// 3. Create specialized indexes for your query patterns
// 4. Use EXPLAIN and PROFILE to optimize queries
// 5. Consider using APOC procedures for complex operations
