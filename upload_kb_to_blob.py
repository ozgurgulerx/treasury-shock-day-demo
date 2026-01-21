#!/usr/bin/env python3
"""
Upload KB documents to Azure Blob Storage using Entra ID authentication.
"""

from pathlib import Path
from azure.identity import AzureCliCredential
from azure.storage.blob import BlobServiceClient, ContentSettings

# Configuration
STORAGE_ACCOUNT = "sttreasurydemo01"
CONTAINER_NAME = "treasury-demo"
LOCAL_KB_PATH = Path(__file__).parent / "kb" / "v1"
BLOB_PREFIX = "kb/v1"

def upload_kb_to_blob():
    """Upload all KB documents to Azure Blob Storage."""
    print("=" * 60)
    print("KB Documents -> Azure Blob Storage Uploader")
    print("=" * 60)

    # Initialize client with AzureCliCredential (uses az login explicitly)
    account_url = f"https://{STORAGE_ACCOUNT}.blob.core.windows.net"
    credential = AzureCliCredential()
    blob_service_client = BlobServiceClient(account_url, credential=credential)

    print(f"Connected to: {account_url}")
    print(f"Container: {CONTAINER_NAME}")
    print(f"Local path: {LOCAL_KB_PATH}")
    print(f"Blob prefix: {BLOB_PREFIX}")
    print()

    # Get container client
    container_client = blob_service_client.get_container_client(CONTAINER_NAME)

    # Find all markdown files
    md_files = list(LOCAL_KB_PATH.rglob("*.md"))
    print(f"Found {len(md_files)} markdown files to upload")
    print()

    uploaded = 0
    failed = 0

    for md_file in md_files:
        # Calculate blob path
        relative_path = md_file.relative_to(LOCAL_KB_PATH)
        blob_path = f"{BLOB_PREFIX}/{relative_path}"

        try:
            # Read file content
            with open(md_file, "r", encoding="utf-8") as f:
                content = f.read()

            # Upload to blob
            blob_client = container_client.get_blob_client(blob_path)
            blob_client.upload_blob(
                content,
                overwrite=True,
                content_settings=ContentSettings(content_type="text/markdown")
            )

            print(f"✓ Uploaded: {blob_path}")
            uploaded += 1

        except Exception as e:
            print(f"✗ Failed: {blob_path} - {e}")
            failed += 1

    print()
    print("=" * 60)
    print(f"Upload complete: {uploaded} succeeded, {failed} failed")
    print("=" * 60)

    return uploaded, failed


def list_uploaded_files():
    """List all files in the kb/v1 path to verify upload."""
    print("\nVerifying uploaded files...")

    account_url = f"https://{STORAGE_ACCOUNT}.blob.core.windows.net"
    credential = AzureCliCredential()
    blob_service_client = BlobServiceClient(account_url, credential=credential)
    container_client = blob_service_client.get_container_client(CONTAINER_NAME)

    blobs = list(container_client.list_blobs(name_starts_with=BLOB_PREFIX))

    print(f"\nFiles in {CONTAINER_NAME}/{BLOB_PREFIX}/:")
    for blob in blobs:
        print(f"  - {blob.name} ({blob.size} bytes)")

    print(f"\nTotal: {len(blobs)} files")
    return blobs


if __name__ == "__main__":
    upload_kb_to_blob()
    list_uploaded_files()
