"""Neo4j database client for code intelligence graph storage."""

import logging
import os
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
import json

from neo4j import GraphDatabase, Driver, Session, Transaction
from neo4j.exceptions import ServiceUnavailable, AuthError

from ..models.universal import (
    CodeIntelligence, UniversalNode, UniversalFile, Relationship, Reference,
    RelationType, ElementType, Language, SourceLocation
)
from ..common.database import BaseDataClient

logger = logging.getLogger(__name__)


class Neo4jClient(BaseDataClient):
    """Client for interacting with Neo4j graph database."""
    
    def __init__(self, uri: Optional[str] = None, username: Optional[str] = None, password: Optional[str] = None):
        super().__init__(
            connection_string=uri,
            username=username,
            password=password,
            connection_env_var="NEO4J_URI",
            username_env_var="NEO4J_USERNAME", 
            password_env_var="NEO4J_PASSWORD",
            default_connection="bolt://localhost:7687"
        )
        
        # Neo4j specific properties
        self.uri = self.connection_string  # Alias for backward compatibility
        self.driver: Optional[Driver] = None
        
    # BaseDataClient implementation methods
    def _create_connection(self) -> Driver:
        """Create Neo4j driver connection."""
        return GraphDatabase.driver(
            self.uri,
            auth=(self.username, self.password),
            encrypted=False,  # Set to True for production with SSL
            max_connection_lifetime=3600,
            max_connection_pool_size=50,
            connection_acquisition_timeout=60
        )
    
    def _test_connection(self) -> bool:
        """Test Neo4j connection with a simple query."""
        try:
            with self.driver.session() as session:
                result = session.run("RETURN 1 AS test")
                test_value = result.single()["test"]
                return test_value == 1
        except Exception:
            return False
    
    def _close_connection(self) -> None:
        """Close Neo4j driver connection."""
        if self.driver:
            self.driver.close()
            self.driver = None
    
    @property
    def connection_type(self) -> str:
        """Return connection type for logging."""
        return "Neo4j"
    
    @property 
    def driver(self) -> Optional[Driver]:
        """Get the Neo4j driver (for backward compatibility)."""
        return self._connection
    
    @driver.setter
    def driver(self, value: Optional[Driver]) -> None:
        """Set the Neo4j driver (for backward compatibility)."""
        self._connection = value
    
    def execute_query(self, query: str, parameters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Execute a Cypher query and return results."""
        if not self.ensure_connection():
            raise ConnectionError("Cannot connect to Neo4j database")
        
        try:
            with self.driver.session() as session:
                result = session.run(query, parameters or {})
                return [record.data() for record in result]
        except Exception as e:
            logger.error(f"Error executing query: {e}")
            raise
    
    def execute_write_query(self, query: str, parameters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Execute a write query in a transaction."""
        if not self.ensure_connection():
            raise ConnectionError("Cannot connect to Neo4j database")
        
        def write_transaction(tx: Transaction):
            result = tx.run(query, parameters or {})
            return [record.data() for record in result]
        
        try:
            with self.driver.session() as session:
                return session.execute_write(write_transaction)
        except Exception as e:
            logger.error(f"Error executing write query: {e}")
            raise
    
    def store_code_intelligence(self, intelligence: CodeIntelligence) -> bool:
        """Store complete code intelligence data in Neo4j."""
        if not self.ensure_connection():
            return False
        
        try:
            with self.driver.session() as session:
                # Start transaction
                with session.begin_transaction() as tx:
                    # 1. Create/update project
                    self._store_project(tx, intelligence)
                    
                    # 2. Store files
                    for file_path, file_obj in intelligence.files.items():
                        self._store_file(tx, file_obj, intelligence.project_id)
                    
                    # 3. Store symbols
                    for symbol_id, symbol in intelligence.symbols.items():
                        self._store_symbol(tx, symbol, intelligence.project_id)
                    
                    # 4. Store relationships
                    for relationship in intelligence.relationships:
                        self._store_relationship(tx, relationship, intelligence.project_id)
                    
                    # 5. Store references
                    for symbol_id, references in intelligence.references.items():
                        for reference in references:
                            self._store_reference(tx, reference, intelligence.project_id)
                    
                    # Commit transaction
                    tx.commit()
                    
            logger.info(f"Successfully stored intelligence for project {intelligence.project_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to store code intelligence: {e}")
            return False
    
    def _store_project(self, tx: Transaction, intelligence: CodeIntelligence):
        """Store project information."""
        query = """
        MERGE (p:Project {id: $project_id})
        SET p.updated_at = datetime(),
            p.total_symbols = $total_symbols,
            p.total_files = $total_files,
            p.total_relationships = $total_relationships,
            p.total_references = $total_references
        """
        
        tx.run(query, {
            "project_id": intelligence.project_id,
            "total_symbols": len(intelligence.symbols),
            "total_files": len(intelligence.files),
            "total_relationships": len(intelligence.relationships),
            "total_references": sum(len(refs) for refs in intelligence.references.values())
        })
    
    def _store_file(self, tx: Transaction, file_obj: UniversalFile, project_id: str):
        """Store file information."""
        query = """
        MERGE (f:File {path: $path})
        SET f.language = $language,
            f.total_lines = $total_lines,
            f.code_lines = $code_lines,
            f.imports = $imports,
            f.exports = $exports,
            f.complexity = $complexity,
            f.maintainability_index = $maintainability_index,
            f.updated_at = datetime()
        
        WITH f
        MATCH (p:Project {id: $project_id})
        MERGE (p)-[:CONTAINS]->(f)
        """
        
        tx.run(query, {
            "path": file_obj.path,
            "language": file_obj.language.value,
            "total_lines": file_obj.total_lines,
            "code_lines": file_obj.code_lines,
            "imports": file_obj.imports,
            "exports": file_obj.exports,
            "complexity": file_obj.complexity,
            "maintainability_index": file_obj.maintainability_index,
            "project_id": project_id
        })
    
    def _store_symbol(self, tx: Transaction, symbol: UniversalNode, project_id: str):
        """Store symbol information."""
        query = """
        MERGE (s:Symbol {id: $id})
        SET s.name = $name,
            s.type = $type,
            s.language = $language,
            s.file_path = $file_path,
            s.start_line = $start_line,
            s.end_line = $end_line,
            s.start_column = $start_column,
            s.end_column = $end_column,
            s.complexity = $complexity,
            s.cognitive_complexity = $cognitive_complexity,
            s.lines_of_code = $lines_of_code,
            s.access_level = $access_level,
            s.is_abstract = $is_abstract,
            s.is_static = $is_static,
            s.is_async = $is_async,
            s.docstring = $docstring,
            s.tree_sitter_type = $tree_sitter_type,
            s.updated_at = datetime()
        
        WITH s
        MATCH (f:File {path: $file_path})
        MERGE (f)-[:CONTAINS]->(s)
        
        WITH s
        MATCH (p:Project {id: $project_id})
        MERGE (p)-[:HAS_SYMBOL]->(s)
        """
        
        tx.run(query, {
            "id": symbol.id,
            "name": symbol.name,
            "type": symbol.type.name,
            "language": symbol.language.value,
            "file_path": symbol.location.file_path,
            "start_line": symbol.location.start_line,
            "end_line": symbol.location.end_line,
            "start_column": symbol.location.start_column,
            "end_column": symbol.location.end_column,
            "complexity": symbol.complexity,
            "cognitive_complexity": getattr(symbol, 'cognitive_complexity', 1),
            "lines_of_code": symbol.lines_of_code,
            "access_level": symbol.access_level.value if symbol.access_level else None,
            "is_abstract": symbol.is_abstract,
            "is_static": symbol.is_static,
            "is_async": symbol.is_async,
            "docstring": symbol.docstring,
            "tree_sitter_type": getattr(symbol, 'tree_sitter_type', None),
            "project_id": project_id
        })
        
        # Handle parent-child relationships
        if symbol.parent_id:
            parent_query = """
            MATCH (parent:Symbol {id: $parent_id})
            MATCH (child:Symbol {id: $child_id})
            MERGE (parent)-[:CONTAINS]->(child)
            """
            tx.run(parent_query, {
                "parent_id": symbol.parent_id,
                "child_id": symbol.id
            })
    
    def _store_relationship(self, tx: Transaction, relationship: Relationship, project_id: str):
        """Store relationship between symbols."""
        query = """
        MATCH (source:Symbol {id: $source_id})
        MATCH (target:Symbol {id: $target_id})
        MERGE (source)-[r:RELATES_TO {
            id: $rel_id,
            type: $rel_type
        }]->(target)
        SET r.confidence = $confidence,
            r.context = $context,
            r.updated_at = datetime()
        """
        
        tx.run(query, {
            "source_id": relationship.source_id,
            "target_id": relationship.target_id,
            "rel_id": relationship.id,
            "rel_type": relationship.type.value,
            "confidence": relationship.confidence,
            "context": relationship.context
        })
    
    def _store_reference(self, tx: Transaction, reference: Reference, project_id: str):
        """Store symbol reference."""
        query = """
        MATCH (s:Symbol {id: $symbol_id})
        MERGE (r:Reference {id: $ref_id})
        SET r.file_path = $file_path,
            r.start_line = $start_line,
            r.end_line = $end_line,
            r.start_column = $start_column,
            r.end_column = $end_column,
            r.kind = $kind,
            r.is_definition = $is_definition,
            r.context = $context,
            r.updated_at = datetime()
        
        MERGE (s)-[:REFERENCED_AT]->(r)
        """
        
        tx.run(query, {
            "symbol_id": reference.symbol_id,
            "ref_id": reference.id,
            "file_path": reference.location.file_path,
            "start_line": reference.location.start_line,
            "end_line": reference.location.end_line,
            "start_column": reference.location.start_column,
            "end_column": reference.location.end_column,
            "kind": reference.kind,
            "is_definition": reference.is_definition,
            "context": reference.context
        })
    
    def get_project_overview(self, project_id: str) -> Dict[str, Any]:
        """Get project overview statistics."""
        query = """
        MATCH (p:Project {id: $project_id})
        OPTIONAL MATCH (p)-[:CONTAINS]->(f:File)
        OPTIONAL MATCH (p)-[:HAS_SYMBOL]->(s:Symbol)
        OPTIONAL MATCH (s)-[r:RELATES_TO]->()
        RETURN 
            p.id as project_id,
            count(DISTINCT f) as total_files,
            count(DISTINCT s) as total_symbols,
            count(DISTINCT r) as total_relationships,
            collect(DISTINCT f.language) as languages,
            avg(s.complexity) as avg_complexity
        """
        
        result = self.execute_query(query, {"project_id": project_id})
        return result[0] if result else {}
    
    def get_symbols_by_type(self, project_id: str, symbol_type: str) -> List[Dict[str, Any]]:
        """Get all symbols of a specific type."""
        query = """
        MATCH (p:Project {id: $project_id})-[:HAS_SYMBOL]->(s:Symbol {type: $symbol_type})
        RETURN s.id, s.name, s.file_path, s.complexity, s.lines_of_code
        ORDER BY s.complexity DESC
        """
        
        return self.execute_query(query, {
            "project_id": project_id,
            "symbol_type": symbol_type
        })
    
    def get_call_graph(self, symbol_id: str, max_depth: int = 3) -> Dict[str, Any]:
        """Get call graph for a symbol."""
        query = """
        MATCH path = (s:Symbol {id: $symbol_id})-[:RELATES_TO* {type: "CALLS"}..{max_depth}]->(target:Symbol)
        RETURN path
        """.format(max_depth=max_depth)
        
        paths = self.execute_query(query, {"symbol_id": symbol_id})
        
        # Convert paths to nodes and edges
        nodes = set()
        edges = []
        
        for path_data in paths:
            path = path_data["path"]
            # Extract nodes and relationships from path
            # This would need more detailed implementation based on Neo4j path structure
        
        return {
            "nodes": list(nodes),
            "edges": edges,
            "root_symbol": symbol_id
        }
    
    def get_dependencies(self, project_id: str) -> List[Dict[str, Any]]:
        """Get dependency relationships for a project."""
        query = """
        MATCH (p:Project {id: $project_id})-[:HAS_SYMBOL]->(s1:Symbol)
        MATCH (s1)-[r:RELATES_TO {type: "USES"}]->(s2:Symbol)
        RETURN s1.id as source, s2.id as target, r.type as relationship,
               s1.name as source_name, s2.name as target_name,
               s1.file_path as source_file, s2.file_path as target_file
        """
        
        return self.execute_query(query, {"project_id": project_id})
    
    def find_circular_dependencies(self, project_id: str) -> List[List[str]]:
        """Find circular dependencies in the project."""
        query = """
        MATCH (p:Project {id: $project_id})-[:HAS_SYMBOL]->(s:Symbol)
        MATCH path = (s)-[:RELATES_TO* {type: "USES"}]->(s)
        WHERE length(path) > 1 AND length(path) <= 10
        RETURN [node in nodes(path) | node.id] as cycle
        LIMIT 50
        """
        
        results = self.execute_query(query, {"project_id": project_id})
        return [result["cycle"] for result in results]
    
    def get_high_complexity_symbols(self, project_id: str, min_complexity: float = 10.0) -> List[Dict[str, Any]]:
        """Get symbols with high complexity."""
        query = """
        MATCH (p:Project {id: $project_id})-[:HAS_SYMBOL]->(s:Symbol)
        WHERE s.complexity >= $min_complexity
        RETURN s.id, s.name, s.type, s.complexity, s.file_path, s.lines_of_code
        ORDER BY s.complexity DESC
        LIMIT 50
        """
        
        return self.execute_query(query, {
            "project_id": project_id,
            "min_complexity": min_complexity
        })
    
    def setup_schema(self) -> bool:
        """Set up Neo4j schema (constraints and indexes)."""
        if not self.ensure_connection():
            return False
        
        schema_queries = [
            # Constraints
            "CREATE CONSTRAINT symbol_id_unique IF NOT EXISTS FOR (s:Symbol) REQUIRE s.id IS UNIQUE",
            "CREATE CONSTRAINT file_path_unique IF NOT EXISTS FOR (f:File) REQUIRE f.path IS UNIQUE",
            "CREATE CONSTRAINT project_id_unique IF NOT EXISTS FOR (p:Project) REQUIRE p.id IS UNIQUE",
            "CREATE CONSTRAINT reference_id_unique IF NOT EXISTS FOR (r:Reference) REQUIRE r.id IS UNIQUE",
            
            # Indexes
            "CREATE INDEX symbol_name_index IF NOT EXISTS FOR (s:Symbol) ON (s.name)",
            "CREATE INDEX symbol_type_index IF NOT EXISTS FOR (s:Symbol) ON (s.type)",
            "CREATE INDEX file_language_index IF NOT EXISTS FOR (f:File) ON (f.language)",
            "CREATE INDEX symbol_complexity_index IF NOT EXISTS FOR (s:Symbol) ON (s.complexity)",
            "CREATE INDEX relationship_type_index IF NOT EXISTS FOR ()-[r:RELATES_TO]-() ON (r.type)",
            
            # Composite indexes
            "CREATE INDEX symbol_file_type_index IF NOT EXISTS FOR (s:Symbol) ON (s.file_path, s.type)",
            "CREATE INDEX symbol_name_type_index IF NOT EXISTS FOR (s:Symbol) ON (s.name, s.type)",
        ]
        
        try:
            for query in schema_queries:
                self.execute_write_query(query)
            
            logger.info("Neo4j schema setup completed")
            return True
            
        except Exception as e:
            logger.error(f"Failed to setup Neo4j schema: {e}")
            return False


def check_neo4j_connection() -> bool:
    """Check if Neo4j is available and accessible."""
    try:
        client = Neo4jClient()
        return client.connect()
    except Exception as e:
        logger.error(f"Neo4j connection check failed: {e}")
        return False
