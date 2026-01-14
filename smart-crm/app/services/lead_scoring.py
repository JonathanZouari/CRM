"""
Lead Scoring Service

Calculate a score from 0-100 based on weighted criteria:
1. Business Size (20 points max)
2. Estimated Budget (25 points max)
3. Lead Source Quality (15 points max)
4. Interest Level (15 points max)
5. AI Readiness Score (15 points max)
6. Engagement Recency (10 points max)
"""
from datetime import datetime, timedelta
from typing import Dict, Any, Tuple


# Scoring weights and values
BUSINESS_SIZE_SCORES = {
    'micro': 8,   # 1-5 employees
    'small': 15,  # 6-20 employees
    'medium': 20  # 21-50 employees
}

BUDGET_THRESHOLDS = [
    (30000, 25),  # > 30,000 ILS: 25 points
    (15000, 20),  # 15,000-30,000 ILS: 20 points
    (5000, 12),   # 5,000-15,000 ILS: 12 points
    (0, 5)        # < 5,000 ILS: 5 points
]

SOURCE_SCORES = {
    'referral': 15,
    'website': 12,
    'linkedin': 10,
    'event': 10,
    'google_ads': 8,
    'facebook': 6,
    'cold_outreach': 4,
    'other': 3
}


def calculate_business_size_score(business_size: str) -> Tuple[float, str]:
    """Calculate score based on business size."""
    score = BUSINESS_SIZE_SCORES.get(business_size, 0)

    if business_size == 'medium':
        explanation = "עסק בינוני (21-50 עובדים) - פוטנציאל גבוה"
    elif business_size == 'small':
        explanation = "עסק קטן (6-20 עובדים) - פוטנציאל טוב"
    elif business_size == 'micro':
        explanation = "עסק זעיר (1-5 עובדים) - פוטנציאל מוגבל"
    else:
        explanation = "גודל עסק לא ידוע"

    return score, explanation


def calculate_budget_score(estimated_budget: float) -> Tuple[float, str]:
    """Calculate score based on estimated budget."""
    if estimated_budget is None:
        return 0, "תקציב לא ידוע"

    for threshold, score in BUDGET_THRESHOLDS:
        if estimated_budget >= threshold:
            if estimated_budget >= 30000:
                explanation = f"תקציב גבוה (₪{estimated_budget:,.0f}) - פוטנציאל מצוין"
            elif estimated_budget >= 15000:
                explanation = f"תקציב בינוני-גבוה (₪{estimated_budget:,.0f}) - פוטנציאל טוב"
            elif estimated_budget >= 5000:
                explanation = f"תקציב בינוני (₪{estimated_budget:,.0f}) - פוטנציאל סביר"
            else:
                explanation = f"תקציב נמוך (₪{estimated_budget:,.0f}) - פוטנציאל מוגבל"
            return score, explanation

    return 5, f"תקציב נמוך (₪{estimated_budget:,.0f})"


def calculate_source_score(source: str) -> Tuple[float, str]:
    """Calculate score based on lead source."""
    score = SOURCE_SCORES.get(source, 3)

    source_names = {
        'referral': 'הפניה - מקור אמין ביותר',
        'website': 'אתר - עניין אקטיבי',
        'linkedin': 'לינקדאין - מקור מקצועי',
        'event': 'אירוע - פגישה אישית',
        'google_ads': 'גוגל - חיפוש יזום',
        'facebook': 'פייסבוק - רשת חברתית',
        'cold_outreach': 'פנייה קרה - יש לבנות עניין',
        'other': 'מקור אחר'
    }

    explanation = source_names.get(source, 'מקור לא ידוע')
    return score, explanation


def calculate_interest_score(interest_level: int) -> Tuple[float, str]:
    """Calculate score based on interest level (1-10)."""
    if interest_level is None:
        return 0, "רמת עניין לא ידועה"

    score = (interest_level / 10) * 15

    if interest_level >= 8:
        explanation = f"רמת עניין גבוהה ({interest_level}/10) - מוכנים להתקדם"
    elif interest_level >= 5:
        explanation = f"רמת עניין בינונית ({interest_level}/10) - דורש טיפוח"
    else:
        explanation = f"רמת עניין נמוכה ({interest_level}/10) - יש לבנות עניין"

    return score, explanation


