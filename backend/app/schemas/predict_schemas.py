"""
Pydantic Request and Response Schemas for SentinelML Production Fraud Prediction Service.
"""
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field, ConfigDict


class TransactionFeatures(BaseModel):
    """Transaction feature dictionary validation schema."""
    model_config = ConfigDict(extra="allow")

    amount: Optional[float] = Field(default=None, description="Transaction amount")
    oldbalanceOrg: Optional[float] = Field(default=None, description="Origin initial balance")
    newbalanceOrig: Optional[float] = Field(default=None, description="Origin new balance")
    oldbalanceDest: Optional[float] = Field(default=None, description="Destination initial balance")
    newbalanceDest: Optional[float] = Field(default=None, description="Destination new balance")


class PredictionRequest(BaseModel):
    """Single transaction prediction request schema."""
    transaction_id: Optional[str] = Field(default=None, description="Optional unique transaction identifier")
    features: Dict[str, Any] = Field(..., description="Transaction feature key-value payload")


class PredictionResponse(BaseModel):
    """Single transaction prediction response schema."""
    prediction: int = Field(..., description="Binary fraud prediction (0: Legitimate, 1: Fraudulent)")
    fraud_probability: float = Field(..., description="Predicted fraud probability score [0.0 - 1.0]")
    model: str = Field(..., description="Model identifier name")
    model_version: str = Field(..., description="Active production model version")
    prediction_id: str = Field(..., description="Unique prediction log UUID")
    latency_ms: float = Field(..., description="End-to-end inference latency in milliseconds")


class BatchPredictionRequest(BaseModel):
    """Batch transactions prediction request schema."""
    transactions: List[PredictionRequest] = Field(..., min_length=1, description="List of transaction requests")


class BatchPredictionResponse(BaseModel):
    """Batch transactions prediction response schema."""
    predictions: List[PredictionResponse] = Field(..., description="List of inference predictions")
    total_transactions: int = Field(..., description="Total processed count")
    batch_latency_ms: float = Field(..., description="Total batch inference latency in milliseconds")


class LabelFeedbackRequest(BaseModel):
    """Delayed ground truth label feedback submission schema."""
    prediction_id: str = Field(..., description="Prediction identifier to associate ground truth label with")
    actual_label: float = Field(..., description="Ground truth target outcome (0.0: Legitimate, 1.0: Fraudulent)")
    feedback_source: Optional[str] = Field(default="manual_review", description="Feedback source (e.g. chargeback, manual_review)")


class LabelFeedbackResponse(BaseModel):
    """Delayed ground truth label feedback response schema."""
    prediction_id: str = Field(..., description="Prediction identifier")
    actual_label: float = Field(..., description="Ground truth label")
    predicted_label: int = Field(..., description="Model original prediction")
    fraud_probability: float = Field(..., description="Model original probability")
    error_val: float = Field(..., description="Prediction error metric")
    is_binary_error: bool = Field(..., description="Flag indicating if prediction misclassified outcome")
    concept_drift_status: Dict[str, Any] = Field(..., description="Updated concept drift evaluation status")
    drift_event_id: Optional[str] = Field(default=None, description="DriftEvent UUID if concept drift alert was generated")
