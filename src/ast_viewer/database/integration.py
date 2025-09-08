"""Database integration module that connects Neo4j and PostgreSQL with the intelligence system."""

import logging
import asyncio
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import uuid

from .neo4j_client import Neo4jClient
from .postgres_client import PostgresClient
from ..models.universal import CodeIntelligence, UniversalFile
from ..analyzers.integrated import IntegratedCodeAnalyzer

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Central database manager that coordinates between Neo4j and PostgreSQL."""
    
    def __init__(self):
        self.neo4j_client = Neo4jClient()
        self.postgres_client = PostgresClient()
        self._connected = False
    
    async def connect(self) -> bool:
        """Connect to both databases."""
        try:
            # Connect to PostgreSQL
            postgres_ok = await self.postgres_client.connect()
            if not postgres_ok:
                logger.error("Failed to connect to PostgreSQL")
                return False
            
            # Connect to Neo4j
            neo4j_ok = self.neo4j_client.connect()
            if not neo4j_ok:
                logger.error("Failed to connect to Neo4j")
                return False
            
            self._connected = True
            logger.info("Successfully connected to both databases")
            return True
            
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            return False
    
    async def disconnect(self):
        """Disconnect from both databases."""
        try:
            await self.postgres_client.disconnect()
            self.neo4j_client.disconnect()
            self._connected = False
            logger.info("Disconnected from databases")
        except Exception as e:
            logger.error(f"Error disconnecting from databases: {e}")
    
    def is_connected(self) -> bool:
        """Check if connected to both databases."""
        return (self._connected and 
                self.postgres_client.is_connected() and 
                self.neo4j_client.is_connected())
    
    async def store_project_analysis(self, 
                                   project_id: str,
                                   project_name: str,
                                   owner_id: str,
                                   intelligence: CodeIntelligence,
                                   analysis_config: Dict[str, Any] = None) -> bool:
        """Store complete project analysis in both databases."""
        if not self.is_connected():
            logger.error("Not connected to databases")
            return False
        
        try:
            # Start by creating/updating project in PostgreSQL
            pg_project_id = await self._ensure_project_exists(
                project_id, project_name, owner_id, analysis_config
            )
            
            if not pg_project_id:
                logger.error("Failed to create/update project in PostgreSQL")
                return False
            
            # Create analysis run record
            run_id = await self._create_analysis_run(pg_project_id, owner_id, analysis_config)
            if not run_id:
                logger.error("Failed to create analysis run")
                return False
            
            # Store intelligence data in Neo4j
            neo4j_success = self.neo4j_client.store_code_intelligence(intelligence)
            if not neo4j_success:
                logger.error("Failed to store intelligence in Neo4j")
                await self._mark_analysis_failed(run_id)
                return False
            
            # Store file analysis results in PostgreSQL
            await self._store_file_analyses(run_id, pg_project_id, intelligence.files)
            
            # Update project with analysis results
            await self._update_project_analysis_results(pg_project_id, intelligence, run_id)
            
            # Mark analysis as completed
            await self._mark_analysis_completed(run_id, intelligence)
            
            logger.info(f"Successfully stored project analysis for {project_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to store project analysis: {e}")
            if 'run_id' in locals():
                await self._mark_analysis_failed(run_id, str(e))
            return False
    
    async def get_project_intelligence(self, project_id: str) -> Optional[Dict[str, Any]]:
        """Get combined project intelligence from both databases."""
        try:
            # Get project metadata from PostgreSQL
            project_data = await self.postgres_client.get_project_by_id(project_id)
            if not project_data:
                return None
            
            # Get graph data from Neo4j
            neo4j_project_id = project_data.get('neo4j_project_id', f"project:{project_id}")
            graph_overview = self.neo4j_client.get_project_overview(neo4j_project_id)
            
            # Get recent analysis runs
            recent_runs = await self.postgres_client.get_recent_analysis_runs(project_id, limit=5)
            
            return {
                'project': project_data,
                'graph_overview': graph_overview,
                'recent_analyses': recent_runs,
                'combined_stats': {
                    'total_files': project_data.get('total_files', 0),
                    'total_symbols': project_data.get('total_symbols', 0),
                    'total_lines': project_data.get('total_lines', 0),
                    'last_analysis': project_data.get('last_analysis_at'),
                    'neo4j_symbols': graph_overview.get('total_symbols', 0),
                    'neo4j_relationships': graph_overview.get('total_relationships', 0),
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to get project intelligence: {e}")
            return None
    
    async def analyze_and_store_project(self, 
                                      project_path: str,
                                      project_name: str,
                                      owner_id: str,
                                      config: Dict[str, Any] = None) -> Optional[str]:
        """Analyze a project and store results in both databases."""
        try:
            # Generate project ID
            project_id = str(uuid.uuid4())
            
            # Perform analysis using IntegratedCodeAnalyzer
            analyzer = IntegratedCodeAnalyzer()
            analysis_result = analyzer.analyze_project(project_path, project_name)
            
            if not analysis_result:
                logger.error("Project analysis failed")
                return None
            
            # Get the intelligence data
            intelligence = analyzer.get_intelligence(f"project:{project_name}")
            if not intelligence:
                logger.error("No intelligence data generated")
                return None
            
            # Store in databases
            success = await self.store_project_analysis(
                project_id, project_name, owner_id, intelligence, config
            )
            
            if success:
                logger.info(f"Successfully analyzed and stored project: {project_name}")
                return project_id
            else:
                logger.error("Failed to store analysis results")
                return None
            
        except Exception as e:
            logger.error(f"Failed to analyze and store project: {e}")
            return None
    
    async def get_user_projects(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all projects accessible by a user."""
        try:
            projects = await self.postgres_client.get_user_projects(user_id)
            
            # Enrich with Neo4j data
            for project in projects:
                neo4j_id = project.get('neo4j_project_id')
                if neo4j_id:
                    overview = self.neo4j_client.get_project_overview(neo4j_id)
                    project['graph_stats'] = overview
            
            return projects
            
        except Exception as e:
            logger.error(f"Failed to get user projects: {e}")
            return []
    
    async def get_symbol_details(self, project_id: str, symbol_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed symbol information from Neo4j."""
        try:
            # Get project Neo4j ID
            project_data = await self.postgres_client.get_project_by_id(project_id)
            if not project_data:
                return None
            
            neo4j_project_id = project_data.get('neo4j_project_id', f"project:{project_id}")
            
            # Query Neo4j for symbol details
            query = """
            MATCH (p:Project {id: $project_id})-[:HAS_SYMBOL]->(s:Symbol {id: $symbol_id})
            OPTIONAL MATCH (s)-[r:RELATES_TO]->(target:Symbol)
            OPTIONAL MATCH (source:Symbol)-[r2:RELATES_TO]->(s)
            RETURN s as symbol,
                   collect(DISTINCT {target: target, relationship: r.type, confidence: r.confidence}) as outgoing,
                   collect(DISTINCT {source: source, relationship: r2.type, confidence: r2.confidence}) as incoming
            """
            
            results = self.neo4j_client.execute_query(query, {
                'project_id': neo4j_project_id,
                'symbol_id': symbol_id
            })
            
            if results:
                return results[0]
            return None
            
        except Exception as e:
            logger.error(f"Failed to get symbol details: {e}")
            return None
    
    async def search_symbols(self, 
                           project_id: str, 
                           query: str, 
                           symbol_type: str = None,
                           limit: int = 50) -> List[Dict[str, Any]]:
        """Search symbols in a project."""
        try:
            # Get project Neo4j ID
            project_data = await self.postgres_client.get_project_by_id(project_id)
            if not project_data:
                return []
            
            neo4j_project_id = project_data.get('neo4j_project_id', f"project:{project_id}")
            
            # Build Neo4j query
            cypher_query = """
            MATCH (p:Project {id: $project_id})-[:HAS_SYMBOL]->(s:Symbol)
            WHERE toLower(s.name) CONTAINS toLower($query)
            """
            
            params = {
                'project_id': neo4j_project_id,
                'query': query
            }
            
            if symbol_type:
                cypher_query += " AND s.type = $symbol_type"
                params['symbol_type'] = symbol_type
            
            cypher_query += " RETURN s ORDER BY s.name LIMIT $limit"
            params['limit'] = limit
            
            results = self.neo4j_client.execute_query(cypher_query, params)
            return [result['s'] for result in results]
            
        except Exception as e:
            logger.error(f"Failed to search symbols: {e}")
            return []
    
    # Helper methods
    async def _ensure_project_exists(self, 
                                   project_id: str,
                                   project_name: str, 
                                   owner_id: str,
                                   config: Dict[str, Any] = None) -> Optional[str]:
        """Ensure project exists in PostgreSQL."""
        try:
            # Check if project already exists
            existing = await self.postgres_client.get_project_by_id(project_id)
            if existing:
                return str(existing['id'])
            
            # Create new project
            project_data = {
                'id': project_id,
                'name': project_name,
                'slug': project_name.lower().replace(' ', '-'),
                'owner_id': owner_id,
                'analysis_config': config or {},
                'neo4j_project_id': f"project:{project_name}",
                'status': 'active'
            }
            
            return await self.postgres_client.create_project(project_data)
            
        except Exception as e:
            logger.error(f"Failed to ensure project exists: {e}")
            return None
    
    async def _create_analysis_run(self, 
                                 project_id: str,
                                 user_id: str,
                                 config: Dict[str, Any] = None) -> Optional[str]:
        """Create analysis run record."""
        try:
            run_data = {
                'project_id': project_id,
                'triggered_by': user_id,
                'config': config or {},
                'status': 'running'
            }
            
            return await self.postgres_client.create_analysis_run(run_data)
            
        except Exception as e:
            logger.error(f"Failed to create analysis run: {e}")
            return None
    
    async def _store_file_analyses(self, 
                                 run_id: str,
                                 project_id: str,
                                 files: Dict[str, UniversalFile]):
        """Store file analysis results."""
        try:
            for file_path, file_obj in files.items():
                file_data = {
                    'analysis_run_id': run_id,
                    'project_id': project_id,
                    'file_path': file_path,
                    'language': file_obj.language.value,
                    'total_lines': file_obj.total_lines,
                    'code_lines': file_obj.code_lines,
                    'complexity': float(file_obj.complexity),
                    'maintainability_index': file_obj.maintainability_index,
                    'symbols_count': len(file_obj.nodes),
                    'imports_count': len(file_obj.imports),
                    'exports_count': len(file_obj.exports),
                    'neo4j_file_id': file_path
                }
                
                # This would need to be implemented in PostgresClient
                # await self.postgres_client.create_file_analysis(file_data)
                
        except Exception as e:
            logger.error(f"Failed to store file analyses: {e}")
    
    async def _update_project_analysis_results(self, 
                                             project_id: str,
                                             intelligence: CodeIntelligence,
                                             run_id: str):
        """Update project with analysis results."""
        try:
            analysis_data = {
                'total_files': len(intelligence.files),
                'total_symbols': len(intelligence.symbols),
                'total_lines': sum(f.total_lines for f in intelligence.files.values()),
            }
            
            await self.postgres_client.update_project_analysis(project_id, analysis_data)
            
        except Exception as e:
            logger.error(f"Failed to update project analysis results: {e}")
    
    async def _mark_analysis_completed(self, run_id: str, intelligence: CodeIntelligence):
        """Mark analysis run as completed."""
        try:
            updates = {
                'status': 'completed',
                'completed_at': 'NOW()',
                'files_analyzed': len(intelligence.files),
                'symbols_extracted': len(intelligence.symbols),
                'relationships_found': len(intelligence.relationships),
            }
            
            await self.postgres_client.update_analysis_run(run_id, updates)
            
        except Exception as e:
            logger.error(f"Failed to mark analysis completed: {e}")
    
    async def _mark_analysis_failed(self, run_id: str, error_message: str = None):
        """Mark analysis run as failed."""
        try:
            updates = {
                'status': 'failed',
                'completed_at': 'NOW()',
                'error_log': error_message or 'Unknown error'
            }
            
            await self.postgres_client.update_analysis_run(run_id, updates)
            
        except Exception as e:
            logger.error(f"Failed to mark analysis failed: {e}")


# Global database manager instance
db_manager = DatabaseManager()


async def get_database_manager() -> DatabaseManager:
    """Get the global database manager instance."""
    if not db_manager.is_connected():
        await db_manager.connect()
    return db_manager


async def close_database_connections():
    """Close all database connections."""
    await db_manager.disconnect()
