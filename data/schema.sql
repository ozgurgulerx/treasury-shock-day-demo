-- Treasury Demo PostgreSQL Schema
-- Database: treasurydb
-- Server: treasurydb.postgres.database.azure.com

-- Create schema
CREATE SCHEMA IF NOT EXISTS treasury;

-- ============================================================================
-- 1. ledger_today - Daily payment transactions (3,001 rows)
-- ============================================================================
CREATE TABLE IF NOT EXISTS treasury.ledger_today (
    txn_id VARCHAR(50) PRIMARY KEY,
    timestamp_utc TIMESTAMP NOT NULL,
    entity VARCHAR(100) NOT NULL,
    account_id VARCHAR(50) NOT NULL,
    beneficiary_name VARCHAR(255),
    payment_type VARCHAR(100),
    amount DECIMAL(18, 2) NOT NULL,
    direction VARCHAR(10) NOT NULL CHECK (direction IN ('IN', 'OUT')),
    currency VARCHAR(3) NOT NULL,
    status VARCHAR(50) NOT NULL,
    alert_flag VARCHAR(100),
    channel VARCHAR(50)
);

-- Indexes for common query patterns
CREATE INDEX IF NOT EXISTS idx_ledger_account_currency ON treasury.ledger_today(account_id, currency);
CREATE INDEX IF NOT EXISTS idx_ledger_entity ON treasury.ledger_today(entity);
CREATE INDEX IF NOT EXISTS idx_ledger_timestamp ON treasury.ledger_today(timestamp_utc);
CREATE INDEX IF NOT EXISTS idx_ledger_status ON treasury.ledger_today(status);

-- ============================================================================
-- 2. starting_balances - Account opening balances (260 rows)
-- ============================================================================
CREATE TABLE IF NOT EXISTS treasury.starting_balances (
    id SERIAL PRIMARY KEY,
    entity VARCHAR(100) NOT NULL,
    account_id VARCHAR(50) NOT NULL,
    currency VARCHAR(3) NOT NULL,
    start_of_day_balance DECIMAL(18, 2) NOT NULL,
    UNIQUE (entity, account_id, currency)
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_balances_account_currency ON treasury.starting_balances(account_id, currency);
CREATE INDEX IF NOT EXISTS idx_balances_entity ON treasury.starting_balances(entity);

-- ============================================================================
-- 3. buffers - Liquidity buffer thresholds (6 rows)
-- ============================================================================
CREATE TABLE IF NOT EXISTS treasury.buffers (
    id SERIAL PRIMARY KEY,
    entity VARCHAR(100) NOT NULL,
    currency VARCHAR(3) NOT NULL,
    min_buffer DECIMAL(18, 2) NOT NULL,
    cutoff_time_utc TIME,
    description TEXT,
    UNIQUE (entity, currency)
);

-- Index
CREATE INDEX IF NOT EXISTS idx_buffers_entity_currency ON treasury.buffers(entity, currency);
