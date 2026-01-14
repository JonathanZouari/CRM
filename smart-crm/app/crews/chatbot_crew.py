"""
CrewAI Chatbot Crew - Multi-mode customer chatbot

Three specialized agents:
1. ServiceAgent - Customer support persona
2. SalesAgent - Lead qualification persona
3. ConsultantAgent - AI consulting persona
"""
import os
from typing import Dict, Any, List, Optional
from crewai import Agent, Task, Crew, Process
from langchain_openai import ChatOpenAI

# System prompts for each mode
SERVICE_SYSTEM_PROMPT = """You are a friendly customer service representative for {company_name},
an AI implementation company. Your role is to:
- Answer questions about our services and solutions
- Help with technical support inquiries
- Collect relevant information to assist customers
- Escalate complex issues when needed

Tone: Warm, helpful, patient
Language: Always respond in the same language as the customer (Hebrew or English)

Our Services:
- AI Chatbots for customer service and sales
- Business Process Automation
- Data Analytics and Insights
- AI Consulting and Strategy
- Training and Workshops

Be helpful, professional, and always aim to resolve the customer's issue or direct them to the right resource.
"""

SALES_SYSTEM_PROMPT = """You are a knowledgeable sales representative for {company_name}.
Your role is to:
- Understand customer needs and pain points
- Explain how our AI solutions can help their business
- Qualify leads by gathering: company size, budget range, timeline, current challenges
- Schedule demos and meetings with human sales team
- Handle objections professionally

Tone: Professional, consultative, not pushy
Language: Always respond in the same language as the customer (Hebrew or English)

Key Qualification Questions:
1. What is your company name and industry?
2. How many employees do you have?
3. What challenges are you trying to solve with AI?
4. What is your timeline for implementation?
5. Do you have a budget range in mind?

Our Pricing Ranges:
- Basic Chatbot: Starting at ₪5,000
- Full Automation Suite: ₪15,000-30,000
- Enterprise Solutions: Custom pricing

Always try to collect: Name, Company, Email, Phone before ending the conversation.
"""

CONSULTANT_SYSTEM_PROMPT = """You are an AI implementation consultant for {company_name}.
Your role is to:
- Provide expert guidance on AI adoption strategies
- Assess business readiness for AI implementation
- Recommend appropriate solutions based on business needs
- Educate about AI capabilities and limitations
- Help prioritize AI initiatives

Tone: Expert, educational, strategic
Language: Always respond in the same language as the customer (Hebrew or English)

Key Areas of Expertise:
1. AI Readiness Assessment
2. Use Case Identification
3. Implementation Roadmap
4. ROI Analysis
5. Change Management
6. Technology Selection

Provide genuine value and build trust by sharing knowledge freely.
Help the customer understand what AI can and cannot do for their business.
"""


def get_llm():
    """Get the LLM instance."""
    return ChatOpenAI(
        model="gpt-4o",
        temperature=0.7,
        api_key=os.getenv('OPENAI_API_KEY')
    )


class ChatbotCrew:
    """Multi-mode chatbot using CrewAI."""

    def __init__(self, company_name: str = None):
        self.company_name = company_name or os.getenv('COMPANY_NAME', 'Smart CRM AI Solutions')
        self.llm = get_llm()

    def _create_agent(self, mode: str) -> Agent:
        """Create an agent for the specified mode."""
        prompts = {
            'service': SERVICE_SYSTEM_PROMPT,
            'sales': SALES_SYSTEM_PROMPT,
            'consulting': CONSULTANT_SYSTEM_PROMPT
        }

        roles = {
            'service': 'Customer Service Representative',
            'sales': 'Sales Representative',
            'consulting': 'AI Consultant'
        }

        goals = {
            'service': 'Help customers with their inquiries and provide excellent support',
            'sales': 'Qualify leads and help potential customers understand our solutions',
            'consulting': 'Provide expert guidance on AI implementation strategies'
        }

        backstories = {
            'service': f'You are an experienced customer service representative at {self.company_name}, known for your patience and problem-solving skills.',
            'sales': f'You are a consultative sales professional at {self.company_name}, focused on understanding customer needs and providing value.',
            'consulting': f'You are a senior AI consultant at {self.company_name} with years of experience helping businesses adopt AI successfully.'
        }

        system_prompt = prompts.get(mode, SERVICE_SYSTEM_PROMPT).format(company_name=self.company_name)

        return Agent(
            role=roles.get(mode, 'Customer Service Representative'),
            goal=goals.get(mode, 'Help customers'),
            backstory=backstories.get(mode, f'You work at {self.company_name}'),
            verbose=False,
            allow_delegation=False,
            llm=self.llm
        )

    def get_response(
        self,
        mode: str,
        user_message: str,
        history: List[Dict[str, str]] = None,
        visitor_info: Dict[str, Any] = None
    ) -> str:
        """Get a response from the chatbot in the specified mode."""
        agent = self._create_agent(mode)

        # Build context from history
        context = ""
        if history:
            context = "Previous conversation:\n"
            for msg in history[-5:]:  # Last 5 messages
                role = "Customer" if msg['role'] == 'user' else "You"
                context += f"{role}: {msg['content']}\n"
            context += "\n"

        # Add visitor info if available
        visitor_context = ""
        if visitor_info:
            if visitor_info.get('name'):
                visitor_context += f"Customer name: {visitor_info['name']}\n"
            if visitor_info.get('company'):
                visitor_context += f"Company: {visitor_info['company']}\n"
            if visitor_info.get('email'):
                visitor_context += f"Email: {visitor_info['email']}\n"

        task_description = f"""
{context}
{visitor_context}
Current customer message: {user_message}

Respond to the customer's message in a helpful and professional manner.
Use the same language as the customer (Hebrew or English).
Keep your response concise but complete.
"""

        task = Task(
            description=task_description,
            expected_output="A helpful response to the customer's message",
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


# Convenience function for route usage
def get_chatbot_response(
    mode: str,
    user_message: str,
    history: List[Dict[str, str]] = None,
    visitor_info: Dict[str, Any] = None
) -> str:
    """Get a chatbot response (convenience function)."""
    chatbot = ChatbotCrew()
    return chatbot.get_response(mode, user_message, history, visitor_info)
