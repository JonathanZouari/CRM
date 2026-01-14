"""
Seed Data Script for Smart CRM

Generates realistic test data:
- 3 users (1 admin, 2 representatives)
- 50 leads (Hebrew/English mix)
- 15 deals in various stages
- 30 interactions
- 20 tasks
- Sample expenses
- Work logs
"""
import os
import sys
import random
from datetime import datetime, timedelta
from uuid import uuid4

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from app.models.base import get_db
from app.models.user import User, UserCreate
from app.models.lead import Lead, LeadCreate
from app.models.deal import Deal, DealCreate
from app.models.interaction import Interaction, InteractionCreate
from app.models.task import Task, TaskCreate
from app.models.expense import Expense, ExpenseCreate
from app.models.work_log import WorkLog, WorkLogCreate
from app.services.lead_scoring import calculate_lead_score

# ==================== DATA TEMPLATES ====================

# Hebrew company names
HEBREW_COMPANIES = [
    ("טכנולוגיות חכמות בע\"מ", "יוסי כהן"),
    ("דיגיטל פלוס", "מיכל לוי"),
    ("סטארט-אפ ישראל", "אורי גולן"),
    ("מערכות מידע מתקדמות", "רונית שרון"),
    ("פתרונות ענן", "דני אברהם"),
    ("חדשנות דיגיטלית", "נועה ברק"),
    ("אוטומציה פלוס", "גיא מזרחי"),
    ("טרנספורמציה עסקית", "שירה כץ"),
    ("פייננס טק", "אבי פרידמן"),
    ("מדיה חכמה", "תמר אלון"),
    ("אינטליגנציה עסקית", "עידו רוזנברג"),
    ("דאטה סנטר", "הילה גרינברג"),
    ("קריאייטיב סטודיו", "יובל שמיר"),
    ("לוגיסטיקה חכמה", "ליאת ביטון"),
    ("פודטק ישראל", "עמית דהן"),
    ("הלת'טק פלוס", "רוני ויצמן"),
    ("אדטק מדיה", "שני גל"),
    ("סייבר סקיוריטי", "אלעד נחמיאס"),
    ("אגריטק חדשנות", "מורן כהן"),
    ("אנרגיה ירוקה", "יעל שפירא"),
]

# English company names
ENGLISH_COMPANIES = [
    ("TechFlow Solutions", "David Miller"),
    ("InnovateTech Ltd", "Sarah Johnson"),
    ("DataStream Corp", "Michael Chen"),
    ("CloudFirst Inc", "Emily Williams"),
    ("AutomateNow", "James Anderson"),
    ("DigitalEdge", "Lisa Thompson"),
    ("SmartBiz Systems", "Robert Garcia"),
    ("FutureTech Partners", "Jennifer Martinez"),
    ("AI Pioneers", "Christopher Lee"),
    ("NextGen Software", "Amanda Wilson"),
    ("ByteLogic", "Daniel Brown"),
    ("Quantum Dynamics", "Rachel Taylor"),
    ("Apex Innovations", "Kevin Moore"),
    ("Synergy Tech", "Nicole Jackson"),
    ("Elevate Digital", "Brandon White"),
    ("Prime Analytics", "Stephanie Harris"),
    ("Catalyst Systems", "Andrew Martin"),
    ("Horizon Ventures", "Michelle Thompson"),
    ("Velocity Labs", "Jason Rodriguez"),
    ("Summit Software", "Laura Clark"),
    ("Nexus Technologies", "Ryan Lewis"),
    ("Pulse Digital", "Samantha Walker"),
    ("Zenith Solutions", "Matthew Hall"),
    ("Optima Group", "Christina Young"),
    ("Vertex Tech", "Joshua Allen"),
    ("Ascend Analytics", "Melissa King"),
    ("Pinnacle Systems", "Eric Wright"),
    ("Clarity Software", "Rebecca Scott"),
    ("Momentum Digital", "Tyler Green"),
    ("Stellar Innovations", "Katherine Adams"),
]

INDUSTRIES = [
    "E-commerce", "Healthcare", "Finance", "Real Estate", "Education",
    "Manufacturing", "Retail", "Logistics", "Marketing", "Legal",
    "Insurance", "Hospitality", "Construction", "Agriculture", "Media"
]

PAIN_POINTS_HE = [
    "תהליכי עבודה ידניים ואיטיים",
    "קושי בניהול לידים",
    "חוסר יעילות בשירות לקוחות",
    "בעיות באינטגרציה בין מערכות",
    "קושי בניתוח נתונים",
    "תקשורת לא יעילה עם לקוחות",
    "בעיות בניהול מלאי",
    "חוסר תובנות עסקיות",
    "קושי בתחזית מכירות",
    "בעיות בניהול זמן"
]

