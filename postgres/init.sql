-- E-Commerce Events Database Initialization

-- Create the events table
CREATE TABLE IF NOT EXISTS user_events (
    event_id SERIAL PRIMARY KEY,
    user_id VARCHAR(50) NOT NULL,
    event_type VARCHAR(20) NOT NULL,
    product_id VARCHAR(50) NOT NULL,
    product_name VARCHAR(200),
    product_category VARCHAR(100),
    price DECIMAL(10, 2),
    event_timestamp TIMESTAMP NOT NULL,
    session_id VARCHAR(100),
    device_type VARCHAR(50),
    inserted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for faster queries
CREATE INDEX idx_user_id ON user_events(user_id);
CREATE INDEX idx_event_type ON user_events(event_type);
CREATE INDEX idx_event_timestamp ON user_events(event_timestamp);
CREATE INDEX idx_product_category ON user_events(product_category);

-- Create a view for quick analytics
CREATE VIEW event_summary AS
SELECT 
    event_type,
    COUNT(*) as event_count,
    COUNT(DISTINCT user_id) as unique_users,
    AVG(price) as avg_price,
    DATE(event_timestamp) as event_date
FROM user_events
GROUP BY event_type, DATE(event_timestamp);

-- Grant necessary permissions
GRANT ALL PRIVILEGES ON TABLE user_events TO sparkuser;
GRANT ALL PRIVILEGES ON SEQUENCE user_events_event_id_seq TO sparkuser;
GRANT SELECT ON event_summary TO sparkuser;

-- Insert some test data to verify setup
INSERT INTO user_events (
    user_id, 
    event_type, 
    product_id, 
    product_name, 
    product_category, 
    price, 
    event_timestamp,
    session_id,
    device_type
) VALUES 
    ('test_user_001', 'view', 'PROD_001', 'Wireless Mouse', 'Electronics', 29.99, NOW(), 'session_001', 'mobile'),
    ('test_user_002', 'purchase', 'PROD_002', 'USB Cable', 'Accessories', 9.99, NOW(), 'session_002', 'desktop');

-- Display confirmation message
DO $$
BEGIN
    RAISE NOTICE 'Database initialized successfully!';
    RAISE NOTICE 'Table: user_events created';
    RAISE NOTICE 'Indexes created for performance optimization';
    RAISE NOTICE 'Test data inserted: 2 rows';
END $$;