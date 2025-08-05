-- SwissKnife AI Scraper Database Schema
-- PostgreSQL/Supabase Schema Definition

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Enable full-text search
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Users table for authentication and session management
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    username VARCHAR(100) UNIQUE,
    password_hash VARCHAR(255),
    full_name VARCHAR(255),
    avatar_url TEXT,
    is_active BOOLEAN DEFAULT true,
    is_verified BOOLEAN DEFAULT false,
    subscription_tier VARCHAR(50) DEFAULT 'free',
    api_key VARCHAR(255) UNIQUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_login_at TIMESTAMP WITH TIME ZONE,
    metadata JSONB DEFAULT '{}'::jsonb
);

-- Sessions table for managing user sessions
CREATE TABLE sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    session_token VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255),
    description TEXT,
    is_active BOOLEAN DEFAULT true,
    expires_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'::jsonb
);

-- Scraping projects for organizing scraping tasks
CREATE TABLE projects (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    status VARCHAR(50) DEFAULT 'active',
    settings JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'::jsonb
);

-- Scraping jobs/tasks
CREATE TABLE scraping_jobs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    session_id UUID REFERENCES sessions(id) ON DELETE SET NULL,
    name VARCHAR(255),
    url TEXT NOT NULL,
    query TEXT,
    content_type VARCHAR(50),
    status VARCHAR(50) DEFAULT 'pending',
    priority INTEGER DEFAULT 0,
    scheduled_at TIMESTAMP WITH TIME ZONE,
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    error_message TEXT,
    retry_count INTEGER DEFAULT 0,
    max_retries INTEGER DEFAULT 3,
    processing_time_seconds NUMERIC(10,3),
    extraction_config JSONB DEFAULT '{}'::jsonb,
    proxy_config JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'::jsonb
);

-- Scraped content storage
CREATE TABLE scraped_content (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    job_id UUID REFERENCES scraping_jobs(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    url TEXT NOT NULL,
    content_type VARCHAR(50),
    title VARCHAR(500),
    raw_content TEXT,
    processed_content JSONB,
    extracted_data JSONB,
    llm_analysis JSONB,
    content_hash VARCHAR(64),
    file_size BIGINT,
    language VARCHAR(10),
    sentiment_score NUMERIC(3,2),
    quality_score NUMERIC(3,2),
    is_duplicate BOOLEAN DEFAULT false,
    duplicate_of UUID REFERENCES scraped_content(id),
    scraped_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'::jsonb
);

-- Extracted entities (people, places, organizations, etc.)
CREATE TABLE extracted_entities (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    content_id UUID REFERENCES scraped_content(id) ON DELETE CASCADE,
    entity_type VARCHAR(50) NOT NULL,
    entity_value TEXT NOT NULL,
    confidence_score NUMERIC(3,2),
    start_position INTEGER,
    end_position INTEGER,
    context TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'::jsonb
);

-- Content relationships and links
CREATE TABLE content_relationships (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    source_content_id UUID REFERENCES scraped_content(id) ON DELETE CASCADE,
    target_content_id UUID REFERENCES scraped_content(id) ON DELETE CASCADE,
    relationship_type VARCHAR(50) NOT NULL,
    confidence_score NUMERIC(3,2),
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'::jsonb,
    UNIQUE(source_content_id, target_content_id, relationship_type)
);

-- Proxy usage tracking
CREATE TABLE proxy_usage (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    job_id UUID REFERENCES scraping_jobs(id) ON DELETE CASCADE,
    proxy_id VARCHAR(100) NOT NULL,
    proxy_type VARCHAR(50),
    proxy_location VARCHAR(100),
    success BOOLEAN NOT NULL,
    response_time_ms INTEGER,
    error_message TEXT,
    used_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'::jsonb
);

-- API usage tracking
CREATE TABLE api_usage (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    endpoint VARCHAR(255) NOT NULL,
    method VARCHAR(10) NOT NULL,
    status_code INTEGER,
    response_time_ms INTEGER,
    request_size BIGINT,
    response_size BIGINT,
    ip_address INET,
    user_agent TEXT,
    api_key_used VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'::jsonb
);

-- System logs and events
CREATE TABLE system_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    level VARCHAR(20) NOT NULL,
    component VARCHAR(100),
    message TEXT NOT NULL,
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    job_id UUID REFERENCES scraping_jobs(id) ON DELETE SET NULL,
    error_details JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'::jsonb
);

-- Indexes for performance
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_api_key ON users(api_key);
CREATE INDEX idx_sessions_token ON sessions(session_token);
CREATE INDEX idx_sessions_user_id ON sessions(user_id);
CREATE INDEX idx_projects_user_id ON projects(user_id);
CREATE INDEX idx_scraping_jobs_user_id ON scraping_jobs(user_id);
CREATE INDEX idx_scraping_jobs_status ON scraping_jobs(status);
CREATE INDEX idx_scraping_jobs_scheduled_at ON scraping_jobs(scheduled_at);
CREATE INDEX idx_scraped_content_job_id ON scraped_content(job_id);
CREATE INDEX idx_scraped_content_user_id ON scraped_content(user_id);
CREATE INDEX idx_scraped_content_url ON scraped_content(url);
CREATE INDEX idx_scraped_content_content_hash ON scraped_content(content_hash);
CREATE INDEX idx_scraped_content_scraped_at ON scraped_content(scraped_at);
CREATE INDEX idx_extracted_entities_content_id ON extracted_entities(content_id);
CREATE INDEX idx_extracted_entities_type_value ON extracted_entities(entity_type, entity_value);
CREATE INDEX idx_content_relationships_source ON content_relationships(source_content_id);
CREATE INDEX idx_content_relationships_target ON content_relationships(target_content_id);
CREATE INDEX idx_proxy_usage_job_id ON proxy_usage(job_id);
CREATE INDEX idx_proxy_usage_proxy_id ON proxy_usage(proxy_id);
CREATE INDEX idx_api_usage_user_id ON api_usage(user_id);
CREATE INDEX idx_api_usage_created_at ON api_usage(created_at);
CREATE INDEX idx_system_logs_level ON system_logs(level);
CREATE INDEX idx_system_logs_component ON system_logs(component);
CREATE INDEX idx_system_logs_created_at ON system_logs(created_at);

