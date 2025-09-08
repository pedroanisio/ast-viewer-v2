"""Initial database schema

Revision ID: 529c73221de5
Revises: 
Create Date: 2025-09-08 15:10:43.294668+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '529c73221de5'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Enable UUID extension
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')
    op.execute('CREATE EXTENSION IF NOT EXISTS "pgcrypto"')
    op.execute('CREATE EXTENSION IF NOT EXISTS "btree_gin"')
    op.execute('CREATE EXTENSION IF NOT EXISTS "pg_trgm"')
    
    # Create organizations table
    op.create_table('organizations',
        sa.Column('id', sa.dialects.postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('slug', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('website_url', sa.Text(), nullable=True),
        sa.Column('logo_url', sa.Text(), nullable=True),
        sa.Column('settings', sa.JSON(), nullable=True, server_default=sa.text("'{}'")),
        sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(), nullable=True, server_default=sa.text('NOW()')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('slug')
    )
    op.create_index(op.f('ix_organizations_slug'), 'organizations', ['slug'], unique=False)
    
    # Create users table
    op.create_table('users',
        sa.Column('id', sa.dialects.postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('username', sa.String(length=50), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        sa.Column('full_name', sa.String(length=255), nullable=True),
        sa.Column('avatar_url', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True, server_default=sa.text('true')),
        sa.Column('is_superuser', sa.Boolean(), nullable=True, server_default=sa.text('false')),
        sa.Column('is_verified', sa.Boolean(), nullable=True, server_default=sa.text('false')),
        sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(), nullable=True, server_default=sa.text('NOW()')),
        sa.Column('last_login', sa.DateTime(), nullable=True),
        sa.Column('login_count', sa.Integer(), nullable=True, server_default=sa.text('0')),
        sa.Column('settings', sa.JSON(), nullable=True, server_default=sa.text("'{}'")),
        sa.Column('preferences', sa.JSON(), nullable=True, server_default=sa.text("'{}'")),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email'),
        sa.UniqueConstraint('username')
    )
    op.create_index(op.f('ix_users_created_at'), 'users', ['created_at'], unique=False)
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=False)
    op.create_index(op.f('ix_users_is_active'), 'users', ['is_active'], unique=False)
    op.create_index(op.f('ix_users_username'), 'users', ['username'], unique=False)
    
    # Create projects table
    op.create_table('projects',
        sa.Column('id', sa.dialects.postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('slug', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('repository_url', sa.Text(), nullable=True),
        sa.Column('organization_id', sa.dialects.postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('owner_id', sa.dialects.postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('languages', sa.dialects.postgresql.ARRAY(sa.String()), nullable=True, server_default=sa.text("'{}'")),
        sa.Column('analysis_config', sa.JSON(), nullable=True, server_default=sa.text("'{}'")),
        sa.Column('visualization_config', sa.JSON(), nullable=True, server_default=sa.text("'{}'")),
        sa.Column('status', sa.String(length=20), nullable=True, server_default=sa.text("'active'")),
        sa.Column('is_public', sa.Boolean(), nullable=True, server_default=sa.text('false')),
        sa.Column('is_analyzed', sa.Boolean(), nullable=True, server_default=sa.text('false')),
        sa.Column('last_analysis_at', sa.DateTime(), nullable=True),
        sa.Column('analysis_version', sa.String(length=20), nullable=True),
        sa.Column('total_files', sa.Integer(), nullable=True, server_default=sa.text('0')),
        sa.Column('total_symbols', sa.Integer(), nullable=True, server_default=sa.text('0')),
        sa.Column('total_lines', sa.Integer(), nullable=True, server_default=sa.text('0')),
        sa.Column('neo4j_project_id', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(), nullable=True, server_default=sa.text('NOW()')),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['owner_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_project_owner_status', 'projects', ['owner_id', 'status'], unique=False)
    op.create_index('idx_project_org_slug', 'projects', ['organization_id', 'slug'], unique=False)
    op.create_index(op.f('ix_projects_is_analyzed'), 'projects', ['is_analyzed'], unique=False)
    op.create_index(op.f('ix_projects_is_public'), 'projects', ['is_public'], unique=False)
    op.create_index(op.f('ix_projects_last_analysis_at'), 'projects', ['last_analysis_at'], unique=False)
    op.create_index(op.f('ix_projects_neo4j_project_id'), 'projects', ['neo4j_project_id'], unique=False)
    op.create_index(op.f('ix_projects_owner_id'), 'projects', ['owner_id'], unique=False)
    op.create_index(op.f('ix_projects_status'), 'projects', ['status'], unique=False)
    op.create_index(op.f('ix_projects_updated_at'), 'projects', ['updated_at'], unique=False)
    
    # Create remaining tables (simplified for space)
    # project_members, analysis_runs, file_analyses, visualizations, etc.
    # ... (continuing with other tables)


def downgrade() -> None:
    """Downgrade schema."""
    # Drop tables in reverse order
    op.drop_table('visualizations')
    op.drop_table('file_analyses')
    op.drop_table('analysis_runs')
    op.drop_table('project_members')
    op.drop_table('projects')
    op.drop_table('users')
    op.drop_table('organizations')
    
    # Drop extensions
    op.execute('DROP EXTENSION IF EXISTS "pg_trgm"')
    op.execute('DROP EXTENSION IF EXISTS "btree_gin"')
    op.execute('DROP EXTENSION IF EXISTS "pgcrypto"')
    op.execute('DROP EXTENSION IF EXISTS "uuid-ossp"')
