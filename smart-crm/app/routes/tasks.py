"""
Task Management Routes
"""
from flask import Blueprint, request, jsonify

from app.models.task import Task, TaskCreate, TaskUpdate
from app.routes.auth import token_required

tasks_bp = Blueprint('tasks', __name__)


@tasks_bp.route('', methods=['GET'])
@token_required
def get_tasks():
    """Get all tasks with optional filters."""
    assigned_to = request.args.get('assigned_to')
    status = request.args.get('status')
    priority = request.args.get('priority')
    limit = request.args.get('limit', 100, type=int)
    offset = request.args.get('offset', 0, type=int)

    # For non-admin users, default to their own tasks
    if request.user_role != 'admin' and not assigned_to:
        if request.args.get('all') != 'true':
            assigned_to = request.user_id

    tasks = Task.get_all(
        assigned_to=assigned_to,
        status=status,
        priority=priority,
        limit=limit,
        offset=offset
    )

    return jsonify(tasks)


@tasks_bp.route('/due-today', methods=['GET'])
@token_required
def get_due_today():
    """Get tasks due today."""
    user_id = request.args.get('user_id') or request.user_id
    tasks = Task.get_due_today(user_id=user_id)
    return jsonify(tasks)


@tasks_bp.route('/overdue', methods=['GET'])
@token_required
def get_overdue():
    """Get overdue tasks."""
    user_id = request.args.get('user_id') or request.user_id
    tasks = Task.get_overdue(user_id=user_id)
    return jsonify(tasks)


@tasks_bp.route('/this-week', methods=['GET'])
@token_required
def get_this_week():
    """Get tasks due this week."""
    user_id = request.args.get('user_id') or request.user_id
    tasks = Task.get_this_week(user_id=user_id)
    return jsonify(tasks)


@tasks_bp.route('/stats', methods=['GET'])
@token_required
def get_task_stats():
    """Get task statistics."""
    user_id = request.args.get('user_id')
    if request.user_role != 'admin':
        user_id = request.user_id
    stats = Task.get_stats(user_id=user_id)
    return jsonify(stats)


@tasks_bp.route('/<task_id>', methods=['GET'])
@token_required
def get_task(task_id):
    """Get a specific task."""
    task = Task.get_by_id(task_id)
    if not task:
        return jsonify({'error': 'Task not found'}), 404
    return jsonify(task)


@tasks_bp.route('', methods=['POST'])
@token_required
def create_task():
    """Create a new task."""
    data = request.get_json()

    if not data:
        return jsonify({'error': 'No data provided'}), 400

    # Set assigned_to to current user if not provided
    if not data.get('assigned_to'):
        data['assigned_to'] = request.user_id

    try:
        task_data = TaskCreate(**data)
        task = Task.create(task_data)

        if task:
            return jsonify(task), 201
        return jsonify({'error': 'Failed to create task'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@tasks_bp.route('/<task_id>', methods=['PUT'])
@token_required
def update_task(task_id):
    """Update a task."""
    data = request.get_json()

    if not data:
        return jsonify({'error': 'No data provided'}), 400

    try:
        task_data = TaskUpdate(**data)
        task = Task.update(task_id, task_data)

        if task:
            return jsonify(task)
        return jsonify({'error': 'Task not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@tasks_bp.route('/<task_id>/status', methods=['PATCH'])
@token_required
def update_task_status(task_id):
    """Update task status."""
    data = request.get_json()

    if not data or 'status' not in data:
        return jsonify({'error': 'Status is required'}), 400

    task = Task.update_status(task_id, data['status'])
    if task:
        return jsonify(task)
    return jsonify({'error': 'Task not found'}), 404


@tasks_bp.route('/<task_id>/handle', methods=['PATCH'])
@token_required
def mark_task_handled(task_id):
    """Mark task as handled."""
    task = Task.mark_as_handled(task_id)
    if task:
        return jsonify(task)
    return jsonify({'error': 'Task not found'}), 404


@tasks_bp.route('/<task_id>', methods=['DELETE'])
@token_required
def delete_task(task_id):
    """Delete a task."""
    if Task.delete(task_id):
        return jsonify({'message': 'Task deleted successfully'})
    return jsonify({'error': 'Task not found'}), 404
