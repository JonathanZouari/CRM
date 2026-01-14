"""
CrewAI RAG Crew - Natural language queries about CRM data

Handles questions like:
- "מי הלידים הכי חמים השבוע?"
- "כמה עסקאות נסגרו החודש?"
- "מה הסטטוס של חברת ABC?"
- "אילו לידים לא טופלו יותר משבוע?"
- "מה הרווחיות שלי החודש?"
"""
import os
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from crewai import Agent, Task, Crew, Process
from crewai.tools import BaseTool
from langchain_openai import ChatOpenAI
from pydantic import Field

from app.services.vector_store import get_vector_store
from app.models.lead import Lead
from app.models.deal import Deal
from app.models.task import Task as TaskModel
from app.models.expense import Expense
from app.models.work_log import WorkLog


def get_llm():
    """Get the LLM instance."""
    return ChatOpenAI(
        model="gpt-4o",
        temperature=0.3,
        api_key=os.getenv('OPENAI_API_KEY')
    )


class CRMSearchTool(BaseTool):
    """Tool for searching CRM data using vector similarity."""
    name: str = "crm_search"
    description: str = "Search CRM data (leads, deals) by natural language query. Returns relevant matches."

    def _run(self, query: str) -> str:
        vector_store = get_vector_store()
        results = vector_store.search_all(query, n_results=5)

        output = "Search Results:\n\n"

        if results['leads']:
            output += "=== LEADS ===\n"
            for r in results['leads']:
                output += f"- {r['document']}\n"

        if results['deals']:
            output += "\n=== DEALS ===\n"
            for r in results['deals']:
                output += f"- {r['document']}\n"

        return output


class LeadStatsTool(BaseTool):
    """Tool for getting lead statistics."""
    name: str = "lead_stats"
    description: str = "Get lead statistics including counts by status and source."

    def _run(self, query: str = "") -> str:
        stats = Lead.get_stats()
        top_leads = Lead.get_top_scored(limit=5)

        output = f"Total Leads: {stats['total']}\n\n"

        output += "By Status:\n"
        for status, count in stats['by_status'].items():
            output += f"  - {status}: {count}\n"

        output += "\nBy Source:\n"
        for source, count in stats['by_source'].items():
            output += f"  - {source}: {count}\n"

        if top_leads:
            output += "\nTop 5 Scored Leads:\n"
            for lead in top_leads:
                output += f"  - {lead['company_name']} ({lead['contact_name']}): Score {lead.get('lead_score', 'N/A')}\n"

        return output


class DealStatsTool(BaseTool):
    """Tool for getting deal and revenue statistics."""
    name: str = "deal_stats"
    description: str = "Get deal pipeline statistics and revenue data."

    def _run(self, query: str = "") -> str:
        stats = Deal.get_pipeline_stats()

        # Get current month revenue
        today = datetime.now()
        month_start = today.replace(day=1).date().isoformat()
        revenue = Deal.get_revenue_stats(start_date=month_start)

        output = f"Pipeline Statistics:\n"
        output += f"  - Total Value: ₪{stats['total_value']:,.0f}\n"
        output += f"  - Weighted Value: ₪{stats['weighted_value']:,.0f}\n"
        output += f"  - Active Deals: {stats['active_deals']}\n\n"

        output += "By Stage:\n"
        for stage, data in stats['by_stage'].items():
            output += f"  - {stage}: {data['count']} deals, ₪{data['value']:,.0f}\n"

        output += f"\nThis Month's Revenue:\n"
        output += f"  - Closed Deals: {revenue['deal_count']}\n"
        output += f"  - Total Revenue: ₪{revenue['total_revenue']:,.0f}\n"
        output += f"  - Average Deal Size: ₪{revenue['average_deal_size']:,.0f}\n"

        return output


