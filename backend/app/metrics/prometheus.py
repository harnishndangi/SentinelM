import time
from fastapi import Request, Response
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST, REGISTRY

# 1. HTTP Request Metrics
HTTP_REQUESTS_TOTAL = Counter(
    "http_requests_total",
    "Total count of HTTP requests handled by API server",
    ["method", "endpoint", "status_code"],
)

HTTP_ERRORS_TOTAL = Counter(
    "http_errors_total",
    "Total count of HTTP 4xx and 5xx errors",
    ["method", "endpoint", "status_code"],
)

HTTP_REQUEST_DURATION_SECONDS = Histogram(
    "http_request_duration_seconds",
    "HTTP request execution latency in seconds",
    ["method", "endpoint"],
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0),
)

# 2. Model Inference & Reliability Metrics
MODEL_PREDICTIONS_TOTAL = Counter(
    "model_predictions_total",
    "Total count of model inference predictions served",
    ["model_name", "model_version"],
)

MODEL_PREDICTION_LATENCY_SECONDS = Histogram(
    "model_prediction_latency_seconds",
    "Model inference calculation latency in seconds",
    ["model_name", "model_version"],
    buckets=(0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0),
)

DRIFT_DETECTIONS_TOTAL = Counter(
    "drift_detections_total",
    "Total statistical feature and concept drift detection events",
    ["model_name", "severity"],
)

INCIDENTS_CREATED_TOTAL = Counter(
    "incidents_created_total",
    "Total operational ML incidents and RCA alerts created",
    ["severity", "incident_type"],
)

RETRAINING_RUNS_TOTAL = Counter(
    "retraining_runs_total",
    "Total automated retraining flow execution runs triggered",
    ["model_name", "trigger"],
)

TRAINING_FAILURES_TOTAL = Counter(
    "training_failures_total",
    "Total automated retraining flow pipeline stage failures",
    ["model_name", "stage"],
)

MODEL_PROMOTIONS_TOTAL = Counter(
    "model_promotions_total",
    "Total model version promotions to production",
    ["model_name", "target_environment"],
)

MODEL_ROLLBACKS_TOTAL = Counter(
    "model_rollbacks_total",
    "Total model version automated rollbacks triggered by SLA monitors",
    ["model_name", "reason_category"],
)


async def prometheus_middleware(request: Request, call_next):
    start_time = time.time()
    method = request.method
    path = request.url.path

    # Normalize low-cardinality endpoint paths (avoid route parameters bloat)
    endpoint = path
    if path.startswith("/api/v1/models/"):
        endpoint = "/api/v1/models/{id}"
    elif path.startswith("/api/v1/incidents/"):
        endpoint = "/api/v1/incidents/{id}"
    elif path.startswith("/api/v1/drift/"):
        endpoint = "/api/v1/drift/{feature}"

    response = await call_next(request)

    status_code = str(response.status_code)
    duration = time.time() - start_time

    # Record metrics
    HTTP_REQUESTS_TOTAL.labels(method=method, endpoint=endpoint, status_code=status_code).inc()
    HTTP_REQUEST_DURATION_SECONDS.labels(method=method, endpoint=endpoint).observe(duration)

    if response.status_code >= 400:
        HTTP_ERRORS_TOTAL.labels(method=method, endpoint=endpoint, status_code=status_code).inc()

    return response


def get_metrics_response() -> Response:
    """Returns the Prometheus metrics format response."""
    return Response(content=generate_latest(REGISTRY), media_type=CONTENT_TYPE_LATEST)
