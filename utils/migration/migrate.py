# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Command line migration utility for Firestore metadata and GCS files."""

import argparse
import sys
from google.cloud import firestore, storage
from google.oauth2 import service_account

# Global stats counters
STATS = {
    "docs_scanned": 0,
    "docs_migrated": 0,
    "files_copied": 0,
    "files_skipped": 0,
    "errors": 0
}


def get_firestore_client(project_id, database_id, credentials_path=None):
    """Initialize and return a Firestore Client."""
    if credentials_path:
        creds = service_account.Credentials.from_service_account_file(credentials_path)
        return firestore.Client(project=project_id, database=database_id, credentials=creds)
    return firestore.Client(project=project_id, database=database_id)


def get_storage_client(project_id, credentials_path=None):
    """Initialize and return a GCS Storage Client."""
    if credentials_path:
        creds = service_account.Credentials.from_service_account_file(credentials_path)
        return storage.Client(project=project_id, credentials=creds)
    return storage.Client(project=project_id)


def copy_gcs_object(src_client, src_bucket_name, dest_client, dest_bucket_name, relative_path, dry_run=False):
    """Copy blob from source bucket to destination bucket, preserving relative path."""
    try:
        src_bucket = src_client.bucket(src_bucket_name)
        src_blob = src_bucket.blob(relative_path)
        
        dest_bucket = dest_client.bucket(dest_bucket_name)
        dest_blob = dest_bucket.blob(relative_path)

        if not src_blob.exists():
            print(f"  [WARN] Source GCS file does not exist: gs://{src_bucket_name}/{relative_path}")
            STATS["errors"] += 1
            return False

        if dest_blob.exists():
            print(f"  [SKIP] Destination GCS file already exists: gs://{dest_bucket_name}/{relative_path}")
            STATS["files_skipped"] += 1
            return True

        print(f"  [COPY] gs://{src_bucket_name}/{relative_path} -> gs://{dest_bucket_name}/{relative_path}")
        if not dry_run:
            # Download blob contents as bytes and upload directly to dest
            blob_data = src_blob.download_as_bytes()
            dest_blob.upload_from_string(blob_data, content_type=src_blob.content_type)
        
        STATS["files_copied"] += 1
        return True
    except Exception as e:
        print(f"  [ERROR] Failed to copy gs://{src_bucket_name}/{relative_path}: {e}")
        STATS["errors"] += 1
        return False


def process_value(val, source_bucket, dest_bucket, storage_source, storage_dest, dry_run=False):
    """Recursively search for GCS paths matching the source bucket, copy files, and rewrite paths."""
    if isinstance(val, str):
        if val.startswith(f"gs://{source_bucket}/"):
            relative_path = val[len(f"gs://{source_bucket}/"):]
            new_val = f"gs://{dest_bucket}/{relative_path}"
            
            # Copy GCS object
            copy_success = copy_gcs_object(
                storage_source, source_bucket,
                storage_dest, dest_bucket,
                relative_path, dry_run=dry_run
            )
            
            # Only rewrite path if copy succeeded or dry_run/skipped
            if copy_success:
                return new_val
            else:
                return val  # Keep original if copy failed
    elif isinstance(val, list):
        return [
            process_value(item, source_bucket, dest_bucket, storage_source, storage_dest, dry_run)
            for item in val
        ]
    elif isinstance(val, dict):
        return {
            k: process_value(v, source_bucket, dest_bucket, storage_source, storage_dest, dry_run)
            for k, v in val.items()
        }
    return val


def migrate_collection(source_col_ref, dest_col_ref, source_bucket, dest_bucket, storage_source, storage_dest, dry_run=False, force=False):
    """Recursively migrate documents in a collection and all of their sub-collections."""
    print(f"\nMigrating collection: {source_col_ref.path} -> {dest_col_ref.path}")
    docs = list(source_col_ref.stream())
    
    for doc in docs:
        STATS["docs_scanned"] += 1
        print(f"Processing document: {doc.id}")
        
        # Check if doc exists in destination
        dest_doc_ref = dest_col_ref.document(doc.id)
        if dest_doc_ref.get().exists and not force:
            print(f"  [SKIP] Document '{doc.id}' already exists at destination (use --force to overwrite)")
            # Still scan subcollections in case some nested collections or files are missing
        else:
            doc_data = doc.to_dict()
            
            # Recursively scan and rewrite GCS URIs in doc fields
            updated_data = process_value(
                doc_data, source_bucket, dest_bucket,
                storage_source, storage_dest, dry_run=dry_run
            )
            
            if not dry_run:
                dest_doc_ref.set(updated_data)
                print(f"  [WRITE] Saved document: {doc.id}")
            else:
                print(f"  [DRY-RUN] Would save document: {doc.id}")
            
            STATS["docs_migrated"] += 1

        # Check for sub-collections under this document and migrate them
        subcollections = list(doc.reference.collections())
        for sub_col in subcollections:
            dest_sub_col_ref = dest_doc_ref.collection(sub_col.id)
            migrate_collection(
                sub_col, dest_sub_col_ref,
                source_bucket, dest_bucket,
                storage_source, storage_dest,
                dry_run=dry_run, force=force
            )


