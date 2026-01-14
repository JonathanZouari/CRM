"""
Analytics Routes
"""
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify

from app.models.lead import Lead
from app.models.deal import Deal
from app.models.task import Task
from app.models.expense import Expense
from app.models.work_log import WorkLog
from app.models.user import User
from app.models.interaction import Interaction
from app.routes.auth import token_required, admin_required

analytics_bp = Blueprint('analytics', __name__)


@analytics_bp.route('/dashboard', methods=['GET'])
@token_required
def get_dashboard():
    """Get dashboard data."""
    user_id = request.user_id if request.user_role != 'admin' else request.args.get('user_id')

    # Get current month date range
    today = datetime.now()
    month_start = today.replace(day=1).date().isoformat()
    month_end = today.date().isoformat()

    # Lead stats
    lead_stats = Lead.get_stats()

    # Deal stats
    deal_stats = Deal.get_pipeline_stats()
    revenue_stats = Deal.get_revenue_stats(start_date=month_start, end_date=month_end)

    # Task stats
    task_stats = Task.get_stats(user_id=user_id)
    tasks_due_today = len(Task.get_due_today(user_id=user_id))

    # Calculate conversion rate
    total_leads = lead_stats['total']
    won_leads = lead_stats['by_status'].get('won', 0)
    conversion_rate = (won_leads / total_leads * 100) if total_leads > 0 else 0

    # Recent activity
    recent_interactions = Interaction.get_recent(limit=10)

    return jsonify({
        'kpis': {
            'total_leads': total_leads,
            'leads_this_month': total_leads,  # Should be filtered by month in production
            'conversion_rate': round(conversion_rate, 1),
            'total_revenue': revenue_stats['total_revenue'],
            'active_deals': deal_stats['active_deals'],
            'active_deals_value': deal_stats['total_value'],
            'average_deal_size': revenue_stats['average_deal_size'],
            'tasks_due_today': tasks_due_today,
            'overdue_tasks': task_stats['overdue']
        },
        'lead_stats': lead_stats,
        'deal_stats': deal_stats,
        'task_stats': task_stats,
        'recent_activity': recent_interactions
    })


@analytics_bp.route('/profitability', methods=['GET'])
@token_required
def get_profitability():
    """Calculate profitability."""
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')

    # If no dates provided, use current month
    if not start_date:
        today = datetime.now()
        start_date = today.replace(day=1).date().isoformat()
    if not end_date:
        end_date = datetime.now().date().isoformat()

    # Get revenue from closed deals
    revenue_stats = Deal.get_revenue_stats(start_date=start_date, end_date=end_date)
    total_revenue = revenue_stats['total_revenue']

    # Get expenses
    expense_totals = Expense.get_totals(start_date=start_date, end_date=end_date)
    fixed_costs = expense_totals['fixed']
    variable_costs = expense_totals['variable']

    # Calculate labor costs
    # Get all users' hourly rates and work logs
    users = User.get_all()
    total_labor_cost = 0
    total_hours = 0

    for user in users:
        hourly_rate = float(user.get('hourly_rate', 0))
        if hourly_rate > 0:
            user_hours = WorkLog.get_user_hours(user['id'], start_date=start_date, end_date=end_date)
            billable_hours = user_hours['billable_hours']
            total_labor_cost += billable_hours * hourly_rate
            total_hours += billable_hours

    # Calculate totals
    total_costs = fixed_costs + variable_costs + total_labor_cost
    net_profit = total_revenue - total_costs
    profit_margin = (net_profit / total_revenue * 100) if total_revenue > 0 else 0

    return jsonify({
        'period': {
            'start_date': start_date,
            'end_date': end_date
        },
        'revenue': {
            'total': total_revenue,
            'deal_count': revenue_stats['deal_count'],
            'average_deal_size': revenue_stats['average_deal_size']
        },
        'costs': {
            'fixed': fixed_costs,
            'variable': variable_costs,
            'labor': total_labor_cost,
            'total': total_costs,
            'by_type': expense_totals['by_type']
        },
        'labor': {
            'total_hours': total_hours,
            'total_cost': total_labor_cost
        },
        'profit': {
            'net': net_profit,
            'margin_percent': round(profit_margin, 2)
        }
    })


