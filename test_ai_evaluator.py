# test_ai_evaluator.py

# ---------------------------------------------------
# ध्यान दें: ai_evaluator.py utils folder में है
# इसलिए import को update किया गया है
# ---------------------------------------------------
from utils.ai_evaluator import evaluate_resume
import os

# -------------------- Set your resume file --------------------
# अपनी resume file का exact नाम डालो यहाँ (PDF या DOCX)
resume_file = "sample_resume.pdf.docx"  # ध्यान दें: यही file तुम्हारे folder में है

# -------------------- Optional Job Description --------------------
job_description = """
We are looking for a Python Developer with experience in Django, Flask,
REST API, and SQL databases. Strong problem-solving skills and teamwork
ability are required.
"""

# -------------------- Check if resume exists --------------------
current_dir = os.path.dirname(os.path.abspath(__file__))
resume_path = os.path.join(current_dir, resume_file)

if not os.path.exists(resume_path):
    print(f"Error: Resume file '{resume_file}' not found in the project folder.")
else:
    # -------------------- Evaluate resume --------------------
    result = evaluate_resume(resume_path, job_description)

    if result:
        print("=== Resume Evaluation Result ===")
        print(f"Overall Score: {result['overall_score']}")
        print(f"ATS Score: {result['ats_score']}")
        print(f"Keyword Score: {result['keyword_score']}")
        print(f"Grammar Score: {result['grammar_score']}")
        print(f"Structure Score: {result['structure_score']}")
        print(f"Skills Score: {result['skills_score']}")
        print(f"JD Match %: {result['jd_match_percentage']}")
        print(f"Suggested Roles: {result['suggested_roles']}\n")
        
        print("=== Feedback ===")
        print(result['detailed_feedback'])
    else:
        print("Error: Resume file not supported or evaluation failed.")
