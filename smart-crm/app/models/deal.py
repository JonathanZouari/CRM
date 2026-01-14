"""
Deal Model
"""
from datetime import datetime, date
from typing import Optional, List, Dict, Any
from pydantic import BaseModel

from app.models.base import get_db


class DealCreate(BaseModel):
    """Schema for creating a deal."""
    title: str
    value: float
    lead_id: Optional[str] = None
    assigned_to: Optional[str] = None
    description: Optional[str] = None
    expected_close_date: Optional[str] = None
    stage: str = 'discovery'
    probability: Optional[int] = None
    estimated_hours: Optional[float] = None
    service_type: Optional[str] = None


class DealUpdate(BaseModel):
    """Schema for updating a deal."""
    title: Optional[str] = None
    value: Optional[float] = None
    lead_id: Optional[str] = None
    assigned_to: Optional[str] = None
    description: Optional[str] = None
    expected_close_date: Optional[str] = None
    actual_close_date: Optional[str] = None
    stage: Optional[str] = None
    probability: Optional[int] = None
    estimated_hours: Optional[float] = None
    actual_hours: Optional[float] = None
    service_type: Optional[str] = None
    closed_at: Optional[str] = None


class Deal:
    """Deal model with database operations."""

    TABLE = 'deals'

    # Stage probability mapping
    STAGE_PROBABILITIES = {
        'discovery': 10,
        'proposal': 30,
        'negotiation': 50,
        'contract': 80,
        'closed_won': 100,
        'closed_lost': 0
    }

    @classmethod
    def create(cls, deal_data: DealCreate) -> Dict[str, Any]:
        """Create a new deal."""
        db = get_db()
        data = {k: v for k, v in deal_data.model_dump().items() if v is not None}

        # Set default probability based on stage if not provided
        if 'probability' not in data and 'stage' in data:
            data['probability'] = cls.STAGE_PROBABILITIES.get(data['stage'], 10)

        result = db.table(cls.TABLE).insert(data).execute()
        return result.data[0] if result.data else None

    @classmethod
    def get_by_id(cls, deal_id: str) -> Optional[Dict[str, Any]]:
        """Get deal by ID."""
        db = get_db()
        result = db.table(cls.TABLE).select(
            '*, leads(id, company_name, contact_name), users!assigned_to(id, full_name, email)'
        ).eq('id', deal_id).execute()
        return result.data[0] if result.data else None

    @classmethod
    def get_all(
        cls,
        stage: Optional[str] = None,
        assigned_to: Optional[str] = None,
        lead_id: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
        order_by: str = 'created_at',
        ascending: bool = False
    ) -> List[Dict[str, Any]]:
        """Get all deals with optional filters."""
        db = get_db()
        query = db.table(cls.TABLE).select(
            '*, leads(id, company_name, contact_name), users!assigned_to(id, full_name, email)'
        )

        if stage:
            query = query.eq('stage', stage)
        if assigned_to:
            query = query.eq('assigned_to', assigned_to)
        if lead_id:
            query = query.eq('lead_id', lead_id)

        query = query.order(order_by, desc=not ascending).range(offset, offset + limit - 1)
        result = query.execute()
        return result.data

    @classmethod
    def get_by_stage(cls) -> Dict[str, List[Dict[str, Any]]]:
        """Get deals grouped by stage (for Kanban view)."""
        db = get_db()
        result = db.table(cls.TABLE).select(
            '*, leads(id, company_name, contact_name), users!assigned_to(id, full_name, email)'
        ).execute()

        stages = {
            'discovery': [],
            'proposal': [],
            'negotiation': [],
            'contract': [],
            'closed_won': [],
            'closed_lost': []
        }

        for deal in result.data:
            stage = deal.get('stage', 'discovery')
            if stage in stages:
                stages[stage].append(deal)

        return stages

    @classmethod
    def update(cls, deal_id: str, deal_data: DealUpdate) -> Optional[Dict[str, Any]]:
        """Update a deal."""
        db = get_db()
        data = {k: v for k, v in deal_data.model_dump().items() if v is not None}

        if not data:
            return cls.get_by_id(deal_id)

        # Handle stage changes
        if 'stage' in data:
            if data['stage'] in ('closed_won', 'closed_lost'):
                data['closed_at'] = datetime.now().isoformat()
                if data['stage'] == 'closed_won':
                    data['actual_close_date'] = date.today().isoformat()
            # Update probability based on stage if not explicitly set
            if 'probability' not in data:
                data['probability'] = cls.STAGE_PROBABILITIES.get(data['stage'], data.get('probability'))

        result = db.table(cls.TABLE).update(data).eq('id', deal_id).execute()
        return result.data[0] if result.data else None

    @classmethod
    def update_stage(cls, deal_id: str, stage: str) -> Optional[Dict[str, Any]]:
        """Update deal stage."""
        return cls.update(deal_id, DealUpdate(stage=stage))

    @classmethod
    def delete(cls, deal_id: str) -> bool:
        """Delete a deal."""
        db = get_db()
        result = db.table(cls.TABLE).delete().eq('id', deal_id).execute()
        return len(result.data) > 0

    @classmethod
    def get_pipeline_stats(cls) -> Dict[str, Any]:
        """Get pipeline statistics."""
        db = get_db()
        result = db.table(cls.TABLE).select('stage, value, probability').execute()

        stats = {
            'total_value': 0,
            'weighted_value': 0,
            'by_stage': {},
            'active_deals': 0
        }

        for deal in result.data:
            stage = deal.get('stage', 'discovery')
            value = float(deal.get('value', 0))
            probability = int(deal.get('probability', 0))

            stats['total_value'] += value
            stats['weighted_value'] += value * (probability / 100)

            if stage not in stats['by_stage']:
                stats['by_stage'][stage] = {'count': 0, 'value': 0}
            stats['by_stage'][stage]['count'] += 1
            stats['by_stage'][stage]['value'] += value

            if stage not in ('closed_won', 'closed_lost'):
                stats['active_deals'] += 1

        return stats

    @classmethod
    def get_revenue_stats(cls, start_date: Optional[str] = None, end_date: Optional[str] = None) -> Dict[str, Any]:
        """Get revenue statistics for closed won deals."""
        db = get_db()
        query = db.table(cls.TABLE).select('value, actual_close_date, closed_at').eq('stage', 'closed_won')

        if start_date:
            query = query.gte('actual_close_date', start_date)
        if end_date:
            query = query.lte('actual_close_date', end_date)

        result = query.execute()

        total_revenue = sum(float(deal.get('value', 0)) for deal in result.data)
        deal_count = len(result.data)

        return {
            'total_revenue': total_revenue,
            'deal_count': deal_count,
            'average_deal_size': total_revenue / deal_count if deal_count > 0 else 0
        }
