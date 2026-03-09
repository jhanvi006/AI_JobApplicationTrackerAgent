"""
app.py — AI Job Application Assistant
Main Streamlit application with 4 tabs:
  Tab 1: Apply (Resume Preparation)
  Tab 2: Tracking (Application Tracker)
  Tab 3: Not Selected (Rejection Analysis)
  Tab 4: Global Analysis
"""

import streamlit as st
import json
import datetime
from dotenv import load_dotenv
load_dotenv()
from utils import load_data, save_data, get_empty_schema, extract_text
from ai_engine import (
    extract_jd_metadata,
    extract_profile_data,
    analyze_jd_and_profile,
    analyze_rejection,
    generate_global_analysis,
    generate_resume_summary,
    generate_revised_score,
)
from pdf_generator import generate_resume
from email_sender import send_status_email

# ---------------------------------------------------------------------------
# Page config & custom CSS
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="AI Job Application Assistant",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
    /* ---- Global ---- */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

    /* ---- Sidebar ---- */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0F3460 0%, #1A1A2E 100%);
    }
    section[data-testid="stSidebar"] * {
        color: #E0E0E0 !important;
    }
    section[data-testid="stSidebar"] h1,
    section[data-testid="stSidebar"] h2,
    section[data-testid="stSidebar"] h3 {
        color: #FFFFFF !important;
    }

    /* ---- Tab styling ---- */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background: linear-gradient(90deg, #0F3460, #1A1A2E);
        border-radius: 12px;
        padding: 6px 10px;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px;
        padding: 10px 20px;
        color: #B0B0B0;
        font-weight: 500;
    }
    .stTabs [aria-selected="true"] {
        background: rgba(233, 69, 96, 0.15) !important;
        color: #E94560 !important;
        font-weight: 700;
        border-bottom: 3px solid #E94560;
    }

    /* ---- Metric cards (sidebar only) ---- */
    section[data-testid="stSidebar"] div[data-testid="stMetric"] {
        background: linear-gradient(135deg, #0F3460 0%, #1A1A2E 100%);
        border-radius: 12px;
        padding: 16px 20px;
        color: white;
        box-shadow: 0 4px 15px rgba(15, 52, 96, 0.3);
    }
    section[data-testid="stSidebar"] div[data-testid="stMetric"] label {
        color: #B0B0B0 !important;
    }
    section[data-testid="stSidebar"] div[data-testid="stMetric"] [data-testid="stMetricValue"] {
        color: #FFFFFF !important;
        font-weight: 700;
    }

    /* ---- Metric cards (main content) ---- */
    .main div[data-testid="stMetric"] {
        background: #FFFFFF;
        border: 1px solid #E0E0E0;
        border-radius: 12px;
        padding: 16px 20px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.06);
    }
    .main div[data-testid="stMetric"] label {
        color: #666666 !important;
    }
    .main div[data-testid="stMetric"] [data-testid="stMetricValue"] {
        color: #1A1A2E !important;
        font-weight: 700;
    }

    /* ---- Buttons ---- */
    .stButton > button {
        border-radius: 8px;
        font-weight: 600;
        transition: all 0.3s ease;
        border: none;
    }
    .stButton > button:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(233, 69, 96, 0.4);
    }

    /* ---- Status badges ---- */
    .status-submitted {
        background: #4CAF50; color: white; padding: 4px 12px;
        border-radius: 20px; font-size: 0.8em; font-weight: 600;
        display: inline-block; animation: pulse 2s infinite;
    }
    .status-interview {
        background: #FF9800; color: white; padding: 4px 12px;
        border-radius: 20px; font-size: 0.8em; font-weight: 600;
        display: inline-block;
    }
    .status-selected {
        background: #2196F3; color: white; padding: 4px 12px;
        border-radius: 20px; font-size: 0.8em; font-weight: 600;
        display: inline-block;
    }
    .status-not-selected {
        background: #E94560; color: white; padding: 4px 12px;
        border-radius: 20px; font-size: 0.8em; font-weight: 600;
        display: inline-block;
    }
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.6; }
    }

    /* ---- Cards ---- */
    .app-card {
        background: #FFFFFF;
        border: 1px solid #D0D0D0;
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 12px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.06);
        transition: all 0.2s ease;
        color: #1A1A1A;
    }
    .app-card:hover {
        box-shadow: 0 4px 16px rgba(0,0,0,0.12);
    }

    /* ---- Header banner ---- */
    .hero-banner {
        background: linear-gradient(135deg, #0F3460 0%, #1A1A2E 60%, #E94560 100%);
        border-radius: 16px;
        padding: 28px 32px;
        color: white;
        margin-bottom: 24px;
    }
    .hero-banner h1 { color: white; margin: 0; font-size: 1.8em; }
    .hero-banner p { color: #D0D0D0; margin: 8px 0 0 0; font-size: 0.95em; }
</style>
""", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------

with st.sidebar:
    st.markdown("## 🚀 AI Job Assistant")
    st.markdown("---")

    data = load_data()
    total_apps = len(data.get("applications", []))
    active = sum(1 for a in data.get("applications", []) if a.get("status") not in ("Not Selected", "Selected"))
    rejected = sum(1 for a in data.get("applications", []) if a.get("status") == "Not Selected")

    st.metric("Total Applications", total_apps)
    st.metric("Active Pipeline", active)
    st.metric("Rejected", rejected)

    st.markdown("---")

    # ---- Clear All Data ----
    if st.button("🗑️ Clear All Data", use_container_width=True, type="secondary"):
        st.session_state["confirm_clear"] = True

    if st.session_state.get("confirm_clear"):
        st.warning("⚠️ This will permanently delete all data!")
        col_y, col_n = st.columns(2)
        with col_y:
            if st.button("✅ Confirm", use_container_width=True):
                save_data(get_empty_schema())
                st.session_state.clear()
                st.rerun()
        with col_n:
            if st.button("❌ Cancel", use_container_width=True):
                st.session_state["confirm_clear"] = False
                st.rerun()


# ---------------------------------------------------------------------------
# Hero Banner
# ---------------------------------------------------------------------------

st.markdown("""
<div class="hero-banner">
    <h1>🚀 AI Job Application Assistant</h1>
    <p>Intelligent resume tailoring • Application tracking • AI-powered career evolution</p>
</div>
""", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Helper: render profile state as plain text summary
# ---------------------------------------------------------------------------

def _render_profile_summary(profile: dict):
    """Render the profile state dict as a readable plain text summary."""
    html = (
        "<div style='background:#FFFFFF;border:1px solid #D0D0D0;border-radius:12px;"
        "padding:20px 24px;font-size:0.93em;line-height:1.7;color:#1A1A1A;'>"
    )

    # Skills
    skills = profile.get("skills", [])
    if skills:
        html += "<div style='margin-bottom:16px;'>"
        html += "<strong style='color:#0D2137;font-size:1.05em;'>🛠️ Skills</strong><br>"
        badges = " ".join(
            f"<span style='background:#1A237E;color:#FFFFFF;padding:4px 12px;"
            f"border-radius:14px;margin:3px;display:inline-block;font-size:0.85em;"
            f"font-weight:500;'>{s}</span>"
            for s in skills
        )
        html += badges + "</div>"

    # Strengths
    strengths = profile.get("strengths", [])
    if strengths:
        html += "<div style='margin-bottom:16px;'>"
        html += "<strong style='color:#0D2137;font-size:1.05em;'>💪 Strengths</strong><br>"
        for s in strengths:
            html += f"<div style='margin-left:8px;color:#1A1A1A;'>• {s}</div>"
        html += "</div>"

    # Experience
    experience = profile.get("experience", [])
    if experience:
        html += "<div style='margin-bottom:16px;'>"
        html += "<strong style='color:#0D2137;font-size:1.05em;'>💼 Experience</strong><br>"
        for exp in experience:
            if isinstance(exp, dict):
                title = exp.get("title", exp.get("role", ""))
                company = exp.get("company", "")
                desc = exp.get("description", "")
                line = f"<strong style='color:#1A1A1A;'>{title}</strong>"
                if company:
                    line += f" — <span style='color:#333;'>{company}</span>"
                html += f"<div style='margin-left:8px;margin-bottom:6px;'>{line}"
                if desc:
                    html += f"<br><span style='color:#444;font-size:0.9em;'>{desc}</span>"
                html += "</div>"
            else:
                html += f"<div style='margin-left:8px;color:#1A1A1A;'>• {exp}</div>"
        html += "</div>"

    # Weaknesses
    weaknesses = profile.get("weaknesses", [])
    if weaknesses:
        html += "<div style='margin-bottom:16px;'>"
        html += "<strong style='color:#0D2137;font-size:1.05em;'>📌 Areas to Watch</strong><br>"
        for w in weaknesses:
            w_text = w if isinstance(w, str) else w.get("skill", str(w))
            html += f"<div style='margin-left:8px;color:#1A1A1A;'>• {w_text}</div>"
        html += "</div>"

    # Improvement areas
    improvements = profile.get("improvement_areas", [])
    if improvements:
        html += "<div style='margin-bottom:16px;'>"
        html += "<strong style='color:#0D2137;font-size:1.05em;'>🌱 Improvement Areas</strong><br>"
        for item in improvements:
            html += f"<div style='margin-left:8px;color:#1A1A1A;'>• {item}</div>"
        html += "</div>"

    html += "</div>"
    st.markdown(html, unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Tabs
# ---------------------------------------------------------------------------

tab1, tab2, tab3, tab4 = st.tabs([
    "📝 Apply", "📊 Tracking", "❌ Not Selected", "🌐 Global Analysis"
])


# =========================================================================
# TAB 1 — APPLY
# =========================================================================
with tab1:
    st.subheader("Resume Preparation & Match Analysis")

    # Reset counter drives dynamic widget keys so uploaders can be fully cleared
    if "reset_counter" not in st.session_state:
        st.session_state["reset_counter"] = 0
    rc = st.session_state["reset_counter"]

    col_left, col_right = st.columns([1, 1], gap="large")

    with col_left:
        st.markdown("##### 📄 Upload Your Profile")
        profile_file = st.file_uploader(
            "Candidate Profile (.pdf / .txt / .docx)",
            type=["pdf", "txt", "docx"],
            key=f"profile_upload_{rc}",
        )

        st.markdown("##### 📋 Reference Resume *(optional)*")
        ref_file = st.file_uploader(
            "Reference Resume (.pdf / .docx)",
            type=["pdf", "docx"],
            key=f"ref_upload_{rc}",
        )

    with col_right:
        st.markdown("##### 💼 Job Description")
        jd_text = st.text_area(
            "Paste the full Job Description here",
            height=280,
            key=f"jd_input_{rc}",
            placeholder="Paste the complete job description including requirements, responsibilities, and qualifications...",
        )

    # ---- Process uploads ----
    if profile_file:
        # Detect new file upload by tracking file identity (name + size)
        file_identity = f"{profile_file.name}_{profile_file.size}"
        if st.session_state.get("profile_file_id") != file_identity:
            with st.spinner("Extracting profile text..."):
                st.session_state["profile_text"] = extract_text(profile_file)
                st.session_state["profile_file_id"] = file_identity
                # Clear any prior analysis when a new profile is uploaded
                for key in ["match_result", "jd_meta", "pdf_bytes", "resume_ready", "download_done", "resume_summary", "resume_prepared_at"]:
                    st.session_state.pop(key, None)

            # Use AI to extract structured profile data from raw text
            data["original_profile"] = st.session_state["profile_text"]
            with st.spinner("🧠 AI is parsing your profile into structured data..."):
                structured_profile = extract_profile_data(st.session_state["profile_text"])
                data["current_profile_state"] = structured_profile
            save_data(data)
            st.success(f"✅ Profile parsed: {len(structured_profile.get('skills', []))} skills, "
                       f"{len(structured_profile.get('strengths', []))} strengths, "
                       f"{len(structured_profile.get('experience', []))} experience entries extracted.")

    # Show profile preview
    if st.session_state.get("profile_text"):
        with st.expander("👁️ Profile Preview", expanded=False):
            st.text(st.session_state["profile_text"][:2000])
        # Show extracted structured data as plain text summary
        profile_state = data.get("current_profile_state", {})
        if profile_state.get("skills"):
            with st.expander("🧬 Extracted Profile Summary", expanded=False):
                _render_profile_summary(profile_state)

    st.markdown("---")

    # ---- Analyze Match ----
    analyze_disabled = not (st.session_state.get("profile_text") and jd_text)
    if st.button(
        "🔍 Analyze Match",
        disabled=analyze_disabled,
        use_container_width=True,
        type="primary",
    ):
        with st.spinner("🤖 AI is analyzing the job description and your profile..."):
            jd_meta = extract_jd_metadata(jd_text)
            profile_state = data.get("current_profile_state", {})
            # Pass the full raw profile text as additional context for better matching
            profile_state["_raw_profile_text"] = st.session_state.get("profile_text", "")[:3000]
            match_result = analyze_jd_and_profile(jd_text, profile_state)
            # Remove temporary key
            profile_state.pop("_raw_profile_text", None)

            st.session_state["jd_meta"] = jd_meta
            st.session_state["match_result"] = match_result

    # ---- Display results ----
    if st.session_state.get("match_result"):
        jd_meta = st.session_state["jd_meta"]
        match = st.session_state["match_result"]

        st.success("✅ Analysis Complete!")

        m1, m2, m3 = st.columns(3)
        m1.metric("🏢 Company", jd_meta.get("company_name", "Unknown"))
        m2.metric("💼 Role", jd_meta.get("role", "Unknown"))
        m3.metric("📊 Match Score", f"{match.get('match_percentage', 0)}%")

        col_match, col_miss = st.columns(2)
        with col_match:
            st.markdown("##### ✅ Matching Skills")
            matching = match.get("matching_skills", [])
            if matching:
                for s in matching:
                    st.markdown(f"<span style='background:#4CAF50;color:white;padding:3px 10px;border-radius:12px;margin:2px;display:inline-block;font-size:0.85em'>{s}</span>", unsafe_allow_html=True)
            else:
                st.info("No direct skill matches found.")

        with col_miss:
            st.markdown("##### ⚠️ Missing Skills")
            missing = match.get("missing_skills", [])
            if missing:
                for s in missing:
                    st.markdown(f"<span style='background:#FF9800;color:white;padding:3px 10px;border-radius:12px;margin:2px;display:inline-block;font-size:0.85em'>{s}</span>", unsafe_allow_html=True)
            else:
                st.success("All required skills matched!")

        if match.get("analysis_summary"):
            with st.expander("📝 AI Analysis Summary"):
                st.markdown(match["analysis_summary"])

        # ---- Reset & Start Fresh ----
        st.markdown("---")
        st.markdown(
            "<div style='text-align:center;margin:8px 0 4px 0;'>"
            "<span style='color:#888;font-size:0.9em;'>Not satisfied? Want to try a different role or profile?</span>"
            "</div>",
            unsafe_allow_html=True,
        )
        if st.button("🔄 Reset & Start Fresh", use_container_width=True, type="secondary"):
            # Clear all analysis and context data
            for key in [
                "match_result", "jd_meta", "pdf_bytes", "resume_ready",
                "download_done", "profile_text", "profile_file_id",
                "resume_summary", "resume_prepared_at",
                "original_profile_snapshot", "tailored_jd_data",
                "revised_score_data", "original_score",
            ]:
                st.session_state.pop(key, None)
            # Increment reset counter to force fresh file uploaders & JD text area
            st.session_state["reset_counter"] = st.session_state.get("reset_counter", 0) + 1
            st.rerun()

        st.markdown("---")

        # ---- Generate Resume ----
        if st.button("📄 Prepare Resume", use_container_width=True, type="primary"):
            # Save a snapshot of original profile before tailoring
            import copy
            st.session_state["original_profile_snapshot"] = copy.deepcopy(data["current_profile_state"])

            with st.spinner("🔨 Generating tailored PDF resume..."):
                ref_style = None
                if ref_file:
                    ref_style = {"raw": extract_text(ref_file)}

                combined_jd = {**jd_meta, **match}

                # Try to guess candidate name from profile
                raw_profile = st.session_state.get("profile_text", "")
                first_line = raw_profile.strip().split("\n")[0] if raw_profile else "Candidate"
                cand_name = first_line[:60] if len(first_line) < 60 else "Candidate"

                pdf_bytes = generate_resume(
                    profile_data=data["current_profile_state"],
                    jd_data=combined_jd,
                    candidate_name=cand_name,
                    reference_style=ref_style,
                )
                st.session_state["pdf_bytes"] = pdf_bytes
                st.session_state["resume_ready"] = True
                st.session_state["resume_prepared_at"] = datetime.datetime.now().strftime("%B %d, %Y at %I:%M %p")
                st.session_state["tailored_jd_data"] = combined_jd

            # Generate tailoring summary
            with st.spinner("📝 Summarizing resume changes..."):
                summary_points = generate_resume_summary(
                    profile_state=data["current_profile_state"],
                    jd_data=combined_jd,
                )
                st.session_state["resume_summary"] = summary_points

            # Generate revised match score
            with st.spinner("📊 Re-evaluating match score for tailored resume..."):
                original_score = match.get("match_percentage", 0)
                revised = generate_revised_score(
                    original_score=original_score,
                    profile_state=data["current_profile_state"],
                    jd_data=combined_jd,
                )
                st.session_state["revised_score_data"] = revised
                st.session_state["original_score"] = original_score

        # ---- Download + Summary ----
        if st.session_state.get("resume_ready"):
            st.success("🎉 Resume generated successfully!")

            # Show preparation timestamp
            prepared_at = st.session_state.get("resume_prepared_at", "")
            if prepared_at:
                st.markdown(
                    f"<div style='background:#FFFFFF;border-left:4px solid #0F3460;"
                    f"padding:12px 16px;border-radius:0 8px 8px 0;margin-bottom:16px;"
                    f"color:#333333;'>"
                    f"🕐 <strong style='color:#1A1A2E;'>Resume Prepared:</strong> "
                    f"<span style='color:#333333;'>{prepared_at}</span>"
                    f"</div>",
                    unsafe_allow_html=True,
                )

            # Show tailoring summary as a single HTML block
            summary_points = st.session_state.get("resume_summary", [])
            if summary_points:
                st.markdown("##### 📋 Resume Tailoring Summary")
                summary_html = (
                    "<div style='background:#FFFFFF;border:1px solid #E0E0E0;"
                    "border-radius:12px;padding:20px 24px;margin-bottom:16px;"
                    "box-shadow:0 2px 8px rgba(0,0,0,0.06);'>"
                )
                for i, point in enumerate(summary_points, 1):
                    summary_html += (
                        f"<div style='display:flex;align-items:flex-start;margin-bottom:10px;'>"
                        f"<span style='background:#0F3460;color:#FFFFFF;border-radius:50%;"
                        f"min-width:26px;height:26px;display:inline-flex;align-items:center;"
                        f"justify-content:center;font-size:0.75em;font-weight:700;"
                        f"margin-right:12px;flex-shrink:0;'>{i}</span>"
                        f"<span style='color:#333333;font-size:0.92em;line-height:1.5;'>{point}</span>"
                        f"</div>"
                    )
                summary_html += "</div>"
                st.markdown(summary_html, unsafe_allow_html=True)

            # ---- Revised Match Score ----
            revised_data = st.session_state.get("revised_score_data", {})
            orig_score = st.session_state.get("original_score", 0)
            if revised_data:
                revised_score = revised_data.get("revised_score", orig_score)
                explanation = revised_data.get("explanation", [])
                score_diff = revised_score - orig_score

                st.markdown("##### 📊 Revised Match Score")
                score_html = (
                    "<div style='background:#FFFFFF;border:1px solid #D0D0D0;"
                    "border-radius:12px;padding:20px 24px;margin-bottom:16px;"
                    "box-shadow:0 2px 6px rgba(0,0,0,0.05);'>"
                    "<div style='display:flex;align-items:center;justify-content:center;gap:24px;margin-bottom:16px;'>"
                    # Original score
                    f"<div style='text-align:center;'>"
                    f"<div style='color:#666;font-size:0.8em;font-weight:500;'>ORIGINAL</div>"
                    f"<div style='background:#E0E0E0;color:#333;font-size:1.8em;font-weight:700;"
                    f"padding:10px 20px;border-radius:12px;min-width:80px;'>{orig_score}%</div>"
                    f"</div>"
                    # Arrow
                    f"<div style='font-size:1.8em;color:#4CAF50;'>→</div>"
                    # Revised score
                    f"<div style='text-align:center;'>"
                    f"<div style='color:#1B5E20;font-size:0.8em;font-weight:500;'>TAILORED</div>"
                    f"<div style='background:#2E7D32;color:#FFFFFF;font-size:1.8em;font-weight:700;"
                    f"padding:10px 20px;border-radius:12px;min-width:80px;'>{revised_score}%</div>"
                    f"</div>"
                )
                if score_diff > 0:
                    score_html += (
                        f"<div style='background:#E8F5E9;color:#1B5E20;padding:4px 14px;"
                        f"border-radius:20px;font-weight:600;font-size:0.9em;'>▲ +{score_diff}%</div>"
                    )
                score_html += "</div>"

                # Explanation lines
                if explanation:
                    score_html += "<div style='border-top:1px solid #E0E0E0;padding-top:12px;'>"
                    for line in explanation[:3]:
                        score_html += (
                            f"<div style='color:#333;font-size:0.9em;line-height:1.6;margin-bottom:4px;'>"
                            f"✦ {line}</div>"
                        )
                    score_html += "</div>"

                score_html += "</div>"
                st.markdown(score_html, unsafe_allow_html=True)

            # ---- Side-by-Side Comparison ----
            original_snap = st.session_state.get("original_profile_snapshot", {})
            tailored_jd = st.session_state.get("tailored_jd_data", {})
            if original_snap and tailored_jd:
                with st.expander("🔍 Original vs Tailored Resume Comparison", expanded=False):
                    col_orig, col_tailored = st.columns(2)

                    matching_skills = set(
                        s.lower() for s in tailored_jd.get("matching_skills", [])
                    )
                    all_orig_skills = original_snap.get("skills", [])
                    tailored_matching = tailored_jd.get("matching_skills", [])
                    tailored_other = [
                        s for s in all_orig_skills
                        if s.lower() not in matching_skills
                    ]
                    reordered_skills = tailored_matching + tailored_other

                    # ---- Build ORIGINAL column as single HTML ----
                    orig_html = (
                        "<div style='background:#FFFFFF;border:1px solid #D0D0D0;"
                        "border-radius:12px;padding:16px 18px;'>"
                        "<h4 style='color:#0D2137;margin:0 0 14px 0;font-size:1.05em;'>"
                        "📄 Original Profile</h4>"
                        "<strong style='color:#0D2137;font-size:0.92em;'>Skills</strong><br>"
                    )
                    for s in all_orig_skills:
                        orig_html += (
                            f"<span style='background:#E0E0E0;color:#333;padding:3px 10px;"
                            f"border-radius:12px;margin:2px;display:inline-block;"
                            f"font-size:0.82em;'>{s}</span>"
                        )
                    if not all_orig_skills:
                        orig_html += "<span style='color:#999;'>None</span>"

                    orig_html += "<br><br><strong style='color:#0D2137;font-size:0.92em;'>Strengths</strong><br>"
                    for s in original_snap.get("strengths", []):
                        orig_html += f"<div style='color:#1A1A1A;margin-left:6px;font-size:0.88em;'>• {s}</div>"

                    orig_html += "<br><strong style='color:#0D2137;font-size:0.92em;'>Experience</strong><br>"
                    for exp in original_snap.get("experience", []):
                        if isinstance(exp, dict):
                            title = exp.get("title", exp.get("role", ""))
                            company = exp.get("company", "")
                            orig_html += (
                                f"<div style='color:#1A1A1A;margin-left:6px;font-size:0.88em;margin-bottom:4px;'>"
                                f"• <strong>{title}</strong>{' — ' + company if company else ''}</div>"
                            )
                        else:
                            orig_html += f"<div style='color:#1A1A1A;margin-left:6px;font-size:0.88em;'>• {exp}</div>"
                    orig_html += "</div>"

                    with col_orig:
                        st.markdown(orig_html, unsafe_allow_html=True)

                    # ---- Build TAILORED column as single HTML ----
                    tail_html = (
                        "<div style='background:#F0FFF0;border:1px solid #A5D6A7;"
                        "border-radius:12px;padding:16px 18px;'>"
                        "<h4 style='color:#1B5E20;margin:0 0 14px 0;font-size:1.05em;'>"
                        "✨ Tailored Resume</h4>"
                        "<strong style='color:#1B5E20;font-size:0.92em;'>Skills (reordered for JD)</strong><br>"
                    )
                    for s in reordered_skills:
                        if s.lower() in matching_skills:
                            tail_html += (
                                f"<span style='background:#2E7D32;color:#FFFFFF;padding:3px 10px;"
                                f"border-radius:12px;margin:2px;display:inline-block;"
                                f"font-size:0.82em;font-weight:600;'>✓ {s}</span>"
                            )
                        else:
                            tail_html += (
                                f"<span style='background:#E0E0E0;color:#333;padding:3px 10px;"
                                f"border-radius:12px;margin:2px;display:inline-block;"
                                f"font-size:0.82em;'>{s}</span>"
                            )
                    if not reordered_skills:
                        tail_html += "<span style='color:#999;'>None</span>"

                    tail_html += "<br><br><strong style='color:#1B5E20;font-size:0.92em;'>Strengths (prioritized)</strong><br>"
                    for s in original_snap.get("strengths", []):
                        tail_html += f"<div style='color:#1A1A1A;margin-left:6px;font-size:0.88em;'>• {s}</div>"

                    tail_html += "<br><strong style='color:#1B5E20;font-size:0.92em;'>Experience (aligned to role)</strong><br>"
                    for exp in original_snap.get("experience", []):
                        if isinstance(exp, dict):
                            title = exp.get("title", exp.get("role", ""))
                            company = exp.get("company", "")
                            tail_html += (
                                f"<div style='color:#1A1A1A;margin-left:6px;font-size:0.88em;margin-bottom:4px;'>"
                                f"• <strong>{title}</strong>{' — ' + company if company else ''}</div>"
                            )
                        else:
                            tail_html += f"<div style='color:#1A1A1A;margin-left:6px;font-size:0.88em;'>• {exp}</div>"

                    match_pct = tailored_jd.get("match_percentage", 0)
                    tail_html += (
                        f"<br><div style='background:#1B5E20;color:#FFF;padding:6px 14px;"
                        f"border-radius:8px;text-align:center;font-weight:600;font-size:0.9em;'>"
                        f"🎯 Match: {match_pct}%</div>"
                    )
                    tail_html += "</div>"

                    with col_tailored:
                        st.markdown(tail_html, unsafe_allow_html=True)

            st.download_button(
                label="⬇️ Download Resume PDF",
                data=st.session_state["pdf_bytes"],
                file_name=f"resume_{jd_meta.get('company_name', 'company').replace(' ', '_')}.pdf",
                mime="application/pdf",
                use_container_width=True,
            )
            st.session_state["download_done"] = True

        # ---- Submit Application ----
        if st.session_state.get("download_done"):
            st.markdown("---")
            if st.button("🚀 Mark as Submitted", use_container_width=True, type="primary"):
                jd_meta = st.session_state["jd_meta"]
                match = st.session_state["match_result"]

                new_app = {
                    "id": len(data["applications"]) + 1,
                    "company_name": jd_meta.get("company_name", "Unknown"),
                    "role": jd_meta.get("role", "Unknown"),
                    "jd_text": jd_text,
                    "required_skills": jd_meta.get("required_skills", []),
                    "match_score": match.get("match_percentage", 0),
                    "status": "Submitted",
                    "rejection_notes": "",
                    "ai_analysis_summary": match.get("analysis_summary", ""),
                    "submitted_at": datetime.datetime.now().isoformat(),
                }
                data["applications"].append(new_app)
                save_data(data)

                # Clear tab 1 session state
                for key in ["match_result", "jd_meta", "pdf_bytes", "resume_ready", "download_done", "profile_text", "resume_summary", "resume_prepared_at", "original_profile_snapshot", "tailored_jd_data", "revised_score_data", "original_score"]:
                    st.session_state.pop(key, None)

                st.success("✅ Application submitted! Check the **Tracking** tab.")
                st.rerun()


# =========================================================================
# TAB 2 — TRACKING
# =========================================================================
with tab2:
    st.subheader("Application Pipeline")
    data = load_data()
    apps = data.get("applications", [])

    if not apps:
        st.info("📭 No applications yet. Head to the **Apply** tab to get started!")
    else:
        for idx, app in enumerate(apps):
            status = app.get("status", "Submitted")
            if status == "Not Selected":
                continue  # These show in Tab 3

            # Status badge
            badge_class = {
                "Submitted": "status-submitted",
                "Interview": "status-interview",
                "Selected": "status-selected",
            }.get(status, "status-submitted")

            st.markdown(f"""
            <div class="app-card">
                <div style="display:flex;justify-content:space-between;align-items:center">
                    <div>
                        <strong style="font-size:1.1em;color:#1A1A1A">{app.get('company_name','')}</strong>
                        <span style="color:#333">&nbsp;·&nbsp; {app.get('role','')}</span>
                    </div>
                    <span class="{badge_class}">{status}</span>
                </div>
                <div style="margin-top:8px;color:#444;font-size:0.85em">
                    Match: {app.get('match_score',0)}% &nbsp;|&nbsp;
                    Submitted: {app.get('submitted_at','')[:10]}
                </div>
            </div>
            """, unsafe_allow_html=True)

            # Action buttons
            bcols = st.columns(4)

            with bcols[0]:
                if status == "Submitted":
                    if st.button("🎤 Interview", key=f"interview_{idx}", use_container_width=True):
                        data["applications"][idx]["status"] = "Interview"
                        save_data(data)
                        st.rerun()

            with bcols[1]:
                if status in ("Submitted", "Interview"):
                    if st.button("🏆 Selected", key=f"selected_{idx}", use_container_width=True):
                        if status == "Submitted":
                            st.session_state[f"confirm_select_{idx}"] = True
                        else:
                            data["applications"][idx]["status"] = "Selected"
                            save_data(data)
                            st.rerun()

            with bcols[2]:
                if status in ("Submitted", "Interview"):
                    if st.button("❌ Not Selected", key=f"reject_{idx}", use_container_width=True):
                        st.session_state[f"confirm_reject_{idx}"] = True

            with bcols[3]:
                pass  # spacer

            # Confirmation dialogs
            if st.session_state.get(f"confirm_select_{idx}"):
                st.warning("⚠️ Candidate has not been marked for Interview. Mark as Selected directly?")
                cc1, cc2 = st.columns(2)
                with cc1:
                    if st.button("✅ Yes, Select", key=f"yes_sel_{idx}", use_container_width=True):
                        data["applications"][idx]["status"] = "Selected"
                        save_data(data)
                        st.session_state.pop(f"confirm_select_{idx}", None)
                        st.rerun()
                with cc2:
                    if st.button("❌ Cancel", key=f"no_sel_{idx}", use_container_width=True):
                        st.session_state.pop(f"confirm_select_{idx}", None)
                        st.rerun()

            if st.session_state.get(f"confirm_reject_{idx}"):
                st.warning("⚠️ Move this application to Not Selected?")
                cr1, cr2 = st.columns(2)
                with cr1:
                    if st.button("✅ Confirm", key=f"yes_rej_{idx}", use_container_width=True):
                        data["applications"][idx]["status"] = "Not Selected"
                        save_data(data)
                        st.session_state.pop(f"confirm_reject_{idx}", None)
                        st.rerun()
                with cr2:
                    if st.button("❌ Cancel", key=f"no_rej_{idx}", use_container_width=True):
                        st.session_state.pop(f"confirm_reject_{idx}", None)
                        st.rerun()

            st.markdown("")  # spacer

        # ---- Email Status Update ----
        st.markdown("---")
        st.markdown("##### 📧 Email Status Update")

        with st.expander("ℹ️ How to get a Gmail App Password", expanded=False):
            st.markdown(
                "<div style='background:#FFFFFF;border:1px solid #D0D0D0;border-radius:8px;"
                "padding:14px 18px;color:#333;font-size:0.88em;line-height:1.6;'>"
                "<strong>Step 1:</strong> Go to your "
                "<a href='https://myaccount.google.com/security' target='_blank'>Google Account Security</a><br>"
                "<strong>Step 2:</strong> Enable <em>2-Step Verification</em> if not already enabled<br>"
                "<strong>Step 3:</strong> Search for <em>App Passwords</em> in the search bar<br>"
                "<strong>Step 4:</strong> Create a new App Password (name it anything, e.g. 'Job Assistant')<br>"
                "<strong>Step 5:</strong> Copy the 16-character password and paste it below"
                "</div>",
                unsafe_allow_html=True,
            )

        email_col1, email_col2 = st.columns(2)
        with email_col1:
            sender_email = st.text_input(
                "Your Gmail Address",
                placeholder="you@gmail.com",
                key="sender_email",
            )
        with email_col2:
            app_password = st.text_input(
                "Gmail App Password",
                type="password",
                placeholder="xxxx xxxx xxxx xxxx",
                key="app_password",
            )

        recipient_email = st.text_input(
            "Recipient Email",
            placeholder="recipient@gmail.com",
            key="recipient_email",
        )

        send_disabled = not (sender_email and app_password and recipient_email and apps)
        if st.button("📤 Send Status Email", disabled=send_disabled, use_container_width=True, type="primary"):
            with st.spinner("📧 Sending email..."):
                error = send_status_email(
                    sender_email=sender_email,
                    app_password=app_password,
                    recipient_email=recipient_email,
                    applications=apps,
                )
            if error:
                st.error(f"❌ {error}")
            else:
                st.success("✅ Status email sent successfully!")


# =========================================================================
# TAB 3 — NOT SELECTED
# =========================================================================
with tab3:
    st.subheader("Rejection Analysis & Profile Evolution")
    data = load_data()
    apps = data.get("applications", [])
    rejected_apps = [(i, a) for i, a in enumerate(apps) if a.get("status") == "Not Selected"]

    if not rejected_apps:
        st.info("🎉 No rejected applications. Keep going!")
    else:
        for idx, app in rejected_apps:
            with st.expander(
                f"❌ {app.get('company_name','')} — {app.get('role','')}  "
                f"(Match: {app.get('match_score',0)}%)",
                expanded=True,
            ):
                st.markdown(f"**Submitted:** {app.get('submitted_at','')[:10]}")

                # Rejection notes text area
                notes_key = f"rejection_notes_{idx}"
                existing_notes = app.get("rejection_notes", "")
                notes = st.text_area(
                    "📝 Rejection Notes (interview feedback, what went wrong...)",
                    value=existing_notes,
                    height=120,
                    key=notes_key,
                    placeholder="e.g., I failed the system design round. They asked about distributed caching and I couldn't answer well...",
                )

                # Save notes on change
                if notes != existing_notes:
                    data["applications"][idx]["rejection_notes"] = notes
                    save_data(data)

                acol1, acol2 = st.columns([1, 3])
                with acol1:
                    if st.button(
                        "🤖 Analyze", key=f"analyze_{idx}",
                        use_container_width=True, type="primary",
                        disabled=not notes.strip(),
                    ):
                        with st.spinner("🧠 AI is analyzing the rejection and evolving your profile..."):
                            updated_state = analyze_rejection(
                                jd_text=app.get("jd_text", ""),
                                rejection_notes=notes,
                                profile_state=data["current_profile_state"],
                            )
                            data["current_profile_state"] = updated_state
                            data["applications"][idx]["ai_analysis_summary"] = (
                                f"Analyzed on {datetime.datetime.now().strftime('%Y-%m-%d')}. "
                                f"Profile state updated based on rejection from {app.get('company_name','')}."
                            )
                            save_data(data)
                            st.success("✅ Profile state updated! Future resumes will reflect this analysis.")
                            st.rerun()

                # Show current analysis if exists
                if app.get("ai_analysis_summary"):
                    st.info(f"📋 {app['ai_analysis_summary']}")

        # Show current profile state
        st.markdown("---")
        st.markdown("##### 🧬 Current Evolved Profile State")
        with st.expander("View Profile Summary", expanded=False):
            _render_profile_summary(data["current_profile_state"])


# =========================================================================
# TAB 4 — GLOBAL ANALYSIS
# =========================================================================
with tab4:
    st.subheader("Career Macro-Analysis")
    st.markdown(
        "Identify recurring patterns across all your rejections and get strategic recommendations."
    )

    data = load_data()
    rejected_count = sum(1 for a in data.get("applications", []) if a.get("status") == "Not Selected")

    if rejected_count == 0:
        st.info("📊 No rejected applications to analyze yet. Data will appear here as your pipeline grows.")
    else:
        st.markdown(f"**{rejected_count}** rejected application(s) available for analysis.")

        if st.button("🌐 Generate Global Analysis", use_container_width=True, type="primary"):
            with st.spinner("🧠 AI is synthesizing macro-patterns across all rejections..."):
                report = generate_global_analysis(data["applications"])
                data["global_insights"] = report
                save_data(data)

    # Display stored insights
    insights = data.get("global_insights")
    if insights:
        st.markdown("---")

        # Handle legacy string format (from before the update)
        if isinstance(insights, str):
            st.markdown(insights)
        elif isinstance(insights, dict):
            # ---- Improvement Pointers ----
            pointers = insights.get("improvement_pointers", [])
            if pointers:
                st.markdown("##### 💪 Here's How You Can Grow")
                pointers_html = (
                    "<div style='background:#FFFFFF;border:1px solid #E0E0E0;"
                    "border-radius:12px;padding:20px 24px;margin-bottom:16px;"
                    "box-shadow:0 2px 6px rgba(0,0,0,0.05);'>"
                )
                for i, p in enumerate(pointers, 1):
                    pointer_text = str(p)
                    pointers_html += (
                        f"<div style='display:flex;align-items:flex-start;margin-bottom:10px;'>"
                        f"<span style='background:#4CAF50;color:#FFF;border-radius:50%;"
                        f"min-width:26px;height:26px;display:inline-flex;align-items:center;"
                        f"justify-content:center;font-size:0.75em;font-weight:700;"
                        f"margin-right:12px;flex-shrink:0;'>{i}</span>"
                        f"<span style='color:#333;font-size:0.93em;line-height:1.5;'>{pointer_text}</span>"
                        f"</div>"
                    )
                pointers_html += "</div>"
                st.markdown(pointers_html, unsafe_allow_html=True)

            # ---- Recurring Gaps Summary ----
            gaps_summary = insights.get("recurring_gaps_summary", "")
            if gaps_summary:
                st.markdown("##### 🔍 Growth Opportunities")
                st.markdown(
                    f"<div style='background:#FFF8E1;border:1px solid #FFE082;"
                    f"border-radius:12px;padding:16px 20px;margin-bottom:16px;'>"
                    f"<span style='color:#333;font-size:0.92em;'>{gaps_summary}</span>"
                    f"</div>",
                    unsafe_allow_html=True,
                )

            # ---- Strategic Advice ----
            strategic = insights.get("strategic_advice", "")
            if strategic:
                st.markdown("##### 🚀 Your Next Steps")
                st.markdown(
                    f"<div style='background:#E3F2FD;border:1px solid #90CAF9;"
                    f"border-radius:12px;padding:16px 20px;margin-bottom:16px;'>"
                    f"<span style='color:#333;font-size:0.92em;'>{strategic}</span>"
                    f"</div>",
                    unsafe_allow_html=True,
                )

            # ---- Recommended Courses ----
            courses = insights.get("recommended_courses", [])
            if courses:
                st.markdown("##### 📚 Recommended Courses")
                for c in courses[:3]:
                    if isinstance(c, dict):
                        name = c.get("course_name", "")
                        platform = c.get("platform", "")
                        covers = c.get("covers", "")
                    else:
                        name = str(c)
                        platform = ""
                        covers = ""

                    course_html = (
                        f"<div style='background:#FFFFFF;border:1px solid #E0E0E0;"
                        f"border-left:4px solid #4CAF50;border-radius:0 12px 12px 0;"
                        f"padding:14px 18px;margin-bottom:8px;"
                        f"box-shadow:0 2px 4px rgba(0,0,0,0.04);'>"
                        f"<div style='color:#1A1A2E;font-weight:600;font-size:0.95em;'>"
                        f"📖 {name}</div>"
                    )
                    if platform:
                        course_html += (
                            f"<span style='background:#E8EAF6;color:#3949AB;padding:2px 10px;"
                            f"border-radius:12px;font-size:0.78em;font-weight:500;"
                            f"margin-top:4px;display:inline-block;'>{platform}</span> "
                        )
                    if covers:
                        course_html += (
                            f"<span style='color:#666;font-size:0.85em;margin-top:4px;"
                            f"display:inline-block;margin-left:4px;'>— {covers}</span>"
                        )
                    course_html += "</div>"
                    st.markdown(course_html, unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Footer
# ---------------------------------------------------------------------------
st.markdown("---")
st.markdown(
    "<div style='text-align:center;color:#999;font-size:0.8em;padding:10px'>"
    "AI Job Application Assistant · Powered by OpenAI · Built with Streamlit"
    "</div>",
    unsafe_allow_html=True,
)
