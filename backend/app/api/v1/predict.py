"""
FastAPI Router for Production Fraud Prediction Endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.dependencies import get_db
from backend.app.schemas.predict_schemas import (
    PredictionRequest,
    PredictionResponse,
    BatchPredictionRequest,
    BatchPredictionResponse,
    LabelFeedbackRequest,
    LabelFeedbackResponse,
)
from backend.app.services.prediction_service import PredictionService

router = APIRouter(prefix="", tags=["Prediction Engine"])


@router.post(
    "/predict",
    response_model=PredictionResponse,
    status_code=status.HTTP_200_OK,
    summary="Predict Fraud Probability for Single Transaction",
    description="Dynamically evaluates input transaction features using the active production model.",
)
def predict_fraud(
    request: PredictionRequest,
    db: Session = Depends(get_db),
) -> PredictionResponse:
    """Executes single transaction fraud prediction."""
    try:
        service = PredictionService(db)
        return service.predict_single(request)
    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Inference error: {str(e)}",
        )


@router.post(
    "/predict/batch",
    response_model=BatchPredictionResponse,
    status_code=status.HTTP_200_OK,
    summary="Predict Fraud Probability for Batch Transactions",
    description="Vectorized inference for batch transactions using the active production model.",
)
def predict_fraud_batch(
    request: BatchPredictionRequest,
    db: Session = Depends(get_db),
) -> BatchPredictionResponse:
    """Executes batch transaction fraud predictions."""
    try:
        service = PredictionService(db)
        return service.predict_batch(request)
    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Batch inference error: {str(e)}",
        )


@router.post(
    "/feedback/label",
    response_model=LabelFeedbackResponse,
    status_code=status.HTTP_200_OK,
    summary="Ingest Delayed Ground Truth Label Feedback",
    description="Ingests delayed actual outcomes (e.g. chargebacks) and evaluates stream concept drift.",
)
def submit_label_feedback(
    request: LabelFeedbackRequest,
    db: Session = Depends(get_db),
) -> LabelFeedbackResponse:
    """Submits delayed label feedback for a past prediction."""
    try:
        service = PredictionService(db)
        res = service.process_delayed_label(
            prediction_id=request.prediction_id,
            actual_label=request.actual_label,
            feedback_source=request.feedback_source or "manual_review",
        )
        return LabelFeedbackResponse(**res)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Delayed label feedback processing error: {str(e)}",
        )
