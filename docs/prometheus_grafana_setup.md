# Prometheus & Grafana Setup Guide (Standalone / Non-Docker)

This guide documents how to configure **Prometheus** and **Grafana** to scrape and visualize real-time telemetry metrics from SentinelML without requiring Docker.

> [!NOTE]
> The custom **SentinelML Next.js Dashboard** (`http://localhost:3000`) remains the **primary product interface** for model reliability, drift alerts, and automated self-healing control. Grafana serves as an optional infrastructure monitoring tool.

---

## 1. Exposed Prometheus Metrics (`/metrics`)

SentinelML exposes a standard Prometheus scraping endpoint at `http://localhost:8000/metrics`.

### Core Metrics Summary

| Metric Name | Type | Labels | Description |
| :--- | :--- | :--- | :--- |
| `http_requests_total` | Counter | `method`, `endpoint`, `status_code` | Total HTTP requests handled |
| `http_errors_total` | Counter | `method`, `endpoint`, `status_code` | Total 4xx & 5xx HTTP error count |
| `http_request_duration_seconds` | Histogram | `method`, `endpoint` | HTTP request processing latency |
| `model_predictions_total` | Counter | `model_name`, `model_version` | Model inference prediction volume |
| `model_prediction_latency_seconds` | Histogram | `model_name`, `model_version` | Model inference latency buckets |
| `drift_detections_total` | Counter | `model_name`, `severity` | Statistical feature/concept drift events |
| `incidents_created_total` | Counter | `severity`, `incident_type` | Operational incidents and RCA alerts created |
| `retraining_runs_total` | Counter | `model_name`, `trigger` | Automated retraining runs triggered |
| `training_failures_total` | Counter | `model_name`, `stage` | Retraining pipeline stage failures |
| `model_promotions_total` | Counter | `model_name`, `target_environment` | Model version promotions |
| `model_rollbacks_total` | Counter | `model_name`, `reason_category` | Automated SLA circuit breaker rollbacks |

---

## 2. Prometheus Setup (Standalone Windows / Linux)

### A. Download & Install Prometheus
1. Download official Prometheus binary from [prometheus.io/download](https://prometheus.io/download/).
2. Extract to `C:\prometheus` (Windows) or `/opt/prometheus` (Linux).

### B. Create `prometheus.yml` Configuration
Create `prometheus.yml` in your Prometheus directory:

```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: "sentinelml_backend"
    metrics_path: "/metrics"
    static_configs:
      - targets: ["localhost:8000"]
```

### C. Launch Prometheus
- **Windows (PowerShell)**:
  ```powershell
  .\prometheus.exe --config.file=prometheus.yml
  ```
- **Linux / macOS**:
  ```bash
  ./prometheus --config.file=prometheus.yml
  ```
- Prometheus Web UI will be available at: `http://localhost:9090`.

---

## 3. Grafana Setup (Standalone Windows / Linux)

### A. Download & Install Grafana
1. Download Grafana OSS binary or installer from [grafana.com/grafana/download](https://grafana.com/grafana/download).
2. Install and launch Grafana server service (`http://localhost:3000` or port `3001` if Next.js occupies 3000).

### B. Add Prometheus Data Source in Grafana
1. Navigate to **Connections -> Data Sources -> Add data source**.
2. Select **Prometheus**.
3. Set **Prometheus server URL**: `http://localhost:9090`.
4. Click **Save & test**.

### C. PromQL Queries for SentinelML Dashboard Panels

- **Inference Request Rate (req/sec)**:
  ```promql
  sum(rate(model_predictions_total[5m])) by (model_name)
  ```
- **P95 Prediction Latency (seconds)**:
  ```promql
  histogram_quantile(0.95, sum(rate(model_prediction_latency_seconds_bucket[5m])) by (le, model_name))
  ```
- **HTTP Error Rate (%)**:
  ```promql
  sum(rate(http_errors_total[5m])) / sum(rate(http_requests_total[5m])) * 100
  ```
- **Total Retraining Runs**:
  ```promql
  sum(retraining_runs_total)
  ```
- **Automated Rollbacks Triggered**:
  ```promql
  sum(model_rollbacks_total)
  ```