def main():
    parser = argparse.ArgumentParser(
        description="Migrate Firestore 'genmedia' metadata and GCS files across GCP projects."
    )
    parser.add_argument("--source-project", required=True, help="Source GCP Project ID")
    parser.add_argument("--dest-project", required=True, help="Destination GCP Project ID")
    parser.add_argument("--source-bucket", required=True, help="Source GCS assets bucket name")
    parser.add_argument("--dest-bucket", required=True, help="Destination GCS assets bucket name")
    parser.add_argument("--source-db", default="(default)", help="Source Firestore database name (default: '(default)')")
    parser.add_argument("--dest-db", default="(default)", help="Destination Firestore database name (default: '(default)')")
    parser.add_argument("--source-credentials", help="Path to source service account key JSON file")
    parser.add_argument("--dest-credentials", help="Path to destination service account key JSON file")
    parser.add_argument("--collection", default="genmedia", help="Root collection to migrate (default: 'genmedia')")
    parser.add_argument("--dry-run", action="store_true", help="Log migration actions without modifying files or database")
    parser.add_argument("--force", action="store_true", help="Overwrite existing Firestore documents and force copying GCS assets")

    args = parser.parse_args()

    print("=" * 60)
    print("                GCP PROJECT MIGRATION UTILITY")
    print("=" * 60)
    print(f"Source Project:      {args.source_project} [DB: {args.source_db}]")
    print(f"Destination Project: {args.dest_project} [DB: {args.dest_db}]")
    print(f"Source Bucket:       {args.source_bucket}")
    print(f"Destination Bucket:  {args.dest_bucket}")
    print(f"Root Collection:     {args.collection}")
    print(f"Dry Run Mode:        {args.dry-run}")
    print(f"Force Overwrite:     {args.force}")
    print("=" * 60)

    try:
        # Initialize clients
        print("Initializing database and storage clients...")
        db_source = get_firestore_client(args.source_project, args.source_db, args.source_credentials)
        db_dest = get_firestore_client(args.dest_project, args.dest_db, args.dest_credentials)
        
        storage_source = get_storage_client(args.source_project, args.source_credentials)
        storage_dest = get_storage_client(args.dest_project, args.dest_credentials)
        
        # Verify buckets exist
        if not storage_source.bucket(args.source_bucket).exists():
            print(f"CRITICAL: Source bucket '{args.source_bucket}' does not exist.")
            sys.exit(1)
        if not storage_dest.bucket(args.dest_bucket).exists():
            print(f"CRITICAL: Destination bucket '{args.dest_bucket}' does not exist.")
            sys.exit(1)

        # Get root collection references
        source_root_col = db_source.collection(args.collection)
        dest_root_col = db_dest.collection(args.collection)

        # Start recursive migration
        migrate_collection(
            source_root_col, dest_root_col,
            args.source_bucket, args.dest_bucket,
            storage_source, storage_dest,
            dry_run=args.dry_run, force=args.force
        )

        print("\n" + "=" * 60)
        print("                      MIGRATION SUMMARY")
        print("=" * 60)
        print(f"Documents Scanned:       {STATS['docs_scanned']}")
        print(f"Documents Migrated:      {STATS['docs_migrated']}")
        print(f"Files Copied (GCS):      {STATS['files_copied']}")
        print(f"Files Skipped (Exists):  {STATS['files_skipped']}")
        print(f"Errors Encountered:      {STATS['errors']}")
        print("=" * 60)
        print("Migration process finished successfully.")

    except Exception as e:
        print(f"\n[CRITICAL ERROR] Migration failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
