-- Failed Messages Tracking Table
-- Run this on the warehouse database
-- Only stores messages that failed processing for retry

CREATE TABLE IF NOT EXISTS failed_messages (
    failed_message_id SERIAL PRIMARY KEY,

    -- Kafka message metadata
    topic VARCHAR(255) NOT NULL,
    partition INTEGER NOT NULL,
    message_offset BIGINT NOT NULL,  -- 'offset' is reserved keyword, use 'message_offset'
    message_timestamp TIMESTAMP,

    -- Message content
    message_key VARCHAR(500),
    message_value JSONB NOT NULL, -- Full message for replay

    -- Error information
    error_type VARCHAR(100),
    error_message TEXT,
    error_stacktrace TEXT,

    -- Retry management
    retry_count INTEGER DEFAULT 0,
    max_retries INTEGER DEFAULT 3,
    last_retry_at TIMESTAMP,
    next_retry_at TIMESTAMP,

    -- Status tracking
    status VARCHAR(50) DEFAULT 'pending', -- 'pending', 'retrying', 'resolved', 'ignored', 'dead_letter'
    resolution_notes TEXT,

    -- Timestamps
    failed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMP,

    -- Prevent duplicate storage of same failed message
    UNIQUE(topic, partition, message_offset)
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_failed_msg_status
    ON failed_messages(status) WHERE status IN ('pending', 'retrying');

CREATE INDEX IF NOT EXISTS idx_failed_msg_next_retry
    ON failed_messages(next_retry_at) WHERE status = 'pending';

CREATE INDEX IF NOT EXISTS idx_failed_msg_topic_partition
    ON failed_messages(topic, partition, message_offset);

CREATE INDEX IF NOT EXISTS idx_failed_msg_failed_at
    ON failed_messages(failed_at DESC);

-- View for monitoring failed messages
CREATE OR REPLACE VIEW v_failed_messages_summary AS
SELECT
    topic,
    status,
    error_type,
    COUNT(*) as message_count,
    MIN(failed_at) as first_failure,
    MAX(failed_at) as last_failure,
    AVG(retry_count) as avg_retry_count,
    SUM(CASE WHEN retry_count >= max_retries THEN 1 ELSE 0 END) as dead_letter_count
FROM failed_messages
GROUP BY topic, status, error_type
ORDER BY message_count DESC;

-- View for messages ready to retry
CREATE OR REPLACE VIEW v_messages_ready_for_retry AS
SELECT
    failed_message_id,
    topic,
    partition,
    message_offset,
    error_type,
    retry_count,
    max_retries,
    failed_at,
    last_retry_at
FROM failed_messages
WHERE status = 'pending'
  AND retry_count < max_retries
  AND (next_retry_at IS NULL OR next_retry_at <= CURRENT_TIMESTAMP)
ORDER BY failed_at;

COMMENT ON TABLE failed_messages IS 'Stores only failed Kafka messages for retry and debugging. Successful messages are not stored.';
COMMENT ON COLUMN failed_messages.message_value IS 'Full JSON message content preserved for replay';
COMMENT ON COLUMN failed_messages.status IS 'pending: awaiting retry, retrying: currently being retried, resolved: successfully processed, ignored: manually ignored, dead_letter: exceeded max retries';