@analytics_bp.route('/pipeline', methods=['GET'])
@token_required
def get_pipeline_analytics():
    """Get pipeline analytics."""
    pipeline = Deal.get_by_stage()
    stats = Deal.get_pipeline_stats()

    # Calculate stage summaries
    stage_summaries = {}
    for stage, deals in pipeline.items():
        stage_summaries[stage] = {
            'count': len(deals),
            'total_value': sum(float(d.get('value', 0)) for d in deals),
            'weighted_value': sum(float(d.get('value', 0)) * (int(d.get('probability', 0)) / 100) for d in deals)
        }

    return jsonify({
        'pipeline': pipeline,
        'stats': stats,
        'stage_summaries': stage_summaries
    })


@analytics_bp.route('/lead-sources', methods=['GET'])
@token_required
def get_lead_source_analytics():
    """Get lead source effectiveness."""
    lead_stats = Lead.get_stats()

    # Get conversion by source
    source_data = {}
    for source, count in lead_stats['by_source'].items():
        source_data[source] = {
            'total': count,
            'converted': 0,  # Would need to track this separately
            'conversion_rate': 0
        }

    return jsonify({
        'by_source': lead_stats['by_source'],
        'source_effectiveness': source_data
    })


@analytics_bp.route('/representative-performance', methods=['GET'])
@admin_required
def get_representative_performance():
    """Get representative performance metrics (admin only)."""
    users = User.get_all()
    performance = []

    for user in users:
        if user.get('role') != 'admin':
            user_id = user['id']

            # Get user's deals
            user_deals = Deal.get_all(assigned_to=user_id)
            won_deals = [d for d in user_deals if d.get('stage') == 'closed_won']
            total_revenue = sum(float(d.get('value', 0)) for d in won_deals)

            # Get user's leads
            user_leads = Lead.get_all(assigned_to=user_id)
            total_leads = len(user_leads)
            converted_leads = len([l for l in user_leads if l.get('status') == 'won'])

            # Get task stats
            task_stats = Task.get_stats(user_id=user_id)

            performance.append({
                'user_id': user_id,
                'name': user.get('full_name'),
                'email': user.get('email'),
                'metrics': {
                    'total_leads': total_leads,
                    'converted_leads': converted_leads,
                    'conversion_rate': (converted_leads / total_leads * 100) if total_leads > 0 else 0,
                    'total_deals': len(user_deals),
                    'won_deals': len(won_deals),
                    'total_revenue': total_revenue,
                    'target_revenue': float(user.get('target_monthly_revenue', 0)),
                    'target_deals': user.get('target_monthly_deals', 0),
                    'tasks_completed': task_stats['completed'],
                    'tasks_pending': task_stats['pending']
                }
            })

    return jsonify(performance)


@analytics_bp.route('/revenue-chart', methods=['GET'])
@token_required
def get_revenue_chart_data():
    """Get revenue data for charts."""
    # Get last 6 months of data
    months_data = []
    today = datetime.now()

    for i in range(5, -1, -1):
        # Calculate month range
        month_date = today - timedelta(days=30 * i)
        month_start = month_date.replace(day=1).date()
        if month_date.month == 12:
            month_end = month_date.replace(year=month_date.year + 1, month=1, day=1).date() - timedelta(days=1)
        else:
            month_end = month_date.replace(month=month_date.month + 1, day=1).date() - timedelta(days=1)

        # Get revenue for this month
        revenue = Deal.get_revenue_stats(
            start_date=month_start.isoformat(),
            end_date=month_end.isoformat()
        )

        months_data.append({
            'month': month_date.strftime('%B %Y'),
            'month_short': month_date.strftime('%b'),
            'actual_revenue': revenue['total_revenue'],
            'deal_count': revenue['deal_count']
        })

    return jsonify(months_data)
