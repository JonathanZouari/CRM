"""
Services for Smart CRM
"""
from app.services.lead_scoring import calculate_lead_score
from app.services.vector_store import VectorStore

__all__ = [
    'calculate_lead_score',
    'VectorStore'
]
