"""
Chat Routes for Customer Chatbot
"""
from flask import Blueprint, request, jsonify
import uuid

from app.models.chat import ChatSession, ChatSessionCreate, ChatSessionUpdate, ChatMessage, ChatMessageCreate
from app.routes.auth import token_required

chat_bp = Blueprint('chat', __name__)


@chat_bp.route('/session', methods=['POST'])
def create_session():
    """Create a new chat session (public endpoint)."""
    data = request.get_json() or {}

    # Generate visitor ID if not provided
    if not data.get('visitor_id'):
        data['visitor_id'] = str(uuid.uuid4())

    try:
        session_data = ChatSessionCreate(**data)
        session = ChatSession.create(session_data)

        if session:
            return jsonify(session), 201
        return jsonify({'error': 'Failed to create session'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@chat_bp.route('/session/<session_id>', methods=['GET'])
def get_session(session_id):
    """Get a chat session."""
    session = ChatSession.get_by_id(session_id)
    if not session:
        return jsonify({'error': 'Session not found'}), 404
    return jsonify(session)


@chat_bp.route('/session/<session_id>/mode', methods=['PATCH'])
def change_mode(session_id):
    """Change chat mode."""
    data = request.get_json()

    if not data or 'mode' not in data:
        return jsonify({'error': 'Mode is required'}), 400

    mode = data['mode']
    if mode not in ('service', 'sales', 'consulting'):
        return jsonify({'error': 'Invalid mode'}), 400

    session = ChatSession.change_mode(session_id, mode)
    if session:
        return jsonify(session)
    return jsonify({'error': 'Session not found'}), 404


@chat_bp.route('/session/<session_id>/escalate', methods=['POST'])
def escalate_session(session_id):
    """Escalate session to human."""
    session = ChatSession.escalate(session_id)
    if session:
        return jsonify(session)
    return jsonify({'error': 'Session not found'}), 404


@chat_bp.route('/session/<session_id>/close', methods=['POST'])
def close_session(session_id):
    """Close a chat session."""
    session = ChatSession.close(session_id)
    if session:
        return jsonify(session)
    return jsonify({'error': 'Session not found'}), 404


@chat_bp.route('/session/<session_id>/update', methods=['PATCH'])
def update_session(session_id):
    """Update session info (visitor details)."""
    data = request.get_json()

    if not data:
        return jsonify({'error': 'No data provided'}), 400

    try:
        session_data = ChatSessionUpdate(**data)
        session = ChatSession.update(session_id, session_data)

        if session:
            return jsonify(session)
        return jsonify({'error': 'Session not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@chat_bp.route('/message', methods=['POST'])
def send_message():
    """Send a message and get AI response."""
    data = request.get_json()

    if not data:
        return jsonify({'error': 'No data provided'}), 400

    session_id = data.get('session_id')
    content = data.get('content')

    if not session_id or not content:
        return jsonify({'error': 'session_id and content are required'}), 400

    # Get session to determine mode
    session = ChatSession.get_by_id(session_id)
    if not session:
        return jsonify({'error': 'Session not found'}), 404

    current_mode = session.get('current_mode', 'service')

    # Save user message
    try:
        user_message_data = ChatMessageCreate(
            session_id=session_id,
            role='user',
            content=content,
            mode=current_mode
        )
        user_message = ChatMessage.create(user_message_data)
    except Exception as e:
        return jsonify({'error': f'Failed to save message: {str(e)}'}), 500

    # Get AI response using CrewAI chatbot
    try:
        from app.crews.chatbot_crew import get_chatbot_response

        # Get conversation history
        history = ChatMessage.get_history_for_llm(session_id, limit=10)

        # Get AI response
        ai_response = get_chatbot_response(
            mode=current_mode,
            user_message=content,
            history=history,
            visitor_info={
                'name': session.get('visitor_name'),
                'company': session.get('visitor_company'),
                'email': session.get('visitor_email')
            }
        )

        # Save AI response
        ai_message_data = ChatMessageCreate(
            session_id=session_id,
            role='assistant',
            content=ai_response,
            mode=current_mode
        )
        ai_message = ChatMessage.create(ai_message_data)

        return jsonify({
            'user_message': user_message,
            'ai_response': ai_message
        })

    except Exception as e:
        # If AI fails, return error but keep user message saved
        return jsonify({
            'user_message': user_message,
            'error': f'AI response failed: {str(e)}'
        }), 500


@chat_bp.route('/history/<session_id>', methods=['GET'])
def get_history(session_id):
    """Get chat history for a session."""
    limit = request.args.get('limit', 100, type=int)
    messages = ChatMessage.get_by_session(session_id, limit=limit)
    return jsonify(messages)


# Admin endpoints for managing chats

@chat_bp.route('/sessions/active', methods=['GET'])
@token_required
def get_active_sessions():
    """Get all active chat sessions (requires auth)."""
    sessions = ChatSession.get_active()
    return jsonify(sessions)


@chat_bp.route('/sessions/escalated', methods=['GET'])
@token_required
def get_escalated_sessions():
    """Get all escalated chat sessions (requires auth)."""
    sessions = ChatSession.get_escalated()
    return jsonify(sessions)
