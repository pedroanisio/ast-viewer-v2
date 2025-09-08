"""SQLAlchemy models for PostgreSQL metadata database."""

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import (
    Column, String, Integer, Boolean, DateTime, Text, JSON, 
    ForeignKey, DECIMAL, ARRAY, Index
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

Base = declarative_base()


class User(Base):
    """User model for authentication and project management."""
    __tablename__ = 'users'
    
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(255))
    avatar_url = Column(Text)
    is_active = Column(Boolean, default=True, index=True)
    is_superuser = Column(Boolean, default=False)
    is_verified = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = Column(DateTime)
    login_count = Column(Integer, default=0)
    settings = Column(JSON, default=dict)
    preferences = Column(JSON, default=dict)
    
    # Relationships
    owned_projects = relationship("Project", back_populates="owner", foreign_keys="Project.owner_id")
    project_memberships = relationship("ProjectMember", back_populates="user")
    analysis_runs = relationship("AnalysisRun", back_populates="triggered_by_user")
    visualizations = relationship("Visualization", back_populates="creator")


class Organization(Base):
    """Organization model for grouping projects."""
    __tablename__ = 'organizations'
    
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    slug = Column(String(100), unique=True, nullable=False, index=True)
    description = Column(Text)
    website_url = Column(Text)
    logo_url = Column(Text)
    settings = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    projects = relationship("Project", back_populates="organization")


