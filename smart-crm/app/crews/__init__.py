"""
CrewAI Crews for Smart CRM
"""
from app.crews.chatbot_crew import get_chatbot_response, ChatbotCrew
from app.crews.rag_crew import RAGCrew, query_crm_data

__all__ = [
    'get_chatbot_response',
    'ChatbotCrew',
    'RAGCrew',
    'query_crm_data'
]
