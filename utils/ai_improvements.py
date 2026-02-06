"""
AI-powered improvement suggestions and advanced analysis
"""
import re
from collections import Counter

def generate_improvement_suggestions(resume_text, scores, job_description=None):
    """Generate detailed improvement suggestions based on scores"""
    suggestions = []
    
    # ATS Compliance Suggestions
    if scores['ats_score'] < 80:
        suggestions.append({
            'category': 'ATS Compliance',
            'priority': 'High',
            'suggestions': [
                'Add clear section headers: EXPERIENCE, EDUCATION, SKILLS, SUMMARY',
                'Ensure your contact information (email, phone) is prominently displayed',
                'Use standard fonts like Arial, Calibri, or Times New Roman',
                'Avoid tables, text boxes, and columns that ATS systems struggle with',
                'Save your resume as a .docx or .pdf file for maximum compatibility'
            ]
        })
    
    # Keyword Optimization Suggestions
    if scores['keyword_score'] < 70:
        suggestions.append({
            'category': 'Keyword Optimization',
            'priority': 'High',
            'suggestions': [
                'Include more industry-specific technical keywords',
                'Match the job description language exactly when describing your skills',
                'Add action verbs like: developed, managed, implemented, designed, optimized',
                'Include both acronyms and full terms (e.g., "AI (Artificial Intelligence)")',
                'Mention specific tools, technologies, and methodologies you\'ve used'
            ]
        })
    
    # Grammar Suggestions
    if scores['grammar_score'] < 75:
        suggestions.append({
            'category': 'Grammar & Language',
            'priority': 'Medium',
            'suggestions': [
                'Proofread for spelling and grammatical errors',
                'Use consistent verb tenses (past tense for previous roles, present for current)',
                'Keep sentences concise and professional',
                'Avoid first-person pronouns (I, me, my)',
                'Use bullet points to improve readability'
            ]
        })
    
    # Structure Suggestions
    if scores['structure_score'] < 75:
        suggestions.append({
            'category': 'Resume Structure',
            'priority': 'High',
            'suggestions': [
                'Organize sections in this order: Summary, Experience, Education, Skills',
                'Use bullet points to list achievements and responsibilities',
                'Keep your resume to 1-2 pages maximum',
                'Ensure consistent formatting (font sizes, spacing, alignment)',
                'Add white space to make the document easier to scan'
            ]
        })
    
    # Skills Suggestions
    if scores['skills_score'] < 70:
        suggestions.append({
            'category': 'Skills Section',
            'priority': 'Medium',
            'suggestions': [
                'Create a dedicated "Skills" or "Technical Skills" section',
                'List both technical skills (programming languages, software) and soft skills',
                'Group skills by category (e.g., Programming, Data Analysis, Leadership)',
                'Include proficiency levels if relevant (Expert, Advanced, Intermediate)',
                'Add certifications or training related to key skills'
            ]
        })
    
    # Job Description Specific
    if job_description:
        suggestions.append({
            'category': 'Job Description Matching',
            'priority': 'Critical',
            'suggestions': [
                'Tailor your resume to match the specific job requirements',
                'Mirror the language and terminology used in the job posting',
                'Highlight experiences that directly relate to the role',
                'Quantify your achievements with numbers and metrics',
                'Address all required qualifications mentioned in the posting'
            ]
        })
    
    # General Best Practices
    suggestions.append({
        'category': 'General Best Practices',
        'priority': 'Low',
        'suggestions': [
            'Lead with accomplishments, not just responsibilities',
            'Use numbers and metrics to quantify your impact (e.g., "Increased sales by 25%")',
            'Focus on the last 10-15 years of experience',
            'Include a professional summary or objective at the top',
            'Tailor each resume version to the specific job application'
        ]
    })
    
    return suggestions

