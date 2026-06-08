from typing import List
import requests
import logging
from src.models.incident import Incident

logger = logging.getLogger(__name__)


class RAGPipeline:
    """RAG pipeline using Ollama TinyLLama (Free)"""

    def __init__(self):
        self.ollama_url = "http://localhost:11434/api"
        self.model = "tinyllama"
        logger.info("Initialized Ollama TinyLLama RAG pipeline")

    def analyze_duplicate_incidents(self, new_incident: Incident,
                                    similar_incidents: List[Incident],
                                    similarity_score: float) -> str:
        """Analyze duplicate incidents using TinyLLama"""
        context = self._build_context(similar_incidents)

        prompt = f"""Incident Manager Analysis:

New Incident:
Title: {new_incident.title}
Description: {new_incident.description}
Severity: {new_incident.severity.value}

Similar Incidents:
{context}

Score: {similarity_score:.2%}

Questions:
1. Is duplicate? (YES/NO)
2. Why?
3. Action?"""

        try:
            response = requests.post(
                f"{self.ollama_url}/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "temperature": 0.3
                },
                timeout=60
            )

            if response.status_code == 200:
                result = response.json().get('response', 'No response')
                logger.info(f"Analysis completed for {new_incident.id}")
                return result[:500]  # Limit response
            else:
                return f"Error: {response.status_code}"
        except requests.exceptions.Timeout:
            logger.error("Ollama timeout - model might be too busy")
            return "Analysis pending - model processing"
        except Exception as e:
            logger.error(f"Analysis error: {e}")
            return f"Error: {str(e)}"

    def generate_resolution(self, incident: Incident,
                            historical_context: List[Incident]) -> str:
        """Generate resolution using TinyLLama"""
        context = self._build_context(historical_context)

        prompt = f"""Incident Resolution:

Incident:
Title: {incident.title}
Description: {incident.description}
Severity: {incident.severity.value}

Context:
{context}

Provide:
1. Root Cause
2. Steps
3. Prevention"""

        try:
            response = requests.post(
                f"{self.ollama_url}/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "temperature": 0.3
                },
                timeout=60
            )

            if response.status_code == 200:
                result = response.json().get('response', 'No response')
                logger.info(f"Resolution generated for {incident.id}")
                return result[:800]  # Limit response
            else:
                return f"Error: {response.status_code}"
        except requests.exceptions.Timeout:
            logger.error("Ollama timeout")
            return "Resolution generation pending"
        except Exception as e:
            logger.error(f"Resolution error: {e}")
            return f"Error: {str(e)}"

    def _build_context(self, incidents: List[Incident]) -> str:
        """Build context"""
        if not incidents:
            return "No historical incidents."

        context_parts = []
        for inc in incidents[:3]:  # Limit to 3 for TinyLLama
            context_parts.append(
                f"- {inc.title}: {inc.status.value}"
            )
        return "\n".join(context_parts)