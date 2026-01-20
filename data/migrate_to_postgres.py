#!/usr/bin/env python3
"""
Treasury Data Migration: CSV/JSON to PostgreSQL
================================================
Migrates treasury data from curated files to PostgreSQL.

Usage:
    python migrate_to_postgres.py [--schema-only] [--data-only]

Environment:
    db_password - PostgreSQL password (from .env)
"""

import csv
import json
import os
import sys
import argparse
from pathlib import Path

try:
    import psycopg2
    from psycopg2.extras import execute_values
except ImportError:
    print("Error: psycopg2 not installed. Run: pip install psycopg2-binary")
    sys.exit(1)

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv is optional

# Database configuration
DB_CONFIG = {
    'host': os.environ.get('DB_HOST', 'treasurydb.postgres.database.azure.com'),
    'database': os.environ.get('DB_NAME', 'treasurydb'),
    'user': os.environ.get('DB_USER', 'dbadmin'),
    'password': os.environ.get('db_password'),
    'sslmode': 'require',
    'connect_timeout': 30,
}

# Data file paths
SCRIPT_DIR = Path(__file__).parent
DATA_DIR = SCRIPT_DIR / 'curated'
SCHEMA_FILE = SCRIPT_DIR / 'schema.sql'

LEDGER_FILE = DATA_DIR / 'ledger_today.csv'
BALANCES_FILE = DATA_DIR / 'starting_balances.csv'
BUFFERS_FILE = DATA_DIR / 'buffers.json'


def get_connection():
    """Create a database connection."""
    if not DB_CONFIG['password']:
        raise ValueError(
            "db_password not found in environment.\n"
            "Add to .env file:\n"
            "  db_password=your_password_here"
        )
    return psycopg2.connect(**DB_CONFIG)


def run_schema(conn):
    """Create schema and tables from schema.sql."""
    print(f"\nCreating schema from {SCHEMA_FILE}...")

    if not SCHEMA_FILE.exists():
        raise FileNotFoundError(f"Schema file not found: {SCHEMA_FILE}")

    with open(SCHEMA_FILE, 'r') as f:
        schema_sql = f.read()

    with conn.cursor() as cur:
        cur.execute(schema_sql)

    conn.commit()
    print("  Schema created successfully.")


def migrate_ledger(conn):
    """Migrate ledger_today.csv to PostgreSQL."""
    print(f"\nMigrating ledger from {LEDGER_FILE}...")

    if not LEDGER_FILE.exists():
        raise FileNotFoundError(f"Ledger file not found: {LEDGER_FILE}")

    with open(LEDGER_FILE, 'r') as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    # Clear existing data
    with conn.cursor() as cur:
        cur.execute("TRUNCATE treasury.ledger_today CASCADE")

    insert_sql = """
        INSERT INTO treasury.ledger_today
        (txn_id, timestamp_utc, entity, account_id, beneficiary_name,
         payment_type, amount, direction, currency, status, alert_flag, channel)
        VALUES %s
    """

    values = [
        (
            row['txn_id'],
            row['timestamp_utc'],
            row['entity'],
            row['account_id'],
            row['beneficiary_name'] or None,
            row['payment_type'] or None,
            float(row['amount']),
            row['direction'],
            row['currency'],
            row['status'],
            row['alert_flag'] if row.get('alert_flag') else None,
            row['channel'] or None
        )
        for row in rows
    ]

    with conn.cursor() as cur:
        execute_values(cur, insert_sql, values, page_size=500)

    conn.commit()
    print(f"  Migrated {len(rows)} ledger records.")
    return len(rows)


def migrate_balances(conn):
    """Migrate starting_balances.csv to PostgreSQL."""
    print(f"\nMigrating balances from {BALANCES_FILE}...")

    if not BALANCES_FILE.exists():
        raise FileNotFoundError(f"Balances file not found: {BALANCES_FILE}")

    with open(BALANCES_FILE, 'r') as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    # Clear existing data
    with conn.cursor() as cur:
        cur.execute("TRUNCATE treasury.starting_balances CASCADE")

    insert_sql = """
        INSERT INTO treasury.starting_balances
        (entity, account_id, currency, start_of_day_balance)
        VALUES %s
    """

    values = [
        (
            row['entity'],
            row['account_id'],
            row['currency'],
            float(row['start_of_day_balance'])
        )
        for row in rows
    ]

    with conn.cursor() as cur:
        execute_values(cur, insert_sql, values, page_size=100)

    conn.commit()
    print(f"  Migrated {len(rows)} balance records.")
    return len(rows)


