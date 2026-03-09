"""
ai_engine.py — OpenAI API integration and all LLM prompts
for the AI Job Application Assistant.
"""

import json
import os
from openai import OpenAI

# ---------------------------------------------------------------------------
# Client setup — reads API key from api.txt in the same directory
# ---------------------------------------------------------------------------

def _get_client() -> OpenAI:
    return OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def _chat(system_prompt: str, user_prompt: str, temperature: float = 0.4) -> str:
    """Send a chat completion request and return the assistant's text."""
    client = _get_client()
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        temperature=temperature,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    )
    return response.choices[0].message.content.strip()


def _extract_json(text: str) -> dict:
    """Robustly extract the first JSON object from LLM output."""
    # Try raw parse first
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    # Try to find JSON within markdown fences
    import re
    match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass
    # Last resort: find first { … }
    start = text.find("{")
    end = text.rfind("}") + 1
    if start != -1 and end > start:
        try:
            return json.loads(text[start:end])
        except json.JSONDecodeError:
            pass
    return {}


# ---------------------------------------------------------------------------
# LLM Task: Extract JD metadata
# ---------------------------------------------------------------------------

SYSTEM_EXTRACT_JD = """You are an expert HR analyst. Given a Job Description, extract the following fields and return ONLY a JSON object:
{
  "company_name": "<company name or 'Unknown'>",
  "role": "<job title>",
  "required_skills": ["skill1", "skill2", ...]
}
Do not include any other text or explanation."""


def extract_jd_metadata(jd_text: str) -> dict:
    """Extract company name, role, and required skills from a JD."""
    raw = _chat(SYSTEM_EXTRACT_JD, jd_text)
    result = _extract_json(raw)
    return {
        "company_name": result.get("company_name", "Unknown"),
        "role": result.get("role", "Unknown Role"),
        "required_skills": result.get("required_skills", []),
    }


# ---------------------------------------------------------------------------
# LLM Task: Extract structured profile from raw text
# ---------------------------------------------------------------------------

SYSTEM_EXTRACT_PROFILE = """You are an expert HR analyst and resume parser. Given the raw text extracted from a candidate's resume or profile document, extract structured data.

Carefully identify:
- Skills (technical skills, tools, methodologies, certifications)
- Strengths (core competencies, leadership qualities, domain expertise)
- Experience entries (each role with title, company, and a brief description)
- Weaknesses (leave empty unless explicitly mentioned)

Return ONLY a JSON object with exactly these keys:
{
  "skills": ["skill1", "skill2", ...],
  "strengths": ["strength1", "strength2", ...],
  "weaknesses": [],
  "experience": [
    {"title": "Job Title", "company": "Company Name", "description": "Brief summary of role and achievements"}
  ],
  "improvement_areas": []
}
Extract as many skills and strengths as you can find. For experience, include ALL roles mentioned.
Do not include any other text or explanation."""


def extract_profile_data(raw_text: str) -> dict:
    """Parse raw resume/profile text into structured profile state."""
    # Truncate to avoid exceeding model token limits
    truncated = raw_text[:15000] if len(raw_text) > 15000 else raw_text
    raw = _chat(SYSTEM_EXTRACT_PROFILE, truncated, temperature=0.2)
    result = _extract_json(raw)
    # Validate structure
    if "skills" in result and "experience" in result:
        result.setdefault("strengths", [])
        result.setdefault("weaknesses", [])
        result.setdefault("improvement_areas", [])
        return result
    # Fallback
    return {
        "skills": [],
        "strengths": [],
        "weaknesses": [],
        "experience": [raw_text[:500]],
        "improvement_areas": [],
    }


# ---------------------------------------------------------------------------
# LLM Task 1: Skill Matching & Analysis
# ---------------------------------------------------------------------------

SYSTEM_MATCH = """You are an expert AI Career Strategist. You will be given two inputs:
1. A Job Description (JD).
2. The candidate's current profile state (JSON).

Perform a deep semantic analysis — compare skills, experience, projects, and domain knowledge. Do NOT rely purely on keyword matching; evaluate conceptual alignment.

Return ONLY a JSON object with exactly these keys:
{
  "required_skills": ["skill1", "skill2", ...],
  "matching_skills": ["skill1", "skill2", ...],
  "missing_skills": ["skill1", "skill2", ...],
  "match_percentage": <integer 0-100>,
  "analysis_summary": "<2-3 sentence summary of how the candidate aligns>"
}
Do not include any other text or explanation."""


