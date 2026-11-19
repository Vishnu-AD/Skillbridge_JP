import re
from utils.nlp import tfidf_similarity

KEIGO_POSITIVE = [
    "お世話になっております", "よろしくお願いいたします", "恐れ入ります",
    "ご確認いただけますでしょうか", "申し訳ございません", "承知いたしました"
]
KEIGO_NEGATIVE = [
    "了解です", "すみません", "だよね", "マジ", "やばい", "とりあえず"
]

def score_tech(mcq_correct: int, mcq_total: int, resume_text: str, target_role: str) -> int:
    base = int((mcq_correct / max(mcq_total, 1)) * 70)
    align = int(tfidf_similarity(resume_text or "", target_role or "") * 30)
    return min(100, max(0, base + align))

def score_jlpt(level: str, quiz_correct: int, quiz_total: int) -> int:
    level_weight = {"N5":10,"N4":25,"N3":45,"N2":70,"N1":85}.get(level, 10)
    quiz = int((quiz_correct / max(quiz_total, 1)) * 15)
    return min(100, level_weight + quiz)

def score_keigo(text: str) -> tuple[int, list[str]]:
    t = text.strip()
    tips = []
    pos = sum(1 for p in KEIGO_POSITIVE if p in t)
    neg = sum(1 for n in KEIGO_NEGATIVE if n in t)

    score = 60 + pos * 8 - neg * 10

    if pos == 0:
        tips.append("Try adding formal greetings like 「お世話になっております」 or 「よろしくお願いいたします」.")
    if neg > 0:
        tips.append("Avoid casual phrases like 「了解です」; use 「承知いたしました」 instead.")
    if len(t) < 30:
        tips.append("Provide a fuller polite response (reason + request + closing).")

    if not re.search(r"(お願いいたします|申し上げます|いただけます)", t):
        tips.append("Add request/humble endings: 「〜いただけますでしょうか」 / 「〜お願い申し上げます」.")

    return min(100, max(0, score)), tips

def score_hr_interview(text: str, lang: str = "en") -> tuple[int, list[str]]:
    tips = []
    raw = (text or "").strip()
    t = raw.lower()

    if not raw:
        return 0, ["No speech text detected. Please allow microphone access and speak clearly."]

    score = 45

    if lang == "en":
        if any(x in t for x in ["my name is", "i am", "hello"]):
            score += 10
        else:
            tips.append("Start with a proper self-introduction like 'Hello, my name is ...'.")

        if any(x in t for x in ["experience", "years", "worked"]):
            score += 10
        else:
            tips.append("Mention your experience clearly.")

        if any(x in t for x in ["skills", "python", "java", "flask", "react", "mysql", "project"]):
            score += 15
        else:
            tips.append("Mention your technical skills or projects.")

        if len(raw.split()) >= 20:
            score += 10
        else:
            tips.append("Try to speak a little longer with more details.")

        if any(x in t for x in ["thank you", "nice to meet you"]):
            score += 5
        else:
            tips.append("End politely with 'Thank you' or similar closing.")

    else:
        if any(x in raw for x in ["はじめまして", "私の名前", "申します"]):
            score += 10
        else:
            tips.append("「はじめまして」 or 「私の名前は〜です」 போன்ற self-introduction phrase சேர்க்கவும்.")

        if any(x in raw for x in ["経験", "年", "働いて"]):
            score += 10
        else:
            tips.append("உங்கள் experience பற்றி Japanese-ல் mention செய்யவும்.")

        if any(x in raw for x in ["スキル", "Python", "Java", "Flask", "React", "MySQL", "プロジェクト"]):
            score += 15
        else:
            tips.append("Technical skills அல்லது projects பற்றி சொல்லவும்.")

        if len(raw) >= 30:
            score += 10
        else:
            tips.append("もう少し詳しく自己紹介してください。")

        if any(x in raw for x in ["よろしくお願いいたします", "ありがとうございます"]):
            score += 5
        else:
            tips.append("Polite closing phrase add செய்யவும்: 「よろしくお願いいたします」.")

    return min(100, score), tips

def readiness_score(tech: int, jlpt: int, keigo: int) -> int:
    return int(tech * 0.45 + jlpt * 0.35 + keigo * 0.20)

def roadmap(missing_skills: list[str], tech: int, jlpt: int, keigo: int) -> list[dict]:
    steps = []

    if tech < 60:
        steps.append({"title":"Core coding fundamentals", "items":[
            "Practice DSA basics (arrays, hashmaps, stacks, queues)",
            "Solve 15–20 easy coding problems (daily 1)",
            "Write unit tests for your solutions"
        ]})
    elif tech < 80:
        steps.append({"title":"Interview readiness", "items":[
            "System design basics (API, DB indexing, caching)",
            "Mock interviews (2 per week)",
            "Explain solutions aloud (Japanese/English mix)"
        ]})
    else:
        steps.append({"title":"Advanced polish", "items":[
            "Refactor 2 projects to clean architecture",
            "Add CI/CD pipeline & Dockerization",
            "Prepare STAR stories for behavioral rounds"
        ]})

    if jlpt < 60:
        steps.append({"title":"JLPT improvement", "items":[
            "Daily vocab (30 words) + shadowing",
            "Short business emails practice (Keigo templates)",
            "Weekly mini tests (listening + reading)"
        ]})
    else:
        steps.append({"title":"Business Japanese", "items":[
            "Practice meeting phrases (報連相: Hou-Ren-Sou)",
            "Write polite email for: delay / inquiry / apology",
            "Role-play recruiter calls"
        ]})

    if keigo < 70:
        steps.append({"title":"Keigo etiquette", "items":[
            "Replace casual phrases with humble/polite alternatives",
            "Use greeting + context + request + closing format",
            "Practice 10 templates for common office situations"
        ]})

    if missing_skills:
        steps.append({"title":"Target job skill gaps", "items":[
            f"Learn: {', '.join(missing_skills[:8])}" + (" ..." if len(missing_skills) > 8 else ""),
            "Build mini-project that uses 2–3 missing skills",
            "Update resume with measurable outcomes"
        ]})

    return steps