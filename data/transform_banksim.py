#!/usr/bin/env python3
"""
Transform BankSim CSV into treasury demo curated files:
- ledger_today.csv (payments queue)
- starting_balances.csv (account balances)
- buffers.json (minimum buffer requirements)
"""

import csv
import json
import random
from datetime import datetime, timedelta

# Configuration
RAW_FILE = "bs140513_032310.csv"
TODAY_SLICE_SIZE = 3000  # Number of transactions for "today"
BASE_DATE = datetime(2026, 1, 19, 9, 0)  # Start at 9:00 AM
STEP_MINUTES = 5  # Each BankSim step = 5 minutes

# Seed for reproducibility
random.seed(42)

def load_banksim(filepath):
    """Load BankSim CSV."""
    with open(filepath, 'r') as f:
        reader = csv.DictReader(f)
        return list(reader)

def create_ledger_today(rows):
    """Transform BankSim rows into treasury ledger format."""

    # Take a slice for "today" - mix of fraud and non-fraud
    # Get some fraud cases to make it interesting
    fraud_rows = [r for r in rows if r['fraud'] == '1'][:150]  # 150 fraud cases
    normal_rows = [r for r in rows if r['fraud'] == '0'][:TODAY_SLICE_SIZE - 150]
    today_rows = fraud_rows + normal_rows
    random.shuffle(today_rows)

    # Entity distribution
    entities = ['BankSubsidiary_TR', 'GroupTreasuryCo']
    entity_weights = [0.8, 0.2]

    # Currency distribution
    currencies = ['TRY', 'USD', 'EUR']
    currency_weights = [0.80, 0.15, 0.05]

    # Channel mapping based on category
    channel_map = {
        "'es_transportation'": "INTERNAL",
        "'es_food'": "SEPA",
        "'es_health'": "SWIFT",
        "'es_wellnessandbeauty'": "SEPA",
        "'es_fashion'": "SWIFT",
        "'es_barsandrestaurants'": "SEPA",
        "'es_hyper'": "INTERNAL",
        "'es_sportsandtoys'": "SWIFT",
        "'es_tech'": "SWIFT",
        "'es_home'": "SEPA",
        "'es_hotelservices'": "SWIFT",
        "'es_otherservices'": "INTERNAL",
        "'es_contents'": "INTERNAL",
        "'es_travel'": "SWIFT",
        "'es_leisure'": "SEPA",
    }

    ledger = []

    for i, row in enumerate(today_rows):
        # Parse customer ID to create account
        customer = row['customer'].strip("'")
        customer_num = int(''.join(filter(str.isdigit, customer))) % 50

        # Determine entity and account
        entity = random.choices(entities, weights=entity_weights)[0]
        account_id = f"ACC-{entity[:3]}-{customer_num:03d}"

        # Currency (scale amounts for non-TRY)
        currency = random.choices(currencies, weights=currency_weights)[0]
        base_amount = float(row['amount'])

        # Scale amounts: TRY amounts are larger (exchange rate ~30)
        if currency == 'TRY':
            amount = round(base_amount * 30 * random.uniform(0.8, 1.2), 2)
        elif currency == 'USD':
            amount = round(base_amount * random.uniform(0.9, 1.1), 2)
        else:  # EUR
            amount = round(base_amount * 0.92 * random.uniform(0.9, 1.1), 2)

        # Direction: 90% OUT, 10% IN
        direction = 'IN' if random.random() < 0.10 else 'OUT'

        # Timestamp based on step
        step = int(row['step'])
        timestamp = BASE_DATE + timedelta(minutes=step * STEP_MINUTES + i % 60)

        # Status distribution
        status_roll = random.random()
        if status_roll < 0.6:
            status = 'QUEUED'
        elif status_roll < 0.85:
            status = 'RELEASED'
        elif status_roll < 0.95:
            status = 'PENDING_APPROVAL'
        else:
            status = 'ON_HOLD'

        # Alert flag from fraud (but label as ops anomaly)
        alert_flag = 'ANOMALY_DETECTED' if row['fraud'] == '1' else ''

        # Channel
        category = row['category']
        channel = channel_map.get(category, 'INTERNAL')

        # Clean merchant name
        merchant = row['merchant'].strip("'")

        ledger.append({
            'txn_id': f'TXN-{i+1:06d}',
            'timestamp_utc': timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            'entity': entity,
            'account_id': account_id,
            'beneficiary_name': merchant,
            'payment_type': category.strip("'"),
            'amount': amount,
            'direction': direction,
            'currency': currency,
            'status': status,
            'alert_flag': alert_flag,
            'channel': channel,
        })

    # Sort by timestamp
    ledger.sort(key=lambda x: x['timestamp_utc'])

    # Re-number txn_ids after sorting
    for i, row in enumerate(ledger):
        row['txn_id'] = f'TXN-{i+1:06d}'

    return ledger

