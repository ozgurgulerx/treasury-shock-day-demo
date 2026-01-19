#!/usr/bin/env python3
"""
Upload SDN Enhanced records to Azure AI Search index.

This script:
1. Creates the index with appropriate field schema
2. Uploads all records from sdn_enhanced_records.json
3. Validates the upload by running sample queries
"""

import json
import os
from dotenv import load_dotenv
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (
    SearchIndex,
    SimpleField,
    SearchableField,
    SearchFieldDataType,
)

# Load environment variables
load_dotenv()

# Configuration
INDEX_NAME = "idx-ofac-sdn-v1"
JSON_FILE = "sdn_enhanced_records.json"

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
    """Create the SDN index with appropriate schema."""
    print(f"Creating index: {INDEX_NAME}")

    fields = [
        # Key field
        SimpleField(
            name="uid",
            type=SearchFieldDataType.String,
            key=True,
            filterable=True,
        ),
        # Primary name - searchable
        SearchableField(
            name="primary_name",
            type=SearchFieldDataType.String,
            analyzer_name="en.lucene",
        ),
        # AKA names - collection of strings, searchable
        SearchableField(
            name="aka_names",
            collection=True,
        ),
        # Programs - collection of strings, filterable and searchable
        SearchableField(
            name="programs",
            collection=True,
            filterable=True,
        ),
        # Entity type - filterable
        SimpleField(
            name="entity_type",
            type=SearchFieldDataType.String,
            filterable=True,
        ),
        # Remarks - searchable
        SearchableField(
            name="remarks",
            type=SearchFieldDataType.String,
            analyzer_name="en.lucene",
        ),
        # Source list - filterable
        SimpleField(
            name="source_list",
            type=SearchFieldDataType.String,
            filterable=True,
        ),
        # Snapshot date - filterable and sortable
        SimpleField(
            name="snapshot_date",
            type=SearchFieldDataType.String,
            filterable=True,
            sortable=True,
        ),
    ]

    index = SearchIndex(name=INDEX_NAME, fields=fields)

    # Delete existing index if present
    try:
        index_client.delete_index(INDEX_NAME)
        print(f"Deleted existing index: {INDEX_NAME}")
    except Exception:
        pass  # Index doesn't exist

    result = index_client.create_index(index)
    print(f"Created index: {result.name}")
    return result


def load_records(json_file: str) -> list[dict]:
    """Load records from JSON file."""
    print(f"Loading records from: {json_file}")
    with open(json_file, "r", encoding="utf-8") as f:
        records = json.load(f)
    print(f"Loaded {len(records)} records")
    return records


def upload_records(search_client: SearchClient, records: list[dict], batch_size: int = 1000):
    """Upload records to Azure Search in batches."""
    total = len(records)
    uploaded = 0

    for i in range(0, total, batch_size):
        batch = records[i:i + batch_size]
        result = search_client.upload_documents(documents=batch)

        # Count successful uploads
        success = sum(1 for r in result if r.succeeded)
        uploaded += success

        print(f"Uploaded batch {i // batch_size + 1}: {success}/{len(batch)} successful (total: {uploaded}/{total})")

    print(f"\nUpload complete: {uploaded}/{total} records")
    return uploaded


def validate_index(search_client: SearchClient):
    """Run sample queries to validate the index."""
    print("\n--- Validating Index ---")

    test_queries = [
        "BANK MASKAN",
        "AEROCARIBBEAN",
        "TANCHON",
    ]

    for query in test_queries:
        print(f"\nSearching for: '{query}'")
        results = search_client.search(search_text=query, top=3)

        count = 0
        for result in results:
            count += 1
            print(f"  [{count}] {result['primary_name']}")
            print(f"      UID: {result['uid']}, Type: {result['entity_type']}")
            print(f"      Programs: {result['programs']}")
            if result.get('aka_names'):
                print(f"      AKA: {result['aka_names'][:3]}...")

        if count == 0:
            print("  No results found")


def main():
    print("=" * 60)
    print("OFAC SDN Enhanced -> Azure AI Search Uploader")
    print("=" * 60)

    # Initialize clients
    index_client, search_client = get_search_clients()
    print(f"Connected to: {os.getenv('AZURE_SEARCH_ENDPOINT')}")

    # Create index
    create_index(index_client)

    # Load and upload records
    records = load_records(JSON_FILE)
    upload_records(search_client, records)

    # Validate
    validate_index(search_client)

    print("\n" + "=" * 60)
    print(f"SUCCESS: Index '{INDEX_NAME}' is ready for querying")
    print("=" * 60)


if __name__ == "__main__":
    main()
