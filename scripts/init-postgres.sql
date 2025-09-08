-- AST Viewer Code Intelligence Platform - PostgreSQL Metadata Database
-- This script sets up tables for user management, project metadata, and system configuration

-- =============================================================================
-- EXTENSIONS
-- =============================================================================
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "btree_gin";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- =============================================================================
-- USERS AND AUTHENTICATION
-- =============================================================================
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    avatar_url TEXT,
    is_active BOOLEAN DEFAULT true,
    is_superuser BOOLEAN DEFAULT false,
    is_verified BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_login TIMESTAMP WITH TIME ZONE,
    login_count INTEGER DEFAULT 0,
    settings JSONB DEFAULT '{}',
    preferences JSONB DEFAULT '{}'
);

-- User sessions for JWT management
CREATE TABLE user_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token_hash VARCHAR(255) NOT NULL,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    ip_address INET,
    user_agent TEXT,
    is_active BOOLEAN DEFAULT true
);

-- =============================================================================
-- PROJECTS AND ORGANIZATIONS
-- =============================================================================
CREATE TABLE organizations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(100) UNIQUE NOT NULL,
    description TEXT,
    website_url TEXT,
    logo_url TEXT,
    settings JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE projects (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(100) NOT NULL,
    description TEXT,
    repository_url TEXT,
    organization_id UUID REFERENCES organizations(id) ON DELETE SET NULL,
    owner_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- Project configuration
    languages TEXT[] DEFAULT '{}',
    analysis_config JSONB DEFAULT '{}',
    visualization_config JSONB DEFAULT '{}',
    
    -- Project status
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'archived', 'deleted')),
    is_public BOOLEAN DEFAULT false,
    is_analyzed BOOLEAN DEFAULT false,
    
    -- Analysis metadata
    last_analysis_at TIMESTAMP WITH TIME ZONE,
    analysis_version VARCHAR(20),
    total_files INTEGER DEFAULT 0,
    total_symbols INTEGER DEFAULT 0,
    total_lines INTEGER DEFAULT 0,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    UNIQUE(organization_id, slug)
);

-- Create partial unique index for personal projects (no organization)
CREATE UNIQUE INDEX idx_projects_owner_slug_personal 
    ON projects(owner_id, slug) 
    WHERE organization_id IS NULL;

-- Project members and permissions
CREATE TABLE project_members (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role VARCHAR(20) DEFAULT 'viewer' CHECK (role IN ('owner', 'admin', 'editor', 'viewer')),
    permissions JSONB DEFAULT '{}',
    added_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    added_by UUID REFERENCES users(id),
    
    UNIQUE(project_id, user_id)
);

-- =============================================================================
-- ANALYSIS HISTORY AND RESULTS
-- =============================================================================
CREATE TABLE analysis_runs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    triggered_by UUID REFERENCES users(id),
    
    -- Run configuration
    config JSONB DEFAULT '{}',
    git_commit VARCHAR(40),
    git_branch VARCHAR(255),
    
    -- Run status
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'running', 'completed', 'failed', 'cancelled')),
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE,
    
    -- Results summary
    files_analyzed INTEGER DEFAULT 0,
    symbols_extracted INTEGER DEFAULT 0,
    relationships_found INTEGER DEFAULT 0,
    errors_count INTEGER DEFAULT 0,
    warnings_count INTEGER DEFAULT 0,
    
    -- Detailed results
    results JSONB DEFAULT '{}',
    metrics JSONB DEFAULT '{}',
    error_log TEXT,
    
    -- Performance metrics
    duration_seconds INTEGER,
    memory_peak_mb INTEGER,
    cpu_usage_percent DECIMAL(5,2)
);