def add_emergency_payment(ledger):
    """Add the ACME Trading LLC emergency payment."""

    # Find a good position (around 10:25 AM)
    target_time = datetime(2026, 1, 19, 10, 25)

    # Find insertion point
    insert_idx = 0
    for i, row in enumerate(ledger):
        if row['timestamp_utc'] > target_time.strftime('%Y-%m-%d %H:%M:%S'):
            insert_idx = i
            break

    emergency_payment = {
        'txn_id': f'TXN-EMRG-001',
        'timestamp_utc': '2026-01-19 10:25:00',
        'entity': 'BankSubsidiary_TR',
        'account_id': 'ACC-BAN-001',
        'beneficiary_name': 'ACME Trading LLC',
        'payment_type': 'URGENT_SUPPLIER',
        'amount': 250000.00,
        'direction': 'OUT',
        'currency': 'USD',
        'status': 'QUEUED',
        'alert_flag': '',
        'channel': 'SWIFT',
    }

    ledger.insert(insert_idx, emergency_payment)

    # Re-number all txn_ids
    for i, row in enumerate(ledger):
        if not row['txn_id'].startswith('TXN-EMRG'):
            row['txn_id'] = f'TXN-{i+1:06d}'

    return ledger

def create_starting_balances(ledger):
    """Create starting balances that make the demo dramatic."""

    # Collect unique entity/account/currency combinations from ledger
    accounts = set()
    for row in ledger:
        accounts.add((row['entity'], row['account_id'], row['currency']))

    balances = []

    for entity, account_id, currency in sorted(accounts):
        # Calculate rough outflow for this account/currency
        outflow = sum(
            row['amount'] for row in ledger
            if row['account_id'] == account_id
            and row['currency'] == currency
            and row['direction'] == 'OUT'
            and row['status'] in ('QUEUED', 'RELEASED', 'PENDING_APPROVAL')
        )

        inflow = sum(
            row['amount'] for row in ledger
            if row['account_id'] == account_id
            and row['currency'] == currency
            and row['direction'] == 'IN'
        )

        net_outflow = outflow - inflow

        # Set starting balance to be JUST above buffer (dramatic!)
        # This way the emergency payment will breach the buffer
        if currency == 'TRY':
            # TRY: Set so we're ~5-10% above buffer before emergency
            buffer = 45_000_000
            balance = max(buffer * 1.08 + net_outflow * 0.3, buffer * 1.05)
        elif currency == 'USD':
            # USD: This is where the drama happens with ACME payment
            buffer = 2_000_000
            if account_id == 'ACC-BAN-001':  # The emergency payment account
                # Set balance so ACME payment ($250k) tips us into breach
                # Start with ~$2.15M, after normal outflows we're at ~$2.05M
                # Then ACME $250k payment breaches the $2M buffer
                balance = 2_150_000 + net_outflow * 0.2
            else:
                balance = max(buffer * 1.15 + net_outflow * 0.5, buffer * 1.1)
        else:  # EUR
            buffer = 1_500_000
            balance = max(buffer * 1.2 + net_outflow * 0.5, buffer * 1.1)

        balances.append({
            'entity': entity,
            'account_id': account_id,
            'currency': currency,
            'start_of_day_balance': round(balance, 2),
        })

    return balances

def create_buffers():
    """Create buffer thresholds per entity/currency."""

    buffers = [
        {
            'entity': 'BankSubsidiary_TR',
            'currency': 'TRY',
            'min_buffer': 45_000_000,
            'cutoff_time_utc': '11:30',
            'description': 'Minimum TRY liquidity buffer for Turkish subsidiary'
        },
        {
            'entity': 'BankSubsidiary_TR',
            'currency': 'USD',
            'min_buffer': 2_000_000,
            'cutoff_time_utc': '15:00',
            'description': 'USD nostro buffer for SWIFT payments'
        },
        {
            'entity': 'BankSubsidiary_TR',
            'currency': 'EUR',
            'min_buffer': 1_500_000,
            'cutoff_time_utc': '14:00',
            'description': 'EUR buffer for SEPA payments'
        },
        {
            'entity': 'GroupTreasuryCo',
            'currency': 'TRY',
            'min_buffer': 30_000_000,
            'cutoff_time_utc': '11:30',
            'description': 'Group treasury TRY buffer'
        },
        {
            'entity': 'GroupTreasuryCo',
            'currency': 'USD',
            'min_buffer': 5_000_000,
            'cutoff_time_utc': '16:00',
            'description': 'Group treasury USD buffer'
        },
        {
            'entity': 'GroupTreasuryCo',
            'currency': 'EUR',
            'min_buffer': 3_000_000,
            'cutoff_time_utc': '14:00',
            'description': 'Group treasury EUR buffer'
        },
    ]

    return buffers

