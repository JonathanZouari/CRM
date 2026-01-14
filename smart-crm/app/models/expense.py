"""
Expense Model
"""
from datetime import datetime, date
from typing import Optional, List, Dict, Any
from pydantic import BaseModel

from app.models.base import get_db


class ExpenseCreate(BaseModel):
    """Schema for creating an expense."""
    amount: float
    date: str
    category: str  # 'fixed' or 'variable'
    type: str  # e.g., 'rent', 'software', 'marketing'
    user_id: Optional[str] = None
    description: Optional[str] = None
    is_recurring: bool = False
    recurring_frequency: Optional[str] = None


class ExpenseUpdate(BaseModel):
    """Schema for updating an expense."""
    amount: Optional[float] = None
    date: Optional[str] = None
    category: Optional[str] = None
    type: Optional[str] = None
    description: Optional[str] = None
    is_recurring: Optional[bool] = None
    recurring_frequency: Optional[str] = None


class Expense:
    """Expense model with database operations."""

    TABLE = 'expenses'

    @classmethod
    def create(cls, expense_data: ExpenseCreate) -> Dict[str, Any]:
        """Create a new expense."""
        db = get_db()
        data = {k: v for k, v in expense_data.model_dump().items() if v is not None}

        result = db.table(cls.TABLE).insert(data).execute()
        return result.data[0] if result.data else None

    @classmethod
    def get_by_id(cls, expense_id: str) -> Optional[Dict[str, Any]]:
        """Get expense by ID."""
        db = get_db()
        result = db.table(cls.TABLE).select('*, users(id, full_name)').eq('id', expense_id).execute()
        return result.data[0] if result.data else None

    @classmethod
    def get_all(
        cls,
        category: Optional[str] = None,
        user_id: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Get all expenses with optional filters."""
        db = get_db()
        query = db.table(cls.TABLE).select('*, users(id, full_name)')

        if category:
            query = query.eq('category', category)
        if user_id:
            query = query.eq('user_id', user_id)
        if start_date:
            query = query.gte('date', start_date)
        if end_date:
            query = query.lte('date', end_date)

        query = query.order('date', desc=True).range(offset, offset + limit - 1)
        result = query.execute()
        return result.data

    @classmethod
    def update(cls, expense_id: str, expense_data: ExpenseUpdate) -> Optional[Dict[str, Any]]:
        """Update an expense."""
        db = get_db()
        data = {k: v for k, v in expense_data.model_dump().items() if v is not None}

        if not data:
            return cls.get_by_id(expense_id)

        result = db.table(cls.TABLE).update(data).eq('id', expense_id).execute()
        return result.data[0] if result.data else None

    @classmethod
    def delete(cls, expense_id: str) -> bool:
        """Delete an expense."""
        db = get_db()
        result = db.table(cls.TABLE).delete().eq('id', expense_id).execute()
        return len(result.data) > 0

    @classmethod
    def get_totals(cls, start_date: Optional[str] = None, end_date: Optional[str] = None) -> Dict[str, Any]:
        """Get expense totals by category."""
        db = get_db()
        query = db.table(cls.TABLE).select('category, type, amount')

        if start_date:
            query = query.gte('date', start_date)
        if end_date:
            query = query.lte('date', end_date)

        result = query.execute()

        totals = {
            'fixed': 0,
            'variable': 0,
            'total': 0,
            'by_type': {}
        }

        for expense in result.data:
            amount = float(expense.get('amount', 0))
            category = expense.get('category', 'variable')
            expense_type = expense.get('type', 'other')

            totals['total'] += amount
            totals[category] = totals.get(category, 0) + amount

            if expense_type not in totals['by_type']:
                totals['by_type'][expense_type] = 0
            totals['by_type'][expense_type] += amount

        return totals
