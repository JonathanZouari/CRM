"""
Vector Store Service using ChromaDB

Handles indexing and retrieval of CRM data for RAG queries.
"""
import os
from typing import List, Dict, Any, Optional
import chromadb
from chromadb.config import Settings
from openai import OpenAI


class VectorStore:
    """ChromaDB-based vector store for CRM data."""

    def __init__(self, persist_directory: str = None):
        self.persist_directory = persist_directory or os.getenv('CHROMA_PERSIST_DIR', './chroma_data')
        self.openai_client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

        # Initialize ChromaDB client
        self.client = chromadb.PersistentClient(
            path=self.persist_directory,
            settings=Settings(anonymized_telemetry=False)
        )

        # Create collections
        self.leads_collection = self.client.get_or_create_collection(
            name="leads",
            metadata={"description": "CRM leads data"}
        )
        self.deals_collection = self.client.get_or_create_collection(
            name="deals",
            metadata={"description": "CRM deals data"}
        )
        self.interactions_collection = self.client.get_or_create_collection(
            name="interactions",
            metadata={"description": "CRM interactions data"}
        )

    def _get_embedding(self, text: str) -> List[float]:
        """Get embedding for text using OpenAI."""
        response = self.openai_client.embeddings.create(
            model="text-embedding-3-small",
            input=text
        )
        return response.data[0].embedding

    def _lead_to_text(self, lead: Dict[str, Any]) -> str:
        """Convert lead to searchable text."""
        parts = [
            f"Company: {lead.get('company_name', 'Unknown')}",
            f"Contact: {lead.get('contact_name', 'Unknown')}",
            f"Industry: {lead.get('industry', 'Unknown')}",
            f"Status: {lead.get('status', 'Unknown')}",
            f"Source: {lead.get('source', 'Unknown')}",
            f"Business Size: {lead.get('business_size', 'Unknown')}",
            f"Budget: {lead.get('estimated_budget', 'Unknown')}",
            f"Interest Level: {lead.get('interest_level', 'Unknown')}/10",
            f"AI Readiness: {lead.get('ai_readiness_score', 'Unknown')}/10",
            f"Lead Score: {lead.get('lead_score', 'Unknown')}/100",
            f"Pain Points: {lead.get('current_pain_points', 'Not specified')}",
            f"Notes: {lead.get('notes', 'No notes')}"
        ]
        return " | ".join(parts)

    def _deal_to_text(self, deal: Dict[str, Any]) -> str:
        """Convert deal to searchable text."""
        lead_info = deal.get('leads', {}) or {}
        parts = [
            f"Deal: {deal.get('title', 'Unknown')}",
            f"Company: {lead_info.get('company_name', 'Unknown')}",
            f"Value: {deal.get('value', 0)}",
            f"Stage: {deal.get('stage', 'Unknown')}",
            f"Service Type: {deal.get('service_type', 'Unknown')}",
            f"Probability: {deal.get('probability', 0)}%",
            f"Description: {deal.get('description', 'No description')}"
        ]
        return " | ".join(parts)

    def _interaction_to_text(self, interaction: Dict[str, Any]) -> str:
        """Convert interaction to searchable text."""
        lead_info = interaction.get('leads', {}) or {}
        parts = [
            f"Type: {interaction.get('type', 'Unknown')}",
            f"Company: {lead_info.get('company_name', 'Unknown')}",
            f"Subject: {interaction.get('subject', 'No subject')}",
            f"Content: {interaction.get('content', 'No content')}",
            f"Outcome: {interaction.get('outcome', 'No outcome')}"
        ]
        return " | ".join(parts)

    def index_lead(self, lead: Dict[str, Any]):
        """Index a single lead."""
        lead_id = lead.get('id')
        if not lead_id:
            return

        text = self._lead_to_text(lead)
        embedding = self._get_embedding(text)

        self.leads_collection.upsert(
            ids=[lead_id],
            embeddings=[embedding],
            documents=[text],
            metadatas=[{
                'company_name': lead.get('company_name', ''),
                'status': lead.get('status', ''),
                'lead_score': str(lead.get('lead_score', 0)),
                'source': lead.get('source', '')
            }]
        )

    def index_deal(self, deal: Dict[str, Any]):
        """Index a single deal."""
        deal_id = deal.get('id')
        if not deal_id:
            return

        text = self._deal_to_text(deal)
        embedding = self._get_embedding(text)

        self.deals_collection.upsert(
            ids=[deal_id],
            embeddings=[embedding],
            documents=[text],
            metadatas=[{
                'title': deal.get('title', ''),
                'stage': deal.get('stage', ''),
                'value': str(deal.get('value', 0)),
                'service_type': deal.get('service_type', '')
            }]
        )

    def index_interaction(self, interaction: Dict[str, Any]):
        """Index a single interaction."""
        interaction_id = interaction.get('id')
        if not interaction_id:
            return

        text = self._interaction_to_text(interaction)
        embedding = self._get_embedding(text)

        self.interactions_collection.upsert(
            ids=[interaction_id],
            embeddings=[embedding],
            documents=[text],
            metadatas=[{
                'type': interaction.get('type', ''),
                'lead_id': interaction.get('lead_id', ''),
                'deal_id': interaction.get('deal_id', '')
            }]
        )

    def index_all_leads(self, leads: List[Dict[str, Any]]):
        """Index all leads."""
        for lead in leads:
            self.index_lead(lead)

    def index_all_deals(self, deals: List[Dict[str, Any]]):
        """Index all deals."""
        for deal in deals:
            self.index_deal(deal)

    def index_all_interactions(self, interactions: List[Dict[str, Any]]):
        """Index all interactions."""
        for interaction in interactions:
            self.index_interaction(interaction)

    def search_leads(self, query: str, n_results: int = 5) -> List[Dict[str, Any]]:
        """Search leads by query."""
        embedding = self._get_embedding(query)
        results = self.leads_collection.query(
            query_embeddings=[embedding],
            n_results=n_results
        )

        return [
            {
                'id': results['ids'][0][i],
                'document': results['documents'][0][i],
                'metadata': results['metadatas'][0][i],
                'distance': results['distances'][0][i] if results.get('distances') else None
            }
            for i in range(len(results['ids'][0]))
        ]

    def search_deals(self, query: str, n_results: int = 5) -> List[Dict[str, Any]]:
        """Search deals by query."""
        embedding = self._get_embedding(query)
        results = self.deals_collection.query(
            query_embeddings=[embedding],
            n_results=n_results
        )

        return [
            {
                'id': results['ids'][0][i],
                'document': results['documents'][0][i],
                'metadata': results['metadatas'][0][i],
                'distance': results['distances'][0][i] if results.get('distances') else None
            }
            for i in range(len(results['ids'][0]))
        ]

    def search_all(self, query: str, n_results: int = 5) -> Dict[str, List[Dict[str, Any]]]:
        """Search across all collections."""
        return {
            'leads': self.search_leads(query, n_results),
            'deals': self.search_deals(query, n_results)
        }

    def delete_lead(self, lead_id: str):
        """Delete a lead from the index."""
        try:
            self.leads_collection.delete(ids=[lead_id])
        except Exception:
            pass

    def delete_deal(self, deal_id: str):
        """Delete a deal from the index."""
        try:
            self.deals_collection.delete(ids=[deal_id])
        except Exception:
            pass

    def clear_all(self):
        """Clear all collections."""
        self.client.delete_collection("leads")
        self.client.delete_collection("deals")
        self.client.delete_collection("interactions")

        # Recreate collections
        self.leads_collection = self.client.get_or_create_collection(name="leads")
        self.deals_collection = self.client.get_or_create_collection(name="deals")
        self.interactions_collection = self.client.get_or_create_collection(name="interactions")


# Singleton instance
_vector_store = None


def get_vector_store() -> VectorStore:
    """Get singleton vector store instance."""
    global _vector_store
    if _vector_store is None:
        _vector_store = VectorStore()
    return _vector_store
