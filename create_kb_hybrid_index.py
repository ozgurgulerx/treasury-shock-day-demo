#!/usr/bin/env python3
"""
Create Azure AI Search hybrid index (keyword + vector) for KB documents.
Uses Azure OpenAI text-embedding-3-small for embeddings.
"""

import os
import hashlib
from pathlib import Path
from datetime import datetime, timezone
from dotenv import load_dotenv
import requests
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (
    SearchIndex,
    SimpleField,
    SearchableField,
    SearchFieldDataType,
    SearchField,
    VectorSearch,
    HnswAlgorithmConfiguration,
    VectorSearchProfile,
    SemanticConfiguration,
    SemanticField,
    SemanticPrioritizedFields,
    SemanticSearch,
)
from azure.search.documents.models import VectorizedQuery

# Load environment variables
load_dotenv()

# Configuration
INDEX_NAME = "idx-treasury-kb-docs-v2"
LOCAL_KB_PATH = Path(__file__).parent / "kb" / "v1"
EMBEDDING_DIMENSIONS = 1536  # text-embedding-3-small dimensions


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


def get_embedding(text: str) -> list[float]:
    """Get embedding vector from Azure OpenAI."""
    endpoint = os.getenv("AZURE_OPENAI_ENDPOINT").rstrip("/")
    api_key = os.getenv("AZURE_OPENAI_API_KEY")
    deployment = os.getenv("AZURE_TEXT_EMBEDDING_DEPLOYMENT_NAME", "text-embedding-3-small")

    # Truncate text if too long (max ~8000 tokens for embedding model)
    max_chars = 30000  # Rough estimate for token limit
    if len(text) > max_chars:
        text = text[:max_chars]

    url = f"{endpoint}/openai/deployments/{deployment}/embeddings?api-version=2024-02-01"
    headers = {
        "Content-Type": "application/json",
        "api-key": api_key
    }
    payload = {
        "input": text
    }

    response = requests.post(url, headers=headers, json=payload)
    response.raise_for_status()

    data = response.json()
    return data["data"][0]["embedding"]


