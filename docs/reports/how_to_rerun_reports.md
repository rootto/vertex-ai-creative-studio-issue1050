# How to Rerun Workflow Costing Reports

This guide describes the target infrastructure context of the Creative Studio deployment and details how to execute, configure, and rerun the 60-Day Creator Workflow Session & Unit Costing Analysis reports.

---

## 🎯 Target Architecture & Infrastructure Context

For the costing engine to run successfully against live production data, it connects to the following Google Cloud Platform (GCP) resources:

### 1. Active Deployment Metadata
*   **Google Cloud Project (GCP ID):** `creative-studio-867`
*   **Cloud Run Service Name:** `creative-studio-aaie` (Handles front-end interface, API routing, and Vertex AI orchestration)

### 2. Live Database Storage (Firestore)
*   **Database ID:** `(default)` (The project's primary Google Cloud Firestore instance)
*   **Target Collection:** `genmedia` (Configured dynamically in application state)
*   **Data Models:** 
    *   Generative event logs are written as `MediaItem` dataclasses defined in `common/metadata.py`.
    *   Events are saved to the database via the `add_media_item_to_firestore(item: MediaItem)` utility function.

### 3. Application Configuration Code Map
Database paths, GCP project IDs, and service buckets are loaded dynamically during startup:
*   **Code File:** `config/default.py` -> `Default` class
*   **Key Attributes:**
    *   `PROJECT_ID` (Maps to environment variable `PROJECT_ID` or defaults to active GCP credential project)
    *   `GENMEDIA_FIREBASE_DB` (Maps to environment variable `GENMEDIA_FIREBASE_DB`, defaults to `(default)`)
    *   `GENMEDIA_COLLECTION_NAME` (Maps to environment variable `GENMEDIA_COLLECTION_NAME`, defaults to `"genmedia"`)

---

## 🚀 Running the Costing Script

The core analysis engine is implemented in `tools/analyze_workflow_costing.py`.

### Prerequisites

Ensure you are in the virtual environment or have the required Google Cloud Firestore client libraries installed:

```bash
# Recommended using uv (already configured in the project)
uv run python3 tools/analyze_workflow_costing.py

# Alternatively, using standard pip
pip install google-cloud-firestore pydantic dotenv
python3 tools/analyze_workflow_costing.py
```

### CLI Command Options

The script accepts several flags to customize its execution:

| Flag | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `--days` | `int` | `60` | Number of days of historical history to analyze. |
| `--synthetic` | `bool` | `False` | Forces synthetic generation instead of querying live Firestore. |
| `--report-path` | `str` | `docs/reports/workflow_costing_analysis.md` | Path where the main executive markdown report is written. |
| `--json-path` | `str` | `tools/costing_summary.json` | Path where the structured summary JSON data is written. |

### Example Commands

To run a 30-day analysis using the synthetic database:
```bash
python3 tools/analyze_workflow_costing.py --days 30 --synthetic
```

To output the main report to a custom destination:
```bash
python3 tools/analyze_workflow_costing.py --report-path docs/reports/custom_report.md
```

---

## 📂 Output Locations

When you run the script, it automatically generates:

1. **`tools/costing_summary.json`**: Contains raw structured metrics, rate cards, and archetype stats. Perfect for downstream API intake or BI dashboards.
2. **`docs/reports/workflow_costing_analysis_{days}day_{project_id}.md`**: Exactly one clean, formatted executive markdown report corresponding to the specified day range and the target GCP project name (e.g. `workflow_costing_analysis_120day_creative-studio-867.md`).
