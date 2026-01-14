"""
Task Model
"""
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from pydantic import BaseModel

from app.models.base import get_db


class TaskCreate(BaseModel):
    """Schema for creating a task."""
    title: str
    due_date: str
    assigned_to: Optional[str] = None
    lead_id: Optional[str] = None
    deal_id: Optional[str] = None
    description: Optional[str] = None
    priority: str = 'medium'
    requires_urgent_action: bool = False


class TaskUpdate(BaseModel):
    """Schema for updating a task."""
    title: Optional[str] = None
    description: Optional[str] = None
    due_date: Optional[str] = None
    priority: Optional[str] = None
    status: Optional[str] = None
    is_handled: Optional[bool] = None
    requires_urgent_action: Optional[bool] = None


class Task:
    """Task model with database operations."""

    TABLE = 'tasks'

    @classmethod
    def create(cls, task_data: TaskCreate) -> Dict[str, Any]:
        """Create a new task."""
        db = get_db()
        data = {k: v for k, v in task_data.model_dump().items() if v is not None}

        result = db.table(cls.TABLE).insert(data).execute()
        return result.data[0] if result.data else None

    @classmethod
    def get_by_id(cls, task_id: str) -> Optional[Dict[str, Any]]:
        """Get task by ID."""
        db = get_db()
        result = db.table(cls.TABLE).select(
            '*, leads(id, company_name, contact_name), deals(id, title), users!assigned_to(id, full_name)'
        ).eq('id', task_id).execute()
        return result.data[0] if result.data else None

    @classmethod
    def get_all(
        cls,
        assigned_to: Optional[str] = None,
        status: Optional[str] = None,
        priority: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Get all tasks with optional filters."""
        db = get_db()
        query = db.table(cls.TABLE).select(
            '*, leads(id, company_name, contact_name), deals(id, title), users!assigned_to(id, full_name)'
        )

        if assigned_to:
            query = query.eq('assigned_to', assigned_to)
        if status:
            query = query.eq('status', status)
        if priority:
            query = query.eq('priority', priority)

        query = query.order('due_date').range(offset, offset + limit - 1)
        result = query.execute()
        return result.data

    @classmethod
    def get_due_today(cls, user_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get tasks due today."""
        db = get_db()
        today = datetime.now().date().isoformat()
        tomorrow = (datetime.now().date() + timedelta(days=1)).isoformat()

        query = db.table(cls.TABLE).select(
            '*, leads(id, company_name, contact_name), deals(id, title)'
        ).gte('due_date', today).lt('due_date', tomorrow).neq('status', 'completed').neq('status', 'cancelled')

        if user_id:
            query = query.eq('assigned_to', user_id)

        result = query.order('due_date').execute()
        return result.data

    @classmethod
    def get_overdue(cls, user_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get overdue tasks."""
        db = get_db()
        today = datetime.now().date().isoformat()

        query = db.table(cls.TABLE).select(
            '*, leads(id, company_name, contact_name), deals(id, title)'
        ).lt('due_date', today).neq('status', 'completed').neq('status', 'cancelled')

        if user_id:
            query = query.eq('assigned_to', user_id)

        result = query.order('due_date').execute()
        return result.data

    @classmethod
    def get_this_week(cls, user_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get tasks due this week."""
        db = get_db()
        today = datetime.now().date()
        week_end = (today + timedelta(days=7)).isoformat()

        query = db.table(cls.TABLE).select(
            '*, leads(id, company_name, contact_name), deals(id, title)'
        ).lte('due_date', week_end).neq('status', 'completed').neq('status', 'cancelled')

        if user_id:
            query = query.eq('assigned_to', user_id)

        result = query.order('due_date').execute()
        return result.data

    @classmethod
    def update(cls, task_id: str, task_data: TaskUpdate) -> Optional[Dict[str, Any]]:
        """Update a task."""
        db = get_db()
        data = {k: v for k, v in task_data.model_dump().items() if v is not None}

        if not data:
            return cls.get_by_id(task_id)

        # Handle completion
        if data.get('status') == 'completed':
            data['completed_at'] = datetime.now().isoformat()
            data['is_handled'] = True

        result = db.table(cls.TABLE).update(data).eq('id', task_id).execute()
        return result.data[0] if result.data else None

    @classmethod
    def update_status(cls, task_id: str, status: str) -> Optional[Dict[str, Any]]:
        """Update task status."""
        return cls.update(task_id, TaskUpdate(status=status))

    @classmethod
    def mark_as_handled(cls, task_id: str) -> Optional[Dict[str, Any]]:
        """Mark task as handled."""
        return cls.update(task_id, TaskUpdate(is_handled=True))

    @classmethod
    def delete(cls, task_id: str) -> bool:
        """Delete a task."""
        db = get_db()
        result = db.table(cls.TABLE).delete().eq('id', task_id).execute()
        return len(result.data) > 0

    @classmethod
    def get_stats(cls, user_id: Optional[str] = None) -> Dict[str, Any]:
        """Get task statistics."""
        db = get_db()
        query = db.table(cls.TABLE).select('status, priority, due_date')

        if user_id:
            query = query.eq('assigned_to', user_id)

        result = query.execute()

        today = datetime.now().date().isoformat()
        stats = {
            'total': len(result.data),
            'pending': 0,
            'in_progress': 0,
            'completed': 0,
            'overdue': 0,
            'urgent': 0
        }

        for task in result.data:
            status = task.get('status', 'pending')
            stats[status] = stats.get(status, 0) + 1

            if task.get('priority') == 'urgent' and status not in ('completed', 'cancelled'):
                stats['urgent'] += 1

            if task.get('due_date') and task['due_date'] < today and status not in ('completed', 'cancelled'):
                stats['overdue'] += 1

        return stats
