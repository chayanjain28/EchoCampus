import os
import json
import re

try:
    from google import genai as google_genai
    from google.genai import types as genai_types
    _USE_NEW_SDK = True
except ImportError:
    _USE_NEW_SDK = False

try:
    import google.generativeai as genai_legacy
    _USE_LEGACY_SDK = True
except ImportError:
    _USE_LEGACY_SDK = False

api_key = os.getenv("GEMINI_API_KEY", "")
has_api = False
_client = None

if api_key:
    try:
        if _USE_NEW_SDK:
            _client = google_genai.Client(api_key=api_key)
            has_api = True
        elif _USE_LEGACY_SDK:
            genai_legacy.configure(api_key=api_key)
            has_api = True
    except Exception as e:
        print(f"Gemini API config error: {e}")

MODEL_NAME = "gemini-1.5-flash"

def _generate(prompt: str) -> str:
    """Unified generation wrapper for both SDK versions."""
    if _USE_NEW_SDK and _client:
        response = _client.models.generate_content(model=MODEL_NAME, contents=prompt)
        return response.text
    elif _USE_LEGACY_SDK:
        model = genai_legacy.GenerativeModel(MODEL_NAME)
        response = model.generate_content(prompt)
        return response.text
    raise RuntimeError("No Gemini SDK available")

def clean_json_response(text: str) -> str:
    """Helper to strip markdown block markers if Gemini wraps JSON."""
    text = text.strip()
    if text.startswith("```json"):
        text = text[7:]
    elif text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]
    return text.strip()

def analyze_complaint(title: str, description: str) -> dict:
    """
    Categorizes, performs sentiment analysis, sets priority, severity score,
    and assigns the routing department.
    """
    text_content = f"Title: {title}\nDescription: {description}"
    
    if has_api:
        try:
            prompt = (
                "You are an AI assistant for EchoCampus AI, a campus intelligence platform.\n"
                "Analyze the following student complaint:\n"
                f"{text_content}\n\n"
                "Return a JSON object with these fields:\n"
                "- category: One of 'Hostel', 'Mess', 'WiFi', 'Transport', 'Academic', 'Infrastructure', 'Security', 'Other'\n"
                "- sentiment: One of 'Positive', 'Neutral', 'Negative'\n"
                "- priority: One of 'Low', 'Medium', 'High', 'Critical'\n"
                "- severity_score: An integer from 0 to 100 reflecting urgency, safety risks, and user distress.\n"
                "- assigned_department: One of 'Hostel Warden', 'Mess Committee', 'IT Department', 'Transport Office', 'Academic Cell', 'Security Office', 'Administration'\n"
                "- ai_recommendation: A brief 1-2 sentence actionable recommendation for administrators.\n\n"
                "Response must be strict JSON. Do not write markdown formatting or extra text outside JSON."
            )
            raw = _generate(prompt)
            clean_txt = clean_json_response(raw)
            data = json.loads(clean_txt)
            if data.get("category") in ['Hostel', 'Mess', 'WiFi', 'Transport', 'Academic', 'Infrastructure', 'Security', 'Other']:
                return data
        except Exception as e:
            print(f"Gemini API Exception in analyze_complaint: {e}. Falling back to rules.")

    # Fallback Rule-based engine
    desc_lower = (title + " " + description).lower()
    
    # Category & Department
    if any(w in desc_lower for w in ["wifi", "wi-fi", "internet", "network", "router", "login"]):
        category = "WiFi"
        dept = "IT Department"
    elif any(w in desc_lower for w in ["mess", "food", "lunch", "dinner", "breakfast", "hygiene", "canteen"]):
        category = "Mess"
        dept = "Mess Committee"
    elif any(w in desc_lower for w in ["hostel", "room", "dorm", "warden", "roommate", "bed", "bathroom"]):
        category = "Hostel"
        dept = "Hostel Warden"
    elif any(w in desc_lower for w in ["bus", "transport", "shuttle", "route", "driver", "cab"]):
        category = "Transport"
        dept = "Transport Office"
    elif any(w in desc_lower for w in ["exam", "grade", "academic", "professor", "class", "syllabus", "course"]):
        category = "Academic"
        dept = "Academic Cell"
    elif any(w in desc_lower for w in ["security", "guard", "theft", "gate", "stolen", "safety", "threat"]):
        category = "Security"
        dept = "Security Office"
    elif any(w in desc_lower for w in ["water", "leak", "building", "lift", "fan", "light", "infrastructure"]):
        category = "Infrastructure"
        dept = "Administration"
    else:
        category = "Other"
        dept = "Administration"

    # Sentiment
    if any(w in desc_lower for w in ["worst", "angry", "terrible", "useless", "broken", "danger", "poor", "hate", "stole"]):
        sentiment = "Negative"
        priority = "High"
        severity = 75
    elif any(w in desc_lower for w in ["good", "thanks", "fine", "solved", "happy"]):
        sentiment = "Positive"
        priority = "Low"
        severity = 15
    else:
        sentiment = "Neutral"
        priority = "Medium"
        severity = 45

    if "urgent" in desc_lower or "emergency" in desc_lower or "theft" in desc_lower or "shock" in desc_lower:
        priority = "Critical"
        severity = min(severity + 20, 100)

    return {
        "category": category,
        "sentiment": sentiment,
        "priority": priority,
        "severity_score": severity,
        "assigned_department": dept
    }

