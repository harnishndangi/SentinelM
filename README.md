# SentinelML

> **Autonomous ML Reliability & Self-Healing Platform**

SentinelML is a portfolio-grade, production-oriented MLOps platform engineered to continuously monitor machine learning models in production. It identifies data drift, concept drift, and performance degradation in real-time, executing self-healing workflows (such as automated model retraining, fallback routing, and alert notifications) to maintain strict SLAs for AI systems.

---

## 🏗 Architecture Overview

SentinelML is designed using a decoupled monorepo architecture combining a high-performance Python FastAPI backend, a Next.js App Router frontend, a dedicated Machine Learning engine, and async processing layers.

```
                               ┌───────────────────────────┐
                               │  Frontend (Next.js 14)    │
                               │  Tailwind CSS & React     │
                               └─────────────┬─────────────┘
                                             │ HTTP / WS
                                             ▼
                               ┌───────────────────────────┐
                               │  Backend (FastAPI Core)   │
                               │  REST API & WebSockets    │
                               └──────┬──────┬──────┬──────┘
                                      │      │      │
             ┌────────────────────────┘      │      └────────────────────────┐
             ▼                               ▼                               ▼
   ┌───────────────────┐           ┌───────────────────┐           ┌───────────────────┐
   │ Database Layer    │           │ Caching & Broker  │           │ ML Engine         │
   │ SQLAlchemy ORM    │           │ Redis Cache       │           │ Drift, Training,  │
   │ PostgreSQL/SQLite │           │ Async Queue       │           │ & Explainability  │
   └───────────────────┘           └───────────────────┘           └───────────────────┘
```

---

## 🛠 Technologies & Tools

- **Backend Framework**: Python 3.10+, FastAPI, Uvicorn, Pydantic v2, Pydantic-Settings
- **Frontend Framework**: Next.js 14, React 18, TypeScript, Tailwind CSS, Lucide React, Zustand
- **Database & Cache**: SQLAlchemy 2.0, Asyncpg / SQLite (dev), Redis
- **ML & Data Stack**: NumPy, Pandas, Scikit-learn, SciPy
- **Telemetry & Logging**: Structlog (Structured JSON logging), Prometheus Client
- **Testing & Tooling**: Pytest, Pytest-asyncio, HTTPX

---

## 📁 Directory Structure Breakdown

```
sentinel-ml/
│
├── frontend/                     # Next.js 14 Frontend Application
│   ├── public/                   # Public static assets
│   ├── src/
│   │   ├── app/                  # Next.js App Router (Layouts, Pages, Global CSS)
│   │   ├── components/           # Reusable UI components
│   │   ├── features/             # Feature modules (Drift Monitoring, Self-Healing)
│   │   ├── hooks/                # Custom React hooks
│   │   ├── lib/                  # Shared utilities & HTTP configuration
│   │   ├── services/             # API client methods
│   │   ├── store/                # Global state stores (Zustand)
│   │   ├── types/                # TypeScript interface definitions
│   │   └── utils/                # Helper functions
│   ├── package.json              # Frontend Node dependencies
│   ├── tsconfig.json             # TypeScript config
│   ├── tailwind.config.ts        # Tailwind CSS config
│   ├── postcss.config.mjs        # PostCSS config
│   └── next.config.js            # Next.js config & API rewrites
│
├── backend/                      # FastAPI Backend Core
│   └── app/
│       ├── main.py               # Application entry point & CORS configuration
│       ├── config.py             # Centralized env settings (Pydantic BaseSettings)
│       ├── database.py           # SQLAlchemy engine & session management
│       ├── dependencies.py       # FastAPI dependency providers (DB, Redis)
│       ├── api/                  # API routes & versions
│       │   └── v1/               # Version 1 endpoints (Health, Metrics, Models)
│       ├── models/               # Database ORM models
│       ├── schemas/              # Request & Response Pydantic schemas
│       ├── repositories/         # Database access abstraction layer
│       ├── services/             # Core application business logic
│       ├── workers/              # Asynchronous queue workers
│       ├── websocket/            # Real-time WebSocket connection manager
│       ├── monitoring/           # Telemetry & metric collectors
│       └── core/                 # Shared utilities (Structured JSON Logging)
│
├── ml/                           # Core Machine Learning Engine
│   ├── training/                 # Model training & hyperparameter tuning
│   ├── preprocessing/            # Feature transformation & scaling pipelines
│   ├── evaluation/               # Metrics computation (F1, ROC-AUC, RMSE)
│   ├── drift/                    # Kolmogorov-Smirnov, PSI, Wasserstein drift engines
│   ├── explainability/           # Feature importance & attribution (SHAP)
│   └── models/                   # Model architecture definitions & wrappers
│
├── pipelines/                    # Data orchestration workflows
├── monitoring/                   # Prometheus & OpenTelemetry exporters
│
├── data/                         # Datasets (gitignored)
│   ├── raw/                      # Ingested raw payloads
│   ├── processed/                # Preprocessed feature tables
│   └── reference/                # Baseline reference datasets
│
├── artifacts/                    # Model binary checkpoints & scalers (gitignored)
├── experiments/                  # Experiment tracking logs (gitignored)
│
├── tests/                        # Automated Pytest Suite
│   ├── unit/                     # Isolated unit tests
│   └── integration/              # API and DB integration tests
│
├── scripts/                      # Setup & dev launcher scripts
├── docs/                         # Architecture documentation
├── .github/workflows/            # CI/CD Workflows
│
├── .env.example                  # Environment configuration template
├── .gitignore                    # Git ignore specifications
├── README.md                     # Project documentation
└── requirements.txt              # Python dependencies
```

