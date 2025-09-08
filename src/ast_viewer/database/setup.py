"""Database setup and initialization."""

import logging
import asyncio
from typing import Optional

from .neo4j_client import Neo4jClient, check_neo4j_connection
from .postgres_client import PostgresClient, check_postgres_connection
from .models import Base, User, SystemConfig

logger = logging.getLogger(__name__)


async def setup_database() -> bool:
    """Set up both Neo4j and PostgreSQL databases."""
    logger.info("Setting up databases...")
    
    # Setup PostgreSQL
    postgres_success = await setup_postgres()
    
    # Setup Neo4j
    neo4j_success = setup_neo4j()
    
    if postgres_success and neo4j_success:
        logger.info("Database setup completed successfully")
        return True
    else:
        logger.error("Database setup failed")
        return False


async def setup_postgres() -> bool:
    """Set up PostgreSQL database with tables and initial data."""
    try:
        client = PostgresClient()
        
        # Connect to database
        if not await client.connect():
            logger.error("Failed to connect to PostgreSQL")
            return False
        
        # Create tables
        if not await client.create_tables():
            logger.error("Failed to create PostgreSQL tables")
            return False
        
        # Insert initial data
        await insert_initial_data(client)
        
        await client.disconnect()
        logger.info("PostgreSQL setup completed")
        return True
        
    except Exception as e:
        logger.error(f"PostgreSQL setup failed: {e}")
        return False


def setup_neo4j() -> bool:
    """Set up Neo4j database with schema."""
    try:
        client = Neo4jClient()
        
        # Connect to database
        if not client.connect():
            logger.error("Failed to connect to Neo4j")
            return False
        
        # Setup schema
        if not client.setup_schema():
            logger.error("Failed to setup Neo4j schema")
            return False
        
        client.disconnect()
        logger.info("Neo4j setup completed")
        return True
        
    except Exception as e:
        logger.error(f"Neo4j setup failed: {e}")
        return False


async def insert_initial_data(client: PostgresClient):
    """Insert initial system configuration and admin user."""
    try:
        # Insert system configuration
        config_items = [
            ('app.name', 'AST Viewer Code Intelligence Platform', 'Application name'),
            ('app.version', '2.0.0', 'Application version'),
            ('app.max_file_size', 104857600, 'Maximum file size for analysis (100MB)'),
            ('app.max_project_size', 1073741824, 'Maximum project size for analysis (1GB)'),
            ('analysis.default_languages', ['python', 'javascript', 'typescript', 'go', 'rust'], 'Default supported languages'),
            ('visualization.max_nodes', 1000, 'Maximum nodes in visualization'),
            ('api.rate_limit', 100, 'API rate limit per minute'),
            ('neo4j.batch_size', 1000, 'Neo4j batch insert size'),
            ('cache.ttl', 3600, 'Default cache TTL in seconds'),
        ]
        
        for key, value, description in config_items:
            await client.set_system_config(key, value, description)
        
        # Create default admin user if not exists
        admin_user = await client.get_user_by_email('admin@astviewer.com')
        if not admin_user:
            import bcrypt
            password_hash = bcrypt.hashpw('admin123'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            
            admin_data = {
                'username': 'admin',
                'email': 'admin@astviewer.com',
                'password_hash': password_hash,
                'full_name': 'System Administrator',
                'is_superuser': True,
                'is_verified': True,
                'is_active': True
            }
            
            admin_id = await client.create_user(admin_data)
            if admin_id:
                logger.info(f"Created admin user with ID: {admin_id}")
            else:
                logger.warning("Failed to create admin user")
        
        logger.info("Initial data inserted successfully")
        
    except Exception as e:
        logger.error(f"Failed to insert initial data: {e}")


async def check_database_connections() -> dict:
    """Check the status of all database connections."""
    results = {}
    
    # Check PostgreSQL
    try:
        postgres_ok = await check_postgres_connection()
        results['postgresql'] = {
            'status': 'connected' if postgres_ok else 'disconnected',
            'healthy': postgres_ok
        }
    except Exception as e:
        results['postgresql'] = {
            'status': 'error',
            'healthy': False,
            'error': str(e)
        }
    
    # Check Neo4j
    try:
        neo4j_ok = check_neo4j_connection()
        results['neo4j'] = {
            'status': 'connected' if neo4j_ok else 'disconnected',
            'healthy': neo4j_ok
        }
    except Exception as e:
        results['neo4j'] = {
            'status': 'error',
            'healthy': False,
            'error': str(e)
        }
    
    # Overall health
    all_healthy = all(db.get('healthy', False) for db in results.values())
    results['overall'] = {
        'healthy': all_healthy,
        'status': 'healthy' if all_healthy else 'degraded'
    }
    
    return results


async def reset_database() -> bool:
    """Reset both databases (WARNING: This will delete all data!)."""
    logger.warning("Resetting databases - ALL DATA WILL BE LOST!")
    
    try:
        # Reset PostgreSQL
        client = PostgresClient()
        if await client.connect():
            async with client.engine.begin() as conn:
                await conn.run_sync(Base.metadata.drop_all)
                await conn.run_sync(Base.metadata.create_all)
            await client.disconnect()
            logger.info("PostgreSQL database reset")
        
        # Reset Neo4j
        neo4j_client = Neo4jClient()
        if neo4j_client.connect():
            # Delete all nodes and relationships
            neo4j_client.execute_write_query("MATCH (n) DETACH DELETE n")
            neo4j_client.setup_schema()
            neo4j_client.disconnect()
            logger.info("Neo4j database reset")
        
        # Reinitialize with basic data
        await setup_database()
        
        return True
        
    except Exception as e:
        logger.error(f"Database reset failed: {e}")
        return False


async def migrate_database() -> bool:
    """Run database migrations."""
    try:
        # For now, just ensure tables exist
        # In production, this would run Alembic migrations
        client = PostgresClient()
        if await client.connect():
            await client.create_tables()
            await client.disconnect()
            return True
        return False
    except Exception as e:
        logger.error(f"Database migration failed: {e}")
        return False


def get_database_info() -> dict:
    """Get database configuration information."""
    import os
    
    return {
        'postgresql': {
            'host': os.getenv('POSTGRES_HOST', 'localhost'),
            'port': os.getenv('POSTGRES_PORT', '5432'),
            'database': os.getenv('POSTGRES_DB', 'ast_viewer_metadata'),
            'user': os.getenv('POSTGRES_USER', 'ast_viewer'),
        },
        'neo4j': {
            'uri': os.getenv('NEO4J_URI', 'bolt://localhost:7687'),
            'username': os.getenv('NEO4J_USERNAME', 'neo4j'),
        },
        'redis': {
            'url': os.getenv('REDIS_URL', 'redis://localhost:6379/0'),
        }
    }


if __name__ == "__main__":
    # Allow running setup directly
    asyncio.run(setup_database())
