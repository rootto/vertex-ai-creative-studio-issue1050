# Firestore & GCS Migration Utility

This command-line utility migrates `genmedia` metadata documents and corresponding GCS assets from a source GCP project/bucket to a destination GCP project/bucket, dynamically updating references during the copy.

---

## Prerequisites

The migration script includes PEP 723 inline script metadata for its dependencies. If you have `uv` installed, you can run the script directly. It will automatically download the required libraries into an ephemeral, self-contained environment:

```bash
uv run utils/migration/migrate.py [args]
```

No manual installation of `google-cloud-firestore`, `google-cloud-storage`, or `google-auth` is necessary.

---

## Authentication Setup

The migration utility needs authentication to read from the source project and write to the destination project. You can authenticate in one of two ways:

### Method A: Application Default Credentials (ADC) — Recommended
If you are logged into an identity that has access to **both** the source and destination projects, you can use your local ADC.

1. Authenticate with your Google account:
   ```bash
   gcloud auth application-default login
   ```
2. Run the script directly without specifying credentials parameters. The script will automatically inherit your user credentials.

---

### Method B: Service Account JSON Keys
If you are migrating across different organizations, or your user account doesn't have cross-project permissions:

1. In the **Source Project**, create a Service Account, grant it the `Storage Object Viewer` and `Cloud Datastore Viewer` (or `Firestore Viewer`) roles, and download its JSON key file.
2. In the **Destination Project**, create a Service Account, grant it the `Storage Object Creator` and `Cloud Datastore User` (or `Firestore User`) roles, and download its JSON key file.
3. Pass the paths to these key files using the `--source-credentials` and `--dest-credentials` flags:
   ```bash
   uv run utils/migration/migrate.py \
     --source-project "source-project-id" \
     --dest-project "dest-project-id" \
     --source-bucket "source-bucket-name" \
     --dest-bucket "dest-bucket-name" \
     --source-credentials "/path/to/source-sa.json" \
     --dest-credentials "/path/to/dest-sa.json"
   ```

---

## Command Line Arguments

| Argument | Required | Default | Description |
| :--- | :--- | :--- | :--- |
| `--source-project` | Yes | - | Source Google Cloud Project ID. |
| `--dest-project` | Yes | - | Destination Google Cloud Project ID. |
| `--source-bucket` | Yes | - | Source GCS assets bucket name. |
| `--dest-bucket` | Yes | - | Destination GCS assets bucket name. |
| `--source-db` | No | `(default)` | Source Firestore database name. |
| `--dest-db` | No | `(default)` | Destination Firestore database name. |
| `--source-credentials` | No | - | Path to the source Service Account key JSON file. |
| `--dest-credentials` | No | - | Path to the destination Service Account key JSON file. |
| `--collection` | No | `genmedia` | The root collection ID to migrate (e.g. `genmedia`). |
| `--dry-run` | No | `False` | Run the script in dry-run mode (scans and prints changes without writing to destination). |
| `--force` | No | `False` | Overwrite existing Firestore documents and force copying GCS assets. |

---

## Examples

### 1. Preview Migration (Dry Run)
It is highly recommended to run a dry-run first to verify credentials, GCS bucket names, and see a preview of what files/records will be migrated:

```bash
uv run utils/migration/migrate.py \
  --source-project "vertex-creative-official" \
  --source-db "create-studio-asset-metadata" \
  --source-bucket "creative-studio-vertex-creative-official-assets" \
  --dest-project "release-candidate-495709" \
  --dest-bucket "release-candidate-495709-assets" \
  --dry-run
```

### 2. Execute Migration (ADC Authentication)
Once verified, run the actual migration:

```bash
uv run utils/migration/migrate.py \
  --source-project "vertex-creative-official" \
  --source-db "create-studio-asset-metadata" \
  --source-bucket "creative-studio-vertex-creative-official-assets" \
  --dest-project "release-candidate-495709" \
  --dest-bucket "release-candidate-495709-assets"
```

### 3. Force Overwrite / Resume Interrupted Migration
If a migration was interrupted, you can run it again. By default, the tool skips already migrated files/documents. If you want to force re-copying everything, use `--force`:

```bash
uv run utils/migration/migrate.py \
  --source-project "vertex-creative-official" \
  --source-db "create-studio-asset-metadata" \
  --source-bucket "creative-studio-vertex-creative-official-assets" \
  --dest-project "release-candidate-495709" \
  --dest-bucket "release-candidate-495709-assets" \
  --force
```