-- File analysis results
CREATE TABLE file_analyses (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    analysis_run_id UUID NOT NULL REFERENCES analysis_runs(id) ON DELETE CASCADE,
    file_path TEXT NOT NULL,
    file_hash VARCHAR(64),
    language VARCHAR(50),
    
    -- File metrics
    total_lines INTEGER DEFAULT 0,
    code_lines INTEGER DEFAULT 0,
    complexity DECIMAL(8,2) DEFAULT 0,
    maintainability_index DECIMAL(5,2),
    
    -- Analysis results
    symbols_count INTEGER DEFAULT 0,
    imports_count INTEGER DEFAULT 0,
    exports_count INTEGER DEFAULT 0,
    
    -- Detailed data (stored in Neo4j, referenced here)
    neo4j_file_id VARCHAR(255),
    
    -- Timestamps
    analyzed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- =============================================================================
-- VISUALIZATION AND EXPORTS
-- =============================================================================
CREATE TABLE visualizations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    created_by UUID NOT NULL REFERENCES users(id),
    
    -- Visualization metadata
    name VARCHAR(255) NOT NULL,
    description TEXT,
    type VARCHAR(50) NOT NULL,
    config JSONB DEFAULT '{}',
    
    -- Access control
    is_public BOOLEAN DEFAULT false,
    shared_with UUID[] DEFAULT '{}',
    
    -- Export data
    export_format VARCHAR(20),
    export_url TEXT,
    export_size_bytes BIGINT,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_accessed_at TIMESTAMP WITH TIME ZONE
);

