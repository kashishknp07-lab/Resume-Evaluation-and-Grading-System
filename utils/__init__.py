"""
Utils package for Resume Evaluator application
"""
# Import main evaluation function
try:
    from .ai_evaluator import evaluate_resume
except ImportError as e:
    evaluate_resume = None
    import warnings
    warnings.warn(f"Could not import evaluate_resume: {e}")

# Import improvement functions (optional)
try:
    from .ai_improvements import (
        generate_improvement_suggestions,
        identify_missing_keywords,
        suggest_action_verbs,
        analyze_resume_gaps,
        generate_example_phrases
    )
except ImportError:
    generate_improvement_suggestions = None
    identify_missing_keywords = None
    suggest_action_verbs = None
    analyze_resume_gaps = None
    generate_example_phrases = None

# Import NLP functions (optional)
try:
    from .nlp import (
        parse_resume_sections,
        extract_keywords,
        compute_match_score,
        ats_checks,
        grammar_issues,
        build_score_breakdown
    )
except ImportError:
    parse_resume_sections = None
    extract_keywords = None
    compute_match_score = None
    ats_checks = None
    grammar_issues = None
    build_score_breakdown = None

__all__ = [
    'evaluate_resume',
    'generate_improvement_suggestions',
    'identify_missing_keywords',
    'suggest_action_verbs',
    'analyze_resume_gaps',
    'generate_example_phrases',
    'parse_resume_sections',
    'extract_keywords',
    'compute_match_score',
    'ats_checks',
    'grammar_issues',
    'build_score_breakdown'
]