PAIN_POINTS_EN = [
    "Manual and slow work processes",
    "Difficulty managing leads",
    "Inefficient customer service",
    "Integration issues between systems",
    "Difficulty analyzing data",
    "Ineffective customer communication",
    "Inventory management issues",
    "Lack of business insights",
    "Sales forecasting challenges",
    "Time management problems"
]

SOURCES = ['website', 'referral', 'linkedin', 'facebook', 'google_ads', 'cold_outreach', 'event', 'other']
BUSINESS_SIZES = ['micro', 'small', 'medium']
LEAD_STATUSES = ['new', 'contacted', 'qualified', 'proposal', 'negotiation', 'won', 'lost']
DEAL_STAGES = ['discovery', 'proposal', 'negotiation', 'contract', 'closed_won', 'closed_lost']
SERVICE_TYPES = ['chatbot', 'automation', 'analytics', 'consulting', 'training', 'custom']
INTERACTION_TYPES = ['call', 'email', 'meeting', 'demo', 'proposal_sent', 'follow_up', 'note']
PRIORITIES = ['low', 'medium', 'high', 'urgent']


def generate_israeli_phone():
    """Generate a realistic Israeli phone number."""
    prefixes = ['050', '052', '053', '054', '055', '058']
    return f"+972-{random.choice(prefixes)}-{random.randint(100,999)}-{random.randint(1000,9999)}"


def generate_email(name, company):
    """Generate an email from name and company."""
    first_name = name.split()[0].lower()
    company_domain = company.lower().replace(' ', '').replace('"', '').replace("'", '')[:10]
    domains = ['.com', '.io', '.co.il', '.tech']
    return f"{first_name}@{company_domain}{random.choice(domains)}"


def random_date(start_days_ago=90, end_days_ago=0):
    """Generate a random date between start_days_ago and end_days_ago."""
    days = random.randint(end_days_ago, start_days_ago)
    return (datetime.now() - timedelta(days=days)).isoformat()


def seed_users():
    """Create sample users."""
    print("Creating users...")

    users_data = [
        {
            "email": "admin@smartcrm.com",
            "password": "admin123",
            "full_name": "Admin User",
            "role": "admin",
            "phone": "+972-50-123-4567",
            "target_monthly_revenue": 100000,
            "target_monthly_deals": 10,
            "hourly_rate": 250
        },
        {
            "email": "alex@smartcrm.com",
            "password": "alex123",
            "full_name": "Alex Rivera",
            "role": "representative",
            "phone": "+972-52-234-5678",
            "target_monthly_revenue": 50000,
            "target_monthly_deals": 5,
            "hourly_rate": 150
        },
        {
            "email": "maya@smartcrm.com",
            "password": "maya123",
            "full_name": "Maya Cohen",
            "role": "representative",
            "phone": "+972-54-345-6789",
            "target_monthly_revenue": 50000,
            "target_monthly_deals": 5,
            "hourly_rate": 150
        }
    ]

    created_users = []
    for user_data in users_data:
        try:
            user = User.create(UserCreate(**user_data))
            if user:
                created_users.append(user)
                print(f"  Created user: {user['email']}")
        except Exception as e:
            print(f"  Error creating user {user_data['email']}: {e}")

    return created_users


def seed_leads(users):
    """Create sample leads."""
    print("\nCreating leads...")

    rep_ids = [u['id'] for u in users if u['role'] == 'representative']
    all_companies = HEBREW_COMPANIES + ENGLISH_COMPANIES
    random.shuffle(all_companies)

    created_leads = []

    for i, (company, contact) in enumerate(all_companies[:50]):
        is_hebrew = i < len(HEBREW_COMPANIES)
        pain_points = random.choice(PAIN_POINTS_HE if is_hebrew else PAIN_POINTS_EN)

        lead_data = {
            "company_name": company,
            "contact_name": contact,
            "email": generate_email(contact, company),
            "phone": generate_israeli_phone(),
            "business_size": random.choice(BUSINESS_SIZES),
            "estimated_budget": random.choice([3000, 5000, 8000, 10000, 15000, 20000, 25000, 30000, 40000, 50000]),
            "source": random.choice(SOURCES),
            "interest_level": random.randint(3, 10),
            "industry": random.choice(INDUSTRIES),
            "current_pain_points": pain_points,
            "ai_readiness_score": random.randint(3, 10),
            "status": random.choice(LEAD_STATUSES),
            "assigned_to": random.choice(rep_ids),
            "notes": f"Lead from {random.choice(SOURCES)} - {pain_points[:50]}..."
        }

        try:
            lead = Lead.create(LeadCreate(**lead_data))
            if lead:
                # Calculate and update score
                score, explanation = calculate_lead_score(lead)
                Lead.update_score(lead['id'], score, explanation)
                lead['lead_score'] = score
                lead['lead_score_explanation'] = explanation

                created_leads.append(lead)
                print(f"  Created lead: {company} (Score: {score:.1f})")
        except Exception as e:
            print(f"  Error creating lead {company}: {e}")

    return created_leads


