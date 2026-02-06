"""
AI Evaluator module for Resume Evaluator application
Handles resume parsing, scoring, and feedback generation
"""
import spacy
import re
from collections import Counter
import PyPDF2
from docx import Document
import os

# ---------------------- Load spaCy model ----------------------
try:
    nlp = spacy.load('en_core_web_sm')
except Exception:
    nlp = None
    try:
        print("Warning: spaCy model not loaded. Grammar evaluation will use default scores.")
    except UnicodeEncodeError:
        print("Warning: spaCy model not loaded. Grammar evaluation will use default scores.")

# ---------------------- Common ATS keywords ----------------------
ATS_KEYWORDS = {
    'technical': [
        'python', 'java', 'javascript', 'sql', 'aws', 'docker', 'kubernetes', 'react',
        'node.js', 'git', 'agile', 'api', 'data', 'analytics', 'machine learning',
        'ai', 'cloud', 'devops', 'ci/cd', 'testing'
    ],
    'soft_skills': [
        'leadership', 'communication', 'teamwork', 'problem-solving', 'management',
        'collaboration', 'analytical', 'creative', 'organized', 'adaptable'
    ],
    'action_verbs': [
        'developed', 'managed', 'led', 'created', 'implemented', 'designed',
        'achieved', 'improved', 'optimized', 'delivered', 'coordinated'
    ]
}

# ---------------------- Job role keywords mapping ----------------------
JOB_ROLES = {
    'Software Developer': ['python', 'java', 'javascript', 'programming', 'development', 'coding', 'software', 'git'],
    'Data Analyst': ['data', 'analytics', 'sql', 'excel', 'statistics', 'visualization', 'tableau', 'power bi'],
    'Data Scientist': ['machine learning', 'ai', 'python', 'data science', 'statistics', 'modeling', 'algorithms'],
    'DevOps Engineer': ['devops', 'aws', 'docker', 'kubernetes', 'ci/cd', 'jenkins', 'terraform', 'cloud'],
    'Product Manager': ['product', 'management', 'agile', 'scrum', 'roadmap', 'stakeholder', 'strategy'],
    'UI/UX Designer': ['design', 'ui', 'ux', 'figma', 'wireframe', 'prototype', 'user experience', 'adobe'],
    'Marketing Manager': ['marketing', 'campaign', 'seo', 'analytics', 'social media', 'brand', 'strategy'],
    'Business Analyst': ['business', 'analysis', 'requirements', 'stakeholder', 'process', 'documentation']
}

