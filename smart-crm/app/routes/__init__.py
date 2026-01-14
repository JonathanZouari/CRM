"""
API Routes for Smart CRM
"""
from app.routes.auth import auth_bp
from app.routes.leads import leads_bp
from app.routes.deals import deals_bp
from app.routes.tasks import tasks_bp
from app.routes.analytics import analytics_bp
from app.routes.chat import chat_bp

__all__ = [
    'auth_bp',
    'leads_bp',
    'deals_bp',
    'tasks_bp',
    'analytics_bp',
    'chat_bp'
]
