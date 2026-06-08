from typing import List, Tuple, Optional
from datetime import datetime, timedelta
from src.models.incident import Incident, IncidentStatus
from src.embeddings.embedding_service import EmbeddingService
from src.vector_db.vector_store import VectorStore
from config import config
import logging

logger = logging.getLogger(__name__)


class DeduplicationEngine:
    """AI-powered incident deduplication engine"""

    def __init__(self, embedding_service: EmbeddingService, vector_store: VectorStore):
        self.embedding_service = embedding_service
        self.vector_store = vector_store
        self.similarity_threshold = config.SIMILARITY_THRESHOLD
        self.time_window = timedelta(minutes=config.TIME_WINDOW_MINUTES)

    def deduplicate(self, new_incident: Incident, existing_incidents: List[Incident]) -> Tuple[
        bool, Optional[Incident], float]:
        """
        Check if new incident is duplicate of existing ones

        Args:
            new_incident: New incident to check
            existing_incidents: List of existing incidents

        Returns:
            Tuple of (is_duplicate, parent_incident, similarity_score)
        """
        # Generate embedding for new incident
        incident_text = f"{new_incident.title} {new_incident.description}"
        embedding = self.embedding_service.embed_text(incident_text)
        new_incident.embedding_vector = embedding

        # Search similar incidents in vector store
        similar_ids, similarity_scores = self.vector_store.search(embedding, k=5)

        # Check time window and similarity threshold
        for idx, (incident_id, score) in enumerate(zip(similar_ids, similarity_scores)):
            if score < self.similarity_threshold:
                continue

            # Find existing incident
            matching_incident = next((inc for inc in existing_incidents if inc.id == incident_id), None)

            if matching_incident is None:
                continue

            # Check time window
            time_diff = new_incident.timestamp - matching_incident.timestamp
            if time_diff > self.time_window:
                continue

            logger.info(f"Duplicate found: {new_incident.id} matches {matching_incident.id} with score {score:.4f}")
            return True, matching_incident, score

        return False, None, 0.0

    def mark_as_duplicate(self, incident: Incident, parent_incident: Incident):
        """Mark incident as duplicate"""
        incident.status = IncidentStatus.DUPLICATE
        incident.duplicate_of = parent_incident.id
        parent_incident.duplicate_count += 1
        logger.info(f"Marked {incident.id} as duplicate of {parent_incident.id}")

    def index_incident(self, incident: Incident):
        """Index incident in vector store"""
        if incident.embedding_vector is None:
            incident_text = f"{incident.title} {incident.description}"
            incident.embedding_vector = self.embedding_service.embed_text(incident_text)

        self.vector_store.add([incident.embedding_vector], [incident.id])