def identify_missing_keywords(resume_text, job_description):
    """Identify keywords present in JD but missing from resume"""
    if not job_description:
        return []
    
    resume_lower = resume_text.lower()
    jd_lower = job_description.lower()
    
    # Extract significant words from JD (4+ characters)
    jd_words = set(re.findall(r'\b[a-z]{4,}\b', jd_lower))
    resume_words = set(re.findall(r'\b[a-z]{4,}\b', resume_lower))
    
    # Common words to ignore
    common_words = {'will', 'with', 'have', 'from', 'this', 'that', 'your', 'about',
                    'into', 'than', 'them', 'these', 'those', 'could', 'would', 'should',
                    'there', 'their', 'where', 'which', 'while', 'other', 'more', 'some',
                    'such', 'only', 'also', 'both', 'been', 'were', 'when', 'what'}
    
    # Find missing important keywords
    missing = jd_words - resume_words - common_words
    
    # Count frequency in JD to prioritize
    jd_word_counts = Counter(re.findall(r'\b[a-z]{4,}\b', jd_lower))
    missing_with_freq = [(word, jd_word_counts[word]) for word in missing]
    missing_with_freq.sort(key=lambda x: x[1], reverse=True)
    
    return [word for word, _ in missing_with_freq[:20]]  # Top 20 missing keywords

def suggest_action_verbs(resume_text):
    """Suggest strong action verbs to improve resume impact"""
    action_verbs = {
        'Leadership': ['led', 'managed', 'directed', 'coordinated', 'supervised', 'mentored'],
        'Achievement': ['achieved', 'accomplished', 'exceeded', 'surpassed', 'delivered', 'completed'],
        'Innovation': ['created', 'developed', 'designed', 'pioneered', 'launched', 'introduced'],
        'Improvement': ['improved', 'enhanced', 'optimized', 'streamlined', 'upgraded', 'transformed'],
        'Analysis': ['analyzed', 'evaluated', 'assessed', 'researched', 'identified', 'investigated'],
        'Communication': ['presented', 'communicated', 'collaborated', 'negotiated', 'facilitated', 'consulted']
    }
    
    resume_lower = resume_text.lower()
    suggestions = {}
    
    for category, verbs in action_verbs.items():
        found_count = sum(1 for verb in verbs if verb in resume_lower)
        if found_count < 2:  # If using fewer than 2 verbs from category
            suggestions[category] = [v for v in verbs if v not in resume_lower][:3]
    
    return suggestions

def analyze_resume_gaps(scores):
    """Analyze which areas need the most improvement"""
    gaps = []
    
    score_items = [
        ('ATS Compliance', scores['ats_score']),
        ('Keyword Optimization', scores['keyword_score']),
        ('Grammar Quality', scores['grammar_score']),
        ('Resume Structure', scores['structure_score']),
        ('Skills Assessment', scores['skills_score'])
    ]
    
    # Sort by score (lowest first)
    score_items.sort(key=lambda x: x[1])
    
    for category, score in score_items:
        if score < 70:
            gap_size = 70 - score
            gaps.append({
                'category': category,
                'current_score': score,
                'target_score': 70,
                'gap': gap_size,
                'priority': 'High' if gap_size > 20 else 'Medium'
            })
    
    return gaps

def generate_example_phrases(role):
    """Generate example phrases based on suggested role"""
    examples = {
        'Software Developer': [
            'Developed and maintained scalable web applications using Python and JavaScript',
            'Implemented RESTful APIs serving 100K+ daily requests with 99.9% uptime',
            'Collaborated with cross-functional teams to deliver features ahead of schedule'
        ],
        'Data Analyst': [
            'Analyzed large datasets using SQL and Python to uncover business insights',
            'Created interactive dashboards in Tableau, improving decision-making speed by 40%',
            'Presented data-driven recommendations to executive leadership'
        ],
        'Data Scientist': [
            'Built machine learning models achieving 95% accuracy in customer churn prediction',
            'Developed predictive analytics solutions that increased revenue by $2M annually',
            'Automated data pipelines processing 10TB+ of data daily'
        ],
        'Product Manager': [
            'Led product roadmap for 3 major features, resulting in 50% user growth',
            'Conducted user research and A/B testing to validate product hypotheses',
            'Coordinated with engineering, design, and marketing teams to launch on schedule'
        ],
        'DevOps Engineer': [
            'Implemented CI/CD pipelines reducing deployment time from hours to minutes',
            'Managed cloud infrastructure on AWS, optimizing costs by 30%',
            'Automated infrastructure provisioning using Terraform and Kubernetes'
        ]
    }
    
    return examples.get(role, [
        'Achieved measurable results in your previous role',
        'Collaborated effectively with team members and stakeholders',
        'Demonstrated expertise in relevant tools and technologies'
    ])