---

## ⚡ Environment Variables

SentinelML uses centralized environment variable management via `Pydantic-Settings`. Key environment variables defined in `.env.example`:

| Environment Variable | Default Value | Description |
|----------------------|---------------|-------------|
| `ENVIRONMENT` | `development` | Environment mode (`development` / `production`) |
| `LOG_LEVEL` | `INFO` | Logging level (`DEBUG`, `INFO`, `WARNING`, `ERROR`) |
| `DEBUG` | `true` | Debug flag |
| `SECRET_KEY` | `sentinelml-default...` | Secret key for JWT & session hashing |
| `DATABASE_URL` | `sqlite:///./sentinelml.db` | SQLAlchemy connection string |
| `REDIS_URL` | `redis://localhost:6379/0` | Redis URI for caching & worker queues |
| `NEXT_PUBLIC_API_URL` | `http://localhost:8000/api/v1` | Backend API base URL for frontend |

---

## 🚀 Local Setup & Installation

### 1. Prerequisites
- Python 3.10+
- Node.js 18+ & npm
- Git

### 2. Python Virtual Environment Setup

**Windows (PowerShell):**
```powershell
# Navigate to project root
python -m venv venv
.\venv\Scripts\Activate.ps1

# Upgrade pip and install dependencies
python -m pip install --upgrade pip
pip install -r requirements.txt
```

**macOS / Linux:**
```bash
# Navigate to project root
python3 -m venv venv
source venv/bin/activate

# Upgrade pip and install dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

### 3. Initialize Local Environment File
```bash
python scripts/setup_env.py
```

### 4. Running the Backend Server
```bash
# From project root with venv activated:
python -m uvicorn backend.app.main:app --reload --port 8000
```
Backend API will be accessible at:
- **Health Check Endpoint**: `http://localhost:8000/api/v1/health`
- **Swagger Interactive Docs**: `http://localhost:8000/api/v1/docs`

### 5. Running the Frontend Server
```bash
# Navigate to frontend directory
cd frontend

# Install Node dependencies
npm install

# Run Next.js development server
npm run dev
```
Frontend Dashboard will be accessible at `http://localhost:3000`.

---

## 📊 Launching MLflow Experiment Tracking Locally (Without Docker)

SentinelML tracks all model training runs, hyperparameters, metrics, and model artifacts using MLflow. You can run MLflow locally without Docker.

### Option 1: Launch MLflow Interactive UI
To launch the local MLflow dashboard and browse tracked experiments (`SentinelML-FraudDetection`):
```bash
# From project root with venv activated:
python -m mlflow ui --port 5000
```
Open your browser at [http://127.0.0.1:5000](http://127.0.0.1:5000).

### Option 2: Launch MLflow Tracking Server with SQLite Backend
For persistent experiment tracking with SQLite store and local artifact repository:
```bash
python -m mlflow server --backend-store-uri sqlite:///mlflow.db --default-artifact-root ./mlruns --host 127.0.0.1 --port 5000
```

### Environment Configuration (Optional)
To point SentinelML to your running local MLflow server, set the environment variable:
```bash
# PowerShell:
$env:MLFLOW_TRACKING_URI="http://127.0.0.1:5000"

# Bash / Zsh:
export MLFLOW_TRACKING_URI="http://127.0.0.1:5000"
```

---

## 🧪 Verification & Testing

Run the automated Pytest test suite from the root directory:
```bash
pytest tests/
```

To verify the backend health endpoint manually via `curl` or browser:
```bash
curl http://localhost:8000/api/v1/health
```
**Expected Response:**
```json
{
  "status": "healthy",
  "service": "sentinelml-api",
  "version": "1.0.0"
}
```
