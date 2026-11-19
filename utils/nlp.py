import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

SKILL_BANK = sorted(set([
    # core
    "python","java","javascript","typescript","c","c++","c#","go","rust","php",
    "flask","django","fastapi","spring","react","next.js","node.js","express",
    "mysql","postgresql","mongodb","redis","sqlite",
    "aws","azure","gcp","docker","kubernetes","linux","git","ci/cd",
    "rest","graphql","microservices",
    "machine learning","deep learning","tensorflow","pytorch","opencv",
    "data structures","algorithms","system design",
    "testing","pytest","junit",
    "html","css","bootstrap","tailwind",
    # japan workplace relevant
    "jira","confluence","scrum","agile"
]))

def normalize(text: str) -> str:
    t = text.lower()
    t = re.sub(r"[\n\r\t]+", " ", t)
    t = re.sub(r"[^a-z0-9\+\#\.\-/ ]+", " ", t)
    t = re.sub(r"\s{2,}", " ", t).strip()
    return t

def extract_skills(text: str) -> list[str]:
    t = normalize(text)
    found = []
    for skill in SKILL_BANK:
        patt = r"\b" + re.escape(skill) + r"\b"
        if re.search(patt, t):
            found.append(skill)
    return sorted(set(found))

def tfidf_similarity(a: str, b: str) -> float:
    vec = TfidfVectorizer(stop_words="english")
    X = vec.fit_transform([a, b])
    sim = cosine_similarity(X[0], X[1])[0][0]
    return float(sim)