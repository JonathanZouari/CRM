"""
Lead Management Routes
"""
from flask import Blueprint, request, jsonify

from app.models.lead import Lead, LeadCreate, LeadUpdate
from app.models.interaction import Interaction, InteractionCreate
from app.routes.auth import token_required

leads_bp = Blueprint('leads', __name__)


@leads_bp.route('', methods=['GET'])
@token_required
def get_leads():
    """Get all leads with optional filters."""
    # Parse query parameters
    status = request.args.get('status')
    source = request.args.get('source')
    assigned_to = request.args.get('assigned_to')
    min_score = request.args.get('min_score', type=float)
    limit = request.args.get('limit', 100, type=int)
    offset = request.args.get('offset', 0, type=int)
    order_by = request.args.get('order_by', 'created_at')
    ascending = request.args.get('ascending', 'false').lower() == 'true'

    # For non-admin users, optionally filter by their own leads
    if request.user_role != 'admin' and request.args.get('my_leads') == 'true':
        assigned_to = request.user_id

    leads = Lead.get_all(
        status=status,
        source=source,
        assigned_to=assigned_to,
        min_score=min_score,
        limit=limit,
        offset=offset,
        order_by=order_by,
        ascending=ascending
    )

    return jsonify(leads)


@leads_bp.route('/top-scored', methods=['GET'])
@token_required
def get_top_scored_leads():
    """Get top scored leads."""
    limit = request.args.get('limit', 10, type=int)
    leads = Lead.get_top_scored(limit=limit)
    return jsonify(leads)


@leads_bp.route('/stats', methods=['GET'])
@token_required
def get_lead_stats():
    """Get lead statistics."""
    stats = Lead.get_stats()
    return jsonify(stats)


@leads_bp.route('/check-duplicate', methods=['GET'])
@token_required
def check_duplicate():
    """Check for potential duplicate leads."""
    email = request.args.get('email')
    phone = request.args.get('phone')
    company_name = request.args.get('company_name')

    if not email and not phone and not company_name:
        return jsonify({'error': 'At least one search parameter required'}), 400

    duplicates = Lead.check_duplicate(email=email, phone=phone, company_name=company_name)
    return jsonify({
        'has_duplicates': len(duplicates) > 0,
        'duplicates': duplicates
    })


@leads_bp.route('/<lead_id>', methods=['GET'])
@token_required
def get_lead(lead_id):
    """Get a specific lead."""
    lead = Lead.get_by_id(lead_id)
    if not lead:
        return jsonify({'error': 'Lead not found'}), 404
    return jsonify(lead)


@leads_bp.route('', methods=['POST'])
@token_required
def create_lead():
    """Create a new lead."""
    data = request.get_json()

    if not data:
        return jsonify({'error': 'No data provided'}), 400

    # Set assigned_to to current user if not provided
    if not data.get('assigned_to'):
        data['assigned_to'] = request.user_id

    try:
        lead_data = LeadCreate(**data)
        lead = Lead.create(lead_data)

        if lead:
            # Trigger lead scoring asynchronously (in real app, use celery or similar)
            # For now, we'll calculate score synchronously if enough data exists
            if lead.get('interest_level') and lead.get('ai_readiness_score'):
                from app.services.lead_scoring import calculate_lead_score
                score, explanation = calculate_lead_score(lead)
                Lead.update_score(lead['id'], score, explanation)
                lead['lead_score'] = score
                lead['lead_score_explanation'] = explanation

            return jsonify(lead), 201
        return jsonify({'error': 'Failed to create lead'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@leads_bp.route('/<lead_id>', methods=['PUT'])
@token_required
def update_lead(lead_id):
    """Update a lead."""
    data = request.get_json()

    if not data:
        return jsonify({'error': 'No data provided'}), 400

    try:
        lead_data = LeadUpdate(**data)
        lead = Lead.update(lead_id, lead_data)

        if lead:
            # Recalculate score if relevant fields changed
            score_fields = {'interest_level', 'ai_readiness_score', 'business_size', 'estimated_budget', 'source'}
            if score_fields & set(data.keys()):
                from app.services.lead_scoring import calculate_lead_score
                full_lead = Lead.get_by_id(lead_id)
                if full_lead:
                    score, explanation = calculate_lead_score(full_lead)
                    Lead.update_score(lead_id, score, explanation)
                    lead['lead_score'] = score
                    lead['lead_score_explanation'] = explanation

            return jsonify(lead)
        return jsonify({'error': 'Lead not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@leads_bp.route('/<lead_id>', methods=['DELETE'])
@token_required
def delete_lead(lead_id):
    """Delete a lead."""
    if Lead.delete(lead_id):
        return jsonify({'message': 'Lead deleted successfully'})
    return jsonify({'error': 'Lead not found'}), 404


@leads_bp.route('/<lead_id>/score', methods=['POST'])
@token_required
def recalculate_score(lead_id):
    """Recalculate lead score."""
    lead = Lead.get_by_id(lead_id)
    if not lead:
        return jsonify({'error': 'Lead not found'}), 404

    from app.services.lead_scoring import calculate_lead_score
    score, explanation = calculate_lead_score(lead)
    updated = Lead.update_score(lead_id, score, explanation)

    return jsonify({
        'lead_id': lead_id,
        'score': score,
        'explanation': explanation
    })


@leads_bp.route('/<lead_id>/interactions', methods=['GET'])
@token_required
def get_lead_interactions(lead_id):
    """Get interactions for a lead."""
    lead = Lead.get_by_id(lead_id)
    if not lead:
        return jsonify({'error': 'Lead not found'}), 404

    interactions = Interaction.get_by_lead(lead_id)
    return jsonify(interactions)


@leads_bp.route('/<lead_id>/interactions', methods=['POST'])
@token_required
def add_lead_interaction(lead_id):
    """Add an interaction to a lead."""
    lead = Lead.get_by_id(lead_id)
    if not lead:
        return jsonify({'error': 'Lead not found'}), 404

    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400

    data['lead_id'] = lead_id
    data['user_id'] = request.user_id

    try:
        interaction_data = InteractionCreate(**data)
        interaction = Interaction.create(interaction_data)

        if interaction:
            return jsonify(interaction), 201
        return jsonify({'error': 'Failed to create interaction'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 400
