from datetime import datetime
from enum import Enum
from dataclasses import dataclass
from typing import Optional, List
import uuid


class IncidentStatus(Enum):
    OPEN = "open"
    RESOLVED = "resolved"
    CLOSED = "closed"
    DUPLICATE = "duplicate"


class SeverityLevel(Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class Incident:
    title: str
    description: str
    severity: SeverityLevel
    source: str
    id: str = None
    timestamp: datetime = None
    status: IncidentStatus = IncidentStatus.OPEN
    resolved_at: Optional[datetime] = None
    closed_at: Optional[datetime] = None
    duplicate_of: Optional[str] = None
    resolution_notes: str = ""
    embedding_vector: Optional[List[float]] = None
    duplicate_count: int = 0

    def __post_init__(self):
        if self.id is None:
            self.id = str(uuid.uuid4())
        if self.timestamp is None:
            self.timestamp = datetime.now()

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'severity': self.severity.value,
            'source': self.source,
            'status': self.status.value,
            'timestamp': self.timestamp.isoformat(),
            'resolved_at': self.resolved_at.isoformat() if self.resolved_at else None,
            'closed_at': self.closed_at.isoformat() if self.closed_at else None,
            'duplicate_of': self.duplicate_of,
            'resolution_notes': self.resolution_notes,
            'duplicate_count': self.duplicate_count
        }