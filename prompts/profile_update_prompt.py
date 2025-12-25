import json

def build_profile_update_prompt(
    current_user_profile_json: dict,
    recent_chat_history_text: str
) -> str:
    profile_str = json.dumps(current_user_profile_json, indent=2)

    return f"""
You are a Medical Data Architect.
Your task is to maintain a structured, long-term medical profile for a user.

CURRENT PROFILE:
{profile_str}

LATEST CHAT SESSION:
\"\"\"{recent_chat_history_text}\"\"\"

TASK:
- Detect permanent biological facts:
  Age, Gender, Allergies, Chronic Conditions, Surgeries, Ongoing Medications.
- Detect recurring patterns across conversations.
- Ignore temporary or one-time states.
- If the user explicitly stopped something, REMOVE it.
- Merge intelligently with existing data.

STRICT RULES:
- Do NOT infer facts without explicit evidence.
- Do NOT diagnose diseases.
- Output MUST be valid JSON ONLY.
- No markdown, no explanations.

OUTPUT JSON FORMAT:
{{
  "age": int | null,
  "gender": string | null,
  "allergies": ["string"],
  "chronic_conditions": ["string"],
  "active_medications": ["string"],
  "medical_summary": "Concise 2–3 sentence summary"
}}
"""