class TaskStatsTool(BaseTool):
    """Tool for getting task statistics."""
    name: str = "task_stats"
    description: str = "Get task statistics including due today, overdue, and pending."

    def _run(self, query: str = "") -> str:
        stats = TaskModel.get_stats()
        due_today = TaskModel.get_due_today()
        overdue = TaskModel.get_overdue()

        output = f"Task Statistics:\n"
        output += f"  - Total: {stats['total']}\n"
        output += f"  - Pending: {stats['pending']}\n"
        output += f"  - In Progress: {stats['in_progress']}\n"
        output += f"  - Completed: {stats['completed']}\n"
        output += f"  - Overdue: {stats['overdue']}\n"
        output += f"  - Urgent: {stats['urgent']}\n\n"

        if due_today:
            output += "Tasks Due Today:\n"
            for task in due_today[:5]:
                output += f"  - {task['title']} ({task.get('priority', 'medium')})\n"

        if overdue:
            output += "\nOverdue Tasks:\n"
            for task in overdue[:5]:
                output += f"  - {task['title']} (Due: {task['due_date']})\n"

        return output


class ProfitabilityTool(BaseTool):
    """Tool for calculating profitability."""
    name: str = "profitability"
    description: str = "Calculate profitability including revenue, costs, and profit margin."

    def _run(self, query: str = "") -> str:
        today = datetime.now()
        month_start = today.replace(day=1).date().isoformat()
        month_end = today.date().isoformat()

        # Revenue
        revenue = Deal.get_revenue_stats(start_date=month_start, end_date=month_end)
        total_revenue = revenue['total_revenue']

        # Expenses
        expenses = Expense.get_totals(start_date=month_start, end_date=month_end)
        total_costs = expenses['total']

        # Calculate profit
        net_profit = total_revenue - total_costs
        margin = (net_profit / total_revenue * 100) if total_revenue > 0 else 0

        output = f"Profitability Report ({month_start} to {month_end}):\n\n"
        output += f"Revenue:\n"
        output += f"  - Total: ₪{total_revenue:,.0f}\n"
        output += f"  - Deals Closed: {revenue['deal_count']}\n\n"

        output += f"Costs:\n"
        output += f"  - Fixed: ₪{expenses['fixed']:,.0f}\n"
        output += f"  - Variable: ₪{expenses['variable']:,.0f}\n"
        output += f"  - Total: ₪{total_costs:,.0f}\n\n"

        output += f"Profit:\n"
        output += f"  - Net Profit: ₪{net_profit:,.0f}\n"
        output += f"  - Margin: {margin:.1f}%\n"

        return output


class RAGCrew:
    """RAG-based CRM query crew using CrewAI."""

    def __init__(self):
        self.llm = get_llm()
        self.tools = [
            CRMSearchTool(),
            LeadStatsTool(),
            DealStatsTool(),
            TaskStatsTool(),
            ProfitabilityTool()
        ]

    def _create_agent(self) -> Agent:
        """Create the RAG agent."""
        return Agent(
            role='CRM Data Analyst',
            goal='Answer questions about CRM data accurately and helpfully',
            backstory='''You are an expert CRM analyst who helps sales teams understand their data.
            You have access to lead, deal, task, and financial data.
            You always provide accurate answers based on the actual data.
            You respond in the same language as the question (Hebrew or English).
            When you don't have enough data, you say so clearly.''',
            verbose=False,
            allow_delegation=False,
            llm=self.llm,
            tools=self.tools
        )

    def query(self, question: str, user_context: Dict[str, Any] = None) -> str:
        """Query the CRM data with a natural language question."""
        agent = self._create_agent()

        context = ""
        if user_context:
            context = f"\nUser Context: {user_context}\n"

        task = Task(
            description=f"""
Answer the following question about CRM data:

Question: {question}
{context}

Use the available tools to gather accurate information.
Respond in the same language as the question.
If you cannot find the answer, explain what information is missing.
Provide specific numbers and details when available.
""",
            expected_output="A clear, accurate answer to the question based on CRM data",
            agent=agent
        )

        crew = Crew(
            agents=[agent],
            tasks=[task],
            process=Process.sequential,
            verbose=False
        )

        result = crew.kickoff()
        return str(result)


# Convenience function
def query_crm_data(question: str, user_context: Dict[str, Any] = None) -> str:
    """Query CRM data with natural language (convenience function)."""
    rag = RAGCrew()
    return rag.query(question, user_context)