def create_hybrid_index(index_client: SearchIndexClient):
    """Create the search index with vector search capabilities."""
    print(f"Creating hybrid index: {INDEX_NAME}")

    # Define vector search configuration
    vector_search = VectorSearch(
        algorithms=[
            HnswAlgorithmConfiguration(
                name="hnsw-config",
                parameters={
                    "m": 4,
                    "efConstruction": 400,
                    "efSearch": 500,
                    "metric": "cosine"
                }
            )
        ],
        profiles=[
            VectorSearchProfile(
                name="vector-profile",
                algorithm_configuration_name="hnsw-config",
            )
        ]
    )

    # Define semantic search configuration
    semantic_config = SemanticConfiguration(
        name="semantic-config",
        prioritized_fields=SemanticPrioritizedFields(
            title_field=SemanticField(field_name="title"),
            content_fields=[SemanticField(field_name="content")],
            keywords_fields=[SemanticField(field_name="category")]
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
        # Full content - searchable (keyword)
        SearchableField(
            name="content",
            type=SearchFieldDataType.String,
            analyzer_name="en.lucene",
        ),
        # Vector field for embeddings
        SearchField(
            name="contentVector",
            type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
            searchable=True,
            vector_search_dimensions=EMBEDDING_DIMENSIONS,
            vector_search_profile_name="vector-profile",
        ),
        # Document title
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
        # Category (runbooks, policies, etc.)
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

    index = SearchIndex(
        name=INDEX_NAME,
        fields=fields,
        vector_search=vector_search,
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
    print(f"  - Vector search: HNSW algorithm, cosine similarity")
    print(f"  - Semantic search: enabled with title/content/category")
    return result


def generate_doc_id(file_path: str) -> str:
    """Generate a unique document ID from file path."""
    hash_val = hashlib.md5(file_path.encode()).hexdigest()[:16]
    return hash_val


def load_and_embed_documents() -> list[dict]:
    """Load all markdown documents, generate embeddings, and prepare for indexing."""
    print(f"\nLoading documents from: {LOCAL_KB_PATH}")

    documents = []
    md_files = list(LOCAL_KB_PATH.rglob("*.md"))
    total = len(md_files)

    print(f"Found {total} markdown files")
    print("Generating embeddings (this may take a moment)...\n")

    for i, md_file in enumerate(md_files, 1):
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

        # Generate embedding
        print(f"  [{i}/{total}] Embedding: {md_file.name}...", end=" ")
        try:
            embedding = get_embedding(content)
            print(f"✓ ({len(embedding)} dims)")
        except Exception as e:
            print(f"✗ Error: {e}")
            embedding = [0.0] * EMBEDDING_DIMENSIONS  # Fallback

        # Create document
        doc = {
            "id": generate_doc_id(file_path),
            "content": content,
            "contentVector": embedding,
            "title": md_file.stem,
            "file_path": file_path,
            "category": category,
            "file_size": stat.st_size,
            "last_modified": last_modified,
        }
        documents.append(doc)

    print(f"\nLoaded and embedded {len(documents)} documents")
    return documents


def upload_documents(search_client: SearchClient, documents: list[dict]):
    """Upload documents with vectors to the search index."""
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


def test_hybrid_search(search_client: SearchClient):
    """Test hybrid search (keyword + vector + semantic)."""
    print("\n" + "=" * 70)
    print("HYBRID SEARCH TESTS")
    print("=" * 70)

    test_queries = [
        "What are the steps when sanctions CLEAR but liquidity breaches?",
        "Who approves emergency payments over 1 million dollars?",
        "What documentation is needed for a HOLD decision?",
        "Tell me about the ACME Trading payment",
        "What is the USD buffer threshold for the Turkish subsidiary?",
    ]

    for query in test_queries:
        print(f"\n🔍 Query: \"{query}\"")

        # Generate query embedding
        query_embedding = get_embedding(query)

        # Hybrid search: keyword + vector
        vector_query = VectorizedQuery(
            vector=query_embedding,
            k_nearest_neighbors=3,
            fields="contentVector"
        )

        results = list(search_client.search(
            search_text=query,  # Keyword search
            vector_queries=[vector_query],  # Vector search
            query_type="semantic",  # Enable semantic ranking
            semantic_configuration_name="semantic-config",
            top=3,
            select=["title", "category", "file_path"]
        ))

        if results:
            print("   Results (hybrid: keyword + vector + semantic):")
            for i, r in enumerate(results, 1):
                title = r.get("title", "N/A")
                category = r.get("category", "N/A")
                score = r.get("@search.score", 0)
                reranker_score = r.get("@search.reranker_score", None)
                score_str = f"score: {score:.2f}"
                if reranker_score:
                    score_str += f", reranker: {reranker_score:.2f}"
                print(f"     [{i}] {title} ({category}) - {score_str}")
        else:
            print("   No results")


def compare_search_methods(search_client: SearchClient):
    """Compare keyword-only vs hybrid search."""
    print("\n" + "=" * 70)
    print("COMPARISON: KEYWORD vs HYBRID SEARCH")
    print("=" * 70)

    query = "procedure for handling payment when we have enough money but sanctions flagged"
    print(f"\nQuery: \"{query}\"\n")

    # Keyword-only search
    print("KEYWORD ONLY:")
    kw_results = list(search_client.search(
        search_text=query,
        top=3,
        select=["title", "category"]
    ))
    for i, r in enumerate(kw_results, 1):
        print(f"  [{i}] {r['title']} ({r['category']}) - score: {r['@search.score']:.2f}")

    # Hybrid search
    print("\nHYBRID (keyword + vector + semantic):")
    query_embedding = get_embedding(query)
    vector_query = VectorizedQuery(
        vector=query_embedding,
        k_nearest_neighbors=3,
        fields="contentVector"
    )
    hybrid_results = list(search_client.search(
        search_text=query,
        vector_queries=[vector_query],
        query_type="semantic",
        semantic_configuration_name="semantic-config",
        top=3,
        select=["title", "category"]
    ))
    for i, r in enumerate(hybrid_results, 1):
        score = r.get("@search.score", 0)
        reranker = r.get("@search.reranker_score", "N/A")
        print(f"  [{i}] {r['title']} ({r['category']}) - score: {score:.2f}, reranker: {reranker}")


def main():
    print("=" * 70)
    print("Treasury KB HYBRID Index Creator (v2)")
    print("Keyword + Vector + Semantic Search")
    print("=" * 70)

    # Initialize clients
    index_client, search_client = get_search_clients()
    print(f"Connected to: {os.getenv('AZURE_SEARCH_ENDPOINT')}")

    # Create hybrid index
    create_hybrid_index(index_client)

    # Load documents and generate embeddings
    documents = load_and_embed_documents()

    # Upload documents
    upload_documents(search_client, documents)

    # Test hybrid search
    test_hybrid_search(search_client)

    # Compare search methods
    compare_search_methods(search_client)

    print("\n" + "=" * 70)
    print(f"SUCCESS: Hybrid index '{INDEX_NAME}' is ready")
    print("Features: Keyword search + Vector search + Semantic ranking")
    print("=" * 70)


if __name__ == "__main__":
    main()
