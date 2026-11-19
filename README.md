# SkillBridge JP — International Talent Readiness Platform

**Live Application:** [https://onrender.com](https://onrender.com)  
*(Note: Hosted on Render free tier; initial page load may take ~30 seconds to wake up.)*

## Overview
**SkillBridge JP** is a full-stack International Talent Readiness and Recruitment Platform developed to bridge the gap between international software engineering candidates and the Japanese IT industry. Beyond standard technical screening, the platform evaluates candidates across three key dimensions—**technical skills**, **Japanese language proficiency (JLPT)**, and **cultural preparedness (business etiquette)**—to generate data-driven employer recommendations and personalized skill-gap insights.

> **Academic Recognition:** Developed as a final-year (8th semester) B.E. Computer Science and Engineering project at Paavai Engineering College and presented at the **4th International Conference on Emerging Trends in Science, Technology, Engineering & Management (ICETSTEM-2026)**.

---

## Key Features
* **Multi-Dimensional Candidate Assessment:** Evaluates technical competencies alongside Japanese language readiness and workplace etiquette awareness.
* **Data-Driven Employer Recommendation & Skill-Gap Analysis:** Matches candidate profiles with suitable Japanese IT roles and highlights specific areas for improvement.
* **Three Role-Based Portals:**
  * **Candidate Portal:** Profile creation, readiness assessments, progress tracking, and personalized job recommendations.
  * **Recruiter Portal:** Access to pre-assessed candidate profiles and readiness insights for data-driven hiring.
  * **Administrator Portal:** Platform management, assessment configuration, and user oversight.

---

## Tech Stack
* **Backend:** Python, Flask
* **Database:** MySQL (hosted on Railway)
* **Frontend:** HTML5, CSS3, Bootstrap, JavaScript
* **Deployment:** Render

---

## Project Structure
```text
Skillbridge_JP/
├── app.py               # Main Flask application and route controllers
├── config.py            # Database and environment configuration
├── db.sql               # MySQL relational database schema
├── requirements.txt     # Python dependencies
├── Procfile             # Render deployment configuration
├── static/              # CSS, JavaScript, and static assets
├── templates/           # Jinja2 HTML templates for Candidate, Recruiter, and Admin portals
└── utils/               # Helper modules for assessment scoring and recommendation logic
```

---

## Demo Access (For Reviewers)
You can explore the live platform at [[https://onrender.com](https://onrender.com)](https://skillbridge-jp.onrender.com) by registering a new account or logging in with the demo credentials below:

* **Candidate Portal:** `[your-demo-candidate@email.com]` / `[Password]`
* **Recruiter Portal:** `[your-demo-recruiter@email.com]` / `[Password]`
* **Admin Portal:** `[your-demo-admin@email.com]` / `[Password]`

---

## Local Setup & Installation
1. **Clone the repository:**
   ```bash
   git clone https://github.com
   cd Skillbridge_JP
   ```
2. **Create a virtual environment and install dependencies:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```
3. **Configure the MySQL database:**
   * Import `db.sql` into your local MySQL server.
   * Update database credentials in `config.py` (or via environment variables).
4. **Run the application:**
   ```bash
   python app.py
   ```
   Open `http://127.0.0.1:5000` in your browser.
