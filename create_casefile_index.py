#!/usr/bin/env python3
"""
Create Azure AI Search index for incident casefiles (KB cards).
Third index for Foundry IQ - provides institutional memory / precedent lookup.
"""

import os
import json
from pathlib import Path
from dotenv import load_dotenv
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (
    SearchIndex,
    SimpleField,
    SearchableField,
    SearchFieldDataType,
    SemanticConfiguration,
    SemanticField,
    SemanticPrioritizedFields,
    SemanticSearch,
)

# Load environment variables
load_dotenv()

# Configuration
INDEX_NAME = "idx-incident-casefiles-v1"
CASEFILES_PATH = Path(__file__).parent / "casefiles" / "v1" / "kb_cards"


def get_search_clients():
    """Initialize Azure Search clients."""
    endpoint = os.getenv("AZURE_SEARCH_ENDPOINT")
    api_key = os.getenv("AZURE_SEARCH_ADMIN_KEY")

    if not endpoint or not api_key:
        raise ValueError("Missing AZURE_SEARCH_ENDPOINT or AZURE_SEARCH_ADMIN_KEY in .env")

    credential = AzureKeyCredential(api_key)
    index_client = SearchIndexClient(endpoint=endpoint, credential=credential)
    search_client = SearchClient(endpoint=endpoint, index_name=INDEX_NAME, credential=credential)

    return index_client, search_client


def create_index(index_client: SearchIndexClient):
    """Create the casefile index with semantic configuration."""
    print(f"Creating index: {INDEX_NAME}")

    # Define semantic configuration
    semantic_config = SemanticConfiguration(
        name="casefile-semantic-config",
        prioritized_fields=SemanticPrioritizedFields(
            title_field=SemanticField(field_name="title"),
            content_fields=[SemanticField(field_name="content")],
            keywords_fields=[
                SemanticField(field_name="beneficiary_name"),
                SemanticField(field_name="decision"),
            ]
        )
    )

    semantic_search = SemanticSearch(configurations=[semantic_config])

    # Define fields
    fields = [
        # Key field
        SimpleField(
            name="id",
            type=SearchFieldDataType.String,
            key=True,
            filterable=True,
        ),
        # Searchable fields
        SearchableField(
            name="title",
            type=SearchFieldDataType.String,
            analyzer_name="en.lucene",
        ),
        SearchableField(
            name="content",
            type=SearchFieldDataType.String,
            analyzer_name="en.lucene",
        ),
        SearchableField(
            name="beneficiary_name",
            type=SearchFieldDataType.String,
            filterable=True,
        ),
        # Filterable fields for structured queries
        SimpleField(
            name="doc_type",
            type=SearchFieldDataType.String,
            filterable=True,
        ),
        SimpleField(
            name="incident_id",
            type=SearchFieldDataType.String,
            filterable=True,
        ),
        SimpleField(
            name="entity",
            type=SearchFieldDataType.String,
            filterable=True,
            facetable=True,
        ),
        SimpleField(
            name="account_id",
            type=SearchFieldDataType.String,
            filterable=True,
        ),
        SimpleField(
            name="currency",
            type=SearchFieldDataType.String,
            filterable=True,
            facetable=True,
        ),
        SimpleField(
            name="amount",
            type=SearchFieldDataType.Double,
            filterable=True,
            sortable=True,
        ),
        SimpleField(
            name="sanctions_decision",
            type=SearchFieldDataType.String,
            filterable=True,
            facetable=True,
        ),
        SimpleField(
            name="liquidity_breach",
            type=SearchFieldDataType.Boolean,
            filterable=True,
            facetable=True,
        ),
        SimpleField(
            name="breach_gap",
            type=SearchFieldDataType.Double,
            filterable=True,
        ),
        SimpleField(
            name="cutoff_time_utc",
            type=SearchFieldDataType.String,
            filterable=True,
        ),
        SimpleField(
            name="decision",
            type=SearchFieldDataType.String,
            filterable=True,
            facetable=True,
        ),
        # Complex fields stored as strings
        SimpleField(
            name="approvals_required",
            type=SearchFieldDataType.String,
            filterable=False,
        ),
        SimpleField(
            name="audit_artifacts",
            type=SearchFieldDataType.String,
            filterable=False,
        ),
        SimpleField(
            name="tool_run_ids",
            type=SearchFieldDataType.String,
            filterable=False,
        ),
        # Timestamps
        SimpleField(
            name="created_at_utc",
            type=SearchFieldDataType.DateTimeOffset,
            filterable=True,
            sortable=True,
        ),
        SimpleField(
            name="resolved_at_utc",
            type=SearchFieldDataType.DateTimeOffset,
            filterable=True,
            sortable=True,
        ),
        SimpleField(
            name="resolution_notes",
            type=SearchFieldDataType.String,
            filterable=False,
        ),
    ]

    index = SearchIndex(
        name=INDEX_NAME,
        fields=fields,
        semantic_search=semantic_search
    )

    # Delete existing index if present
    try:
        index_client.delete_index(INDEX_NAME)
        print(f"Deleted existing index: {INDEX_NAME}")
    except Exception:
        pass

    result = index_client.create_index(index)
    print(f"Created index: {result.name}")
    print(f"  - Semantic config: casefile-semantic-config")
    print(f"  - Title field: title")
    print(f"  - Content field: content")
    return result


