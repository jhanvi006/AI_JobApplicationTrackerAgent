**AI Job Application Assistant**
AI-powered assistant that helps job seekers analyze job descriptions, tailor resumes, track applications, and improve based on rejection feedback.

The system uses **Claude Opus 4.6** to perform semantic analysis between job descriptions and candidate profiles.

Unlike traditional static resumes, the system treats the candidate profile as a **dynamic state that evolves over time** based on application outcomes.

**Problem:**

Job seekers spend significant time:
- Understanding job descriptions
- Tailoring resumes for each role
- Tracking multiple applications
- Learning from interview rejections
This process is largely **manual and fragmented**.

**Solution:**

An AI-powered Job Application Assistant that supports candidates across the application lifecycle by:
- Analyzing job descriptions
- Tracking applications
- Learning from rejections
- Suggesting targeted improvements

---
**Core Modules:**

**1. Apply Module**
Analyzes job descriptions, extracts required skills, calculates a match percentage, and generates resume-tailoring insights.

**2. Application Tracker**
Tracks job applications across stages like Submitted → Interview → Selected / Not Selected.

**3. AI Rejection Analysis**
Analyzes rejection feedback to identify skill gaps and improvement areas.

**4. Global Learning Engine**
Identifies patterns across multiple rejections and suggests strategic improvements.

---
**Setup & Run**

Install dependencies:
`pip install -r requirements.txt`

Set your environment variable in a .env file:
`OPENAI_API_KEY=api_key_here`

Run the application with Streamlit:
`streamlit run app.py`

---
**Tech Stack**

- Python
- Streamlit | 
- Claude Opus 4.6