def save_csv(data, filepath):
    """Save data as CSV."""
    if not data:
        return
    with open(filepath, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=data[0].keys())
        writer.writeheader()
        writer.writerows(data)
    print(f"Saved {len(data)} rows to {filepath}")

def save_json(data, filepath):
    """Save data as JSON."""
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2)
    print(f"Saved {len(data)} items to {filepath}")

def main():
    print("="*60)
    print("BankSim to Treasury Demo Data Transformation")
    print("="*60)

    # Load raw data
    print(f"\nLoading {RAW_FILE}...")
    rows = load_banksim(RAW_FILE)
    print(f"Loaded {len(rows):,} transactions")

    # Create ledger
    print(f"\nCreating ledger_today.csv ({TODAY_SLICE_SIZE} transactions)...")
    ledger = create_ledger_today(rows)

    # Add emergency payment
    print("Adding ACME Trading LLC emergency payment...")
    ledger = add_emergency_payment(ledger)

    # Save ledger
    save_csv(ledger, 'curated/ledger_today.csv')

    # Summary stats
    print("\n--- Ledger Summary ---")
    currencies = {}
    for row in ledger:
        curr = row['currency']
        currencies[curr] = currencies.get(curr, 0) + 1
    for curr, count in sorted(currencies.items()):
        print(f"  {curr}: {count} transactions")

    directions = {}
    for row in ledger:
        d = row['direction']
        directions[d] = directions.get(d, 0) + 1
    print(f"  OUT: {directions.get('OUT', 0)}, IN: {directions.get('IN', 0)}")

    alerts = sum(1 for r in ledger if r['alert_flag'])
    print(f"  Anomaly alerts: {alerts}")

    # Find ACME payment
    acme = [r for r in ledger if 'ACME' in r['beneficiary_name']]
    if acme:
        print(f"\n  EMERGENCY PAYMENT: {acme[0]['beneficiary_name']}")
        print(f"    Amount: ${acme[0]['amount']:,.2f} {acme[0]['currency']}")
        print(f"    Account: {acme[0]['account_id']}")
        print(f"    Time: {acme[0]['timestamp_utc']}")

    # Create starting balances
    print("\nCreating starting_balances.csv...")
    balances = create_starting_balances(ledger)
    save_csv(balances, 'curated/starting_balances.csv')

    # Show key balances
    print("\n--- Key Balances ---")
    for b in balances:
        if b['account_id'] == 'ACC-BAN-001' or b['currency'] == 'USD':
            print(f"  {b['account_id']} ({b['currency']}): {b['start_of_day_balance']:,.2f}")

    # Create buffers
    print("\nCreating buffers.json...")
    buffers = create_buffers()
    save_json(buffers, 'curated/buffers.json')

    print("\n--- Buffer Thresholds ---")
    for b in buffers:
        print(f"  {b['entity']} {b['currency']}: {b['min_buffer']:,} (cutoff: {b['cutoff_time_utc']})")

    print("\n" + "="*60)
    print("DONE! Files created in curated/:")
    print("  - ledger_today.csv")
    print("  - starting_balances.csv")
    print("  - buffers.json")
    print("="*60)

    # Sanity check
    print("\n--- SANITY CHECK ---")
    usd_in_ledger = any(r['currency'] == 'USD' for r in ledger)
    acme_exists = any('ACME' in r['beneficiary_name'] for r in ledger)
    usd_balance = any(b['currency'] == 'USD' and b['account_id'] == 'ACC-BAN-001' for b in balances)
    usd_buffer = any(b['currency'] == 'USD' for b in buffers)

    print(f"  USD transactions in ledger: {'✓' if usd_in_ledger else '✗'}")
    print(f"  ACME Trading LLC payment: {'✓' if acme_exists else '✗'}")
    print(f"  USD balance for ACC-BAN-001: {'✓' if usd_balance else '✗'}")
    print(f"  USD buffer defined: {'✓' if usd_buffer else '✗'}")

if __name__ == "__main__":
    main()
