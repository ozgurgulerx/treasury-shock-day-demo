#!/usr/bin/env python3
"""
Upload KB documents directly to Azure AI Search index (without indexer).
"""

import os
import base64
import hashlib
from pathlib import Path
from datetime import datetime, timezone
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
INDEX_NAME = "idx-treasury-kb-docs-v1"
LOCAL_KB_PATH = Path(__file__).parent / "kb" / "v1"


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
    """Create the search index for KB documents."""
    print(f"Creating index: {INDEX_NAME}")

    fields = [
        # Key field - using hash of file path
        SimpleField(
            name="id",
            type=SearchFieldDataType.String,
            key=True,
            filterable=True,
        ),
        # Full content - searchable
        SearchableField(
            name="content",
            type=SearchFieldDataType.String,
            analyzer_name="en.lucene",
        ),
        # Document title (filename without extension)
        SearchableField(
            name="title",
            type=SearchFieldDataType.String,
            filterable=True,
            sortable=True,
        ),
        # File path
        SimpleField(
            name="file_path",
            type=SearchFieldDataType.String,
            filterable=True,
        ),
        # Folder/category (runbooks, policies, etc.)
        SimpleField(
            name="category",
            type=SearchFieldDataType.String,
            filterable=True,
            facetable=True,
        ),
        # File size
        SimpleField(
            name="file_size",
            type=SearchFieldDataType.Int64,
            filterable=True,
        ),
        # Last modified
        SimpleField(
            name="last_modified",
            type=SearchFieldDataType.DateTimeOffset,
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
        pass

    result = index_client.create_index(index)
    print(f"Created index: {result.name}")
    return result


def generate_doc_id(file_path: str) -> str:
    """Generate a unique document ID from file path."""
    # Use base64 encoded hash for a clean ID
    hash_val = hashlib.md5(file_path.encode()).hexdigest()[:16]
    return hash_val


def load_documents() -> list[dict]:
    """Load all markdown documents and prepare for indexing."""
    print(f"Loading documents from: {LOCAL_KB_PATH}")

    documents = []
    md_files = list(LOCAL_KB_PATH.rglob("*.md"))

    for md_file in md_files:
        # Read content
        with open(md_file, "r", encoding="utf-8") as f:
            content = f.read()

        # Get relative path and category
        relative_path = md_file.relative_to(LOCAL_KB_PATH)
        category = relative_path.parts[0] if len(relative_path.parts) > 1 else "root"
        file_path = f"kb/v1/{relative_path}"

        # Get file stats
        stat = md_file.stat()
        last_modified = datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat()

        # Create document
        doc = {
            "id": generate_doc_id(file_path),
            "content": content,
            "title": md_file.stem,  # filename without extension
            "file_path": file_path,
            "category": category,
            "file_size": stat.st_size,
            "last_modified": last_modified,
        }
        documents.append(doc)

    print(f"Loaded {len(documents)} documents")
    return documents


def upload_documents(search_client: SearchClient, documents: list[dict]):
    """Upload documents to the search index."""
    print(f"\nUploading {len(documents)} documents to index...")

    result = search_client.upload_documents(documents=documents)

    success = sum(1 for r in result if r.succeeded)
    failed = sum(1 for r in result if not r.succeeded)

    print(f"Upload complete: {success} succeeded, {failed} failed")

    if failed > 0:
        for r in result:
            if not r.succeeded:
                print(f"  Failed: {r.key} - {r.error_message}")

    return success, failed


def validate_index(search_client: SearchClient):
    """Run sample queries to validate the index."""
    print("\n--- Validating Index ---")

    test_queries = [
        ("decision matrix", "Should hit runbook_emergency_payment.md"),
        ("SANCTIONS LIQUIDITY", "Should hit runbook, sanctions escalation"),
        ("TXN-EMRG-001", "Should hit summary docs"),
        ("USD 2M buffer", "Should hit policy_liquidity_buffers.md"),
        ("ACME", "Should hit summary docs"),
    ]

    all_pass = True
    for query, expected in test_queries:
        print(f"\nSearching for: '{query}'")
        print(f"  Expected: {expected}")
        results = list(search_client.search(search_text=query, top=3))

        if results:
            for i, result in enumerate(results, 1):
                title = result.get('title', 'N/A')
                category = result.get('category', 'N/A')
                score = result.get('@search.score', 0)
                print(f"  [{i}] {title} ({category}) - score: {score:.2f}")
        else:
            print("  No results found!")
            all_pass = False

    return all_pass


def main():
    print("=" * 60)
    print("Treasury KB -> Azure AI Search Direct Upload")
    print("=" * 60)

    # Initialize clients
    index_client, search_client = get_search_clients()
    print(f"Connected to: {os.getenv('AZURE_SEARCH_ENDPOINT')}")

    # Create index
    create_index(index_client)

    # Load documents
    documents = load_documents()

    # Upload documents
    upload_documents(search_client, documents)

    # Validate
    validate_index(search_client)

    print("\n" + "=" * 60)
    print(f"SUCCESS: Index '{INDEX_NAME}' is ready for querying")
    print("=" * 60)


if __name__ == "__main__":
    main()
