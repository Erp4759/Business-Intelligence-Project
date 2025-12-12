-- ============================================
-- VAESTA Analytics Tables for Supabase
-- Run this in Supabase SQL Editor
-- ============================================

-- ============================================
-- API CALLS TRACKING
-- ============================================
CREATE TABLE IF NOT EXISTS analytics_api_calls (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    endpoint TEXT NOT NULL,
    method TEXT DEFAULT 'GET',
    username TEXT,
    request_params JSONB DEFAULT '{}',
    response_status INTEGER DEFAULT 200,
    response_time_ms NUMERIC DEFAULT 0,
    error TEXT,
    success BOOLEAN DEFAULT TRUE
);

CREATE INDEX IF NOT EXISTS idx_api_calls_timestamp ON analytics_api_calls(timestamp);
CREATE INDEX IF NOT EXISTS idx_api_calls_username ON analytics_api_calls(username);
CREATE INDEX IF NOT EXISTS idx_api_calls_endpoint ON analytics_api_calls(endpoint);

-- ============================================
-- RECOMMENDATIONS TRACKING
-- ============================================
CREATE TABLE IF NOT EXISTS analytics_recommendations (
    id TEXT PRIMARY KEY,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    username TEXT NOT NULL,
    recommendation_type TEXT NOT NULL,
    items JSONB DEFAULT '[]',
    num_items INTEGER DEFAULT 0,
    context JSONB DEFAULT '{}',
    algorithm_version TEXT DEFAULT 'v1.0',
    ab_variant TEXT DEFAULT 'control'
);

CREATE INDEX IF NOT EXISTS idx_recommendations_timestamp ON analytics_recommendations(timestamp);
CREATE INDEX IF NOT EXISTS idx_recommendations_username ON analytics_recommendations(username);
CREATE INDEX IF NOT EXISTS idx_recommendations_type ON analytics_recommendations(recommendation_type);
CREATE INDEX IF NOT EXISTS idx_recommendations_ab_variant ON analytics_recommendations(ab_variant);

-- ============================================
-- USER INTERACTIONS
-- ============================================
CREATE TABLE IF NOT EXISTS analytics_interactions (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    username TEXT NOT NULL,
    interaction_type TEXT NOT NULL, -- view, click, save, purchase, dismiss, share
    item_id TEXT NOT NULL,
    recommendation_id TEXT,
    item_rank INTEGER,
    metadata JSONB DEFAULT '{}'
);

CREATE INDEX IF NOT EXISTS idx_interactions_timestamp ON analytics_interactions(timestamp);
CREATE INDEX IF NOT EXISTS idx_interactions_username ON analytics_interactions(username);
CREATE INDEX IF NOT EXISTS idx_interactions_type ON analytics_interactions(interaction_type);
CREATE INDEX IF NOT EXISTS idx_interactions_recommendation ON analytics_interactions(recommendation_id);

-- ============================================
-- USER FEEDBACK
-- ============================================
CREATE TABLE IF NOT EXISTS analytics_feedback (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    username TEXT NOT NULL,
    recommendation_id TEXT,
    feedback_type TEXT DEFAULT 'explicit', -- implicit, explicit, survey
    ratings JSONB DEFAULT '{}', -- relevance, satisfaction, diversity, personalization, would_wear
    items_rated TEXT[] DEFAULT '{}',
    comments TEXT,
    context JSONB DEFAULT '{}',
    nps_score INTEGER
);

CREATE INDEX IF NOT EXISTS idx_feedback_timestamp ON analytics_feedback(timestamp);
CREATE INDEX IF NOT EXISTS idx_feedback_username ON analytics_feedback(username);
CREATE INDEX IF NOT EXISTS idx_feedback_recommendation ON analytics_feedback(recommendation_id);

-- ============================================
-- USER SESSIONS
-- ============================================
CREATE TABLE IF NOT EXISTS analytics_sessions (
    session_id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    username TEXT NOT NULL,
    start_time TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    end_time TIMESTAMP WITH TIME ZONE,
    duration_seconds NUMERIC,
    device_info JSONB DEFAULT '{}',
    ip_address TEXT,
    pages_visited TEXT[] DEFAULT '{}',
    recommendations_viewed INTEGER DEFAULT 0,
    interactions_count INTEGER DEFAULT 0,
    feedback_given BOOLEAN DEFAULT FALSE
);

