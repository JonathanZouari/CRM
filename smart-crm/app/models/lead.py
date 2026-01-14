"""
Lead Model
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel

from app.models.base import get_db


class LeadCreate(BaseModel):
    """Schema for creating a lead."""
    company_name: str
    contact_name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    business_size: Optional[str] = None
    estimated_budget: Optional[float] = None
    source: Optional[str] = None
    source_details: Optional[str] = None
    interest_level: Optional[int] = None
    industry: Optional[str] = None
    current_pain_points: Optional[str] = None
    ai_readiness_score: Optional[int] = None
    status: str = 'new'
    notes: Optional[str] = None
    assigned_to: Optional[str] = None
    next_follow_up: Optional[str] = None


class LeadUpdate(BaseModel):
    """Schema for updating a lead."""
    company_name: Optional[str] = None
    contact_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    business_size: Optional[str] = None
    estimated_budget: Optional[float] = None
    source: Optional[str] = None
    source_details: Optional[str] = None
    interest_level: Optional[int] = None
    industry: Optional[str] = None
    current_pain_points: Optional[str] = None
    ai_readiness_score: Optional[int] = None
    lead_score: Optional[float] = None
    lead_score_explanation: Optional[str] = None
    status: Optional[str] = None
    notes: Optional[str] = None
    assigned_to: Optional[str] = None
    last_contact_date: Optional[str] = None
    next_follow_up: Optional[str] = None


class Lead:
    """Lead model with database operations."""

    TABLE = 'leads'

    @classmethod
    def create(cls, lead_data: LeadCreate) -> Dict[str, Any]:
        """Create a new lead."""
        db = get_db()
        data = {k: v for k, v in lead_data.model_dump().items() if v is not None}

        result = db.table(cls.TABLE).insert(data).execute()
        return result.data[0] if result.data else None

    @classmethod
    def get_by_id(cls, lead_id: str) -> Optional[Dict[str, Any]]:
        """Get lead by ID."""
        db = get_db()
        result = db.table(cls.TABLE).select('*, users!assigned_to(id, full_name, email)').eq('id', lead_id).execute()
        return result.data[0] if result.data else None

    @classmethod
    def get_all(
        cls,
        status: Optional[str] = None,
        source: Optional[str] = None,
        assigned_to: Optional[str] = None,
        min_score: Optional[float] = None,
        limit: int = 100,
        offset: int = 0,
        order_by: str = 'created_at',
        ascending: bool = False
    ) -> List[Dict[str, Any]]:
        """Get all leads with optional filters."""
        db = get_db()
        query = db.table(cls.TABLE).select('*, users!assigned_to(id, full_name, email)')

        if status:
            query = query.eq('status', status)
        if source:
            query = query.eq('source', source)
        if assigned_to:
            query = query.eq('assigned_to', assigned_to)
        if min_score is not None:
            query = query.gte('lead_score', min_score)

        query = query.order(order_by, desc=not ascending).range(offset, offset + limit - 1)
        result = query.execute()
        return result.data

    @classmethod
    def get_top_scored(cls, limit: int = 10) -> List[Dict[str, Any]]:
        """Get top scored leads."""
        db = get_db()
        result = db.table(cls.TABLE).select('*, users!assigned_to(id, full_name, email)') \
            .not_.is_('lead_score', 'null') \
            .order('lead_score', desc=True) \
            .limit(limit) \
            .execute()
        return result.data

    @classmethod
    def update(cls, lead_id: str, lead_data: LeadUpdate) -> Optional[Dict[str, Any]]:
        """Update a lead."""
        db = get_db()
        data = {k: v for k, v in lead_data.model_dump().items() if v is not None}

        if not data:
            return cls.get_by_id(lead_id)

        result = db.table(cls.TABLE).update(data).eq('id', lead_id).execute()
        return result.data[0] if result.data else None

    @classmethod
    def delete(cls, lead_id: str) -> bool:
        """Delete a lead."""
        db = get_db()
        result = db.table(cls.TABLE).delete().eq('id', lead_id).execute()
        return len(result.data) > 0

    @classmethod
    def check_duplicate(cls, email: Optional[str] = None, phone: Optional[str] = None, company_name: Optional[str] = None) -> List[Dict[str, Any]]:
        """Check for potential duplicate leads."""
        db = get_db()
        duplicates = []

        if email:
            result = db.table(cls.TABLE).select('id, company_name, contact_name, email').eq('email', email).execute()
            duplicates.extend(result.data)

        if phone:
            result = db.table(cls.TABLE).select('id, company_name, contact_name, phone').eq('phone', phone).execute()
            duplicates.extend(result.data)

        if company_name:
            result = db.table(cls.TABLE).select('id, company_name, contact_name, email').ilike('company_name', f'%{company_name}%').execute()
            duplicates.extend(result.data)

        # Remove duplicates from list
        seen = set()
        unique_duplicates = []
        for d in duplicates:
            if d['id'] not in seen:
                seen.add(d['id'])
                unique_duplicates.append(d)

        return unique_duplicates

    @classmethod
    def update_score(cls, lead_id: str, score: float, explanation: str) -> Optional[Dict[str, Any]]:
        """Update lead score and explanation."""
        db = get_db()
        result = db.table(cls.TABLE).update({
            'lead_score': score,
            'lead_score_explanation': explanation
        }).eq('id', lead_id).execute()
        return result.data[0] if result.data else None

    @classmethod
    def get_stats(cls) -> Dict[str, Any]:
        """Get lead statistics."""
        db = get_db()

        # Count by status
        all_leads = db.table(cls.TABLE).select('status').execute()
        status_counts = {}
        for lead in all_leads.data:
            status = lead['status']
            status_counts[status] = status_counts.get(status, 0) + 1

        # Count by source
        source_counts = {}
        for lead in all_leads.data:
            source = lead.get('source', 'unknown')
            source_counts[source] = source_counts.get(source, 0) + 1

        return {
            'total': len(all_leads.data),
            'by_status': status_counts,
            'by_source': source_counts
        }
