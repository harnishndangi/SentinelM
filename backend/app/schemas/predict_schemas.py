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