def load_casefiles() -> list[dict]:
    """Load all casefile KB cards from JSON files."""
    print(f"\nLoading casefiles from: {CASEFILES_PATH}")

    documents = []
    json_files = list(CASEFILES_PATH.glob("*.json"))

    for json_file in json_files:
        with open(json_file, "r", encoding="utf-8") as f:
            doc = json.load(f)

        # Convert arrays to strings for storage
        if isinstance(doc.get("approvals_required"), list):
            doc["approvals_required"] = ", ".join(doc["approvals_required"])
        if isinstance(doc.get("audit_artifacts"), list):
            doc["audit_artifacts"] = ", ".join(doc["audit_artifacts"])
        if isinstance(doc.get("tool_run_ids"), dict):
            doc["tool_run_ids"] = json.dumps(doc["tool_run_ids"])

        documents.append(doc)
        print(f"  Loaded: {doc['incident_id']} ({doc['decision']})")

    print(f"Loaded {len(documents)} casefiles")
    return documents


def upload_documents(search_client: SearchClient, documents: list[dict]):
    """Upload casefile documents to the index."""
    print(f"\nUploading {len(documents)} casefiles to index...")

    result = search_client.upload_documents(documents=documents)

    success = sum(1 for r in result if r.succeeded)
    failed = sum(1 for r in result if not r.succeeded)

    print(f"Upload complete: {success} succeeded, {failed} failed")

    if failed > 0:
        for r in result:
            if not r.succeeded:
                print(f"  Failed: {r.key} - {r.error_message}")

    return success, failed


def test_casefile_queries(search_client: SearchClient):
    """Test casefile retrieval queries."""
    print("\n" + "=" * 70)
    print("CASEFILE RETRIEVAL TESTS")
    print("=" * 70)

    # Test 1: Filter by sanctions decision and liquidity breach
    print("\n--- Test 1: Similar cases (CLEAR + breach) ---")
    results = list(search_client.search(
        search_text="*",
        filter="sanctions_decision eq 'CLEAR' and liquidity_breach eq true",
        select=["incident_id", "title", "decision", "currency", "amount"],
    ))
    for r in results:
        print(f"  {r['incident_id']}: {r['decision']} - {r['currency']} {r['amount']:,.0f}")

    # Test 2: Semantic search for similar incidents
    print("\n--- Test 2: Semantic search (liquidity breach approvals) ---")
    results = list(search_client.search(
        search_text="liquidity breach what approvals were required",
        query_type="semantic",
        semantic_configuration_name="casefile-semantic-config",
        top=3,
        select=["incident_id", "title", "approvals_required"],
    ))
    for r in results:
        print(f"  {r['incident_id']}: {r.get('approvals_required', 'N/A')}")

    # Test 3: Filter by decision type
    print("\n--- Test 3: ESCALATE decisions ---")
    results = list(search_client.search(
        search_text="*",
        filter="sanctions_decision eq 'ESCALATE'",
        select=["incident_id", "title", "decision", "approvals_required"],
    ))
    for r in results:
        print(f"  {r['incident_id']}: {r['decision']}")
        print(f"    Approvals: {r.get('approvals_required', 'N/A')}")

    # Test 4: Full-text search for specific beneficiary
    print("\n--- Test 4: Search for ACME ---")
    results = list(search_client.search(
        search_text="ACME Trading",
        query_type="semantic",
        semantic_configuration_name="casefile-semantic-config",
        top=2,
        select=["incident_id", "title", "content"],
    ))
    for r in results:
        print(f"  {r['incident_id']}: {r['title']}")
        content_snippet = r.get('content', '')[:150] + "..."
        print(f"    {content_snippet}")

    # Test 5: Filter by entity and currency
    print("\n--- Test 5: BankSubsidiary_TR + USD cases ---")
    results = list(search_client.search(
        search_text="*",
        filter="entity eq 'BankSubsidiary_TR' and currency eq 'USD'",
        select=["incident_id", "decision", "sanctions_decision", "liquidity_breach"],
    ))
    for r in results:
        print(f"  {r['incident_id']}: sanctions={r['sanctions_decision']}, breach={r['liquidity_breach']}, decision={r['decision']}")


def main():
    print("=" * 70)
    print("Incident Casefiles Index Creator")
    print("Third index for Foundry IQ - Institutional Memory")
    print("=" * 70)

    # Initialize clients
    index_client, search_client = get_search_clients()
    print(f"Connected to: {os.getenv('AZURE_SEARCH_ENDPOINT')}")

    # Create index
    create_index(index_client)

    # Load casefiles
    documents = load_casefiles()

    # Upload documents
    upload_documents(search_client, documents)

    # Test queries
    test_casefile_queries(search_client)

    print("\n" + "=" * 70)
    print(f"SUCCESS: Index '{INDEX_NAME}' is ready")
    print("Features: Semantic search + structured filters for precedent lookup")
    print("=" * 70)


if __name__ == "__main__":
    main()
