"""
Chat Session and Message Models
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel

from app.models.base import get_db


class ChatSessionCreate(BaseModel):
    """Schema for creating a chat session."""
    visitor_id: Optional[str] = None
    visitor_name: Optional[str] = None
    visitor_email: Optional[str] = None
    visitor_company: Optional[str] = None
    current_mode: str = 'service'


class ChatSessionUpdate(BaseModel):
    """Schema for updating a chat session."""
    visitor_name: Optional[str] = None
    visitor_email: Optional[str] = None
    visitor_company: Optional[str] = None
    current_mode: Optional[str] = None
    status: Optional[str] = None


class ChatMessageCreate(BaseModel):
    """Schema for creating a chat message."""
    session_id: str
    role: str  # 'user', 'assistant', 'system'
    content: str
    mode: Optional[str] = None


class ChatSession:
    """Chat session model with database operations."""

    TABLE = 'chat_sessions'

    @classmethod
    def create(cls, session_data: ChatSessionCreate) -> Dict[str, Any]:
        """Create a new chat session."""
        db = get_db()
        data = {k: v for k, v in session_data.model_dump().items() if v is not None}

        result = db.table(cls.TABLE).insert(data).execute()
        return result.data[0] if result.data else None

    @classmethod
    def get_by_id(cls, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session by ID."""
        db = get_db()
        result = db.table(cls.TABLE).select('*').eq('id', session_id).execute()
        return result.data[0] if result.data else None

    @classmethod
    def get_by_visitor(cls, visitor_id: str) -> List[Dict[str, Any]]:
        """Get sessions by visitor ID."""
        db = get_db()
        result = db.table(cls.TABLE).select('*').eq('visitor_id', visitor_id).order('created_at', desc=True).execute()
        return result.data

    @classmethod
    def get_active(cls) -> List[Dict[str, Any]]:
        """Get active chat sessions."""
        db = get_db()
        result = db.table(cls.TABLE).select('*').eq('status', 'active').order('updated_at', desc=True).execute()
        return result.data

    @classmethod
    def get_escalated(cls) -> List[Dict[str, Any]]:
        """Get escalated chat sessions."""
        db = get_db()
        result = db.table(cls.TABLE).select('*').eq('status', 'escalated').order('updated_at', desc=True).execute()
        return result.data

    @classmethod
    def update(cls, session_id: str, session_data: ChatSessionUpdate) -> Optional[Dict[str, Any]]:
        """Update a chat session."""
        db = get_db()
        data = {k: v for k, v in session_data.model_dump().items() if v is not None}

        if not data:
            return cls.get_by_id(session_id)

        result = db.table(cls.TABLE).update(data).eq('id', session_id).execute()
        return result.data[0] if result.data else None

    @classmethod
    def change_mode(cls, session_id: str, mode: str) -> Optional[Dict[str, Any]]:
        """Change chat mode."""
        return cls.update(session_id, ChatSessionUpdate(current_mode=mode))

    @classmethod
    def escalate(cls, session_id: str) -> Optional[Dict[str, Any]]:
        """Escalate session to human."""
        return cls.update(session_id, ChatSessionUpdate(status='escalated'))

    @classmethod
    def close(cls, session_id: str) -> Optional[Dict[str, Any]]:
        """Close a chat session."""
        return cls.update(session_id, ChatSessionUpdate(status='closed'))


class ChatMessage:
    """Chat message model with database operations."""

    TABLE = 'chat_messages'

    @classmethod
    def create(cls, message_data: ChatMessageCreate) -> Dict[str, Any]:
        """Create a new chat message."""
        db = get_db()
        data = message_data.model_dump()

        result = db.table(cls.TABLE).insert(data).execute()

        # Update session's updated_at
        db.table('chat_sessions').update({
            'updated_at': datetime.now().isoformat()
        }).eq('id', data['session_id']).execute()

        return result.data[0] if result.data else None

    @classmethod
    def get_by_session(cls, session_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Get messages for a session."""
        db = get_db()
        result = db.table(cls.TABLE).select('*').eq('session_id', session_id).order('created_at').limit(limit).execute()
        return result.data

    @classmethod
    def get_history_for_llm(cls, session_id: str, limit: int = 20) -> List[Dict[str, str]]:
        """Get message history formatted for LLM context."""
        messages = cls.get_by_session(session_id, limit=limit)
        return [
            {'role': msg['role'], 'content': msg['content']}
            for msg in messages
            if msg['role'] in ('user', 'assistant')
        ]

    @classmethod
    def delete_by_session(cls, session_id: str) -> bool:
        """Delete all messages in a session."""
        db = get_db()
        result = db.table(cls.TABLE).delete().eq('session_id', session_id).execute()
        return True