class Project(Base):
    """Project model for code analysis projects."""
    __tablename__ = 'projects'
    
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    slug = Column(String(100), nullable=False)
    description = Column(Text)
    repository_url = Column(Text)
    organization_id = Column(PG_UUID(as_uuid=True), ForeignKey('organizations.id', ondelete='SET NULL'), index=True)
    owner_id = Column(PG_UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    
    # Project configuration
    languages = Column(ARRAY(String), default=list)
    analysis_config = Column(JSON, default=dict)
    visualization_config = Column(JSON, default=dict)
    
    # Project status
    status = Column(String(20), default='active', index=True)  # active, archived, deleted
    is_public = Column(Boolean, default=False, index=True)
    is_analyzed = Column(Boolean, default=False, index=True)
    
    # Analysis metadata
    last_analysis_at = Column(DateTime, index=True)
    analysis_version = Column(String(20))
    total_files = Column(Integer, default=0)
    total_symbols = Column(Integer, default=0)
    total_lines = Column(Integer, default=0)
    
    # Neo4j reference
    neo4j_project_id = Column(String(255), index=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, index=True)
    
    # Relationships
    organization = relationship("Organization", back_populates="projects")
    owner = relationship("User", back_populates="owned_projects", foreign_keys=[owner_id])
    members = relationship("ProjectMember", back_populates="project")
    analysis_runs = relationship("AnalysisRun", back_populates="project")
    visualizations = relationship("Visualization", back_populates="project")
    file_analyses = relationship("FileAnalysis", back_populates="project")
    
    # Composite indexes
    __table_args__ = (
        Index('idx_project_owner_status', 'owner_id', 'status'),
        Index('idx_project_org_slug', 'organization_id', 'slug'),
    )


class ProjectMember(Base):
    """Project membership and permissions."""
    __tablename__ = 'project_members'
    
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(PG_UUID(as_uuid=True), ForeignKey('projects.id', ondelete='CASCADE'), nullable=False, index=True)
    user_id = Column(PG_UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    role = Column(String(20), default='viewer', index=True)  # owner, admin, editor, viewer
    permissions = Column(JSON, default=dict)
    added_at = Column(DateTime, default=datetime.utcnow)
    added_by = Column(PG_UUID(as_uuid=True), ForeignKey('users.id'))
    
    # Relationships
    project = relationship("Project", back_populates="members")
    user = relationship("User", back_populates="project_memberships")
    
    # Constraints
    __table_args__ = (
        Index('idx_project_member_unique', 'project_id', 'user_id', unique=True),
    )


class AnalysisRun(Base):
    """Analysis run tracking."""
    __tablename__ = 'analysis_runs'
    
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(PG_UUID(as_uuid=True), ForeignKey('projects.id', ondelete='CASCADE'), nullable=False, index=True)
    triggered_by = Column(PG_UUID(as_uuid=True), ForeignKey('users.id'), index=True)
    
    # Run configuration
    config = Column(JSON, default=dict)
    git_commit = Column(String(40))
    git_branch = Column(String(255))
    
    # Run status
    status = Column(String(20), default='pending', index=True)  # pending, running, completed, failed, cancelled
    started_at = Column(DateTime, default=datetime.utcnow, index=True)
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
    
    # Neo4j reference
    neo4j_run_id = Column(String(255), index=True)
    
    # Relationships
    project = relationship("Project", back_populates="analysis_runs")
    triggered_by_user = relationship("User", back_populates="analysis_runs")
    file_analyses = relationship("FileAnalysis", back_populates="analysis_run")
    
    # Composite indexes
    __table_args__ = (
        Index('idx_analysis_run_project_status', 'project_id', 'status'),
    )


class FileAnalysis(Base):
    """File analysis results."""
    __tablename__ = 'file_analyses'
    
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    analysis_run_id = Column(PG_UUID(as_uuid=True), ForeignKey('analysis_runs.id', ondelete='CASCADE'), nullable=False, index=True)
    project_id = Column(PG_UUID(as_uuid=True), ForeignKey('projects.id', ondelete='CASCADE'), nullable=False, index=True)
    file_path = Column(Text, nullable=False, index=True)
    file_hash = Column(String(64), index=True)
    language = Column(String(50), index=True)
    
    # File metrics
    total_lines = Column(Integer, default=0)
    code_lines = Column(Integer, default=0)
    complexity = Column(DECIMAL(8,2), default=0, index=True)
    maintainability_index = Column(DECIMAL(5,2))
    
    # Analysis results
    symbols_count = Column(Integer, default=0)
    imports_count = Column(Integer, default=0)
    exports_count = Column(Integer, default=0)
    
    # Neo4j reference
    neo4j_file_id = Column(String(255), index=True)
    
    # Timestamps
    analyzed_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    analysis_run = relationship("AnalysisRun", back_populates="file_analyses")
    project = relationship("Project", back_populates="file_analyses")
    
    # Composite indexes
    __table_args__ = (
        Index('idx_file_analysis_run_language', 'analysis_run_id', 'language'),
        Index('idx_file_analysis_project_path', 'project_id', 'file_path'),
    )


class Visualization(Base):
    """Visualization metadata."""
    __tablename__ = 'visualizations'
    
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(PG_UUID(as_uuid=True), ForeignKey('projects.id', ondelete='CASCADE'), nullable=False, index=True)
    created_by = Column(PG_UUID(as_uuid=True), ForeignKey('users.id'), nullable=False, index=True)
    
    # Visualization metadata
    name = Column(String(255), nullable=False)
    description = Column(Text)
    type = Column(String(50), nullable=False, index=True)
    config = Column(JSON, default=dict)
    
    # Access control
    is_public = Column(Boolean, default=False, index=True)
    shared_with = Column(ARRAY(PG_UUID(as_uuid=True)), default=list)
    
    # Export data
    export_format = Column(String(20))
    export_url = Column(Text)
    export_size_bytes = Column(Integer)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_accessed_at = Column(DateTime, index=True)
    
    # Relationships
    project = relationship("Project", back_populates="visualizations")
    creator = relationship("User", back_populates="visualizations")


class SystemConfig(Base):
    """System configuration."""
    __tablename__ = 'system_config'
    
    key = Column(String(255), primary_key=True)
    value = Column(JSON, nullable=False)
    description = Column(Text)
    category = Column(String(50), default='general', index=True)
    is_public = Column(Boolean, default=False, index=True)
    updated_by = Column(PG_UUID(as_uuid=True), ForeignKey('users.id'))
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ApiUsage(Base):
    """API usage tracking."""
    __tablename__ = 'api_usage'
    
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(PG_UUID(as_uuid=True), ForeignKey('users.id'), index=True)
    endpoint = Column(String(255), nullable=False, index=True)
    method = Column(String(10), nullable=False)
    status_code = Column(Integer, nullable=False, index=True)
    response_time_ms = Column(Integer)
    request_size_bytes = Column(Integer)
    response_size_bytes = Column(Integer)
    ip_address = Column(String(45))  # IPv6 compatible
    user_agent = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Composite indexes for analytics
    __table_args__ = (
        Index('idx_api_usage_user_timestamp', 'user_id', 'timestamp'),
        Index('idx_api_usage_endpoint_timestamp', 'endpoint', 'timestamp'),
    )


class UserSession(Base):
    """User sessions for JWT management."""
    __tablename__ = 'user_sessions'
    
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(PG_UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    token_hash = Column(String(255), nullable=False, index=True)
    expires_at = Column(DateTime, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    ip_address = Column(String(45))
    user_agent = Column(Text)
    is_active = Column(Boolean, default=True, index=True)
    
    # Relationships
    user = relationship("User")


class SystemMetrics(Base):
    """System metrics for monitoring."""
    __tablename__ = 'system_metrics'
    
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    metric_name = Column(String(100), nullable=False, index=True)
    metric_value = Column(DECIMAL(15,4), nullable=False)
    metric_unit = Column(String(20))
    tags = Column(JSON, default=dict)
    recorded_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Composite index for time series queries
    __table_args__ = (
        Index('idx_system_metrics_name_time', 'metric_name', 'recorded_at'),
    )