def seed_deals(users, leads):
    """Create sample deals."""
    print("\nCreating deals...")

    rep_ids = [u['id'] for u in users if u['role'] == 'representative']
    qualified_leads = [l for l in leads if l['status'] in ('qualified', 'proposal', 'negotiation', 'won')]

    created_deals = []

    for i, lead in enumerate(qualified_leads[:15]):
        stage = random.choice(DEAL_STAGES)
        value = float(lead.get('estimated_budget', 10000)) * random.uniform(0.8, 1.5)

        deal_data = {
            "title": f"{lead['company_name']} - {random.choice(SERVICE_TYPES).title()} Project",
            "lead_id": lead['id'],
            "assigned_to": lead.get('assigned_to') or random.choice(rep_ids),
            "description": f"AI implementation project for {lead['company_name']}",
            "value": round(value, 2),
            "expected_close_date": (datetime.now() + timedelta(days=random.randint(7, 60))).date().isoformat(),
            "stage": stage,
            "probability": {'discovery': 10, 'proposal': 30, 'negotiation': 50, 'contract': 80, 'closed_won': 100, 'closed_lost': 0}[stage],
            "estimated_hours": random.randint(20, 100),
            "service_type": random.choice(SERVICE_TYPES)
        }

        try:
            deal = Deal.create(DealCreate(**deal_data))
            if deal:
                created_deals.append(deal)
                print(f"  Created deal: {deal['title']} (₪{value:,.0f})")
        except Exception as e:
            print(f"  Error creating deal: {e}")

    return created_deals


def seed_interactions(users, leads, deals):
    """Create sample interactions."""
    print("\nCreating interactions...")

    rep_ids = [u['id'] for u in users if u['role'] == 'representative']
    created_interactions = []

    subjects = [
        "Initial call", "Follow-up discussion", "Demo scheduled", "Proposal review",
        "Technical questions", "Budget discussion", "Contract review", "Onboarding call"
    ]

    outcomes = [
        "Positive - moving forward", "Need more info", "Scheduled follow-up",
        "Sent materials", "Waiting for decision", "Referred to technical team"
    ]

    for i in range(30):
        lead = random.choice(leads)
        deal = random.choice(deals) if deals and random.random() > 0.5 else None

        interaction_data = {
            "lead_id": lead['id'],
            "deal_id": deal['id'] if deal else None,
            "user_id": random.choice(rep_ids),
            "type": random.choice(INTERACTION_TYPES),
            "subject": random.choice(subjects),
            "content": f"Discussed with {lead['contact_name']} from {lead['company_name']}",
            "outcome": random.choice(outcomes),
            "duration_minutes": random.randint(5, 60) if random.random() > 0.3 else None
        }

        try:
            interaction = Interaction.create(InteractionCreate(**interaction_data))
            if interaction:
                created_interactions.append(interaction)
        except Exception as e:
            print(f"  Error creating interaction: {e}")

    print(f"  Created {len(created_interactions)} interactions")
    return created_interactions


def seed_tasks(users, leads, deals):
    """Create sample tasks."""
    print("\nCreating tasks...")

    rep_ids = [u['id'] for u in users if u['role'] == 'representative']
    created_tasks = []

    task_titles = [
        "Follow up call", "Send proposal", "Schedule demo", "Review contract",
        "Update CRM notes", "Research competitor", "Prepare presentation",
        "Send invoice", "Check in with client", "Gather requirements"
    ]

    for i in range(20):
        lead = random.choice(leads) if leads and random.random() > 0.3 else None
        deal = random.choice(deals) if deals and random.random() > 0.5 else None

        # Random due date - some past, some future
        days_offset = random.randint(-7, 14)
        due_date = (datetime.now() + timedelta(days=days_offset, hours=random.randint(9, 17)))

        task_data = {
            "title": random.choice(task_titles),
            "due_date": due_date.isoformat(),
            "assigned_to": random.choice(rep_ids),
            "lead_id": lead['id'] if lead else None,
            "deal_id": deal['id'] if deal else None,
            "description": f"Task related to {lead['company_name'] if lead else 'general work'}",
            "priority": random.choice(PRIORITIES),
            "requires_urgent_action": random.random() > 0.8
        }

        try:
            task = Task.create(TaskCreate(**task_data))
            if task:
                created_tasks.append(task)
        except Exception as e:
            print(f"  Error creating task: {e}")

    print(f"  Created {len(created_tasks)} tasks")
    return created_tasks


