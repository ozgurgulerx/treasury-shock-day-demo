#!/usr/bin/env python3
"""Test the SanctionsScreeningFlow Logic App with fuzzy matching."""

import requests
import json

TRIGGER_URL = "https://prod-35.uksouth.logic.azure.com:443/workflows/cc66c376585147c6aab13c262ada26f4/triggers/When_a_HTTP_request_is_received/paths/invoke?api-version=2016-06-01&sp=%2Ftriggers%2FWhen_a_HTTP_request_is_received%2Frun&sv=1.0&sig=R4rI4j2aOC0cxpcU-XYrZlTiPGtL6aV_JTAgJHY1_dU"

def test_screening(name: str, expected_decision: str = None, description: str = None):
    """Test a name against the sanctions screening workflow."""
    print(f"\n{'='*70}")
    print(f"Testing: '{name}'")
    if description:
        print(f"         ({description})")
    print(f"{'='*70}")

    response = requests.post(
        TRIGGER_URL,
        headers={"Content-Type": "application/json"},
        json={"name": name}
    )

    if response.status_code == 200:
        data = response.json()
        decision = data.get("decision", "UNKNOWN")
        confidence = data.get("confidence", 0)
        match_type = data.get("match_type", "NONE")
        match_reason = data.get("match_reason", "")
        search_score = data.get("search_score", 0)
        best_match = data.get("best_match", {})
        fuzzy_query = data.get("input", {}).get("fuzzy_query", "")

        print(f"Decision:     {decision}")
        print(f"Confidence:   {confidence}%")
        print(f"Match Type:   {match_type}")
        print(f"Search Score: {search_score}")

        if match_reason:
            print(f"Match Reason: {match_reason}")

        if best_match and best_match.get("primary_name"):
            print(f"Best Match:   {best_match.get('primary_name')}")
            print(f"Programs:     {best_match.get('programs', [])}")

        print(f"Fuzzy Query:  {fuzzy_query}")
        print(f"Version:      {data.get('audit', {}).get('version', 'N/A')}")

        if expected_decision and decision != expected_decision:
            print(f"⚠️  WARNING: Expected {expected_decision}, got {decision}")
        else:
            print(f"✓ Result as expected")

        return data
    else:
        print(f"Error: {response.status_code}")
        print(response.text)
        return None

def main():
    print("\n" + "="*70)
    print("SANCTIONS SCREENING WORKFLOW TEST (v2.0 - Fuzzy Matching)")
    print("="*70)

    # Test cases with descriptions
    test_cases = [
        # Exact matches - should BLOCK
        ("BANK MASKAN", "BLOCK", "Exact match - Iranian bank"),
        ("TANCHON COMMERCIAL BANK", "BLOCK", "Exact match - NK bank"),
        ("AEROCARIBBEAN AIRLINES", "BLOCK", "Exact match - Cuban airline"),

        # Fuzzy matches - typos and variations (should still catch)
        ("BANKE MASKAN", "BLOCK", "Typo - swapped letter"),
        ("BANK MASKAAN", "BLOCK", "Typo - extra letter"),
        ("BNKA MASKAN", "BLOCK", "Typo - missing letter"),

        # Clear cases - not sanctioned
        ("Microsoft Corporation", "CLEAR", "Not sanctioned"),
        ("Amazon Web Services", "CLEAR", "Not sanctioned"),
        ("XYZ Widgets Ltd", "CLEAR", "Not sanctioned"),

        # AKA name matches - Housing Bank is AKA of BANK MASKAN
        ("Housing Bank", "BLOCK", "Matches AKA of BANK MASKAN (Housing Bank of Iran)"),
    ]

    results = []
    for test_case in test_cases:
        name = test_case[0]
        expected = test_case[1]
        description = test_case[2] if len(test_case) > 2 else None

        result = test_screening(name, expected, description)
        if result:
            results.append({
                "name": name,
                "description": description,
                "expected": expected,
                "actual": result.get("decision"),
                "match_type": result.get("match_type"),
                "confidence": result.get("confidence"),
                "passed": result.get("decision") == expected
            })

    # Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    passed = sum(1 for r in results if r["passed"])
    print(f"Passed: {passed}/{len(results)}")
    print()

    for r in results:
        status = "✓" if r["passed"] else "✗"
        print(f"  {status} {r['name']}: {r['actual']} ({r['match_type']}, {r['confidence']}%)")

if __name__ == "__main__":
    main()