# ---------------------- File Text Extraction ----------------------
def extract_text_from_pdf(file_path):
    if not os.path.exists(file_path):
        return "Error: File not found"
    try:
        with open(file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            text = ''
            for page in pdf_reader.pages:
                text += page.extract_text() or ''
            return text
    except Exception as e:
        return f"Error reading PDF: {str(e)}"

def extract_text_from_docx(file_path):
    if not os.path.exists(file_path):
        return "Error: File not found"
    try:
        doc = Document(file_path)
        return '\n'.join([para.text for para in doc.paragraphs])
    except Exception as e:
        return f"Error reading DOCX: {str(e)}"

def extract_text_from_file(file_path):
    if not os.path.exists(file_path):
        return "Error: File not found"
    if file_path.lower().endswith('.pdf'):
        return extract_text_from_pdf(file_path)
    elif file_path.lower().endswith('.docx'):
        return extract_text_from_docx(file_path)
    else:
        return "Unsupported file format"

# ---------------------- Evaluation Functions ----------------------
def evaluate_ats_compliance(text):
    text_lower = text.lower()
    score = 0

    if re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b', text):
        score += 10
    if re.search(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b', text):
        score += 10

    headers = ['experience', 'education', 'skills', 'summary', 'objective']
    header_count = sum(1 for h in headers if h in text_lower)
    score += min(header_count * 10, 30)

    action_verb_count = sum(1 for verb in ATS_KEYWORDS['action_verbs'] if verb in text_lower)
    score += min(action_verb_count * 2, 20)

    tech_count = sum(1 for keyword in ATS_KEYWORDS['technical'] if keyword in text_lower)
    score += min(tech_count * 2, 20)

    if len(text.split('\n')) > 10:
        score += 10

    return min(score, 100)

def evaluate_keywords(text, job_description=None):
    text_lower = text.lower()

    if job_description:
        jd_words = re.findall(r'\b\w{4,}\b', job_description.lower())
        jd_freq = Counter(jd_words).most_common(20)
        matches = sum(1 for word, _ in jd_freq if word in text_lower)
        score = (matches / len(jd_freq) * 100) if jd_freq else 50
    else:
        all_keywords = ATS_KEYWORDS['technical'] + ATS_KEYWORDS['soft_skills']
        found = sum(1 for kw in all_keywords if kw in text_lower)
        score = min((found / len(all_keywords)) * 200, 100)

    return min(score, 100)

def evaluate_grammar(text):
    if not nlp:
        return 75.0

    doc = nlp(text[:1000000])
    score = 100
    sentences = list(doc.sents)

    if len(sentences) < 5:
        score -= 20

    long_sentences = sum(1 for sent in sentences if len(sent) > 50)
    score -= min(long_sentences * 5, 20)

    if not any(token.text[0].isupper() for token in doc if token.is_alpha):
        score -= 10

    return max(score, 0)

def evaluate_structure(text):
    score = 0
    text_lower = text.lower()

    sections = {
        'contact': ['email', 'phone', 'linkedin'],
        'summary': ['summary', 'objective', 'profile'],
        'experience': ['experience', 'work history', 'employment'],
        'education': ['education', 'degree', 'university', 'college'],
        'skills': ['skills', 'technical skills', 'competencies']
    }

    for kws in sections.values():
        if any(kw in text_lower for kw in kws):
            score += 20

    word_count = len(text.split())
    if 300 <= word_count <= 800:
        score += 10
    elif 200 <= word_count <= 1000:
        score += 5

    if '•' in text or '-' in text or re.search(r'\n\s*\d+\.', text):
        score += 10

    return min(score, 100)

def evaluate_skills(text):
    text_lower = text.lower()
    tech = sum(1 for s in ATS_KEYWORDS['technical'] if s in text_lower)
    soft = sum(1 for s in ATS_KEYWORDS['soft_skills'] if s in text_lower)
    return min((tech * 5) + (soft * 3), 100)

def calculate_jd_match(resume_text, job_description):
    if not job_description:
        return 0

    resume_words = set(re.findall(r'\b\w{4,}\b', resume_text.lower()))
    jd_words = set(re.findall(r'\b\w{4,}\b', job_description.lower()))
    common = resume_words.intersection(jd_words)

    return min((len(common) / len(jd_words)) * 100 if jd_words else 0, 100)

def suggest_job_roles(text):
    text_lower = text.lower()
    role_scores = {role: sum(1 for kw in kws if kw in text_lower) for role, kws in JOB_ROLES.items()}
    top_roles = [
        role for role, score in sorted(role_scores.items(), key=lambda x: x[1], reverse=True)[:3]
        if score > 0
    ]
    return top_roles if top_roles else ['General Professional']

def generate_feedback(scores, resume_text):
    feedback = []

    if scores['ats_score'] < 70:
        feedback.append("⚠️ ATS Compliance: Add clear sections (Experience, Education, Skills) and contact info.")
    else:
        feedback.append("✓ ATS Compliance: Well-structured for ATS systems.")

    if scores['keyword_score'] < 60:
        feedback.append("⚠️ Keywords: Include more role-specific keywords and technical skills.")
    else:
        feedback.append("✓ Keywords: Good keyword optimization.")

    if scores['grammar_score'] < 70:
        feedback.append("⚠️ Grammar: Review grammar, punctuation, and sentence structure.")
    else:
        feedback.append("✓ Grammar: Language quality is good.")

    if scores['structure_score'] < 70:
        feedback.append("⚠️ Structure: Add clear sections and use bullet points.")
    else:
        feedback.append("✓ Structure: Resume layout is good.")

    if scores['skills_score'] < 60:
        feedback.append("⚠️ Skills: Include more technical and soft skills relevant to your field.")
    else:
        feedback.append("✓ Skills: Skills coverage is good.")

    feedback.append("\n📋 General Recommendations:")
    feedback.append("• Keep your resume concise (1-2 pages)")
    feedback.append("• Use action verbs to describe achievements")
    feedback.append("• Quantify your accomplishments with numbers/metrics")
    feedback.append("• Tailor your resume to match the job description")
    feedback.append("• Ensure consistent formatting throughout")

    return '\n'.join(feedback)

# ---------------------- Main Evaluation Function ----------------------
def evaluate_resume(file_path, job_description=None):
    resume_text = extract_text_from_file(file_path)

    if resume_text.startswith("Error") or resume_text == "Unsupported file format":
        return None

    ats_score = evaluate_ats_compliance(resume_text)
    keyword_score = evaluate_keywords(resume_text, job_description)
    grammar_score = evaluate_grammar(resume_text)
    structure_score = evaluate_structure(resume_text)
    skills_score = evaluate_skills(resume_text)

    overall_score = (
        ats_score * 0.25 +
        keyword_score * 0.25 +
        grammar_score * 0.15 +
        structure_score * 0.20 +
        skills_score * 0.15
    )

    jd_match = calculate_jd_match(resume_text, job_description) if job_description else 0
    suggested_roles = suggest_job_roles(resume_text)

    scores = {
        'ats_score': ats_score,
        'keyword_score': keyword_score,
        'grammar_score': grammar_score,
        'structure_score': structure_score,
        'skills_score': skills_score
    }

    feedback = generate_feedback(scores, resume_text)

    return {
        'overall_score': round(overall_score, 2),
        'ats_score': round(ats_score, 2),
        'keyword_score': round(keyword_score, 2),
        'grammar_score': round(grammar_score, 2),
        'structure_score': round(structure_score, 2),
        'skills_score': round(skills_score, 2),
        'jd_match_percentage': round(jd_match, 2),
        'suggested_roles': suggested_roles,
        'detailed_feedback': feedback,
        'resume_text': resume_text
    }