def calculate_ai_readiness_score(ai_readiness: int) -> Tuple[float, str]:
    """Calculate score based on AI readiness (1-10)."""
    if ai_readiness is None:
        return 0, "מוכנות AI לא ידועה"

    score = (ai_readiness / 10) * 15

    if ai_readiness >= 8:
        explanation = f"מוכנות גבוהה ל-AI ({ai_readiness}/10) - מתאים להטמעה"
    elif ai_readiness >= 5:
        explanation = f"מוכנות בינונית ל-AI ({ai_readiness}/10) - דורש הכנה"
    else:
        explanation = f"מוכנות נמוכה ל-AI ({ai_readiness}/10) - דורש חינוך"

    return score, explanation


def calculate_recency_score(last_contact_date: str) -> Tuple[float, str]:
    """Calculate score based on last contact date."""
    if not last_contact_date:
        return 2, "אין היסטוריית קשר"

    try:
        if isinstance(last_contact_date, str):
            # Handle ISO format
            last_contact = datetime.fromisoformat(last_contact_date.replace('Z', '+00:00'))
            if last_contact.tzinfo:
                last_contact = last_contact.replace(tzinfo=None)
        else:
            last_contact = last_contact_date

        days_since = (datetime.now() - last_contact).days

        if days_since <= 7:
            return 10, f"קשר אחרון לפני {days_since} ימים - עדכני"
        elif days_since <= 14:
            return 7, f"קשר אחרון לפני {days_since} ימים - יחסית עדכני"
        elif days_since <= 30:
            return 4, f"קשר אחרון לפני {days_since} ימים - דורש מעקב"
        else:
            return 2, f"קשר אחרון לפני {days_since} ימים - דורש חידוש קשר"

    except Exception:
        return 2, "לא ניתן לחשב זמן מאז הקשר האחרון"


def calculate_lead_score(lead: Dict[str, Any]) -> Tuple[float, str]:
    """
    Calculate total lead score and generate explanation.

    Returns:
        Tuple of (score, explanation)
    """
    scores = []
    explanations = []

    # 1. Business Size (20 points max)
    size_score, size_exp = calculate_business_size_score(lead.get('business_size'))
    scores.append(size_score)
    explanations.append(f"• גודל עסק: {size_exp} ({size_score}/20)")

    # 2. Budget (25 points max)
    budget_score, budget_exp = calculate_budget_score(lead.get('estimated_budget'))
    scores.append(budget_score)
    explanations.append(f"• תקציב: {budget_exp} ({budget_score}/25)")

    # 3. Source (15 points max)
    source_score, source_exp = calculate_source_score(lead.get('source'))
    scores.append(source_score)
    explanations.append(f"• מקור: {source_exp} ({source_score}/15)")

    # 4. Interest Level (15 points max)
    interest_score, interest_exp = calculate_interest_score(lead.get('interest_level'))
    scores.append(interest_score)
    explanations.append(f"• עניין: {interest_exp} ({interest_score:.1f}/15)")

    # 5. AI Readiness (15 points max)
    ai_score, ai_exp = calculate_ai_readiness_score(lead.get('ai_readiness_score'))
    scores.append(ai_score)
    explanations.append(f"• מוכנות AI: {ai_exp} ({ai_score:.1f}/15)")

    # 6. Recency (10 points max)
    recency_score, recency_exp = calculate_recency_score(lead.get('last_contact_date'))
    scores.append(recency_score)
    explanations.append(f"• עדכניות: {recency_exp} ({recency_score}/10)")

    # Calculate total score
    total_score = sum(scores)

    # Generate summary
    if total_score >= 70:
        summary = "🔥 ליד חם - עדיפות גבוהה לטיפול"
    elif total_score >= 50:
        summary = "⚡ ליד חם בינוני - כדאי לטפח"
    elif total_score >= 30:
        summary = "📊 ליד קר - דורש עבודה"
    else:
        summary = "❄️ ליד קר מאוד - עדיפות נמוכה"

    # Combine explanation
    full_explanation = f"{summary}\n\nפירוט הציון ({total_score:.1f}/100):\n" + "\n".join(explanations)

    return round(total_score, 2), full_explanation
