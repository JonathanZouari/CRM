"""
User Model
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, EmailStr
import bcrypt

from app.models.base import get_db


class UserCreate(BaseModel):
    """Schema for creating a user."""
    email: str
    password: str
    full_name: str
    role: str = 'representative'
    phone: Optional[str] = None
    avatar_url: Optional[str] = None
    target_monthly_revenue: float = 0
    target_monthly_deals: int = 0
    hourly_rate: float = 0


class UserUpdate(BaseModel):
    """Schema for updating a user."""
    full_name: Optional[str] = None
    phone: Optional[str] = None
    avatar_url: Optional[str] = None
    target_monthly_revenue: Optional[float] = None
    target_monthly_deals: Optional[int] = None
    hourly_rate: Optional[float] = None
    is_active: Optional[bool] = None


class User:
    """User model with database operations."""

    TABLE = 'users'

    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a password using bcrypt."""
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    @staticmethod
    def verify_password(password: str, password_hash: str) -> bool:
        """Verify a password against its hash."""
        return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))

    @classmethod
    def create(cls, user_data: UserCreate) -> Dict[str, Any]:
        """Create a new user."""
        db = get_db()
        data = user_data.model_dump()
        data['password_hash'] = cls.hash_password(data.pop('password'))

        result = db.table(cls.TABLE).insert(data).execute()
        return result.data[0] if result.data else None

    @classmethod
    def get_by_id(cls, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user by ID."""
        db = get_db()
        result = db.table(cls.TABLE).select('*').eq('id', user_id).execute()
        return result.data[0] if result.data else None

    @classmethod
    def get_by_email(cls, email: str) -> Optional[Dict[str, Any]]:
        """Get user by email."""
        db = get_db()
        result = db.table(cls.TABLE).select('*').eq('email', email).execute()
        return result.data[0] if result.data else None

    @classmethod
    def get_all(cls, active_only: bool = True) -> List[Dict[str, Any]]:
        """Get all users."""
        db = get_db()
        query = db.table(cls.TABLE).select('*')
        if active_only:
            query = query.eq('is_active', True)
        result = query.execute()
        return result.data

    @classmethod
    def update(cls, user_id: str, user_data: UserUpdate) -> Optional[Dict[str, Any]]:
        """Update a user."""
        db = get_db()
        data = {k: v for k, v in user_data.model_dump().items() if v is not None}

        if not data:
            return cls.get_by_id(user_id)

        result = db.table(cls.TABLE).update(data).eq('id', user_id).execute()
        return result.data[0] if result.data else None

    @classmethod
    def delete(cls, user_id: str) -> bool:
        """Soft delete a user (set is_active to False)."""
        db = get_db()
        result = db.table(cls.TABLE).update({'is_active': False}).eq('id', user_id).execute()
        return len(result.data) > 0

    @classmethod
    def authenticate(cls, email: str, password: str) -> Optional[Dict[str, Any]]:
        """Authenticate user with email and password."""
        user = cls.get_by_email(email)
        if user and user.get('is_active') and cls.verify_password(password, user.get('password_hash', '')):
            # Remove password_hash from response
            user.pop('password_hash', None)
            return user
        return None