def analyze_jd_and_profile(jd_text: str, profile_state: dict) -> dict:
    """Analyze JD against candidate profile and return match data."""
    user_msg = (
        f"### Job Description\n{jd_text}\n\n"
        f"### Candidate Profile State\n{json.dumps(profile_state, indent=2)}"
    )
    raw = _chat(SYSTEM_MATCH, user_msg)
    result = _extract_json(raw)
    return {
        "required_skills": result.get("required_skills", []),
        "matching_skills": result.get("matching_skills", []),
        "missing_skills": result.get("missing_skills", []),
        "match_percentage": int(result.get("match_percentage", 0)),
        "analysis_summary": result.get("analysis_summary", ""),
    }


# ---------------------------------------------------------------------------
# LLM Task 2: Rejection Analysis & Profile Evolution
# ---------------------------------------------------------------------------

SYSTEM_REJECTION = """You are an expert AI Career Strategist. You will receive:
1. The original Job Description (JD) for a role the candidate was rejected from.
2. The candidate's free-text rejection notes (interview feedback, what went wrong).
3. The candidate's current_profile_state (JSON).

Your task:
- Analyze the failure in detail.
- Identify specific skill gaps, struggled topics, or mismatched experience.
- Return an UPDATED current_profile_state JSON that:
  • Downgrades confidence in the failed/weak skills (move them to weaknesses or annotate).
  • Adds targeted improvement areas under "improvement_areas".
  • Preserves all original strengths and skills not related to the failure.
  • Does NOT overwrite the original profile text — only modify the active cognitive state.

Return ONLY the updated current_profile_state as a JSON object, no other text."""


def analyze_rejection(jd_text: str, rejection_notes: str, profile_state: dict) -> dict:
    """Analyze rejection and return updated profile state."""
    user_msg = (
        f"### Job Description\n{jd_text}\n\n"
        f"### Rejection Notes\n{rejection_notes}\n\n"
        f"### Current Profile State\n{json.dumps(profile_state, indent=2)}"
    )
    raw = _chat(SYSTEM_REJECTION, user_msg, temperature=0.3)
    result = _extract_json(raw)
    # Validate structure
    if "strengths" in result and "skills" in result:
        return result
    # If LLM returned something unexpected, return original with a note
    profile_state.setdefault("improvement_areas", [])
    profile_state["improvement_areas"].append(
        "AI analysis returned unexpected format — manual review recommended."
    )
    return profile_state


# ---------------------------------------------------------------------------
# LLM Task 3: Global / Macro Pattern Analysis
# ---------------------------------------------------------------------------

SYSTEM_GLOBAL = """You are a warm, encouraging AI Career Coach. You will receive a JSON list of all rejected applications. Each entry contains:
- company_name, role, jd_text, rejection_notes, ai_analysis_summary

Your task:
Synthesize the data across ALL rejections to help the candidate grow. Be supportive, constructive, and positive — the candidate should feel motivated, never intimidated.

Return ONLY a JSON object with exactly these keys:
{
  "improvement_pointers": [
    "A concise, encouraging one-sentence improvement action as a bullet point"
  ],
  "recurring_gaps_summary": "A brief, friendly summary of patterns noticed across rejections — frame gaps as growth opportunities, not failures",
  "strategic_advice": "Warm, actionable strategic advice for the next application cycle — emphasize the candidate's potential and concrete next steps",
  "recommended_courses": [
    {
      "course_name": "Specific course name (e.g., 'System Design Interview by Alex Xu')",
      "platform": "Platform name (e.g., 'Educative', 'Coursera', 'Udemy')",
      "covers": "Brief note on which skill gap this addresses"
    }
  ]
}

Rules:
- Generate exactly 3-4 improvement pointers. Keep them short, specific, and encouraging.
- Generate at most 3 recommended courses. Each must be a real, relevant course that addresses the identified skill gaps.
- Use a friendly, supportive coaching tone throughout. Frame everything as growth opportunities.
- Do not include any text outside the JSON object."""


