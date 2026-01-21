#!/usr/bin/env python3
"""
Create Azure AI Search index for KB documents with blob indexer.
"""

import os
import time
from dotenv import load_dotenv
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from azure.search.documents.indexes import SearchIndexClient, SearchIndexerClient
from azure.search.documents.indexes.models import (
    SearchIndex,
    SimpleField,
    SearchableField,
    SearchFieldDataType,
    SearchIndexer,
    SearchIndexerDataContainer,
    SearchIndexerDataSourceConnection,
    FieldMapping,
    IndexingParameters,
    IndexingParametersConfiguration,
    BlobIndexerParsingMode,
)

# Load environment variables
load_dotenv()

# Configuration
INDEX_NAME = "idx-treasury-kb-docs-v1"
DATA_SOURCE_NAME = "treasury-kb-blob-datasource"
INDEXER_NAME = "treasury-kb-blob-indexer"
STORAGE_ACCOUNT = "sttreasurydemo01"
CONTAINER_NAME = "treasury-demo"
BLOB_FOLDER = "kb/v1"


def get_storage_connection_string():
    """Get storage account connection string via Azure CLI."""
    import subprocess
    result = subprocess.run(
        ["az", "storage", "account", "show-connection-string",
         "--name", STORAGE_ACCOUNT, "-o", "tsv"],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        raise ValueError(f"Failed to get storage connection string: {result.stderr}")
    return result.stdout.strip()


def get_search_clients():
    """Initialize Azure Search clients."""
    endpoint = os.getenv("AZURE_SEARCH_ENDPOINT")
    api_key = os.getenv("AZURE_SEARCH_ADMIN_KEY")

    if not endpoint or not api_key:
        raise ValueError("Missing AZURE_SEARCH_ENDPOINT or AZURE_SEARCH_ADMIN_KEY in .env")

    credential = AzureKeyCredential(api_key)
    index_client = SearchIndexClient(endpoint=endpoint, credential=credential)
    indexer_client = SearchIndexerClient(endpoint=endpoint, credential=credential)
    search_client = SearchClient(endpoint=endpoint, index_name=INDEX_NAME, credential=credential)

    return index_client, indexer_client, search_client


def create_data_source(indexer_client: SearchIndexerClient, connection_string: str):
    """Create the blob data source connection."""
    print(f"Creating data source: {DATA_SOURCE_NAME}")

    container = SearchIndexerDataContainer(
        name=CONTAINER_NAME,
        query=BLOB_FOLDER  # Only index files under kb/v1/
    )

    data_source = SearchIndexerDataSourceConnection(
        name=DATA_SOURCE_NAME,
        type="azureblob",
        connection_string=connection_string,
        container=container
    )

    # Delete existing if present
    try:
        indexer_client.delete_data_source_connection(DATA_SOURCE_NAME)
        print(f"Deleted existing data source: {DATA_SOURCE_NAME}")
    except Exception:
        pass

    result = indexer_client.create_data_source_connection(data_source)
    print(f"Created data source: {result.name}")
    return result


def create_index(index_client: SearchIndexClient):
    """Create the search index for KB documents."""
    print(f"Creating index: {INDEX_NAME}")

    fields = [
        # Key field - using encoded blob path
        SimpleField(
            name="id",
            type=SearchFieldDataType.String,
            key=True,
            filterable=True,
        ),
        # Content from markdown
        SearchableField(
            name="content",
            type=SearchFieldDataType.String,
            analyzer_name="en.lucene",
        ),
        # Metadata fields
        SearchableField(
            name="metadata_storage_name",
            type=SearchFieldDataType.String,
            filterable=True,
            sortable=True,
        ),
        SimpleField(
            name="metadata_storage_path",
            type=SearchFieldDataType.String,
            filterable=True,
        ),
        SimpleField(
            name="metadata_storage_last_modified",
            type=SearchFieldDataType.DateTimeOffset,
            filterable=True,
            sortable=True,
        ),
        SimpleField(
            name="metadata_storage_size",
            type=SearchFieldDataType.Int64,
            filterable=True,
        ),
        SimpleField(
            name="metadata_content_type",
            type=SearchFieldDataType.String,
            filterable=True,
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


def create_indexer(indexer_client: SearchIndexerClient):
    """Create the blob indexer with text parsing (markdown-friendly)."""
    print(f"Creating indexer: {INDEXER_NAME}")

    # Field mappings
    field_mappings = [
        FieldMapping(source_field_name="metadata_storage_path", target_field_name="id"),
        FieldMapping(source_field_name="metadata_storage_name", target_field_name="metadata_storage_name"),
        FieldMapping(source_field_name="metadata_storage_path", target_field_name="metadata_storage_path"),
        FieldMapping(source_field_name="metadata_storage_last_modified", target_field_name="metadata_storage_last_modified"),
        FieldMapping(source_field_name="metadata_storage_size", target_field_name="metadata_storage_size"),
        FieldMapping(source_field_name="metadata_content_type", target_field_name="metadata_content_type"),
    ]

    # Indexing parameters - use text parsing for markdown
    parameters = IndexingParameters(
        configuration={
            "parsingMode": "text",
            "dataToExtract": "contentAndMetadata",
        }
    )

    indexer = SearchIndexer(
        name=INDEXER_NAME,
        data_source_name=DATA_SOURCE_NAME,
        target_index_name=INDEX_NAME,
        field_mappings=field_mappings,
        parameters=parameters,
    )

    # Delete existing indexer if present
    try:
        indexer_client.delete_indexer(INDEXER_NAME)
        print(f"Deleted existing indexer: {INDEXER_NAME}")
    except Exception:
        pass

    result = indexer_client.create_indexer(indexer)
    print(f"Created indexer: {result.name}")
    return result


def run_indexer(indexer_client: SearchIndexerClient):
    """Run the indexer and wait for completion."""
    print(f"\nRunning indexer: {INDEXER_NAME}")
    indexer_client.run_indexer(INDEXER_NAME)

    # Wait for indexer to complete
    for i in range(30):  # Max 30 attempts (5 minutes)
        time.sleep(10)
        status = indexer_client.get_indexer_status(INDEXER_NAME)
        last_result = status.last_result

        if last_result:
            print(f"  Status: {last_result.status}, Items: {last_result.items_processed}/{last_result.items_failed + last_result.items_processed}")

            if last_result.status in ["success", "transientFailure"]:
                print(f"\nIndexer completed: {last_result.items_processed} items processed, {last_result.items_failed} failed")
                return last_result
            elif last_result.status == "inProgress":
                continue
            else:
                print(f"Indexer failed: {last_result.errors}")
                return last_result
        else:
            print("  Waiting for indexer to start...")

    print("Timeout waiting for indexer")
    return None


def validate_index(search_client: SearchClient):
    """Run sample queries to validate the index."""
    print("\n--- Validating Index ---")

    test_queries = [
        "decision matrix",
        "SANCTIONS LIQUIDITY",
        "TXN-EMRG-001",
        "USD buffer",
        "ACME",
    ]

    for query in test_queries:
        print(f"\nSearching for: '{query}'")
        results = search_client.search(search_text=query, top=3)

        count = 0
        for result in results:
            count += 1
            name = result.get('metadata_storage_name', 'N/A')
            score = result.get('@search.score', 0)
            print(f"  [{count}] {name} (score: {score:.2f})")

        if count == 0:
            print("  No results found")


def main():
    print("=" * 60)
    print("Treasury KB -> Azure AI Search Index Creator")
    print("=" * 60)

    # Get storage connection string
    print("\nGetting storage connection string...")
    connection_string = get_storage_connection_string()
    print("Got storage connection string")

    # Initialize clients
    index_client, indexer_client, search_client = get_search_clients()
    print(f"Connected to: {os.getenv('AZURE_SEARCH_ENDPOINT')}")

    # Create data source
    create_data_source(indexer_client, connection_string)

    # Create index
    create_index(index_client)

    # Create indexer
    create_indexer(indexer_client)

    # Run indexer
    run_indexer(indexer_client)

    # Validate
    validate_index(search_client)

    print("\n" + "=" * 60)
    print(f"SUCCESS: Index '{INDEX_NAME}' is ready for querying")
    print("=" * 60)


if __name__ == "__main__":
    main()
