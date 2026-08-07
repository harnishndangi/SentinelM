from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str = Field(default="healthy", json_schema_extra={"example": "healthy"})
    service: str = Field(default="sentinelml-api", json_schema_extra={"example": "sentinelml-api"})
    version: str = Field(default="1.0.0", json_schema_extra={"example": "1.0.0"})