-- Full-text search indexes
CREATE INDEX idx_scraped_content_title_fts ON scraped_content USING gin(to_tsvector('english', title));
CREATE INDEX idx_scraped_content_raw_content_fts ON scraped_content USING gin(to_tsvector('english', raw_content));

-- JSONB indexes for metadata queries
CREATE INDEX idx_users_metadata ON users USING gin(metadata);
CREATE INDEX idx_scraped_content_processed_content ON scraped_content USING gin(processed_content);
CREATE INDEX idx_scraped_content_extracted_data ON scraped_content USING gin(extracted_data);
CREATE INDEX idx_scraped_content_llm_analysis ON scraped_content USING gin(llm_analysis);

-- Triggers for updated_at timestamps
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_sessions_updated_at BEFORE UPDATE ON sessions FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_projects_updated_at BEFORE UPDATE ON projects FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_scraping_jobs_updated_at BEFORE UPDATE ON scraping_jobs FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_scraped_content_updated_at BEFORE UPDATE ON scraped_content FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Row Level Security (RLS) policies for Supabase
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE projects ENABLE ROW LEVEL SECURITY;
ALTER TABLE scraping_jobs ENABLE ROW LEVEL SECURITY;
ALTER TABLE scraped_content ENABLE ROW LEVEL SECURITY;
ALTER TABLE extracted_entities ENABLE ROW LEVEL SECURITY;
ALTER TABLE content_relationships ENABLE ROW LEVEL SECURITY;
ALTER TABLE proxy_usage ENABLE ROW LEVEL SECURITY;
ALTER TABLE api_usage ENABLE ROW LEVEL SECURITY;

-- RLS Policies
CREATE POLICY "Users can view own profile" ON users FOR SELECT USING (auth.uid() = id);
CREATE POLICY "Users can update own profile" ON users FOR UPDATE USING (auth.uid() = id);

CREATE POLICY "Users can view own sessions" ON sessions FOR ALL USING (auth.uid() = user_id);
CREATE POLICY "Users can manage own projects" ON projects FOR ALL USING (auth.uid() = user_id);
CREATE POLICY "Users can manage own scraping jobs" ON scraping_jobs FOR ALL USING (auth.uid() = user_id);
CREATE POLICY "Users can view own scraped content" ON scraped_content FOR ALL USING (auth.uid() = user_id);
CREATE POLICY "Users can view entities from own content" ON extracted_entities FOR SELECT USING (
    EXISTS (SELECT 1 FROM scraped_content WHERE id = content_id AND user_id = auth.uid())
);
CREATE POLICY "Users can view relationships from own content" ON content_relationships FOR SELECT USING (
    EXISTS (SELECT 1 FROM scraped_content WHERE id = source_content_id AND user_id = auth.uid())
);
CREATE POLICY "Users can view own proxy usage" ON proxy_usage FOR SELECT USING (
    EXISTS (SELECT 1 FROM scraping_jobs WHERE id = job_id AND user_id = auth.uid())
);
CREATE POLICY "Users can view own API usage" ON api_usage FOR SELECT USING (auth.uid() = user_id);

-- Views for common queries
CREATE VIEW user_scraping_stats AS
SELECT 
    u.id as user_id,
    u.email,
    COUNT(DISTINCT p.id) as total_projects,
    COUNT(DISTINCT sj.id) as total_jobs,
    COUNT(DISTINCT CASE WHEN sj.status = 'completed' THEN sj.id END) as completed_jobs,
    COUNT(DISTINCT sc.id) as total_content_items,
    SUM(sc.file_size) as total_content_size,
    MAX(sj.completed_at) as last_scraping_activity
FROM users u
LEFT JOIN projects p ON u.id = p.user_id
LEFT JOIN scraping_jobs sj ON u.id = sj.user_id
LEFT JOIN scraped_content sc ON u.id = sc.user_id
GROUP BY u.id, u.email;

CREATE VIEW recent_scraping_activity AS
SELECT 
    sj.id,
    sj.name,
    sj.url,
    sj.status,
    sj.started_at,
    sj.completed_at,
    sj.processing_time_seconds,
    u.email as user_email,
    p.name as project_name,
    COUNT(sc.id) as content_items_extracted
FROM scraping_jobs sj
JOIN users u ON sj.user_id = u.id
LEFT JOIN projects p ON sj.project_id = p.id
LEFT JOIN scraped_content sc ON sj.id = sc.job_id
WHERE sj.created_at >= NOW() - INTERVAL '7 days'
GROUP BY sj.id, sj.name, sj.url, sj.status, sj.started_at, sj.completed_at, 
         sj.processing_time_seconds, u.email, p.name
ORDER BY sj.created_at DESC;
