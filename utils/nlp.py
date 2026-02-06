# =============================
# File: utils/nlp.py
# =============================
import re
from collections import defaultdict
from typing import Dict, List, Tuple

# Simple keyword list (extend as needed)
TECH_SKILLS = set('''python java c c++ c# sql nosql mysql postgresql mongodb html css javascript typescript react angular vue
nodejs express django flask fastapi spring hibernate .net dotnet tensorflow pytorch keras scikit-learn pandas numpy matplotlib
powerbi tableau excel spark hadoop aws azure gcp docker kubernetes linux git github gitlab jira apache kafka kafka airflow
nlp computer vision opencv transformers bert huggingface selenium junit pytest unittest rest soap graphql microservices
ci cd cicd devops mlops data engineering databricks snowflake bigquery redshift'''.split())

SECTION_HEADERS = [
    'summary', 'objective', 'education', 'experience', 'work experience', 'projects', 'skills',
    'certifications', 'achievements', 'publications', 'volunteering', 'contact', 'links'
]

def parse_resume_sections(text: str) -> Dict[str, str]:
    lower = text.lower()
    indices = []
    for h in SECTION_HEADERS:
        m = re.search(rf'\b{re.escape(h)}\b', lower)
        if m:
            indices.append((m.start(), h))
    indices.sort()
    sections = {}
    for i, (pos, name) in enumerate(indices):
        start = pos
        end = indices[i + 1][0] if i + 1 < len(indices) else len(text)
        sections[name] = text[start:end].strip()
    # fallback minimal sections
    if 'skills' not in sections:
        m = re.search(r'skills?[:\-]\s*(.+?)(?:education|experience|projects|\n\n|$)', lower)
        if m:
            sections['skills'] = text[m.start():m.end()]
    return sections or {'full': text}

def tokenize(s: str) -> List[str]:
    return re.findall(r'[a-zA-Z][a-zA-Z+#.\-]*', s.lower())

def extract_keywords(text: str, top_k: int = 20) -> List[str]:
    tokens = tokenize(text)
    freq = defaultdict(int)
    for t in tokens:
        if len(t) < 2:
            continue
        freq[t] += 1
    ranked = sorted(freq.items(), key=lambda x: (x[0] not in TECH_SKILLS, -x[1]))
    return [w for w, _ in ranked[:top_k]]

def cosine_sim(a: List[float], b: List[float]) -> float:
    import math
    dot = sum(x*y for x, y in zip(a, b))
    na = math.sqrt(sum(x*x for x in a))
    nb = math.sqrt(sum(y*y for y in b))
    return 0.0 if na == 0 or nb == 0 else dot / (na * nb)

def tfidf_vectorize(corpus: List[str]):
    try:
        from sklearn.feature_extraction.text import TfidfVectorizer
        vec = TfidfVectorizer(stop_words='english', max_features=5000)
        X = vec.fit_transform(corpus)
        return vec, X
    except ImportError:
        # Fallback if sklearn is not installed
        raise ImportError("scikit-learn is required for TF-IDF vectorization. Install it with: pip install scikit-learn")

def compute_match_score(resume_text: str, jd_text: str) -> Dict:
    if not jd_text:
        return None
    vec, X = tfidf_vectorize([resume_text, jd_text])
    r, j = X[0].toarray()[0], X[1].toarray()[0]
    sim = cosine_sim(r, j)
    jd_top = extract_keywords(jd_text, top_k=30)
    resume_tokens = set(tokenize(resume_text))
    missing = [k for k in jd_top if k not in resume_tokens]
    return {
        'similarity': round(sim * 100, 2),
        'missing_keywords': missing,
        'jd_top_keywords': jd_top,
    }

def ats_checks(resume_text: str, sections: Dict[str, str]) -> Dict:
    text_lower = resume_text.lower()
    missing_sections = []
    for s in ['education', 'experience', 'projects', 'skills']:
        if s not in sections:
            missing_sections.append(s)

    formatting = {
        'has_contact_info': bool(re.search(r'\b(email|@|\+?\d{10,})', text_lower)),
        'has_links': 'linkedin' in text_lower or 'github' in text_lower,
        'has_bullets': ('•' in resume_text) or bool(re.search(r'\n\s*[-*]\s+', resume_text)),
        'has_paragraph_blobs': bool(re.search(r'\n\s*[A-Za-z]{50,}\s', resume_text)),
        'page_length_ok': len(resume_text) < 8000,
    }

    tokens = set(tokenize(resume_text))
    skill_hits = sorted(list(TECH_SKILLS.intersection(tokens)))

    return {
        'missing_sections': missing_sections,
        'formatting': formatting,
        'skill_hits': skill_hits,
    }

def grammar_issues(text: str, max_issues: int = 20) -> Dict:
    try:
        import language_tool_python  # optional
        tool = language_tool_python.LanguageTool('en-US')
        matches = tool.check(text[:10000])
        issues = []
        for m in matches[:max_issues]:
            snippet = text[max(0, m.offset-40): m.offset + 40]
            issues.append({
                'message': m.message,
                'suggestions': m.replacements[:3],
                'context': snippet.replace('\n', ' ')
            })
        return {'count': len(matches), 'samples': issues}
    except Exception:
        return {'count': 0, 'samples': [], 'note': 'language_tool_python not installed'}

def build_score_breakdown(sections, ats_report, match_score=None, grammar_count=0):
    w_match = 0.5 if match_score is not None else 0.0
    w_ats = 0.3
    w_sections = 0.15
    w_grammar = 0.05

    ats_fmt = ats_report['formatting']
    ats_points = 0
    ats_points += 0.25 if ats_fmt['has_contact_info'] else 0
    ats_points += 0.25 if ats_fmt['has_links'] else 0
    ats_points += 0.25 if ats_fmt['has_bullets'] else 0
    ats_points += 0.25 if ats_fmt['page_length_ok'] else 0
    ats_score = ats_points * 100

    required = ['education', 'experience', 'projects', 'skills']
    present = sum(1 for r in required if r in sections)
    section_score = (present / len(required)) * 100

    if grammar_count == 0:
        grammar_score = 100
    else:
        grammar_score = max(60, 100 - min(grammar_count, 20) * 2)

    components = []
    if w_match > 0:
        components.append(('Job Match', w_match, match_score))
    components.append(('ATS/Formatting', w_ats, ats_score))
    components.append(('Sections', w_sections, section_score))
    components.append(('Grammar', w_grammar, grammar_score))

    overall = 0.0
    for name, w, val in components:
        overall += w * (val if val is not None else 0)

    breakdown = [{
        'name': name,
        'weight': int(w * 100),
        'score': round(val if val is not None else 0, 2)
    } for name, w, val in components]

    return round(overall, 2), breakdown
