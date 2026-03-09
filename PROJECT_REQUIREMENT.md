# [cite_start]PROJECT_REQUIREMENT DOCUMENT: AI Job Application Assistant [cite: 1]

## 1. Project Overview
[cite_start]Job seekers spend significant time analyzing job descriptions, tailoring resumes, and managing applications[cite: 3]. [cite_start]This project is a four-tab AI-powered Job Application Assistant designed to automate extraction, perform intelligent skill matching, generate tailored PDF resumes, track application stages, and evolve the candidate's profile based on rejection analysis[cite: 4, 5, 11, 13, 14].

## 2. System Architecture & Data Storage
[cite_start]The system relies on a Streamlit frontend with a shared, local data layer[cite: 22].
* **Data Storage:** No external database is required. [cite_start]All data must be stored in a single `data.json` file on the local machine[cite: 23, 24, 31].
* [cite_start]**State Tracking:** The JSON file must track active/rejected applications, status history, rejection notes, and the core "current internal candidate profile state"[cite: 25, 26, 28, 29].
* [cite_start]**Clear All Data:** A globally accessible "Clear All Data" button must exist[cite: 32, 33]. [cite_start]When clicked, it must trigger a confirmation popup; upon confirmation, the JSON file is wiped, and all tabs immediately reset to an empty state[cite: 34, 35, 36, 37].

## 3. Tab Breakdown & Functional Requirements

### [cite_start]Tab 1: Apply (Resume Preparation) [cite: 38, 39]
* **Inputs:**
  * [cite_start]**Candidate Profile:** Upload via `.txt`, `.pdf`, or `.docx`[cite: 43, 44]. [cite_start]The system extracts text to identify skills, experience, projects, and domain knowledge[cite: 49, 50]. [cite_start]*Note: The system uses an evolving "Living Profile" for subsequent applications, not just the raw upload[cite: 57].*
  * [cite_start]**Reference Resume (Optional):** Upload via `.pdf` or `.docx` to extract layout, section ordering, and tone[cite: 58, 60, 64]. [cite_start]Content is not copied, only stylistic structure[cite: 66].
  * [cite_start]**Job Description (JD):** A text area for pasting the JD[cite: 68, 69].
* **Processing & UI Elements:**
  * [cite_start]The system must auto-extract and display the Company Name, Job Role, and Required Skills[cite: 73].
  * [cite_start]Calculate and display a **Skill Match Percentage** based on semantic overlap, experience alignment, and missing skills[cite: 73, 91, 92, 93, 95].
* **Action Buttons:**
  * [cite_start]**Prepare Resume Button:** Generates a PDF via `ReportLab` highlighting relevant skills and projects based on the JD[cite: 101, 102, 104]. [cite_start]Disabled until all inputs and calculations are complete[cite: 118].
  * [cite_start]**Submitted Button:** Logs the application to Tab 2[cite: 136, 137]. [cite_start]Only active after the resume is downloaded[cite: 128, 129].

### [cite_start]Tab 2: Tracking (Application Tracker) [cite: 140, 141]
* [cite_start]**Interface:** A table displaying Company Name, Job Role, Skills Required, Match %, and Action Buttons[cite: 144].
* **Stage Controls:**
  * [cite_start]**Submitted:** Auto-set with a green blinking indicator[cite: 153, 154].
  * [cite_start]**Interview:** Updates status[cite: 157].
  * [cite_start]**Selected:** If clicked before "Interview", a popup must confirm: *"Candidate has not been marked for Interview. Mark as Selected directly?"*[cite: 160, 161].
  * **Not Selected:** Always active. [cite_start]Triggers a confirmation popup before moving the application to Tab 3[cite: 165, 166, 168].

### [cite_start]Tab 3: Not Selected (Rejection Analysis) [cite: 170, 171]
* [cite_start]**Inputs:** A free-text area per row for "Rejection Notes" (e.g., interview feedback, missed questions, missing skills)[cite: 176, 177, 178].
* **AI Analysis (Core Feature):**
  * [cite_start]The **Analyze Button** cross-references the notes with the original JD[cite: 184, 187].
  * [cite_start]It updates the system's `current_profile_state` in the JSON file by downgrading weaker skills or identifying new learning areas[cite: 198, 200, 206].
  * [cite_start]Future generations in Tab 1 will use this *updated* understanding to de-emphasize weak points in the generated resume[cite: 202, 204, 205].

### [cite_start]Tab 4: Global Analysis [cite: 207, 208]
* [cite_start]**Purpose:** Identifies macro-patterns across *all* rejections[cite: 210].
* [cite_start]**Display:** A plain-text summary highlighting recurring skill gaps, common unanswered topics, and a strategic recommendation for the candidate's next steps[cite: 214, 215, 217, 220].

## [cite_start]4. Expected Deliverables [cite: 238]
* [cite_start]A fully functional Python application utilizing `ReportLab` for styling and intelligent AI prompts for the evolving profile[cite: 240, 241, 245].
* [cite_start]A working local JSON state management system[cite: 247].
* [cite_start]Complete documentation covering system architecture, skill matching logic, and profile evolution[cite: 249, 250, 251].