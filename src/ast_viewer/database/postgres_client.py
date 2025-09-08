"""PostgreSQL database client for metadata and user management."""

import logging
import os
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
import json

import asyncpg
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy import (
    Column, String, Integer, Boolean, DateTime, Text, JSON, 
    ForeignKey, Table, UUID, DECIMAL, ARRAY
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
import uuid

from ..common.database import BaseDataClient

logger = logging.getLogger(__name__)

# SQLAlchemy Base
Base = declarative_base()


class User(Base):
    """User model for authentication and project management."""
    __tablename__ = 'users'
    
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(255))
    avatar_url = Column(Text)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    is_verified = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = Column(DateTime)
    login_count = Column(Integer, default=0)
    settings = Column(JSON, default=dict)
    preferences = Column(JSON, default=dict)


class Organization(Base):
    """Organization model for grouping projects."""
    __tablename__ = 'organizations'
    
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    slug = Column(String(100), unique=True, nullable=False)
    description = Column(Text)
    website_url = Column(Text)
    logo_url = Column(Text)
    settings = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Project(Base):
    """Project model for code analysis projects."""
    __tablename__ = 'projects'
    
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    slug = Column(String(100), nullable=False)
    description = Column(Text)
    repository_url = Column(Text)
    organization_id = Column(PG_UUID(as_uuid=True), ForeignKey('organizations.id', ondelete='SET NULL'))
    owner_id = Column(PG_UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    
    # Project configuration
    languages = Column(ARRAY(String), default=list)
    analysis_config = Column(JSON, default=dict)
    visualization_config = Column(JSON, default=dict)
    
    # Project status
    status = Column(String(20), default='active')  # active, archived, deleted
    is_public = Column(Boolean, default=False)
    is_analyzed = Column(Boolean, default=False)
    
    # Analysis metadata
    last_analysis_at = Column(DateTime)
    analysis_version = Column(String(20))
    total_files = Column(Integer, default=0)
    total_symbols = Column(Integer, default=0)
    total_lines = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ProjectMember(Base):
    """Project membership and permissions."""
    __tablename__ = 'project_members'
    
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(PG_UUID(as_uuid=True), ForeignKey('projects.id', ondelete='CASCADE'), nullable=False)
    user_id = Column(PG_UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    role = Column(String(20), default='viewer')  # owner, admin, editor, viewer
    permissions = Column(JSON, default=dict)
    added_at = Column(DateTime, default=datetime.utcnow)
    added_by = Column(PG_UUID(as_uuid=True), ForeignKey('users.id'))


class AnalysisRun(Base):
    """Analysis run tracking."""
    __tablename__ = 'analysis_runs'
    
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(PG_UUID(as_uuid=True), ForeignKey('projects.id', ondelete='CASCADE'), nullable=False)
    triggered_by = Column(PG_UUID(as_uuid=True), ForeignKey('users.id'))
    
    # Run configuration
    config = Column(JSON, default=dict)
    git_commit = Column(String(40))
    git_branch = Column(String(255))
    
    # Run status
    status = Column(String(20), default='pending')  # pending, running, completed, failed, cancelled
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)
    
    # Results summary
    files_analyzed = Column(Integer, default=0)
    symbols_extracted = Column(Integer, default=0)
    relationships_found = Column(Integer, default=0)
    errors_count = Column(Integer, default=0)
    warnings_count = Column(Integer, default=0)
    
    # Detailed results
    results = Column(JSON, default=dict)
    metrics = Column(JSON, default=dict)
    error_log = Column(Text)
    
    # Performance metrics
    duration_seconds = Column(Integer)
    memory_peak_mb = Column(Integer)
    cpu_usage_percent = Column(DECIMAL(5,2))


class FileAnalysis(Base):
    """File analysis results."""
    __tablename__ = 'file_analyses'
    
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    analysis_run_id = Column(PG_UUID(as_uuid=True), ForeignKey('analysis_runs.id', ondelete='CASCADE'), nullable=False)
    file_path = Column(Text, nullable=False)
    file_hash = Column(String(64))
    language = Column(String(50))
    
    # File metrics
    total_lines = Column(Integer, default=0)
    code_lines = Column(Integer, default=0)
    complexity = Column(DECIMAL(8,2), default=0)
    maintainability_index = Column(DECIMAL(5,2))
    
    # Analysis results
    symbols_count = Column(Integer, default=0)
    imports_count = Column(Integer, default=0)
    exports_count = Column(Integer, default=0)
    
    # Reference to Neo4j data
    neo4j_file_id = Column(String(255))
    
    # Timestamps
    analyzed_at = Column(DateTime, default=datetime.utcnow)


class Visualization(Base):
    """Visualization metadata."""
    __tablename__ = 'visualizations'
    
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(PG_UUID(as_uuid=True), ForeignKey('projects.id', ondelete='CASCADE'), nullable=False)
    created_by = Column(PG_UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    
    # Visualization metadata
    name = Column(String(255), nullable=False)
    description = Column(Text)
    type = Column(String(50), nullable=False)
    config = Column(JSON, default=dict)
    
    # Access control
    is_public = Column(Boolean, default=False)
    shared_with = Column(ARRAY(PG_UUID(as_uuid=True)), default=list)
    
    # Export data
    export_format = Column(String(20))
    export_url = Column(Text)
    export_size_bytes = Column(Integer)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_accessed_at = Column(DateTime)


class SystemConfig(Base):
    """System configuration."""
    __tablename__ = 'system_config'
    
    key = Column(String(255), primary_key=True)
    value = Column(JSON, nullable=False)
    description = Column(Text)
    category = Column(String(50), default='general')
    is_public = Column(Boolean, default=False)
    updated_by = Column(PG_UUID(as_uuid=True), ForeignKey('users.id'))
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class PostgresClient(BaseDataClient):
    """Client for interacting with PostgreSQL database."""
    
    def __init__(self, database_url: Optional[str] = None):
        # Build database URL from environment if not provided
        if not database_url:
            host = os.getenv("POSTGRES_HOST", "localhost")
            port = os.getenv("POSTGRES_PORT", "5432")
            database = os.getenv("POSTGRES_DB", "ast_viewer_metadata")
            username = os.getenv("POSTGRES_USER", "ast_viewer")
            password = os.getenv("POSTGRES_PASSWORD", "password")
            database_url = f"postgresql+asyncpg://{username}:{password}@{host}:{port}/{database}"
        
        super().__init__(
            connection_string=database_url,
            connection_env_var="POSTGRES_URL",  # Allow override via single env var
            default_connection=database_url
        )
        
        # PostgreSQL specific properties
        self.database_url = self.connection_string  # Alias for backward compatibility
        self.engine = None
        self.async_session_maker = None
    
    # BaseDataClient implementation methods for async PostgreSQL
    def _create_connection(self):
        """Create PostgreSQL engine connection."""
        engine = create_async_engine(
            self.database_url,
            pool_size=20,
            max_overflow=30,
            pool_pre_ping=True,
            echo=False  # Set to True for SQL logging
        )
        
        # Create session maker
        self.async_session_maker = async_sessionmaker(
            bind=engine,
            class_=AsyncSession,
            expire_on_commit=False
        )
        
        return engine
    
    def _test_connection(self) -> bool:
        """Test PostgreSQL connection with a simple query."""
        try:
            # Note: This is a sync wrapper for the async test
            # In practice, you might need async/await handling here
            import asyncio
            
            async def async_test():
                async with self.engine.begin() as conn:
                    await conn.execute("SELECT 1")
                return True
            
            return asyncio.run(async_test())
        except Exception:
            return False
    
    def _close_connection(self) -> None:
        """Close PostgreSQL engine connection."""
        if self.engine:
            import asyncio
            asyncio.run(self.engine.dispose())
            self.engine = None
            self.async_session_maker = None
    
    @property
    def connection_type(self) -> str:
        """Return connection type for logging."""
        return "PostgreSQL"
    
    @property 
    def engine(self):
        """Get the PostgreSQL engine (for backward compatibility)."""
        return self._connection
    
    @engine.setter
    def engine(self, value) -> None:
        """Set the PostgreSQL engine (for backward compatibility)."""
        self._connection = value
    
    # Async-specific methods that override base class
    async def connect_async(self) -> bool:
        """Async version of connect for PostgreSQL."""
        return self.connect()
    
    async def disconnect_async(self) -> None:
        """Async version of disconnect for PostgreSQL."""
        self.disconnect()
    
    async def ensure_connection_async(self) -> bool:
        """Async version of ensure_connection for PostgreSQL."""
        return self.ensure_connection()
    
    async def create_tables(self) -> bool:
        """Create database tables."""
        if not await self.ensure_connection():
            return False
        
        try:
            async with self.engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            
            logger.info("Database tables created successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create tables: {e}")
            return False
    
    async def get_session(self) -> AsyncSession:
        """Get database session."""
        if not await self.ensure_connection():
            raise ConnectionError("Cannot connect to PostgreSQL database")
        
        return self.async_session_maker()
    
    # User management methods
    async def create_user(self, user_data: Dict[str, Any]) -> Optional[str]:
        """Create a new user."""
        try:
            async with await self.get_session() as session:
                user = User(**user_data)
                session.add(user)
                await session.commit()
                await session.refresh(user)
                return str(user.id)
        except Exception as e:
            logger.error(f"Failed to create user: {e}")
            return None
    
    async def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Get user by email."""
        try:
            async with await self.get_session() as session:
                result = await session.execute(
                    f"SELECT * FROM users WHERE email = '{email}'"
                )
                user = result.fetchone()
                return dict(user) if user else None
        except Exception as e:
            logger.error(f"Failed to get user by email: {e}")
            return None
    
    async def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user by ID."""
        try:
            async with await self.get_session() as session:
                result = await session.execute(
                    f"SELECT * FROM users WHERE id = '{user_id}'"
                )
                user = result.fetchone()
                return dict(user) if user else None
        except Exception as e:
            logger.error(f"Failed to get user by ID: {e}")
            return None
    
    # Project management methods
    async def create_project(self, project_data: Dict[str, Any]) -> Optional[str]:
        """Create a new project."""
        try:
            async with await self.get_session() as session:
                project = Project(**project_data)
                session.add(project)
                await session.commit()
                await session.refresh(project)
                return str(project.id)
        except Exception as e:
            logger.error(f"Failed to create project: {e}")
            return None
    
    async def get_project_by_id(self, project_id: str) -> Optional[Dict[str, Any]]:
        """Get project by ID."""
        try:
            async with await self.get_session() as session:
                result = await session.execute(
                    f"SELECT * FROM projects WHERE id = '{project_id}'"
                )
                project = result.fetchone()
                return dict(project) if project else None
        except Exception as e:
            logger.error(f"Failed to get project by ID: {e}")
            return None
    
    async def get_user_projects(self, user_id: str) -> List[Dict[str, Any]]:
        """Get projects for a user."""
        try:
            async with await self.get_session() as session:
                # Get projects owned by user
                result = await session.execute(f"""
                    SELECT p.* FROM projects p 
                    WHERE p.owner_id = '{user_id}' AND p.status = 'active'
                    UNION
                    SELECT p.* FROM projects p
                    JOIN project_members pm ON pm.project_id = p.id
                    WHERE pm.user_id = '{user_id}' AND p.status = 'active'
                    ORDER BY updated_at DESC
                """)
                return [dict(row) for row in result.fetchall()]
        except Exception as e:
            logger.error(f"Failed to get user projects: {e}")
            return []
    
    async def update_project_analysis(self, project_id: str, analysis_data: Dict[str, Any]) -> bool:
        """Update project with analysis results."""
        try:
            async with await self.get_session() as session:
                await session.execute(f"""
                    UPDATE projects 
                    SET 
                        total_files = {analysis_data.get('total_files', 0)},
                        total_symbols = {analysis_data.get('total_symbols', 0)},
                        total_lines = {analysis_data.get('total_lines', 0)},
                        is_analyzed = true,
                        last_analysis_at = NOW(),
                        updated_at = NOW()
                    WHERE id = '{project_id}'
                """)
                await session.commit()
                return True
        except Exception as e:
            logger.error(f"Failed to update project analysis: {e}")
            return False
    
    # Analysis run tracking
    async def create_analysis_run(self, run_data: Dict[str, Any]) -> Optional[str]:
        """Create a new analysis run."""
        try:
            async with await self.get_session() as session:
                analysis_run = AnalysisRun(**run_data)
                session.add(analysis_run)
                await session.commit()
                await session.refresh(analysis_run)
                return str(analysis_run.id)
        except Exception as e:
            logger.error(f"Failed to create analysis run: {e}")
            return None
    
    async def update_analysis_run(self, run_id: str, updates: Dict[str, Any]) -> bool:
        """Update analysis run status."""
        try:
            async with await self.get_session() as session:
                update_fields = []
                for key, value in updates.items():
                    if isinstance(value, str):
                        update_fields.append(f"{key} = '{value}'")
                    else:
                        update_fields.append(f"{key} = {value}")
                
                await session.execute(f"""
                    UPDATE analysis_runs 
                    SET {', '.join(update_fields)}
                    WHERE id = '{run_id}'
                """)
                await session.commit()
                return True
        except Exception as e:
            logger.error(f"Failed to update analysis run: {e}")
            return False
    
    async def get_recent_analysis_runs(self, project_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent analysis runs for a project."""
        try:
            async with await self.get_session() as session:
                result = await session.execute(f"""
                    SELECT * FROM analysis_runs 
                    WHERE project_id = '{project_id}'
                    ORDER BY started_at DESC
                    LIMIT {limit}
                """)
                return [dict(row) for row in result.fetchall()]
        except Exception as e:
            logger.error(f"Failed to get recent analysis runs: {e}")
            return []
    
    # Configuration management
    async def get_system_config(self, key: str) -> Optional[Any]:
        """Get system configuration value."""
        try:
            async with await self.get_session() as session:
                result = await session.execute(
                    f"SELECT value FROM system_config WHERE key = '{key}'"
                )
                row = result.fetchone()
                return row[0] if row else None
        except Exception as e:
            logger.error(f"Failed to get system config: {e}")
            return None
    
    async def set_system_config(self, key: str, value: Any, description: str = None) -> bool:
        """Set system configuration value."""
        try:
            async with await self.get_session() as session:
                await session.execute(f"""
                    INSERT INTO system_config (key, value, description, updated_at)
                    VALUES ('{key}', '{json.dumps(value)}', '{description or ""}', NOW())
                    ON CONFLICT (key) DO UPDATE SET
                        value = EXCLUDED.value,
                        description = EXCLUDED.description,
                        updated_at = NOW()
                """)
                await session.commit()
                return True
        except Exception as e:
            logger.error(f"Failed to set system config: {e}")
            return False


async def check_postgres_connection() -> bool:
    """Check if PostgreSQL is available and accessible."""
    try:
        client = PostgresClient()
        return await client.connect()
    except Exception as e:
        logger.error(f"PostgreSQL connection check failed: {e}")
        return False
