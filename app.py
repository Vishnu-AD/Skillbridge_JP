from __future__ import annotations
import os
from datetime import datetime

from flask import Flask, render_template, request, redirect, url_for, session, flash
import mysql.connector
from werkzeug.utils import secure_filename

from config import Config
from utils.security import (
    hash_password, verify_password,
    get_fernet, encrypt_text, decrypt_text,
    new_csrf_token, csrf_protect
)
from utils.resume_parser import read_resume_text
from utils.nlp import extract_skills
from utils.jd_parser import parse_jd, skill_gap
from utils.scoring import (
    score_tech, score_jlpt, score_keigo,
    readiness_score, roadmap, score_hr_interview
)
from utils.scoring import score_hr_interview

app = Flask(__name__)
app.config.from_object(Config)
app.config["MAX_CONTENT_LENGTH"] = Config.MAX_CONTENT_LENGTH

os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
FERNET = get_fernet(app.config["FERNET_KEY"])

import webbrowser
from threading import Timer
from flask import Flask

# ---------- DB ----------
def db():
    return mysql.connector.connect(
        host=app.config["MYSQL_HOST"],
        port=app.config["MYSQL_PORT"],
        user=app.config["MYSQL_USER"],
        password=app.config["MYSQL_PASSWORD"],
        database=app.config["MYSQL_DATABASE"],
        autocommit=True
    )

def q_one(sql, params=()):
    con = db()
    cur = con.cursor(dictionary=True)
    cur.execute(sql, params)
    row = cur.fetchone()
    cur.close(); con.close()
    return row

def q_all(sql, params=()):
    con = db()
    cur = con.cursor(dictionary=True)
    cur.execute(sql, params)
    rows = cur.fetchall()
    cur.close(); con.close()
    return rows

def q_exec(sql, params=()):
    con = db()
    cur = con.cursor()
    cur.execute(sql, params)
    last = cur.lastrowid
    cur.close(); con.close()
    return last

# ---------- AUTH HELPERS ----------
def current_user():
    uid = session.get("uid")
    if not uid:
        return None
    return q_one("SELECT * FROM users WHERE id=%s", (uid,))

def require_login(role=None):
    u = current_user()
    if not u:
        return False
    if role and u["role"] != role:
        return False
    return True

@app.before_request
def ensure_csrf():
    if "csrf_token" not in session:
        session["csrf_token"] = new_csrf_token()

@app.context_processor
def inject_globals():
    return {"csrf_token": session.get("csrf_token"), "me": current_user()}

# ---------- ROUTES ----------
@app.get("/")
def home():
    u = current_user()
    if not u:
        return redirect(url_for("login"))
    if u["role"] == "candidate":
        return redirect(url_for("candidate_dashboard"))
    if u["role"] == "recruiter":
        return redirect(url_for("recruiter_dashboard"))
    return redirect(url_for("admin_dashboard"))

# ---------- REGISTER / LOGIN ----------
@app.route("/register", methods=["GET","POST"])
def register():
    if request.method == "POST":
        if not csrf_protect(session, request.form.get("csrf_token")):
            flash("CSRF token invalid.", "danger")
            return redirect(url_for("register"))

        role = request.form.get("role", "candidate")
        full_name = request.form.get("full_name","").strip()
        email = request.form.get("email","").strip().lower()
        password = request.form.get("password","")

        if not full_name or not email or not password:
            flash("Please fill all fields.", "warning")
            return redirect(url_for("register"))

        if q_one("SELECT id FROM users WHERE email=%s", (email,)):
            flash("Email already exists.", "danger")
            return redirect(url_for("register"))

        uid = q_exec(
            "INSERT INTO users(role, full_name, email, password_hash) VALUES(%s,%s,%s,%s)",
            (role, full_name, email, hash_password(password))
        )

        if role == "candidate":
            q_exec("INSERT INTO candidate_profiles(user_id) VALUES(%s)", (uid,))

        flash("Account created. Please login.", "success")
        return redirect(url_for("login"))

    return render_template("auth_register.html")

@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        if not csrf_protect(session, request.form.get("csrf_token")):
            flash("CSRF token invalid.", "danger")
            return redirect(url_for("login"))

        email = request.form.get("email","").strip().lower()
        password = request.form.get("password","")

        u = q_one("SELECT * FROM users WHERE email=%s", (email,))
        if not u or not verify_password(password, u["password_hash"]):
            flash("Invalid credentials.", "danger")
            return redirect(url_for("login"))

        session["uid"] = u["id"]
        flash("Welcome!", "success")
        return redirect(url_for("home"))

    return render_template("auth_login.html")

