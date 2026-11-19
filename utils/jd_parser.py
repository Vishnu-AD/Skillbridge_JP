from utils.nlp import extract_skills, normalize

def parse_jd(jd_text: str) -> dict:
    skills = extract_skills(jd_text)
    return {
        "skills": skills,
        "normalized": normalize(jd_text),
    }

def skill_gap(candidate_skills: list[str], jd_skills: list[str]) -> tuple[list[str], list[str]]:
    cand = set(candidate_skills or [])
    req = set(jd_skills or [])
    missing = sorted(list(req - cand))
    matched = sorted(list(req & cand))
    return matched, missing