def migrate_buffers(conn):
    """Migrate buffers.json to PostgreSQL."""
    print(f"\nMigrating buffers from {BUFFERS_FILE}...")

    if not BUFFERS_FILE.exists():
        raise FileNotFoundError(f"Buffers file not found: {BUFFERS_FILE}")

    with open(BUFFERS_FILE, 'r') as f:
        buffers = json.load(f)

    # Clear existing data
    with conn.cursor() as cur:
        cur.execute("TRUNCATE treasury.buffers CASCADE")

    insert_sql = """
        INSERT INTO treasury.buffers
        (entity, currency, min_buffer, cutoff_time_utc, description)
        VALUES %s
    """

    values = [
        (
            buf['entity'],
            buf['currency'],
            float(buf['min_buffer']),
            buf.get('cutoff_time_utc'),
            buf.get('description')
        )
        for buf in buffers
    ]

    with conn.cursor() as cur:
        execute_values(cur, insert_sql, values)

    conn.commit()
    print(f"  Migrated {len(buffers)} buffer records.")
    return len(buffers)


def verify_migration(conn):
    """Verify migration counts."""
    print("\n" + "=" * 50)
    print("VERIFICATION")
    print("=" * 50)

    with conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM treasury.ledger_today")
        ledger_count = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM treasury.starting_balances")
        balance_count = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM treasury.buffers")
        buffer_count = cur.fetchone()[0]

    print(f"  Ledger records:  {ledger_count:,}")
    print(f"  Balance records: {balance_count:,}")
    print(f"  Buffer records:  {buffer_count:,}")
    print(f"  TOTAL:           {ledger_count + balance_count + buffer_count:,}")

    # Verify expected counts
    expected = {'ledger': 3001, 'balances': 260, 'buffers': 6}
    issues = []

    if ledger_count != expected['ledger']:
        issues.append(f"Ledger: expected {expected['ledger']}, got {ledger_count}")
    if balance_count != expected['balances']:
        issues.append(f"Balances: expected {expected['balances']}, got {balance_count}")
    if buffer_count != expected['buffers']:
        issues.append(f"Buffers: expected {expected['buffers']}, got {buffer_count}")

    if issues:
        print("\nWARNINGS:")
        for issue in issues:
            print(f"  - {issue}")
    else:
        print("\n  All counts match expected values.")

    return ledger_count, balance_count, buffer_count


def test_query(conn):
    """Run a test query to verify data integrity."""
    print("\n" + "=" * 50)
    print("TEST QUERY: ACME Emergency Payment")
    print("=" * 50)

    with conn.cursor() as cur:
        cur.execute("""
            SELECT txn_id, beneficiary_name, amount, currency, status
            FROM treasury.ledger_today
            WHERE txn_id = 'TXN-EMRG-001'
        """)
        row = cur.fetchone()

        if row:
            print(f"  Found: {row[0]}")
            print(f"  Beneficiary: {row[1]}")
            print(f"  Amount: {row[3]} {row[2]:,.2f}")
            print(f"  Status: {row[4]}")
        else:
            print("  WARNING: TXN-EMRG-001 not found!")

    # Check buffer for this account
    with conn.cursor() as cur:
        cur.execute("""
            SELECT entity, currency, min_buffer
            FROM treasury.buffers
            WHERE entity = 'BankSubsidiary_TR' AND currency = 'USD'
        """)
        row = cur.fetchone()

        if row:
            print(f"\n  Buffer for {row[0]} ({row[1]}): ${row[2]:,.2f}")


def main():
    parser = argparse.ArgumentParser(description='Migrate treasury data to PostgreSQL')
    parser.add_argument('--schema-only', action='store_true', help='Only create schema, skip data')
    parser.add_argument('--data-only', action='store_true', help='Only migrate data, skip schema')
    args = parser.parse_args()

    print("=" * 60)
    print("Treasury Data Migration: CSV/JSON -> PostgreSQL")
    print("=" * 60)
    print(f"\nTarget: {DB_CONFIG['host']}/{DB_CONFIG['database']}")
    print(f"User: {DB_CONFIG['user']}")

    try:
        conn = get_connection()
        print("Connected to PostgreSQL.")
    except Exception as e:
        print(f"\nFailed to connect: {e}")
        sys.exit(1)

    try:
        if not args.data_only:
            run_schema(conn)

        if not args.schema_only:
            migrate_ledger(conn)
            migrate_balances(conn)
            migrate_buffers(conn)
            verify_migration(conn)
            test_query(conn)

        print("\n" + "=" * 60)
        print("MIGRATION COMPLETED SUCCESSFULLY")
        print("=" * 60)

    except Exception as e:
        conn.rollback()
        print(f"\nMigration failed: {e}")
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    main()