@app.get("/logout")
def logout():
    session.clear()
    flash("Logged out.", "info")
    return redirect(url_for("login"))

# ===================== CANDIDATE =====================
@app.get("/candidate/dashboard")
def candidate_dashboard():
    if not require_login("candidate"):
        return redirect(url_for("login"))

    uid = session["uid"]
    prof = q_one("SELECT * FROM candidate_profiles WHERE user_id=%s", (uid,))
    u = current_user()

    # decrypt display fields
    phone = decrypt_text(FERNET, prof.get("encrypted_phone"))
    address = decrypt_text(FERNET, prof.get("encrypted_address"))

    # latest matches (from recruiter jobs)
    top_matches = q_all("""
        SELECT m.match_score, m.gap_summary, j.title, j.company, j.location, j.id as job_id
        FROM matches m JOIN jobs j ON j.id=m.job_id
        WHERE m.candidate_id=%s
        ORDER BY m.match_score DESC
        LIMIT 5
    """, (uid,))

    return render_template(
        "candidate_dashboard.html",
        prof=prof,
        phone=phone,
        address=address,
        top_matches=top_matches
    )

@app.route("/candidate/profile", methods=["POST"])
def candidate_profile_update():
    if not require_login("candidate"):
        return redirect(url_for("login"))
    if not csrf_protect(session, request.form.get("csrf_token")):
        flash("CSRF token invalid.", "danger")
        return redirect(url_for("candidate_dashboard"))

    uid = session["uid"]
    nationality = request.form.get("nationality","").strip()
    years_exp = int(request.form.get("years_exp","0") or 0)
    desired_role = request.form.get("desired_role","").strip()
    jlpt_level = request.form.get("jlpt_level","N5")

    phone = request.form.get("phone","").strip()
    address = request.form.get("address","").strip()

    q_exec("""
        UPDATE candidate_profiles
        SET nationality=%s, years_exp=%s, desired_role=%s, jlpt_level=%s,
            encrypted_phone=%s, encrypted_address=%s
        WHERE user_id=%s
    """, (
        nationality, years_exp, desired_role, jlpt_level,
        encrypt_text(FERNET, phone),
        encrypt_text(FERNET, address),
        uid
    ))

    flash("Profile updated.", "success")
    return redirect(url_for("candidate_dashboard"))

# ---------- Resume Upload ----------
@app.route("/candidate/resume", methods=["GET","POST"])
def candidate_resume():
    if not require_login("candidate"):
        return redirect(url_for("login"))
    uid = session["uid"]
    prof = q_one("SELECT * FROM candidate_profiles WHERE user_id=%s", (uid,))

    if request.method == "POST":
        if not csrf_protect(session, request.form.get("csrf_token")):
            flash("CSRF token invalid.", "danger")
            return redirect(url_for("candidate_resume"))

        f = request.files.get("resume")
        if not f or f.filename.strip() == "":
            flash("Please upload a resume (PDF/TXT).", "warning")
            return redirect(url_for("candidate_resume"))

        filename = secure_filename(f.filename)
        ext = os.path.splitext(filename)[1].lower()
        if ext not in [".pdf", ".txt"]:
            flash("Only PDF or TXT allowed.", "danger")
            return redirect(url_for("candidate_resume"))

        save_name = f"{uid}_{int(datetime.utcnow().timestamp())}_{filename}"
        path = os.path.join(app.config["UPLOAD_FOLDER"], save_name)
        f.save(path)

        text = read_resume_text(path)
        skills = extract_skills(text)

        q_exec("""
            UPDATE candidate_profiles
            SET resume_file=%s, resume_text=%s, resume_skills=%s
            WHERE user_id=%s
        """, (save_name, text, ",".join(skills), uid))

        flash("Resume uploaded & analyzed.", "success")
        return redirect(url_for("candidate_resume"))

    skills_list = (prof.get("resume_skills") or "").split(",") if prof.get("resume_skills") else []
    return render_template("candidate_resume.html", prof=prof, skills_list=sorted([s for s in skills_list if s]))