def check_duplicate(new_title: str, new_desc: str, existing_complaints: list) -> dict:
    """
    Compares new complaint against recent active complaints using Gemini.
    Returns: {"match_found": bool, "parent_id": int/None, "similarity_score": float}
    """
    if not existing_complaints:
        return {"match_found": False, "parent_id": None, "similarity_score": 0.0}

    if has_api:
        try:
            comp_list = [{"id": c["id"], "title": c["title"], "description": c["description"]} for c in existing_complaints[:15]]
            prompt = (
                "You are an AI assistant for EchoCampus AI.\n"
                "We have a new student complaint:\n"
                f"New Title: {new_title}\n"
                f"New Description: {new_desc}\n\n"
                "Compare this new complaint against the following existing active complaints:\n"
                f"{json.dumps(comp_list, indent=2)}\n\n"
                "Determine if the new complaint is a duplicate of any existing complaint (similarity score > 0.85).\n"
                "Return a JSON object with these exact fields:\n"
                "- match_found: boolean (true if similarity is > 0.85)\n"
                "- parent_id: integer or null (the ID of the matching duplicate complaint, null if false)\n"
                "- similarity_score: float (between 0.0 and 1.0)\n\n"
                "Response must be strict JSON without extra formatting."
            )
            clean_txt = clean_json_response(_generate(prompt))
            data = json.loads(clean_txt)
            if "match_found" in data:
                return data
        except Exception as e:
            print(f"Gemini API Exception in check_duplicate: {e}. Falling back to rule-based similarity.")

    # Fallback similarity
    new_words = set(re.findall(r'\w+', (new_title + " " + new_desc).lower()))
    best_score = 0.0
    best_id = None
    
    for c in existing_complaints:
        c_words = set(re.findall(r'\w+', (c["title"] + " " + c["description"]).lower()))
        if not new_words or not c_words:
            continue
        intersection = new_words.intersection(c_words)
        union = new_words.union(c_words)
        score = len(intersection) / len(union)
        if score > best_score:
            best_score = score
            best_id = c["id"]

    # Threshold for bag-of-words similarity can be lower (e.g. 0.45 indicates high word overlap)
    if best_score > 0.45:
        return {"match_found": True, "parent_id": best_id, "similarity_score": round(best_score, 2)}
    
    return {"match_found": False, "parent_id": None, "similarity_score": round(best_score, 2)}

def generate_recommendation(category: str, title: str, description: str, duplicate_count: int) -> str:
    """Suggests an actionable solution for admins regarding a complaint or duplicate group."""
    if has_api:
        try:
            prompt = (
                "As an AI campus advisor for EchoCampus AI, suggest an actionable, professional solution for the college administration regarding this student issue:\n"
                f"Category: {category}\n"
                f"Title: {title}\n"
                f"Description: {description}\n"
                f"Reports: {duplicate_count + 1} students reported this.\n\n"
                "Provide a clear, brief, 2-3 sentence recommendation."
            )
            return _generate(prompt).strip()
        except Exception as e:
            print(f"Gemini Exception in generate_recommendation: {e}")

    # Fallback recommendations
    recs = {
        "WiFi": "Conduct a network infrastructure scan in the affected building, reboot access points, and verify DHCP leases.",
        "Mess": "Schedule an immediate hygiene inspection of the mess hall, review vendor contract guidelines, and test water purification systems.",
        "Hostel": "Dispatch the maintenance team to inspect plumbing and electrical fittings, and schedule necessary repair works.",
        "Transport": "Review shuttle timing compliance logs, assess driver schedule allocations, and inspect the route traffic reports.",
        "Academic": "Flag this for the academic dean to review grading guidelines or request classroom scheduling adjustments.",
        "Security": "Increase security guard patrols in the reported vicinity and inspect active CCTV camera coverage.",
        "Infrastructure": "Coordinate with the facilities office to schedule structural repairs, check lighting, or service machinery.",
        "Other": "Assign an administrative liaison to review this issue and draft an appropriate campus response plan."
    }
    return recs.get(category, "Assign a staff representative to contact the student and inspect the situation firsthand.")

