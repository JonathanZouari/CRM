"""
Work Log Model
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel

from app.models.base import get_db


class WorkLogCreate(BaseModel):
    """Schema for creating a work log."""
    user_id: str
    deal_id: str
    date: str
    hours: float
    description: Optional[str] = None
    billable: bool = True


class WorkLogUpdate(BaseModel):
    """Schema for updating a work log."""
    hours: Optional[float] = None
    description: Optional[str] = None
    billable: Optional[bool] = None


class WorkLog:
    """Work log model with database operations."""

    TABLE = 'work_logs'

    @classmethod
    def create(cls, log_data: WorkLogCreate) -> Dict[str, Any]:
        """Create a new work log."""
        db = get_db()
        data = log_data.model_dump()

        result = db.table(cls.TABLE).insert(data).execute()

        # Update actual_hours on the deal
        if result.data:
            cls._update_deal_hours(data['deal_id'])

        return result.data[0] if result.data else None

    @classmethod
    def _update_deal_hours(cls, deal_id: str):
        """Update total actual hours on a deal."""
        db = get_db()
        logs = db.table(cls.TABLE).select('hours').eq('deal_id', deal_id).execute()
        total_hours = sum(float(log.get('hours', 0)) for log in logs.data)
        db.table('deals').update({'actual_hours': total_hours}).eq('id', deal_id).execute()

    @classmethod
    def get_by_id(cls, log_id: str) -> Optional[Dict[str, Any]]:
        """Get work log by ID."""
        db = get_db()
        result = db.table(cls.TABLE).select(
            '*, users(id, full_name), deals(id, title)'
        ).eq('id', log_id).execute()
        return result.data[0] if result.data else None

    @classmethod
    def get_by_deal(cls, deal_id: str) -> List[Dict[str, Any]]:
        """Get work logs for a deal."""
        db = get_db()
        result = db.table(cls.TABLE).select(
            '*, users(id, full_name)'
        ).eq('deal_id', deal_id).order('date', desc=True).execute()
        return result.data

    @classmethod
    def get_by_user(cls, user_id: str, start_date: Optional[str] = None, end_date: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get work logs for a user."""
        db = get_db()
        query = db.table(cls.TABLE).select(
            '*, deals(id, title, value)'
        ).eq('user_id', user_id)

        if start_date:
            query = query.gte('date', start_date)
        if end_date:
            query = query.lte('date', end_date)

        result = query.order('date', desc=True).execute()
        return result.data

    @classmethod
    def update(cls, log_id: str, log_data: WorkLogUpdate) -> Optional[Dict[str, Any]]:
        """Update a work log."""
        db = get_db()
        data = {k: v for k, v in log_data.model_dump().items() if v is not None}

        if not data:
            return cls.get_by_id(log_id)

        # Get the deal_id before update
        existing = cls.get_by_id(log_id)
        if not existing:
            return None

        result = db.table(cls.TABLE).update(data).eq('id', log_id).execute()

        # Update deal hours if hours changed
        if 'hours' in data:
            cls._update_deal_hours(existing['deal_id'])

        return result.data[0] if result.data else None

    @classmethod
    def delete(cls, log_id: str) -> bool:
        """Delete a work log."""
        db = get_db()

        # Get deal_id before deletion
        existing = cls.get_by_id(log_id)
        if not existing:
            return False

        result = db.table(cls.TABLE).delete().eq('id', log_id).execute()

        if len(result.data) > 0:
            # Update deal hours
            cls._update_deal_hours(existing['deal_id'])
            return True
        return False

    @classmethod
    def get_user_hours(cls, user_id: str, start_date: Optional[str] = None, end_date: Optional[str] = None) -> Dict[str, Any]:
        """Get total hours worked by a user."""
        db = get_db()
        query = db.table(cls.TABLE).select('hours, billable').eq('user_id', user_id)

        if start_date:
            query = query.gte('date', start_date)
        if end_date:
            query = query.lte('date', end_date)

        result = query.execute()

        total_hours = 0
        billable_hours = 0

        for log in result.data:
            hours = float(log.get('hours', 0))
            total_hours += hours
            if log.get('billable'):
                billable_hours += hours

        return {
            'total_hours': total_hours,
            'billable_hours': billable_hours,
            'non_billable_hours': total_hours - billable_hours
        }
