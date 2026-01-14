"""
Deal Management Routes
"""
from flask import Blueprint, request, jsonify

from app.models.deal import Deal, DealCreate, DealUpdate
from app.models.interaction import Interaction, InteractionCreate
from app.models.work_log import WorkLog, WorkLogCreate, WorkLogUpdate
from app.routes.auth import token_required

deals_bp = Blueprint('deals', __name__)


@deals_bp.route('', methods=['GET'])
@token_required
def get_deals():
    """Get all deals with optional filters."""
    stage = request.args.get('stage')
    assigned_to = request.args.get('assigned_to')
    lead_id = request.args.get('lead_id')
    limit = request.args.get('limit', 100, type=int)
    offset = request.args.get('offset', 0, type=int)
    order_by = request.args.get('order_by', 'created_at')
    ascending = request.args.get('ascending', 'false').lower() == 'true'

    # For non-admin users, optionally filter by their own deals
    if request.user_role != 'admin' and request.args.get('my_deals') == 'true':
        assigned_to = request.user_id

    deals = Deal.get_all(
        stage=stage,
        assigned_to=assigned_to,
        lead_id=lead_id,
        limit=limit,
        offset=offset,
        order_by=order_by,
        ascending=ascending
    )

    return jsonify(deals)


@deals_bp.route('/pipeline', methods=['GET'])
@token_required
def get_pipeline():
    """Get deals grouped by stage (for Kanban view)."""
    pipeline = Deal.get_by_stage()
    return jsonify(pipeline)


@deals_bp.route('/stats', methods=['GET'])
@token_required
def get_deal_stats():
    """Get pipeline statistics."""
    stats = Deal.get_pipeline_stats()
    return jsonify(stats)


@deals_bp.route('/revenue', methods=['GET'])
@token_required
def get_revenue_stats():
    """Get revenue statistics."""
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    stats = Deal.get_revenue_stats(start_date=start_date, end_date=end_date)
    return jsonify(stats)


@deals_bp.route('/<deal_id>', methods=['GET'])
@token_required
def get_deal(deal_id):
    """Get a specific deal."""
    deal = Deal.get_by_id(deal_id)
    if not deal:
        return jsonify({'error': 'Deal not found'}), 404
    return jsonify(deal)


@deals_bp.route('', methods=['POST'])
@token_required
def create_deal():
    """Create a new deal."""
    data = request.get_json()

    if not data:
        return jsonify({'error': 'No data provided'}), 400

    # Set assigned_to to current user if not provided
    if not data.get('assigned_to'):
        data['assigned_to'] = request.user_id

    try:
        deal_data = DealCreate(**data)
        deal = Deal.create(deal_data)

        if deal:
            return jsonify(deal), 201
        return jsonify({'error': 'Failed to create deal'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@deals_bp.route('/<deal_id>', methods=['PUT'])
@token_required
def update_deal(deal_id):
    """Update a deal."""
    data = request.get_json()

    if not data:
        return jsonify({'error': 'No data provided'}), 400

    try:
        deal_data = DealUpdate(**data)
        deal = Deal.update(deal_id, deal_data)

        if deal:
            return jsonify(deal)
        return jsonify({'error': 'Deal not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@deals_bp.route('/<deal_id>/stage', methods=['PATCH'])
@token_required
def update_deal_stage(deal_id):
    """Update deal stage (for drag-and-drop)."""
    data = request.get_json()

    if not data or 'stage' not in data:
        return jsonify({'error': 'Stage is required'}), 400

    deal = Deal.update_stage(deal_id, data['stage'])
    if deal:
        return jsonify(deal)
    return jsonify({'error': 'Deal not found'}), 404


@deals_bp.route('/<deal_id>', methods=['DELETE'])
@token_required
def delete_deal(deal_id):
    """Delete a deal."""
    if Deal.delete(deal_id):
        return jsonify({'message': 'Deal deleted successfully'})
    return jsonify({'error': 'Deal not found'}), 404


@deals_bp.route('/<deal_id>/interactions', methods=['GET'])
@token_required
def get_deal_interactions(deal_id):
    """Get interactions for a deal."""
    deal = Deal.get_by_id(deal_id)
    if not deal:
        return jsonify({'error': 'Deal not found'}), 404

    interactions = Interaction.get_by_deal(deal_id)
    return jsonify(interactions)


@deals_bp.route('/<deal_id>/interactions', methods=['POST'])
@token_required
def add_deal_interaction(deal_id):
    """Add an interaction to a deal."""
    deal = Deal.get_by_id(deal_id)
    if not deal:
        return jsonify({'error': 'Deal not found'}), 404

    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400

    data['deal_id'] = deal_id
    data['user_id'] = request.user_id

    # Also associate with lead if deal has a lead
    if deal.get('lead_id'):
        data['lead_id'] = deal['lead_id']

    try:
        interaction_data = InteractionCreate(**data)
        interaction = Interaction.create(interaction_data)

        if interaction:
            return jsonify(interaction), 201
        return jsonify({'error': 'Failed to create interaction'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@deals_bp.route('/<deal_id>/work-logs', methods=['GET'])
@token_required
def get_deal_work_logs(deal_id):
    """Get work logs for a deal."""
    deal = Deal.get_by_id(deal_id)
    if not deal:
        return jsonify({'error': 'Deal not found'}), 404

    logs = WorkLog.get_by_deal(deal_id)
    return jsonify(logs)


@deals_bp.route('/<deal_id>/work-logs', methods=['POST'])
@token_required
def add_work_log(deal_id):
    """Add a work log to a deal."""
    deal = Deal.get_by_id(deal_id)
    if not deal:
        return jsonify({'error': 'Deal not found'}), 404

    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400

    data['deal_id'] = deal_id
    data['user_id'] = request.user_id

    try:
        log_data = WorkLogCreate(**data)
        log = WorkLog.create(log_data)

        if log:
            return jsonify(log), 201
        return jsonify({'error': 'Failed to create work log'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 400