def generate_global_analysis(applications: list) -> dict:
    """Generate a macro-pattern analysis across all rejected applications.

    Returns a dict with keys: improvement_pointers, recurring_gaps_summary,
    strategic_advice, recommended_courses.
    """
    # Filter to only rejected / not-selected applications
    rejected = [
        {
            "company_name": app.get("company_name", ""),
            "role": app.get("role", ""),
            "jd_text": app.get("jd_text", "")[:500],  # truncate to save tokens
            "rejection_notes": app.get("rejection_notes", ""),
            "ai_analysis_summary": app.get("ai_analysis_summary", ""),
        }
        for app in applications
        if app.get("status") == "Not Selected"
    ]
    if not rejected:
        return {
            "improvement_pointers": [],
            "recurring_gaps_summary": "No rejected applications found. Submit and track applications first.",
            "strategic_advice": "",
            "recommended_courses": [],
        }

    user_msg = f"### Rejected Applications\n{json.dumps(rejected, indent=2)}"
    raw = _chat(SYSTEM_GLOBAL, user_msg, temperature=0.5)
    result = _extract_json(raw)
    return {
        "improvement_pointers": result.get("improvement_pointers", []),
        "recurring_gaps_summary": result.get("recurring_gaps_summary", ""),
        "strategic_advice": result.get("strategic_advice", ""),
        "recommended_courses": result.get("recommended_courses", []),
    }


# ---------------------------------------------------------------------------
# Resume Tailoring Summary
# ---------------------------------------------------------------------------

SYSTEM_RESUME_SUMMARY = """You are an expert AI Career Strategist. You have just generated a tailored resume for a candidate.

You will receive:
1. The candidate's profile state (JSON with strengths, weaknesses, skills, experience, improvement_areas).
2. The JD match analysis (matching skills, missing skills, match percentage, company, role).

Write exactly 6-7 concise bullet points summarizing what specific changes and optimizations were made to tailor the resume. Each bullet should be one sentence. Focus on:
- Which skills were prioritized and reordered to match the JD
- Which strengths were highlighted
- Any weak skills that were de-emphasized
- How experience was aligned to the target role
- Any improvement areas that were subtly incorporated
- How the overall layout was optimized for the specific role

Return ONLY a JSON object:
{
  "summary_points": ["point 1", "point 2", "point 3", "point 4", "point 5", "point 6", "point 7"]
}
Do not include any other text."""


def generate_resume_summary(profile_state: dict, jd_data: dict) -> list:
    """Generate 6-7 bullet points summarizing resume tailoring changes."""
    user_msg = (
        f"### Candidate Profile State\n{json.dumps(profile_state, indent=2)}\n\n"
        f"### JD Match Analysis\n{json.dumps(jd_data, indent=2)}"
    )
    raw = _chat(SYSTEM_RESUME_SUMMARY, user_msg, temperature=0.4)
    result = _extract_json(raw)
    points = result.get("summary_points", [])
    if not points:
        return ["Resume was tailored to match the target job description."]
    return points


# ---------------------------------------------------------------------------
# Revised Match Score After Tailoring
# ---------------------------------------------------------------------------

SYSTEM_REVISED_SCORE = """You are an expert AI Career Strategist. A candidate's resume has been tailored to match a specific Job Description.

You will receive:
1. The original match percentage before tailoring.
2. The candidate's profile state (skills, strengths, experience).
3. The JD match analysis (matching skills, missing skills, role, company).

Evaluate how the tailored resume now aligns with the JD. The tailored resume:
- Reordered skills to prioritize JD requirements first
- Highlighted relevant strengths and experience
- De-emphasized weak or irrelevant areas
- Optimized the overall presentation for this specific role

Return ONLY a JSON object:
{
  "revised_score": <integer 0-100, should be higher than original since resume is now tailored>,
  "explanation": [
    "Line 1: Brief explanation of the main improvement",
    "Line 2: What specific tailoring boosted the score",
    "Line 3: Summary of overall alignment improvement"
  ]
}
The revised score should realistically reflect the improvement from tailoring (typically 5-15% higher).
Do not include any other text."""


def generate_revised_score(original_score: int, profile_state: dict, jd_data: dict) -> dict:
    """Generate a revised match score and 3-line explanation after resume tailoring."""
    user_msg = (
        f"### Original Match Score\n{original_score}%\n\n"
        f"### Candidate Profile State\n{json.dumps(profile_state, indent=2)}\n\n"
        f"### JD Match Analysis\n{json.dumps(jd_data, indent=2)}"
    )
    raw = _chat(SYSTEM_REVISED_SCORE, user_msg, temperature=0.4)
    result = _extract_json(raw)
    return {
        "revised_score": int(result.get("revised_score", original_score)),
        "explanation": result.get("explanation", [
            "Resume has been tailored to better match the target role."
        ]),
    }
