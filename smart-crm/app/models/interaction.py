"""
Interaction Model
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel

from app.models.base import get_db


class InteractionCreate(BaseModel):
    """Schema for creating an interaction."""
    lead_id: Optional[str] = None
    deal_id: Optional[str] = None
    user_id: Optional[str] = None
    type: str
    subject: Optional[str] = None
    content: Optional[str] = None
    outcome: Optional[str] = None
    duration_minutes: Optional[int] = None


class Interaction:
    """Interaction model with database operations."""

    TABLE = 'interactions'

    @classmethod
    def create(cls, interaction_data: InteractionCreate) -> Dict[str, Any]:
        """Create a new interaction."""
        db = get_db()
        data = {k: v for k, v in interaction_data.model_dump().items() if v is not None}

        result = db.table(cls.TABLE).insert(data).execute()

        # Update last_contact_date on lead if lead_id is provided
        if data.get('lead_id'):
            db.table('leads').update({
                'last_contact_date': datetime.now().isoformat()
            }).eq('id', data['lead_id']).execute()

        return result.data[0] if result.data else None

    @classmethod
    def get_by_id(cls, interaction_id: str) -> Optional[Dict[str, Any]]:
        """Get interaction by ID."""
        db = get_db()
        result = db.table(cls.TABLE).select(
            '*, leads(id, company_name, contact_name), deals(id, title), users(id, full_name)'
        ).eq('id', interaction_id).execute()
        return result.data[0] if result.data else None

    @classmethod
    def get_by_lead(cls, lead_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get interactions for a lead."""
        db = get_db()
        result = db.table(cls.TABLE).select(
            '*, users(id, full_name)'
        ).eq('lead_id', lead_id).order('created_at', desc=True).limit(limit).execute()
        return result.data

    @classmethod
    def get_by_deal(cls, deal_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get interactions for a deal."""
        db = get_db()
        result = db.table(cls.TABLE).select(
            '*, users(id, full_name)'
        ).eq('deal_id', deal_id).order('created_at', desc=True).limit(limit).execute()
        return result.data

    @classmethod
    def get_by_user(cls, user_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get interactions by a user."""
        db = get_db()
        result = db.table(cls.TABLE).select(
            '*, leads(id, company_name, contact_name), deals(id, title)'
        ).eq('user_id', user_id).order('created_at', desc=True).limit(limit).execute()
        return result.data

    @classmethod
    def get_recent(cls, limit: int = 20) -> List[Dict[str, Any]]:
        """Get recent interactions."""
        db = get_db()
        result = db.table(cls.TABLE).select(
            '*, leads(id, company_name, contact_name), deals(id, title), users(id, full_name)'
        ).order('created_at', desc=True).limit(limit).execute()
        return result.data

    @classmethod
    def delete(cls, interaction_id: str) -> bool:
        """Delete an interaction."""
        db = get_db()
        result = db.table(cls.TABLE).delete().eq('id', interaction_id).execute()
        return len(result.data) > 0
