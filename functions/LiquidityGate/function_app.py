"""
Liquidity Gate Azure Function
=============================
Deterministic intraday liquidity impact simulation.
(PostgreSQL Version using pg8000)

Given an emergency payment, computes:
1. If releasing this payment breaches the minimum cash buffer
2. When the breach would happen
3. By how much (gap to buffer)
4. Context: net outflows, top beneficiaries, anomaly flags
"""

import azure.functions as func
import json
import logging
import os
import uuid
import traceback
from datetime import datetime
from collections import defaultdict
from decimal import Decimal

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)

# Database Configuration
DB_CONFIG = {
    'host': os.environ.get('DB_HOST', 'treasurydb.postgres.database.azure.com'),
    'database': os.environ.get('DB_NAME', 'treasurydb'),
    'user': os.environ.get('DB_USER', 'dbadmin'),
    'password': os.environ.get('db_password'),
}


def get_db_connection():
    """Create a database connection using pg8000."""
    import pg8000.native
    return pg8000.native.Connection(
        host=DB_CONFIG['host'],
        database=DB_CONFIG['database'],
        user=DB_CONFIG['user'],
        password=DB_CONFIG['password'],
        ssl_context=True,
        timeout=30,
    )


def convert_value(val):
    """Convert database values for JSON serialization."""
    if isinstance(val, Decimal):
        return float(val)
    if isinstance(val, datetime):
        return val.strftime('%Y-%m-%d %H:%M:%S')
    return val


def load_ledger() -> list[dict]:
    """Load ledger transactions from PostgreSQL."""
    conn = get_db_connection()
    rows = conn.run("""
        SELECT
            txn_id,
            TO_CHAR(timestamp_utc, 'YYYY-MM-DD HH24:MI:SS') as timestamp_utc,
            entity,
            account_id,
            beneficiary_name,
            payment_type,
            amount,
            direction,
            currency,
            status,
            alert_flag,
            channel
        FROM treasury.ledger_today
        ORDER BY timestamp_utc
    """)
    columns = ['txn_id', 'timestamp_utc', 'entity', 'account_id', 'beneficiary_name',
               'payment_type', 'amount', 'direction', 'currency', 'status', 'alert_flag', 'channel']
    conn.close()
    return [{col: convert_value(val) for col, val in zip(columns, row)} for row in rows]


def load_balances() -> list[dict]:
    """Load starting balances from PostgreSQL."""
    conn = get_db_connection()
    rows = conn.run("""
        SELECT
            entity,
            account_id,
            currency,
            start_of_day_balance
        FROM treasury.starting_balances
    """)
    columns = ['entity', 'account_id', 'currency', 'start_of_day_balance']
    conn.close()
    return [{col: convert_value(val) for col, val in zip(columns, row)} for row in rows]


def load_buffers() -> list[dict]:
    """Load buffer thresholds from PostgreSQL."""
    conn = get_db_connection()
    rows = conn.run("""
        SELECT
            entity,
            currency,
            min_buffer,
            TO_CHAR(cutoff_time_utc, 'HH24:MI') as cutoff_time_utc,
            description
        FROM treasury.buffers
    """)
    columns = ['entity', 'currency', 'min_buffer', 'cutoff_time_utc', 'description']
    conn.close()
    return [{col: convert_value(val) for col, val in zip(columns, row)} for row in rows]


def parse_timestamp(ts: str) -> datetime:
    """Parse timestamp string to datetime."""
    formats = [
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d %H:%M",
        "%Y-%m-%dT%H:%M",
    ]
    for fmt in formats:
        try:
            return datetime.strptime(ts, fmt)
        except ValueError:
            continue
    raise ValueError(f"Unable to parse timestamp: {ts}")


