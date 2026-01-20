#!/usr/bin/env python3
"""
Test script for JiraEscalationFlow Logic App.

Usage:
    python test_workflow.py

Environment variables:
    JIRA_ESCALATION_URL - Logic App trigger URL (required)
"""

import os
import sys
import json
import requests
from datetime import datetime

# Get trigger URL from environment or prompt
TRIGGER_URL = os.environ.get("JIRA_ESCALATION_URL", "")

if not TRIGGER_URL:
    print("Error: JIRA_ESCALATION_URL environment variable not set")
    print("\nSet it with:")
    print('  export JIRA_ESCALATION_URL="<your-logic-app-trigger-url>"')
    sys.exit(1)


def test_escalation(test_case: dict) -> dict:
    """Send a test escalation request and return the response."""
    print(f"\n{'='*60}")
    print(f"Test: {test_case['name']}")
    print(f"{'='*60}")
    print(f"Payload: {json.dumps(test_case['payload'], indent=2)[:200]}...")

    try:
        response = requests.post(
            TRIGGER_URL,
            json=test_case["payload"],
            headers={"Content-Type": "application/json"},
            timeout=30
        )

        result = {
            "test_name": test_case["name"],
            "status_code": response.status_code,
            "success": response.status_code in [200, 201],
            "response": response.json() if response.headers.get("content-type", "").startswith("application/json") else response.text
        }

        if result["success"]:
            print(f"✅ SUCCESS - Status: {response.status_code}")
            if isinstance(result["response"], dict) and "issue" in result["response"]:
                issue = result["response"]["issue"]
                print(f"   Issue Key: {issue.get('key', 'N/A')}")
                print(f"   Issue URL: {issue.get('url', 'N/A')}")
        else:
            print(f"❌ FAILED - Status: {response.status_code}")
            print(f"   Error: {result['response']}")

        return result

    except requests.exceptions.Timeout:
        print(f"❌ TIMEOUT - Request timed out")
        return {"test_name": test_case["name"], "success": False, "error": "Timeout"}
    except requests.exceptions.RequestException as e:
        print(f"❌ ERROR - {str(e)}")
        return {"test_name": test_case["name"], "success": False, "error": str(e)}


# Test cases
TEST_CASES = [
    {
        "name": "Liquidity Gate HOLD - Buffer Breach",
        "payload": {
            "summary": "[HOLD] Payment TXN-EMRG-001 breaches liquidity buffer",
            "description": "Emergency payment to ACME Trading LLC requires treasury review. The payment would breach the minimum cash buffer threshold by $50,000.",
            "priority": "High",
            "source": "liquidity_gate",
            "payment": {
                "payment_id": "TXN-EMRG-001",
                "amount": 250000,
                "currency": "USD",
                "beneficiary": "ACME Trading LLC",
                "account_id": "ACC-BAN-001",
                "entity": "BankSubsidiary_TR"
            },
            "decision": {
                "action": "HOLD",
                "reason": "Payment would breach buffer by $50,000.00",
                "gap": 50000
            }
        }
    },
    {
        "name": "Sanctions Screening ESCALATE - Fuzzy Match",
        "payload": {
            "summary": "[ESCALATE] Counterparty 'BANKE MASKAN' requires sanctions review",
            "description": "Payment beneficiary has a fuzzy match against OFAC SDN list entry 'BANK MASKAN'. Manual review required before release.",
            "priority": "High",
            "source": "sanctions_screening",
            "payment": {
                "payment_id": "TXN-PAY-456",
                "amount": 150000,
                "currency": "EUR",
                "beneficiary": "BANKE MASKAN",
                "account_id": "ACC-EUR-002",
                "entity": "EuropeanSubsidiary"
            },
            "decision": {
                "action": "ESCALATE",
                "reason": "Fuzzy match on OFAC SDN list (90% confidence)",
                "confidence": 90
            }
        }
    },
    {
        "name": "Sanctions Screening BLOCK - Exact Match",
        "payload": {
            "summary": "[BLOCK] Payment to sanctioned entity BANK MASKAN blocked",
            "description": "Payment has been automatically blocked due to exact match on OFAC SDN list. Requires compliance review before any action.",
            "priority": "Highest",
            "source": "sanctions_screening",
            "payment": {
                "payment_id": "TXN-BLK-789",
                "amount": 500000,
                "currency": "USD",
                "beneficiary": "BANK MASKAN",
                "account_id": "ACC-USD-001",
                "entity": "MainBank"
            },
            "decision": {
                "action": "BLOCK",
                "reason": "Exact match on primary_name - OFAC SDN list",
                "confidence": 98
            }
        }
    },
    {
        "name": "Manual Escalation - Simple",
        "payload": {
            "summary": "[REVIEW] Large payment requires manager approval",
            "description": "Payment exceeds single-approver threshold. Manager sign-off required.",
            "priority": "Medium",
            "source": "manual"
        }
    }
]


def main():
    print("=" * 60)
    print("JiraEscalationFlow Test Suite")
    print(f"Timestamp: {datetime.utcnow().isoformat()}Z")
    print("=" * 60)

    results = []
    for test_case in TEST_CASES:
        result = test_escalation(test_case)
        results.append(result)

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)

    passed = sum(1 for r in results if r.get("success"))
    failed = len(results) - passed

    print(f"Total: {len(results)} | Passed: {passed} | Failed: {failed}")

    if failed > 0:
        print("\nFailed tests:")
        for r in results:
            if not r.get("success"):
                print(f"  - {r['test_name']}")

    # Return created issues
    print("\n" + "=" * 60)
    print("CREATED ISSUES")
    print("=" * 60)

    for r in results:
        if r.get("success") and isinstance(r.get("response"), dict):
            issue = r["response"].get("issue", {})
            if issue.get("key"):
                print(f"  {issue['key']}: {r['test_name'][:40]}...")
                print(f"    → {issue.get('url', 'N/A')}")

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