# ---------- Assessments ----------
@app.route("/candidate/assessments", methods=["GET","POST"])
def candidate_assessments():
    if not require_login("candidate"):
        return redirect(url_for("login"))

    uid = session["uid"]
    prof = q_one("SELECT * FROM candidate_profiles WHERE user_id=%s", (uid,))
    resume_text = prof.get("resume_text") or ""
    desired_role = prof.get("desired_role") or "Software Engineer"

    if request.method == "POST":
        if not csrf_protect(session, request.form.get("csrf_token")):
            flash("CSRF token invalid.", "danger")
            return redirect(url_for("candidate_assessments"))

        action = request.form.get("action")

        # TECH MCQ
        if action == "submit_tech":
            answers = {
                "q1": "b", "q2": "a", "q3": "c", "q4": "b", "q5": "a"
            }
            correct = 0
            for k, v in answers.items():
                if request.form.get(k) == v:
                    correct += 1

            tech = score_tech(correct, len(answers), resume_text, desired_role)

            q_exec(
                "UPDATE candidate_profiles SET tech_score=%s WHERE user_id=%s",
                (tech, uid)
            )
            q_exec(
                "INSERT INTO assessments(user_id, kind, score, details) VALUES(%s,'tech',%s,%s)",
                (uid, tech, f"MCQ correct={correct}/{len(answers)}")
            )

            flash(f"Tech assessment updated: {tech}/100", "success")

        # JLPT mini quiz
        elif action == "submit_jlpt":
            answers = {"j1":"a", "j2":"c", "j3":"b"}
            correct = sum(1 for k, v in answers.items() if request.form.get(k) == v)
            level = request.form.get("jlpt_level", prof.get("jlpt_level", "N5"))
            jlpt = score_jlpt(level, correct, len(answers))

            q_exec(
                "UPDATE candidate_profiles SET jlpt_level=%s, jlpt_score=%s WHERE user_id=%s",
                (level, jlpt, uid)
            )
            q_exec(
                "INSERT INTO assessments(user_id, kind, score, details) VALUES(%s,'jlpt',%s,%s)",
                (uid, jlpt, f"Quiz correct={correct}/{len(answers)}; level={level}")
            )

            flash(f"JLPT readiness updated: {jlpt}/100", "success")

        # Keigo analyzer
        elif action == "submit_keigo":
            text = request.form.get("keigo_text", "").strip()
            ks, tips = score_keigo(text)

            q_exec(
                "UPDATE candidate_profiles SET keigo_score=%s WHERE user_id=%s",
                (ks, uid)
            )
            q_exec(
                "INSERT INTO assessments(user_id, kind, score, details) VALUES(%s,'keigo',%s,%s)",
                (uid, ks, " | ".join(tips)[:2000] if tips else "Keigo analyzed successfully")
            )

            flash(f"Keigo etiquette updated: {ks}/100", "success")

        # HR Interview (Voice/Text)
        elif action == "submit_hr":
            text = request.form.get("hr_text", "").strip()
            lang = request.form.get("hr_lang", "en")

            if not text:
                flash("No interview speech detected. Please click Start Voice Input and speak clearly.", "warning")
                return redirect(url_for("candidate_assessments"))

            hr_score, tips = score_hr_interview(text, lang)

            q_exec(
                "INSERT INTO assessments(user_id, kind, score, details) VALUES(%s,'interview',%s,%s)",
                (uid, hr_score, f"Language={lang} | Speech={text[:1200]} | Tips={' | '.join(tips) if tips else 'Good introduction'}")
            )

            flash(f"HR Interview Score: {hr_score}/100", "success")

        # Update readiness score (existing main logic unchanged)
        prof2 = q_one("SELECT * FROM candidate_profiles WHERE user_id=%s", (uid,))
        r = readiness_score(
            prof2.get("tech_score", 0),
            prof2.get("jlpt_score", 0),
            prof2.get("keigo_score", 0)
        )
        q_exec(
            "UPDATE candidate_profiles SET readiness_score=%s WHERE user_id=%s",
            (r, uid)
        )

        return redirect(url_for("candidate_assessments"))

    history = q_all(
        "SELECT * FROM assessments WHERE user_id=%s ORDER BY created_at DESC LIMIT 10",
        (uid,)
    )
    return render_template("candidate_assessments.html", prof=prof, history=history)
# ---------- Job Match (Candidate view) ----------
@app.route("/candidate/jobmatch", methods=["GET","POST"])
def candidate_jobmatch():
    if not require_login("candidate"):
        return redirect(url_for("login"))

    uid = session["uid"]
    prof = q_one("SELECT * FROM candidate_profiles WHERE user_id=%s", (uid,))
    cand_skills = (prof.get("resume_skills") or "").split(",") if prof.get("resume_skills") else []

    jobs = q_all("SELECT * FROM jobs ORDER BY created_at DESC LIMIT 50")

    # Precompute simple match score for display
    enriched = []
    for j in jobs:
        jd_skills = (j.get("extracted_skills") or "").split(",") if j.get("extracted_skills") else []
        matched, missing = skill_gap(cand_skills, jd_skills)
        # match score using overlap + readiness
        overlap = int((len(matched) / max(len(jd_skills), 1)) * 70)
        total = min(100, overlap + int((prof.get("readiness_score",0) * 0.30)))
        enriched.append({
            "job": j,
            "match_score": total,
            "matched": matched[:10],
            "missing": missing[:10],
        })

    enriched.sort(key=lambda x: x["match_score"], reverse=True)
    return render_template("candidate_jobmatch.html", prof=prof, enriched=enriched[:25])

