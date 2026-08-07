# SentinelML System Architecture Overview

SentinelML is an Autonomous ML Reliability & Self-Healing Platform designed to monitor production ML models for data drift, concept drift, and performance degradation, enabling automatic model retraining, fallback routing, and real-time observability.

## High-Level Architecture Diagram

```
[ Frontend: Next.js + React + Tailwind ]
                  │
                  ▼ HTTP / WebSocket
        [ Backend: FastAPI ]
     ┌────────────┼────────────┐
     ▼            ▼            ▼
[ PostgreSQL ] [ Redis ] [ ML Engine ]
                           ├── Drift Detection (KS Test, PSI, Wasserstein)
                           ├── Model Retraining & Evaluation
                           └── Model Registry & Checkpoints
```

## System Layers

1. **Frontend**: Next.js App Router providing real-time telemetry dashboards, alert metrics, drift analytics, and self-healing action logs.
2. **Backend**: FastAPI backend serving REST APIs (`/api/v1/health`, etc.), WebSocket updates, session orchestration, and database access.
3. **ML Engine**: Python ML modules for automated data drift checking, model evaluation, and self-healing actions.
4. **Storage & Caching**: PostgreSQL for metadata/metrics storage and Redis for caching & asynchronous task queues.
