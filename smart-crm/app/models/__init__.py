"""
Data Models for Smart CRM
"""
from app.models.user import User
from app.models.lead import Lead
from app.models.deal import Deal
from app.models.interaction import Interaction
from app.models.task import Task
from app.models.expense import Expense
from app.models.work_log import WorkLog
from app.models.chat import ChatSession, ChatMessage

__all__ = [
    'User',
    'Lead',
    'Deal',
    'Interaction',
    'Task',
    'Expense',
    'WorkLog',
    'ChatSession',
    'ChatMessage'
]
