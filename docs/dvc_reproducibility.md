# DVC Data Versioning & Reproducibility Workflow

This document describes how **DVC (Data Version Control)** is integrated into SentinelML for versioning raw, processed, and baseline reference datasets, guaranteeing 100% end-to-end model reproducibility without introducing AWS S3 dependencies.

---

## 1. DVC Architecture & Storage Policy

- **No AWS S3 Dependency**: DVC is configured using local filesystem cache storage for development (`.dvc/cache`). If remote storage is added later, the storage provider remains fully configurable via environment variables without hardcoding cloud vendor dependencies.
- **Tracked Datasets**:
  - `data/raw.csv.dvc` — Raw incoming inference batch data
  - `data/processed.csv.dvc` — Preprocessed feature matrix used for model training
  - `data/reference.csv.dvc` — Baseline reference distribution dataset used for statistical drift tests (KS & PSI)

---

## 2. Lineage Traceability Matrix

Every `ModelVersion` in SentinelML is explicitly linked to its underlying dataset and code artifacts through `dvc_lineage.py`.

```
[ ModelVersion: v18 ]
       │
       ├──► TrainingRun ID: run-cc4a64a5
       │
       ├──► Dataset Version: ds_v1.4  ◄──► (data/processed.csv.dvc - md5: fee47667)
       │
       └──► Feature Preprocessor: preprocessor_v2.1
```

### Lineage JSON Schema (`data/lineage/v18_lineage.json`)

```json
{
  "model_version": "v18",
  "training_run_id": "run-cc4a64a5",
  "dataset_version": "ds_v1.4",
  "feature_preprocessor_version": "preprocessor_v2.1",
  "timestamp": "2026-08-15T12:30:00Z",
  "reproducibility": {
    "dvc_raw": "data/raw.csv.dvc",
    "dvc_processed": "data/processed.csv.dvc",
    "dvc_reference": "data/reference.csv.dvc"
  }
}
```

---

## 3. End-to-End Reproducibility Commands

To reproduce a historical training run or check out a specific dataset version:

### A. Initialize DVC (Local Cache Mode)
```bash
# Initialize DVC repository locally
dvc init --no-exec

# Configure local DVC storage directory
dvc remote add -d localstorage .dvc/local_cache
```

### B. Track Datasets with DVC
```bash
# Track raw, processed, and reference datasets
dvc add data/raw.csv
dvc add data/processed.csv
dvc add data/reference.csv

# Commit DVC pointer files to Git
git add data/raw.csv.dvc data/processed.csv.dvc data/reference.csv.dvc data/.gitignore
git commit -m "dvc: version dataset snapshot ds_v1.4"
```

### C. Reproduce Historical Run
```bash
# 1. Checkout Git commit for target model version
git checkout v18-tag

# 2. Pull exact dataset files matching the commit
dvc checkout

# 3. Execute retraining flow pipeline using exact dataset snapshot
python -m pipelines.retraining_flow --dataset-version ds_v1.4
```
