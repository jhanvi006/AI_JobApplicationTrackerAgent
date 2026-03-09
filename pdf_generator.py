"""
pdf_generator.py — ReportLab-based professional resume PDF generation
for the AI Job Application Assistant.
"""

import io
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
)


# ---------------------------------------------------------------------------
# Color palette
# ---------------------------------------------------------------------------
PRIMARY   = HexColor("#1A1A2E")
ACCENT    = HexColor("#0F3460")
HIGHLIGHT = HexColor("#E94560")
LIGHT_BG  = HexColor("#F5F5F5")
TEXT_DARK  = HexColor("#222222")
TEXT_MID   = HexColor("#555555")
TEXT_LIGHT = HexColor("#888888")
WHITE      = HexColor("#FFFFFF")


def _build_styles():
    """Create the paragraph style set for the resume."""
    styles = getSampleStyleSheet()

    styles.add(ParagraphStyle(
        name="ResumeName",
        fontName="Helvetica-Bold",
        fontSize=22,
        leading=26,
        textColor=PRIMARY,
        alignment=TA_CENTER,
        spaceAfter=4,
    ))
    styles.add(ParagraphStyle(
        name="ResumeSubtitle",
        fontName="Helvetica",
        fontSize=11,
        leading=14,
        textColor=TEXT_MID,
        alignment=TA_CENTER,
        spaceAfter=12,
    ))
    styles.add(ParagraphStyle(
        name="SectionHeader",
        fontName="Helvetica-Bold",
        fontSize=13,
        leading=16,
        textColor=ACCENT,
        spaceBefore=14,
        spaceAfter=6,
        borderWidth=0,
    ))
    styles.add(ParagraphStyle(
        name="BodyText2",
        fontName="Helvetica",
        fontSize=10,
        leading=14,
        textColor=TEXT_DARK,
        alignment=TA_JUSTIFY,
        spaceAfter=4,
    ))
    styles.add(ParagraphStyle(
        name="SkillTag",
        fontName="Helvetica-Bold",
        fontSize=9,
        leading=12,
        textColor=ACCENT,
    ))
    styles.add(ParagraphStyle(
        name="WeakSkillTag",
        fontName="Helvetica",
        fontSize=9,
        leading=12,
        textColor=TEXT_LIGHT,
    ))
    return styles


def _section_divider():
    return HRFlowable(
        width="100%", thickness=0.5, color=HexColor("#CCCCCC"),
        spaceBefore=6, spaceAfter=6
    )