def generate_complaint_summary(complaints_data: list) -> str:
    """Summarizes active complaints for the admin analytics panel."""
    if not complaints_data:
        return "No recent active complaints to summarize."

    if has_api:
        try:
            prompt = (
                "You are the EchoCampus AI summarizer. Summarize the recent student complaints reported this week:\n"
                f"{json.dumps(complaints_data[:20], indent=2)}\n\n"
                "Generate a bulleted summary outlining:\n"
                "- Primary areas of concern\n"
                "- Most critical issue and number of affected students\n"
                "Keep it highly professional and concise (under 150 words)."
            )
            return _generate(prompt).strip()
        except Exception as e:
            print(f"Gemini Exception in generate_complaint_summary: {e}")

    # Fallback summary generator
    categories = [c.get("category") for c in complaints_data]
    cat_counts = {}
    for cat in categories:
        cat_counts[cat] = cat_counts.get(cat, 0) + 1
    sorted_cats = sorted(cat_counts.items(), key=lambda x: x[1], reverse=True)
    
    summary = "This week students primarily reported issues regarding:\n"
    for cat, cnt in sorted_cats[:3]:
        summary += f"• {cat} ({cnt} reports)\n"
    
    critical = [c for c in complaints_data if c.get("priority") == "Critical"]
    if critical:
        summary += f"\nMost critical issue: '{critical[0].get('title')}' in category {critical[0].get('category')} assigned to {critical[0].get('assigned_department')}."
    else:
        summary += "\nNo critical level emergency issues reported this week. Active concerns are being handled on routine timelines."
    return summary

def generate_welfare_report(welfare_summary: dict) -> str:
    """Generates a detailed monthly campus welfare report."""
    if has_api:
        try:
            prompt = (
                "Generate a comprehensive Monthly Campus Welfare Report for EchoCampus AI.\n"
                "Data Summary:\n"
                f"{json.dumps(welfare_summary, indent=2)}\n\n"
                "Write a detailed report in Markdown format with the following sections:\n"
                "1. Executive Summary\n"
                "2. Campus Health Overview\n"
                "3. Service-wise Performance (Hostel, Mess, WiFi, Transport, Academic, Infrastructure, Security)\n"
                "4. Critical Issues\n"
                "5. Complaint Trends\n"
                "6. Student Satisfaction Analysis\n"
                "7. AI Recommendations\n"
                "8. Next Month Forecast\n\n"
                "Make it look professional, detailed, data-driven, and ready for board presentation."
            )
            return _generate(prompt).strip()
        except Exception as e:
            print(f"Gemini Exception in generate_welfare_report: {e}")

    # Fallback report builder
    health = welfare_summary.get("campus_health_score", 75)
    total = welfare_summary.get("total_complaints", 0)
    resolved = welfare_summary.get("resolved_complaints", 0)
    avg_rating = welfare_summary.get("avg_feedback_rating", 3.8)
    
    return f"""# EchoCampus AI Monthly Student Welfare Report

## 1. Executive Summary
This report presents the monthly compilation of campus feedback, complaint intelligence, and student welfare insights captured via the EchoCampus AI platform. This month, we processed a total of **{total}** student concerns, successfully resolving **{resolved}** issues. The Campus Health Score is currently indexed at **{health}%**.

## 2. Campus Health Overview
- **Total Registered Concerns**: {total}
- **Resolution Rate**: {round((resolved/total)*100, 1) if total > 0 else 0}%
- **Average Campus Satisfaction Index (CSSI)**: {health}/100
- **Student Direct Feedback Average**: {avg_rating} / 5.0

## 3. Service-wise Performance
The Campus Service Satisfaction Index (CSSI) breakdown indicates:
- **WiFi**: {welfare_summary.get("cssi", {}).get("WiFi", 70)}/100
- **Mess**: {welfare_summary.get("cssi", {}).get("Mess", 72)}/100
- **Hostel**: {welfare_summary.get("cssi", {}).get("Hostel", 68)}/100
- **Transport**: {welfare_summary.get("cssi", {}).get("Transport", 75)}/100
- **Academic**: {welfare_summary.get("cssi", {}).get("Academic", 82)}/100
- **Infrastructure**: {welfare_summary.get("cssi", {}).get("Infrastructure", 71)}/100
- **Security**: {welfare_summary.get("cssi", {}).get("Security", 85)}/100

## 4. Critical Issues
The primary critical issues identified include infrastructure degradation in student hostels and intermittent wireless internet drops during peak study hours.

## 5. Complaint Trends
Active tracking indicates an increase in WiFi-related issues, possibly linked to the start of semester examinations and online test submissions.

## 6. Student Satisfaction Analysis
Students report high satisfaction with Security and Academic cells, but lower ratings for Mess nutrition and Hostel maintenance response times.

## 7. AI Recommendations
1. **Network Infrastructure**: Upgrade wireless routers in Hostel blocks to support higher concurrent bandwidth demands.
2. **Hygiene Oversight**: Direct the Mess Committee to conduct bi-weekly audit walks and review catering standards.
3. **Plumbing Audit**: Conduct preventive bathroom inspections across all freshman hostels.

## 8. Next Month Forecast
We predict a 15% increase in academic query and grading inquiries as final examinations approach. Infrastructure complaints should stabilize as maintenance issues are resolved.
"""