-- =============================================================================
-- SYSTEM CONFIGURATION AND MONITORING
-- =============================================================================
CREATE TABLE system_config (
    key VARCHAR(255) PRIMARY KEY,
    value JSONB NOT NULL,
    description TEXT,
    category VARCHAR(50) DEFAULT 'general',
    is_public BOOLEAN DEFAULT false,
    updated_by UUID REFERENCES users(id),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- API usage tracking
CREATE TABLE api_usage (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id),
    endpoint VARCHAR(255) NOT NULL,
    method VARCHAR(10) NOT NULL,
    status_code INTEGER NOT NULL,
    response_time_ms INTEGER,
    request_size_bytes INTEGER,
    response_size_bytes INTEGER,
    ip_address INET,
    user_agent TEXT,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- System metrics
CREATE TABLE system_metrics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    metric_name VARCHAR(100) NOT NULL,
    metric_value DECIMAL(15,4) NOT NULL,
    metric_unit VARCHAR(20),
    tags JSONB DEFAULT '{}',
    recorded_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- =============================================================================
-- INDEXES FOR PERFORMANCE
-- =============================================================================

-- Users indexes
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_active ON users(is_active) WHERE is_active = true;
CREATE INDEX idx_users_created_at ON users(created_at);

-- User sessions indexes
CREATE INDEX idx_user_sessions_user_id ON user_sessions(user_id);
CREATE INDEX idx_user_sessions_token_hash ON user_sessions(token_hash);
CREATE INDEX idx_user_sessions_expires_at ON user_sessions(expires_at);
CREATE INDEX idx_user_sessions_active ON user_sessions(is_active) WHERE is_active = true;

-- Projects indexes
CREATE INDEX idx_projects_owner_id ON projects(owner_id);
CREATE INDEX idx_projects_organization_id ON projects(organization_id);
CREATE INDEX idx_projects_status ON projects(status);
CREATE INDEX idx_projects_public ON projects(is_public) WHERE is_public = true;
CREATE INDEX idx_projects_analyzed ON projects(is_analyzed) WHERE is_analyzed = true;
CREATE INDEX idx_projects_updated_at ON projects(updated_at);

-- Project members indexes
CREATE INDEX idx_project_members_project_id ON project_members(project_id);
CREATE INDEX idx_project_members_user_id ON project_members(user_id);
CREATE INDEX idx_project_members_role ON project_members(role);

-- Analysis runs indexes
CREATE INDEX idx_analysis_runs_project_id ON analysis_runs(project_id);
CREATE INDEX idx_analysis_runs_status ON analysis_runs(status);
CREATE INDEX idx_analysis_runs_started_at ON analysis_runs(started_at);
CREATE INDEX idx_analysis_runs_triggered_by ON analysis_runs(triggered_by);

-- File analyses indexes
CREATE INDEX idx_file_analyses_run_id ON file_analyses(analysis_run_id);
CREATE INDEX idx_file_analyses_file_path ON file_analyses(file_path);
CREATE INDEX idx_file_analyses_language ON file_analyses(language);
CREATE INDEX idx_file_analyses_complexity ON file_analyses(complexity);

-- API usage indexes
CREATE INDEX idx_api_usage_user_id ON api_usage(user_id);
CREATE INDEX idx_api_usage_endpoint ON api_usage(endpoint);
CREATE INDEX idx_api_usage_timestamp ON api_usage(timestamp);
CREATE INDEX idx_api_usage_status_code ON api_usage(status_code);

-- System metrics indexes
CREATE INDEX idx_system_metrics_name ON system_metrics(metric_name);
CREATE INDEX idx_system_metrics_recorded_at ON system_metrics(recorded_at);

-- Composite indexes for common queries
CREATE INDEX idx_projects_owner_status ON projects(owner_id, status);
CREATE INDEX idx_analysis_runs_project_status ON analysis_runs(project_id, status);
CREATE INDEX idx_file_analyses_run_language ON file_analyses(analysis_run_id, language);

-- Full-text search indexes
CREATE INDEX idx_projects_name_search ON projects USING gin(to_tsvector('english', name || ' ' || COALESCE(description, '')));
CREATE INDEX idx_users_name_search ON users USING gin(to_tsvector('english', full_name || ' ' || username));

-- =============================================================================
-- TRIGGERS FOR UPDATED_AT
-- =============================================================================
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_organizations_updated_at BEFORE UPDATE ON organizations FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_projects_updated_at BEFORE UPDATE ON projects FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_visualizations_updated_at BEFORE UPDATE ON visualizations FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_system_config_updated_at BEFORE UPDATE ON system_config FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- =============================================================================
-- INITIAL DATA
-- =============================================================================

-- Insert default system configuration
INSERT INTO system_config (key, value, description, category, is_public) VALUES
('app.name', '"AST Viewer Code Intelligence Platform"', 'Application name', 'general', true),
('app.version', '"2.0.0"', 'Application version', 'general', true),
('app.max_file_size', '104857600', 'Maximum file size for analysis (100MB)', 'analysis', false),
('app.max_project_size', '1073741824', 'Maximum project size for analysis (1GB)', 'analysis', false),
('analysis.default_languages', '["python", "javascript", "typescript", "go", "rust"]', 'Default supported languages', 'analysis', true),
('visualization.max_nodes', '1000', 'Maximum nodes in visualization', 'visualization', false),
('api.rate_limit', '100', 'API rate limit per minute', 'api', false);

-- Create default admin user (password: admin123)
INSERT INTO users (username, email, password_hash, full_name, is_superuser, is_verified) VALUES
('admin', 'admin@astviewer.com', crypt('admin123', gen_salt('bf', 12)), 'System Administrator', true, true);

-- =============================================================================
-- VIEWS FOR COMMON QUERIES
-- =============================================================================

-- User project access view
CREATE VIEW user_project_access AS
SELECT 
    u.id as user_id,
    u.username,
    p.id as project_id,
    p.name as project_name,
    p.slug as project_slug,
    COALESCE(pm.role, 'none') as role,
    p.is_public,
    (p.owner_id = u.id) as is_owner,
    p.organization_id
FROM users u
CROSS JOIN projects p
LEFT JOIN project_members pm ON pm.project_id = p.id AND pm.user_id = u.id
WHERE u.is_active = true 
    AND p.status = 'active'
    AND (p.is_public = true OR p.owner_id = u.id OR pm.user_id IS NOT NULL);

-- Project statistics view
CREATE VIEW project_statistics AS
SELECT 
    p.id,
    p.name,
    p.total_files,
    p.total_symbols,
    p.total_lines,
    COUNT(DISTINCT ar.id) as analysis_runs_count,
    MAX(ar.completed_at) as last_analysis_completed,
    COUNT(DISTINCT pm.user_id) as members_count,
    COUNT(DISTINCT v.id) as visualizations_count
FROM projects p
LEFT JOIN analysis_runs ar ON ar.project_id = p.id AND ar.status = 'completed'
LEFT JOIN project_members pm ON pm.project_id = p.id
LEFT JOIN visualizations v ON v.project_id = p.id
WHERE p.status = 'active'
GROUP BY p.id, p.name, p.total_files, p.total_symbols, p.total_lines;