def seed_expenses():
    """Create sample expenses."""
    print("\nCreating expenses...")

    fixed_expenses = [
        {"type": "rent", "amount": 5000, "description": "Office rent"},
        {"type": "software", "amount": 1500, "description": "Software subscriptions"},
        {"type": "utilities", "amount": 500, "description": "Electricity and internet"},
        {"type": "insurance", "amount": 800, "description": "Business insurance"},
    ]

    variable_expenses = [
        {"type": "marketing", "amount": 2000, "description": "Google Ads campaign"},
        {"type": "marketing", "amount": 1500, "description": "Facebook Ads"},
        {"type": "travel", "amount": 800, "description": "Client meeting travel"},
        {"type": "commission", "amount": 3000, "description": "Sales commission"},
        {"type": "training", "amount": 1200, "description": "Team training"},
    ]

    created_expenses = []

    # Fixed expenses (monthly)
    for expense in fixed_expenses:
        expense_data = {
            "amount": expense["amount"],
            "date": datetime.now().replace(day=1).date().isoformat(),
            "category": "fixed",
            "type": expense["type"],
            "description": expense["description"],
            "is_recurring": True,
            "recurring_frequency": "monthly"
        }
        try:
            exp = Expense.create(ExpenseCreate(**expense_data))
            if exp:
                created_expenses.append(exp)
        except Exception as e:
            print(f"  Error creating expense: {e}")

    # Variable expenses
    for expense in variable_expenses:
        expense_data = {
            "amount": expense["amount"],
            "date": (datetime.now() - timedelta(days=random.randint(0, 30))).date().isoformat(),
            "category": "variable",
            "type": expense["type"],
            "description": expense["description"],
            "is_recurring": False
        }
        try:
            exp = Expense.create(ExpenseCreate(**expense_data))
            if exp:
                created_expenses.append(exp)
        except Exception as e:
            print(f"  Error creating expense: {e}")

    print(f"  Created {len(created_expenses)} expenses")
    return created_expenses


def seed_work_logs(users, deals):
    """Create sample work logs."""
    print("\nCreating work logs...")

    rep_ids = [u['id'] for u in users if u['role'] == 'representative']
    won_deals = [d for d in deals if d['stage'] == 'closed_won']

    if not won_deals:
        print("  No closed deals to log work against")
        return []

    created_logs = []

    for deal in won_deals:
        # Create 3-5 work logs per won deal
        for _ in range(random.randint(3, 5)):
            log_data = {
                "user_id": deal.get('assigned_to') or random.choice(rep_ids),
                "deal_id": deal['id'],
                "date": (datetime.now() - timedelta(days=random.randint(1, 30))).date().isoformat(),
                "hours": round(random.uniform(1, 8), 1),
                "description": random.choice([
                    "Development work", "Client meeting", "Configuration",
                    "Testing", "Documentation", "Training session"
                ]),
                "billable": random.random() > 0.2
            }
            try:
                log = WorkLog.create(WorkLogCreate(**log_data))
                if log:
                    created_logs.append(log)
            except Exception as e:
                print(f"  Error creating work log: {e}")

    print(f"  Created {len(created_logs)} work logs")
    return created_logs


def main():
    """Run all seed functions."""
    print("=" * 60)
    print("Smart CRM - Seed Data Generator")
    print("=" * 60)

    try:
        # Test database connection
        db = get_db()
        print("Database connection successful!\n")

        # Seed in order of dependencies
        users = seed_users()
        if not users:
            print("Failed to create users. Aborting.")
            return

        leads = seed_leads(users)
        deals = seed_deals(users, leads)
        interactions = seed_interactions(users, leads, deals)
        tasks = seed_tasks(users, leads, deals)
        expenses = seed_expenses()
        work_logs = seed_work_logs(users, deals)

        print("\n" + "=" * 60)
        print("Seed Data Summary:")
        print("=" * 60)
        print(f"  Users:        {len(users)}")
        print(f"  Leads:        {len(leads)}")
        print(f"  Deals:        {len(deals)}")
        print(f"  Interactions: {len(interactions)}")
        print(f"  Tasks:        {len(tasks)}")
        print(f"  Expenses:     {len(expenses)}")
        print(f"  Work Logs:    {len(work_logs)}")
        print("=" * 60)
        print("\nTest Credentials:")
        print("  Admin:  admin@smartcrm.com / admin123")
        print("  Rep 1:  alex@smartcrm.com / alex123")
        print("  Rep 2:  maya@smartcrm.com / maya123")
        print("=" * 60)

    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
