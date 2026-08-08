import enum


class ModelVersionStatus(str, enum.Enum):
    TRAINING = "TRAINING"
    CANDIDATE = "CANDIDATE"
    STAGING = "STAGING"
    PRODUCTION = "PRODUCTION"
    ARCHIVED = "ARCHIVED"
    FAILED = "FAILED"


class IncidentSeverity(str, enum.Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class IncidentStatus(str, enum.Enum):
    OPEN = "OPEN"
    INVESTIGATING = "INVESTIGATING"
    RETRAINING = "RETRAINING"
    RESOLVED = "RESOLVED"
    FAILED = "FAILED"


class DeploymentStatus(str, enum.Enum):
    PENDING = "PENDING"
    ACTIVE = "ACTIVE"
    FAILED = "FAILED"
    ROLLED_BACK = "ROLLED_BACK"
    ARCHIVED = "ARCHIVED"


class AlertStatus(str, enum.Enum):
    TRIGGERED = "TRIGGERED"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    RESOLVED = "RESOLVED"
    MUTED = "MUTED"


class AlertSeverity(str, enum.Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class DriftType(str, enum.Enum):
    DATA_DRIFT = "DATA_DRIFT"
    CONCEPT_DRIFT = "CONCEPT_DRIFT"
    FEATURE_DRIFT = "FEATURE_DRIFT"
    PREDICTION_DRIFT = "PREDICTION_DRIFT"
