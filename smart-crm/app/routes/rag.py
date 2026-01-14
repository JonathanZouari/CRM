"""
RAG Query Routes
"""
from flask import Blueprint, request, jsonify

from app.routes.auth import token_required

rag_bp = Blueprint('rag', __name__)


@rag_bp.route('/query', methods=['POST'])
@token_required
def query_rag():
    """Query CRM data using natural language."""
    data = request.get_json()

    if not data or 'question' not in data:
        return jsonify({'error': 'Question is required'}), 400

    question = data['question']

    try:
        from app.crews.rag_crew import query_crm_data

        # Get user context
        user_context = {
            'user_id': request.user_id,
            'user_role': request.user_role
        }

        response = query_crm_data(question, user_context)

        return jsonify({
            'question': question,
            'answer': response
        })

    except Exception as e:
        return jsonify({'error': f'Query failed: {str(e)}'}), 500


@rag_bp.route('/index/refresh', methods=['POST'])
@token_required
def refresh_index():
    """Refresh the vector store index with current CRM data."""
    try:
        from app.services.vector_store import get_vector_store
        from app.models.lead import Lead
        from app.models.deal import Deal
        from app.models.interaction import Interaction

        vector_store = get_vector_store()

        # Index all leads
        leads = Lead.get_all(limit=1000)
        vector_store.index_all_leads(leads)

        # Index all deals
        deals = Deal.get_all(limit=1000)
        vector_store.index_all_deals(deals)

        # Index recent interactions
        interactions = Interaction.get_recent(limit=500)
        vector_store.index_all_interactions(interactions)

        return jsonify({
            'message': 'Index refreshed successfully',
            'indexed': {
                'leads': len(leads),
                'deals': len(deals),
                'interactions': len(interactions)
            }
        })

    except Exception as e:
        return jsonify({'error': f'Index refresh failed: {str(e)}'}), 500
