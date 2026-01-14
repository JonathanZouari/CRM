"""
Authentication Routes
"""
from datetime import datetime, timedelta
from functools import wraps
from flask import Blueprint, request, jsonify, current_app
import jwt

from app.models.user import User, UserCreate, UserUpdate

auth_bp = Blueprint('auth', __name__)


def create_token(user_id: str, role: str) -> str:
    """Create JWT token."""
    payload = {
        'user_id': user_id,
        'role': role,
        'exp': datetime.utcnow() + timedelta(seconds=current_app.config['JWT_ACCESS_TOKEN_EXPIRES']),
        'iat': datetime.utcnow()
    }
    return jwt.encode(payload, current_app.config['JWT_SECRET_KEY'], algorithm='HS256')


def decode_token(token: str) -> dict:
    """Decode JWT token."""
    try:
        return jwt.decode(token, current_app.config['JWT_SECRET_KEY'], algorithms=['HS256'])
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


def token_required(f):
    """Decorator to require valid JWT token."""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        auth_header = request.headers.get('Authorization')

        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]

        if not token:
            return jsonify({'error': 'Token is missing'}), 401

        payload = decode_token(token)
        if not payload:
            return jsonify({'error': 'Invalid or expired token'}), 401

        # Add user info to request
        request.user_id = payload.get('user_id')
        request.user_role = payload.get('role')

        return f(*args, **kwargs)
    return decorated


def admin_required(f):
    """Decorator to require admin role."""
    @wraps(f)
    @token_required
    def decorated(*args, **kwargs):
        if request.user_role != 'admin':
            return jsonify({'error': 'Admin access required'}), 403
        return f(*args, **kwargs)
    return decorated


@auth_bp.route('/login', methods=['POST'])
def login():
    """Login endpoint."""
    data = request.get_json()

    if not data:
        return jsonify({'error': 'No data provided'}), 400

    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({'error': 'Email and password are required'}), 400

    user = User.authenticate(email, password)
    if not user:
        return jsonify({'error': 'Invalid email or password'}), 401

    token = create_token(user['id'], user.get('role', 'representative'))

    return jsonify({
        'token': token,
        'user': user
    })


@auth_bp.route('/logout', methods=['POST'])
@token_required
def logout():
    """Logout endpoint (client should discard token)."""
    return jsonify({'message': 'Logged out successfully'})


@auth_bp.route('/me', methods=['GET'])
@token_required
def get_current_user():
    """Get current user info."""
    user = User.get_by_id(request.user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404

    # Remove sensitive data
    user.pop('password_hash', None)
    return jsonify(user)


@auth_bp.route('/register', methods=['POST'])
@admin_required
def register():
    """Register new user (admin only)."""
    data = request.get_json()

    if not data:
        return jsonify({'error': 'No data provided'}), 400

    # Check if email already exists
    existing = User.get_by_email(data.get('email', ''))
    if existing:
        return jsonify({'error': 'Email already registered'}), 400

    try:
        user_data = UserCreate(**data)
        user = User.create(user_data)

        if user:
            user.pop('password_hash', None)
            return jsonify(user), 201
        return jsonify({'error': 'Failed to create user'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@auth_bp.route('/users', methods=['GET'])
@admin_required
def list_users():
    """List all users (admin only)."""
    users = User.get_all()
    for user in users:
        user.pop('password_hash', None)
    return jsonify(users)


@auth_bp.route('/users/<user_id>', methods=['PUT'])
@token_required
def update_user(user_id):
    """Update user profile."""
    # Users can only update their own profile, admins can update anyone
    if request.user_id != user_id and request.user_role != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403

    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400

    try:
        user_data = UserUpdate(**data)
        user = User.update(user_id, user_data)

        if user:
            user.pop('password_hash', None)
            return jsonify(user)
        return jsonify({'error': 'User not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@auth_bp.route('/users/<user_id>', methods=['DELETE'])
@admin_required
def delete_user(user_id):
    """Delete user (admin only)."""
    if User.delete(user_id):
        return jsonify({'message': 'User deleted successfully'})
    return jsonify({'error': 'User not found'}), 404