# ---------- Interview Simulation (simple) ----------
@app.route("/candidate/interview", methods=["GET","POST"])
def candidate_interview():
    if not require_login("candidate"):
        return redirect(url_for("login"))

    uid = session["uid"]
    prof = q_one("SELECT * FROM candidate_profiles WHERE user_id=%s", (uid,))

    feedback = None
    if request.method == "POST":
        if not csrf_protect(session, request.form.get("csrf_token")):
            flash("CSRF token invalid.", "danger")
            return redirect(url_for("candidate_interview"))

        scenario = request.form.get("scenario","")
        answer = request.form.get("answer","")

        ks, tips = score_keigo(answer)
        # a tiny “tech clarity” heuristic: if includes keywords
        tech_points = 0
        for kw in ["because", "therefore", "tradeoff", "complexity", "api", "database", "latency"]:
            if kw in (answer or "").lower():
                tech_points += 1
        tech_clarity = min(100, 40 + tech_points * 10)

        sim_score = int(ks * 0.6 + tech_clarity * 0.4)
        q_exec("INSERT INTO assessments(user_id, kind, score, details) VALUES(%s,'interview',%s,%s)",
               (uid, sim_score, f"Scenario={scenario} | Keigo={ks} | Tips={' ; '.join(tips)}"))

        feedback = {
            "sim_score": sim_score,
            "keigo_score": ks,
            "tech_clarity": tech_clarity,
            "tips": tips
        }

    return render_template("candidate_interview.html", prof=prof, feedback=feedback)

# ===================== RECRUITER =====================
@app.get("/recruiter/dashboard")
def recruiter_dashboard():
    if not require_login("recruiter"):
        return redirect(url_for("login"))

    rid = session["uid"]
    jobs = q_all("SELECT * FROM jobs WHERE recruiter_id=%s ORDER BY created_at DESC", (rid,))
    total_candidates = q_one("SELECT COUNT(*) AS c FROM candidate_profiles", ())["c"]
    return render_template("recruiter_dashboard.html", jobs=jobs, total_candidates=total_candidates)

@app.route("/recruiter/jobpost", methods=["GET","POST"])
def recruiter_jobpost():
    if not require_login("recruiter"):
        return redirect(url_for("login"))

    rid = session["uid"]

    if request.method == "POST":
        if not csrf_protect(session, request.form.get("csrf_token")):
            flash("CSRF token invalid.", "danger")
            return redirect(url_for("recruiter_jobpost"))

        title = request.form.get("title","").strip()
        company = request.form.get("company","").strip()
        location = request.form.get("location","").strip()
        years_required = int(request.form.get("years_required","0") or 0)
        jd_text = request.form.get("jd_text","").strip()

        if not title or not company or not jd_text:
            flash("Title, company, JD text are required.", "warning")
            return redirect(url_for("recruiter_jobpost"))

        parsed = parse_jd(jd_text)
        jid = q_exec("""
            INSERT INTO jobs(recruiter_id,title,company,location,jd_text,extracted_skills,years_required)
            VALUES(%s,%s,%s,%s,%s,%s,%s)
        """, (rid, title, company, location, jd_text, ",".join(parsed["skills"]), years_required))

        flash("Job posted & skills extracted.", "success")
        return redirect(url_for("recruiter_candidates", job_id=jid))

    return render_template("recruiter_jobpost.html")