CREATE INDEX IF NOT EXISTS idx_sessions_username ON analytics_sessions(username);
CREATE INDEX IF NOT EXISTS idx_sessions_start_time ON analytics_sessions(start_time);

-- ============================================
-- A/B TEST RESULTS
-- ============================================
CREATE TABLE IF NOT EXISTS analytics_ab_tests (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    test_name TEXT NOT NULL,
    variant TEXT NOT NULL,
    username TEXT NOT NULL,
    metric_name TEXT NOT NULL,
    metric_value NUMERIC,
    context JSONB DEFAULT '{}'
);

CREATE INDEX IF NOT EXISTS idx_ab_tests_name ON analytics_ab_tests(test_name);
CREATE INDEX IF NOT EXISTS idx_ab_tests_variant ON analytics_ab_tests(variant);

-- ============================================
-- ROW LEVEL SECURITY
-- ============================================
ALTER TABLE analytics_api_calls ENABLE ROW LEVEL SECURITY;
ALTER TABLE analytics_recommendations ENABLE ROW LEVEL SECURITY;
ALTER TABLE analytics_interactions ENABLE ROW LEVEL SECURITY;
ALTER TABLE analytics_feedback ENABLE ROW LEVEL SECURITY;
ALTER TABLE analytics_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE analytics_ab_tests ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Allow all analytics_api_calls" ON analytics_api_calls FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Allow all analytics_recommendations" ON analytics_recommendations FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Allow all analytics_interactions" ON analytics_interactions FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Allow all analytics_feedback" ON analytics_feedback FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Allow all analytics_sessions" ON analytics_sessions FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Allow all analytics_ab_tests" ON analytics_ab_tests FOR ALL USING (true) WITH CHECK (true);

-- ============================================
-- USEFUL VIEWS FOR DASHBOARD
-- ============================================

-- Daily CTR View
CREATE OR REPLACE VIEW v_daily_ctr AS
SELECT 
    DATE(r.timestamp) as date,
    COUNT(DISTINCT r.id) as impressions,
    COUNT(DISTINCT i.id) as clicks,
    ROUND(COUNT(DISTINCT i.id)::NUMERIC / NULLIF(COUNT(DISTINCT r.id), 0) * 100, 2) as ctr
FROM analytics_recommendations r
LEFT JOIN analytics_interactions i 
    ON i.recommendation_id = r.id 
    AND i.interaction_type = 'click'
GROUP BY DATE(r.timestamp)
ORDER BY date DESC;

-- User Satisfaction Over Time
CREATE OR REPLACE VIEW v_satisfaction_trend AS
SELECT 
    DATE(timestamp) as date,
    AVG((ratings->>'satisfaction')::NUMERIC) as avg_satisfaction,
    AVG((ratings->>'relevance')::NUMERIC) as avg_relevance,
    AVG((ratings->>'diversity')::NUMERIC) as avg_diversity,
    COUNT(*) as feedback_count
FROM analytics_feedback
WHERE ratings->>'satisfaction' IS NOT NULL
GROUP BY DATE(timestamp)
ORDER BY date DESC;

-- Recommendation Performance by Type
CREATE OR REPLACE VIEW v_recommendation_performance AS
SELECT 
    r.recommendation_type,
    COUNT(DISTINCT r.id) as total_recommendations,
    COUNT(DISTINCT i.id) as total_interactions,
    AVG((f.ratings->>'relevance')::NUMERIC) as avg_relevance,
    AVG((f.ratings->>'satisfaction')::NUMERIC) as avg_satisfaction
FROM analytics_recommendations r
LEFT JOIN analytics_interactions i ON i.recommendation_id = r.id
LEFT JOIN analytics_feedback f ON f.recommendation_id = r.id
GROUP BY r.recommendation_type;

-- ============================================
-- SAMPLE DATA FOR TESTING (Optional)
-- ============================================
-- Uncomment below to insert sample data

/*
INSERT INTO analytics_feedback (username, recommendation_id, ratings, feedback_type) VALUES
('demo_user', 'rec_001', '{"relevance": 4, "satisfaction": 5, "diversity": 4}', 'explicit'),
('demo_user', 'rec_002', '{"relevance": 5, "satisfaction": 4, "diversity": 5}', 'explicit'),
('test_user', 'rec_003', '{"relevance": 3, "satisfaction": 4, "diversity": 4}', 'explicit');
*/