def compute_liquidity_impact(
    ledger: list[dict],
    balances: list[dict],
    buffers: list[dict],
    payment_id: str = None,
    hypothetical_payment: dict = None,
    entity_filter: str = None,
    currency_filter: str = None,
) -> dict:
    """
    Core liquidity computation.

    Args:
        ledger: Today's transactions
        balances: Starting balances per account/currency
        buffers: Buffer thresholds per entity/currency
        payment_id: ID of payment to simulate releasing (from ledger)
        hypothetical_payment: Hypothetical payment to simulate
        entity_filter: Filter to specific entity
        currency_filter: Filter to specific currency

    Returns:
        Structured result with breach verdict and evidence
    """
    run_id = str(uuid.uuid4())[:8]
    timestamp_utc = datetime.utcnow().isoformat() + "Z"

    # Find the target payment
    target_payment = None
    if payment_id:
        for txn in ledger:
            if txn.get('txn_id') == payment_id:
                target_payment = {
                    'payment_id': txn['txn_id'],
                    'amount': float(txn['amount']),
                    'currency': txn['currency'],
                    'account_id': txn['account_id'],
                    'entity': txn['entity'],
                    'beneficiary_name': txn['beneficiary_name'],
                    'timestamp_utc': txn['timestamp_utc'],
                    'direction': txn.get('direction', 'OUT'),
                    'status': txn.get('status', 'QUEUED'),
                }
                break
        if not target_payment:
            return {
                "error": f"Payment {payment_id} not found in ledger",
                "audit": {"run_id": run_id, "timestamp_utc": timestamp_utc}
            }
    elif hypothetical_payment:
        target_payment = {
            'payment_id': hypothetical_payment.get('payment_id', 'HYPOTHETICAL'),
            'amount': float(hypothetical_payment['amount']),
            'currency': hypothetical_payment['currency'],
            'account_id': hypothetical_payment['account_id'],
            'entity': hypothetical_payment['entity'],
            'beneficiary_name': hypothetical_payment.get('beneficiary_name', 'Unknown'),
            'timestamp_utc': hypothetical_payment.get('timestamp_utc', datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')),
            'direction': hypothetical_payment.get('direction', 'OUT'),
            'status': 'HYPOTHETICAL',
        }
    else:
        return {
            "error": "Either payment_id or hypothetical_payment must be provided",
            "audit": {"run_id": run_id, "timestamp_utc": timestamp_utc}
        }

    # Determine filters from target payment
    target_entity = entity_filter or target_payment['entity']
    target_currency = currency_filter or target_payment['currency']
    target_account = target_payment['account_id']

    # Get starting balance for target account/currency
    starting_balance = 0
    for bal in balances:
        if bal['account_id'] == target_account and bal['currency'] == target_currency:
            starting_balance = float(bal['start_of_day_balance'])
            break

    # Get buffer threshold for entity/currency
    buffer_threshold = 0
    cutoff_time = None
    for buf in buffers:
        if buf['entity'] == target_entity and buf['currency'] == target_currency:
            buffer_threshold = float(buf['min_buffer'])
            cutoff_time = buf.get('cutoff_time_utc')
            break

    # Filter and sort ledger by timestamp
    relevant_txns = []
    for txn in ledger:
        if txn['account_id'] == target_account and txn['currency'] == target_currency:
            # Skip the target payment if it's QUEUED (we'll simulate its release)
            if txn.get('txn_id') == payment_id and txn.get('status') == 'QUEUED':
                continue
            relevant_txns.append({
                'txn_id': txn['txn_id'],
                'timestamp': parse_timestamp(txn['timestamp_utc']),
                'timestamp_str': txn['timestamp_utc'],
                'amount': float(txn['amount']),
                'direction': txn.get('direction', 'OUT'),
                'beneficiary': txn.get('beneficiary_name', ''),
                'status': txn.get('status', 'RELEASED'),
                'alert_flag': txn.get('alert_flag', ''),
            })

    # Add target payment at its scheduled time
    target_timestamp = parse_timestamp(target_payment['timestamp_utc'])
    relevant_txns.append({
        'txn_id': target_payment['payment_id'],
        'timestamp': target_timestamp,
        'timestamp_str': target_payment['timestamp_utc'],
        'amount': target_payment['amount'],
        'direction': target_payment['direction'],
        'beneficiary': target_payment['beneficiary_name'],
        'status': 'SIMULATED_RELEASE',
        'alert_flag': '',
        'is_target': True,
    })

    # Sort by timestamp
    relevant_txns.sort(key=lambda x: x['timestamp'])

    # Simulate balance trajectory
    balance = starting_balance
    min_balance = starting_balance
    min_balance_time = None
    first_breach_time = None
    breach_gap = 0
    balance_trajectory = []

    # Track beneficiary totals for concentration analysis
    beneficiary_totals = defaultdict(float)
    anomalies = []
    total_outflow = 0
    total_inflow = 0

    for txn in relevant_txns:
        # Apply transaction
        if txn['direction'] == 'OUT':
            balance -= txn['amount']
            total_outflow += txn['amount']
            beneficiary_totals[txn['beneficiary']] += txn['amount']
        else:  # IN
            balance += txn['amount']
            total_inflow += txn['amount']

        # Track trajectory
        balance_trajectory.append({
            'timestamp': txn['timestamp_str'],
            'txn_id': txn['txn_id'],
            'amount': txn['amount'],
            'direction': txn['direction'],
            'balance_after': round(balance, 2),
            'is_target_payment': txn.get('is_target', False),
        })

        # Track minimum balance
        if balance < min_balance:
            min_balance = balance
            min_balance_time = txn['timestamp_str']

        # Check for buffer breach
        if balance < buffer_threshold and first_breach_time is None:
            first_breach_time = txn['timestamp_str']
            breach_gap = buffer_threshold - balance

        # Collect anomalies
        if txn.get('alert_flag'):
            anomalies.append({
                'txn_id': txn['txn_id'],
                'flag': txn['alert_flag'],
                'amount': txn['amount'],
                'beneficiary': txn['beneficiary'],
            })

    # Calculate beneficiary concentration (top 5)
    top_beneficiaries = sorted(
        [{'beneficiary': k, 'total_amount': round(v, 2)} for k, v in beneficiary_totals.items()],
        key=lambda x: x['total_amount'],
        reverse=True
    )[:5]

    # Determine breach status
    breach = min_balance < buffer_threshold

    # Build result
    result = {
        "buffer_breach_risk": {
            "breach": breach,
            "first_breach_time": first_breach_time,
            "gap": round(breach_gap, 2) if breach else 0,
            "projected_balance_min": round(min_balance, 2),
            "min_balance_time": min_balance_time,
            "buffer_threshold": buffer_threshold,
            "headroom": round(min_balance - buffer_threshold, 2),
        },
        "payment_context": {
            "payment_id": target_payment['payment_id'],
            "amount": target_payment['amount'],
            "currency": target_currency,
            "beneficiary": target_payment['beneficiary_name'],
            "account_id": target_account,
            "entity": target_entity,
            "scheduled_time": target_payment['timestamp_utc'],
        },
        "account_summary": {
            "start_of_day_balance": starting_balance,
            "total_outflow": round(total_outflow, 2),
            "total_inflow": round(total_inflow, 2),
            "net_flow": round(total_inflow - total_outflow, 2),
            "end_of_day_balance": round(balance, 2),
            "transaction_count": len(relevant_txns),
        },
        "concentration_analysis": {
            "top_beneficiaries": top_beneficiaries,
            "largest_single_payment": max([t['amount'] for t in relevant_txns if t['direction'] == 'OUT'], default=0),
        },
        "anomalies": anomalies[:10],  # Limit to 10
        "recommendation": {
            "action": "HOLD" if breach else "RELEASE",
            "reason": f"Payment would breach buffer by ${breach_gap:,.2f}" if breach else "Payment within buffer limits",
            "alternatives": [
                "Delay payment until inflows received",
                "Request partial release",
                "Escalate to treasury for funding",
            ] if breach else [],
        },
        "audit": {
            "run_id": run_id,
            "timestamp_utc": timestamp_utc,
            "data_snapshot": {
                "ledger_rows": len(ledger),
                "balance_rows": len(balances),
                "buffer_rules": len(buffers),
            },
            "cutoff_time": cutoff_time,
            "version": "2.0.0",
            "data_source": "PostgreSQL (pg8000)",
        },
    }

    return result


@app.route(route="compute_liquidity_impact", methods=["POST"])
def compute_liquidity_impact_http(req: func.HttpRequest) -> func.HttpResponse:
    """
    HTTP trigger for liquidity impact computation.

    Request body:
    {
        "payment_id": "TXN-EMRG-001",  // OR
        "hypothetical_payment": {
            "amount": 250000,
            "currency": "USD",
            "account_id": "ACC-BAN-001",
            "entity": "BankSubsidiary_TR",
            "beneficiary_name": "ACME Trading LLC",
            "timestamp_utc": "2026-01-19 10:25:00"
        },
        "entity_filter": "BankSubsidiary_TR",  // optional
        "currency_filter": "USD"  // optional
    }
    """
    logging.info("Liquidity impact computation requested")

    try:
        # Parse request
        req_body = req.get_json()
    except ValueError:
        return func.HttpResponse(
            json.dumps({"error": "Invalid JSON in request body"}),
            status_code=400,
            mimetype="application/json"
        )

    payment_id = req_body.get('payment_id')
    hypothetical_payment = req_body.get('hypothetical_payment')
    entity_filter = req_body.get('entity_filter')
    currency_filter = req_body.get('currency_filter')

    if not payment_id and not hypothetical_payment:
        return func.HttpResponse(
            json.dumps({"error": "Either payment_id or hypothetical_payment must be provided"}),
            status_code=400,
            mimetype="application/json"
        )

    try:
        # Load data from PostgreSQL
        logging.info("Loading data from PostgreSQL...")
        ledger = load_ledger()
        balances = load_balances()
        buffers = load_buffers()
        logging.info(f"Loaded {len(ledger)} ledger rows, {len(balances)} balance rows, {len(buffers)} buffer rules")

        # Compute liquidity impact
        result = compute_liquidity_impact(
            ledger=ledger,
            balances=balances,
            buffers=buffers,
            payment_id=payment_id,
            hypothetical_payment=hypothetical_payment,
            entity_filter=entity_filter,
            currency_filter=currency_filter,
        )

        return func.HttpResponse(
            json.dumps(result, indent=2),
            status_code=200,
            mimetype="application/json"
        )

    except Exception as e:
        logging.error(f"Error computing liquidity impact: {str(e)}")
        return func.HttpResponse(
            json.dumps({"error": str(e), "traceback": traceback.format_exc()}),
            status_code=500,
            mimetype="application/json"
        )


@app.route(route="ping", methods=["GET"])
def ping_check(req: func.HttpRequest) -> func.HttpResponse:
    """Simple ping endpoint - no database."""
    return func.HttpResponse(
        json.dumps({
            "status": "pong",
            "message": "Function is running with pg8000!",
            "env_vars": {
                "DB_HOST": DB_CONFIG['host'],
                "DB_USER": DB_CONFIG['user'],
                "has_password": bool(DB_CONFIG['password'])
            }
        }, indent=2),
        status_code=200,
        mimetype="application/json"
    )


# =============================================================================
# MCP Tool Triggers for AI Agent Integration
# =============================================================================

TOOL_PROPERTIES_LIQUIDITY_IMPACT = json.dumps([
    {"propertyName": "payment_id", "propertyType": "string", "description": "Transaction ID of a queued payment to simulate (e.g., TXN-EMRG-001)", "isRequired": False},
    {"propertyName": "amount", "propertyType": "number", "description": "Amount for hypothetical payment simulation", "isRequired": False},
    {"propertyName": "currency", "propertyType": "string", "description": "Currency code (e.g., USD, TRY, EUR)", "isRequired": False},
    {"propertyName": "account_id", "propertyType": "string", "description": "Account ID (e.g., ACC-BAN-001)", "isRequired": False},
    {"propertyName": "entity", "propertyType": "string", "description": "Entity name (e.g., BankSubsidiary_TR)", "isRequired": False},
    {"propertyName": "beneficiary_name", "propertyType": "string", "description": "Beneficiary name", "isRequired": False},
    {"propertyName": "timestamp_utc", "propertyType": "string", "description": "Payment timestamp (YYYY-MM-DD HH:MM:SS)", "isRequired": False}
])


@app.generic_trigger(
    arg_name="context",
    type="mcpToolTrigger",
    toolName="compute_liquidity_impact",
    description="Compute intraday liquidity impact for a payment. Determines if releasing a payment would breach minimum cash buffer thresholds. Returns breach status, timing, gap amount, and recommendations.",
    toolProperties=TOOL_PROPERTIES_LIQUIDITY_IMPACT
)
def compute_liquidity_impact_mcp(context: str) -> str:
    """MCP Tool: Compute liquidity impact of a payment."""
    logging.info(f"MCP compute_liquidity_impact called with context: {context}")

    try:
        content = json.loads(context)
        arguments = content.get("arguments", {})

        payment_id = arguments.get("payment_id")
        hypothetical_payment = None

        if not payment_id and arguments.get("amount"):
            hypothetical_payment = {
                "amount": arguments.get("amount"),
                "currency": arguments.get("currency", "USD"),
                "account_id": arguments.get("account_id"),
                "entity": arguments.get("entity"),
                "beneficiary_name": arguments.get("beneficiary_name", "Unknown"),
                "timestamp_utc": arguments.get("timestamp_utc"),
            }

        if not payment_id and not hypothetical_payment:
            return json.dumps({"error": "Either payment_id or hypothetical payment parameters required"})

        ledger = load_ledger()
        balances = load_balances()
        buffers = load_buffers()

        result = compute_liquidity_impact(
            ledger=ledger,
            balances=balances,
            buffers=buffers,
            payment_id=payment_id,
            hypothetical_payment=hypothetical_payment,
        )

        return json.dumps(result, indent=2)
    except Exception as e:
        logging.error(f"MCP Tool error: {str(e)}")
        return json.dumps({"error": str(e), "traceback": traceback.format_exc()})


@app.route(route="health", methods=["GET"])
def health_check(req: func.HttpRequest) -> func.HttpResponse:
    """Health check endpoint with database connectivity check."""
    db_status = "unknown"
    db_error = None
    row_counts = {}

    try:
        conn = get_db_connection()

        # Test basic connectivity
        conn.run("SELECT 1")
        db_status = "connected"

        # Get row counts from treasury tables
        try:
            ledger_count = conn.run("SELECT COUNT(*) FROM treasury.ledger_today")[0][0]
            balance_count = conn.run("SELECT COUNT(*) FROM treasury.starting_balances")[0][0]
            buffer_count = conn.run("SELECT COUNT(*) FROM treasury.buffers")[0][0]
            row_counts = {
                "ledger_today": ledger_count,
                "starting_balances": balance_count,
                "buffers": buffer_count
            }
        except Exception as e:
            row_counts = {"error": str(e)}

        conn.close()
    except Exception as e:
        db_status = "error"
        db_error = traceback.format_exc()

    status = "healthy" if db_status == "connected" else "degraded"

    response = {
        "status": status,
        "service": "LiquidityGate",
        "version": "2.0.0",
        "database": {
            "host": DB_CONFIG['host'],
            "database": DB_CONFIG['database'],
            "status": db_status,
            "row_counts": row_counts if row_counts else None,
        }
    }

    if db_error:
        response["database"]["error"] = db_error

    return func.HttpResponse(
        json.dumps(response, indent=2),
        status_code=200 if status == "healthy" else 503,
        mimetype="application/json"
    )