@app.get("/recruiter/candidates")
def recruiter_candidates():
    if not require_login("recruiter"):
        return redirect(url_for("login"))

    job_id = request.args.get("job_id", type=int)
    job = q_one("SELECT * FROM jobs WHERE id=%s", (job_id,)) if job_id else None

    candidates = q_all("""
        SELECT u.id, u.full_name, u.email,
               p.years_exp, p.desired_role, p.jlpt_level,
               p.tech_score, p.jlpt_score, p.keigo_score, p.readiness_score,
               p.verified, p.resume_skills
        FROM users u JOIN candidate_profiles p ON p.user_id=u.id
        WHERE u.role='candidate'
        ORDER BY p.readiness_score DESC
        LIMIT 200
    """)

    # if job provided, compute match & store matches
    if job:
        jd_skills = (job.get("extracted_skills") or "").split(",") if job.get("extracted_skills") else []
        for c in candidates:
            cand_skills = (c.get("resume_skills") or "").split(",") if c.get("resume_skills") else []
            matched, missing = skill_gap(cand_skills, jd_skills)
            overlap = int((len(matched) / max(len(jd_skills), 1)) * 70)
            mscore = min(100, overlap + int((c.get("readiness_score",0) * 0.30)))
            gap_txt = f"Matched: {', '.join(matched[:12])} | Missing: {', '.join(missing[:12])}"

            # upsert-ish: remove existing match then insert
            q_exec("DELETE FROM matches WHERE job_id=%s AND candidate_id=%s", (job["id"], c["id"]))
            q_exec("INSERT INTO matches(job_id,candidate_id,match_score,gap_summary) VALUES(%s,%s,%s,%s)",
                   (job["id"], c["id"], mscore, gap_txt[:1500]))

        # fetch ranked matches
        ranked = q_all("""
            SELECT u.full_name, p.jlpt_level, p.readiness_score, p.verified,
                   m.match_score, m.gap_summary
            FROM matches m
            JOIN users u ON u.id=m.candidate_id
            JOIN candidate_profiles p ON p.user_id=u.id
            WHERE m.job_id=%s
            ORDER BY m.match_score DESC
            LIMIT 100
        """, (job["id"],))
    else:
        ranked = None

    return render_template("recruiter_candidates.html", job=job, ranked=ranked, candidates=candidates[:50])

# ===================== ADMIN =====================
@app.get("/admin/dashboard")
def admin_dashboard():
    if not require_login("admin"):
        return redirect(url_for("login"))

    counts = {
        "candidates": q_one("SELECT COUNT(*) AS c FROM users WHERE role='candidate'")["c"],
        "recruiters": q_one("SELECT COUNT(*) AS c FROM users WHERE role='recruiter'")["c"],
        "jobs": q_one("SELECT COUNT(*) AS c FROM jobs")["c"],
        "verified": q_one("SELECT COUNT(*) AS c FROM candidate_profiles WHERE verified=1")["c"],
    }
    recent = q_all("""
        SELECT u.full_name, u.email, p.readiness_score, p.verified, p.updated_at
        FROM users u JOIN candidate_profiles p ON p.user_id=u.id
        ORDER BY p.updated_at DESC
        LIMIT 12
    """)
    return render_template("admin_dashboard.html", counts=counts, recent=recent)

@app.route("/admin/verify", methods=["GET","POST"])
def admin_verify():
    if not require_login("admin"):
        return redirect(url_for("login"))

    if request.method == "POST":
        if not csrf_protect(session, request.form.get("csrf_token")):
            flash("CSRF token invalid.", "danger")
            return redirect(url_for("admin_verify"))

        uid = int(request.form.get("user_id") or 0)
        val = 1 if request.form.get("verified") == "1" else 0
        q_exec("UPDATE candidate_profiles SET verified=%s WHERE user_id=%s", (val, uid))
        flash("Verification updated.", "success")
        return redirect(url_for("admin_verify"))

    candidates = q_all("""
        SELECT u.id, u.full_name, u.email,
               p.readiness_score, p.tech_score, p.jlpt_score, p.keigo_score,
               p.verified
        FROM users u JOIN candidate_profiles p ON p.user_id=u.id
        WHERE u.role='candidate'
        ORDER BY p.readiness_score DESC
        LIMIT 200
    """)
    return render_template("admin_verify.html", candidates=candidates)

# ---------- Utility: recompute roadmap preview ----------
@app.get("/candidate/roadmap")
def candidate_roadmap():
    if not require_login("candidate"):
        return redirect(url_for("login"))

    uid = session["uid"]
    prof = q_one("SELECT * FROM candidate_profiles WHERE user_id=%s", (uid,))
    cand_skills = (prof.get("resume_skills") or "").split(",") if prof.get("resume_skills") else []

    # choose best job from matches if exists
    top = q_one("""
        SELECT j.extracted_skills FROM matches m
        JOIN jobs j ON j.id=m.job_id
        WHERE m.candidate_id=%s
        ORDER BY m.match_score DESC
        LIMIT 1
    """, (uid,))
    jd_skills = (top.get("extracted_skills") or "").split(",") if top else []
    _, missing = skill_gap(cand_skills, jd_skills)

    steps = roadmap(missing, prof.get("tech_score",0), prof.get("jlpt_score",0), prof.get("keigo_score",0))
    # render inside dashboard as a simple page
    return render_template("candidate_dashboard.html", prof=prof, phone=None, address=None, top_matches=[], roadmap_steps=steps)

if __name__ == "__main__":
    app.run(debug=True)