def generate_resume(
    profile_data: dict,
    jd_data: dict,
    candidate_name: str = "Candidate",
    reference_style: dict | None = None,
) -> bytes:
    """
    Generate a professional PDF resume.

    Args:
        profile_data: The current_profile_state dict.
        jd_data: Dict with keys: required_skills, matching_skills, missing_skills,
                 match_percentage, company_name, role.
        candidate_name: Name to display at the top.
        reference_style: Optional dict with layout hints (unused in v1, reserved).

    Returns:
        PDF file as bytes.
    """
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=LETTER,
        leftMargin=0.75 * inch, rightMargin=0.75 * inch,
        topMargin=0.6 * inch, bottomMargin=0.6 * inch,
    )
    styles = _build_styles()
    story = []

    # --- Header ---
    story.append(Paragraph(candidate_name.upper(), styles["ResumeName"]))

    target_role = jd_data.get("role", "")
    company = jd_data.get("company_name", "")
    subtitle_parts = []
    if target_role:
        subtitle_parts.append(target_role)
    if company:
        subtitle_parts.append(f"Application to {company}")
    if subtitle_parts:
        story.append(Paragraph(" · ".join(subtitle_parts), styles["ResumeSubtitle"]))

    story.append(_section_divider())

    # --- Professional Summary ---
    story.append(Paragraph("PROFESSIONAL SUMMARY", styles["SectionHeader"]))
    strengths = profile_data.get("strengths", [])
    experience = profile_data.get("experience", [])
    summary_parts = []
    if strengths:
        summary_parts.append(
            f"Results-driven professional with demonstrated expertise in "
            f"{', '.join(strengths[:5])}."
        )
    if experience:
        for exp in experience[:3]:
            if isinstance(exp, str):
                summary_parts.append(exp)
            elif isinstance(exp, dict):
                summary_parts.append(exp.get("description", str(exp)))
    if not summary_parts:
        summary_parts.append(
            "Motivated professional seeking to leverage skills and experience "
            "in a challenging new role."
        )
    story.append(Paragraph(" ".join(summary_parts), styles["BodyText2"]))
    story.append(Spacer(1, 6))

    # --- Skills Section (prioritized) ---
    story.append(Paragraph("CORE COMPETENCIES", styles["SectionHeader"]))

    weaknesses = set(
        w.lower() if isinstance(w, str) else w.get("skill", "").lower()
        for w in profile_data.get("weaknesses", [])
    )

    required = jd_data.get("required_skills", [])
    matching = jd_data.get("matching_skills", [])
    all_skills = profile_data.get("skills", [])

    # Build ordered skill list: matching first, then other profile skills
    ordered_skills = []
    seen = set()
    for s in matching:
        key = s.lower() if isinstance(s, str) else str(s).lower()
        if key not in seen:
            ordered_skills.append(s)
            seen.add(key)
    for s in all_skills:
        key = s.lower() if isinstance(s, str) else str(s).lower()
        if key not in seen:
            ordered_skills.append(s)
            seen.add(key)

    # Render skills as a table grid
    if ordered_skills:
        cols = 3
        skill_cells = []
        for s in ordered_skills:
            s_str = s if isinstance(s, str) else str(s)
            is_weak = s_str.lower() in weaknesses
            style_name = "WeakSkillTag" if is_weak else "SkillTag"
            prefix = "" if not is_weak else ""
            skill_cells.append(Paragraph(f"• {prefix}{s_str}", styles[style_name]))

        # Pad to fill row
        while len(skill_cells) % cols != 0:
            skill_cells.append(Paragraph("", styles["BodyText2"]))

        rows = [skill_cells[i:i + cols] for i in range(0, len(skill_cells), cols)]
        col_width = (doc.width) / cols
        skill_table = Table(rows, colWidths=[col_width] * cols)
        skill_table.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("TOPPADDING", (0, 0), (-1, -1), 2),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
        ]))
        story.append(skill_table)
    story.append(Spacer(1, 6))

    # --- Experience Section ---
    if experience:
        story.append(Paragraph("EXPERIENCE", styles["SectionHeader"]))
        for exp in experience:
            if isinstance(exp, str):
                story.append(Paragraph(f"• {exp}", styles["BodyText2"]))
            elif isinstance(exp, dict):
                title = exp.get("title", exp.get("role", ""))
                company_exp = exp.get("company", "")
                desc = exp.get("description", "")
                header = f"<b>{title}</b>"
                if company_exp:
                    header += f" — {company_exp}"
                story.append(Paragraph(header, styles["BodyText2"]))
                if desc:
                    story.append(Paragraph(desc, styles["BodyText2"]))
                story.append(Spacer(1, 4))

    # --- Improvement / Learning Areas (subtle) ---
    improvement = profile_data.get("improvement_areas", [])
    if improvement:
        story.append(Paragraph("CONTINUOUS LEARNING", styles["SectionHeader"]))
        for item in improvement[:5]:
            item_str = item if isinstance(item, str) else str(item)
            story.append(Paragraph(f"• Currently developing: {item_str}", styles["BodyText2"]))

    # --- Target Role Alignment ---
    if required:
        story.append(Paragraph("TARGET ROLE ALIGNMENT", styles["SectionHeader"]))
        match_pct = jd_data.get("match_percentage", 0)
        story.append(Paragraph(
            f"This resume has been tailored for the <b>{target_role}</b> position "
            f"at <b>{company}</b>. Profile alignment: <b>{match_pct}%</b>.",
            styles["BodyText2"]
        ))

    # Build PDF
    doc.build(story)
    buf.seek(0)
    return buf.read()
