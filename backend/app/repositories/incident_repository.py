from typing import List, Optional
from sqlalchemy.orm import Session
from backend.app.models.incident import Incident, IncidentEvent
from backend.app.core.enums import IncidentStatus, IncidentSeverity
from backend.app.repositories.base import BaseRepository


class IncidentRepository(BaseRepository[Incident]):
    def __init__(self, db: Session):
        super().__init__(Incident, db)

    def list_open_incidents(self) -> List[Incident]:
        return (
            self.db.query(Incident)
            .filter(Incident.status.in_([IncidentStatus.OPEN, IncidentStatus.INVESTIGATING, IncidentStatus.RETRAINING]))
            .order_by(Incident.opened_at.desc())
            .all()
        )

    def get_by_model_version(self, model_version_id: str) -> List[Incident]:
        return (
            self.db.query(Incident)
            .filter(Incident.model_version_id == model_version_id)
            .order_by(Incident.opened_at.desc())
            .all()
        )


class IncidentEventRepository(BaseRepository[IncidentEvent]):
    def __init__(self, db: Session):
        super().__init__(IncidentEvent, db)

    def list_events_for_incident(self, incident_id: str) -> List[IncidentEvent]:
        return (
            self.db.query(IncidentEvent)
            .filter(IncidentEvent.incident_id == incident_id)
            .order_by(IncidentEvent.created_at.asc())
            .all()
        )
