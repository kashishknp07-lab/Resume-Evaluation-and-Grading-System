# AI-Powered Resume Evaluation and Grading System

## Project Overview
A comprehensive web application built with Flask that provides AI-powered resume analysis, evaluation, and generation capabilities. Users can upload their resumes to receive detailed feedback, compare them against job descriptions, and generate new resumes using an AI-assisted builder.

## Current State
✅ **Fully Functional** - All core features implemented and tested
- Application running successfully on Flask development server (port 5000)
- Database initialized with user authentication and evaluation history
- All pages accessible and working (home, login, signup, upload, result, generate, dashboard)
- AI evaluation engine operational using spaCy NLP

## Features Implemented

### 1. User Authentication
- Secure signup and login system with password hashing (Werkzeug)
- Session management using Flask-Login
- Protected routes requiring authentication
- User-specific data isolation

### 2. Resume Upload & Evaluation
- Support for PDF and DOCX file formats (max 16MB)
- File validation and secure filename handling
- AI-powered analysis using spaCy NLP:
  - ATS Compliance scoring
  - Keyword optimization analysis
  - Grammar and language quality assessment
  - Resume structure evaluation
  - Skills assessment
- Overall score calculation (0-100 weighted average)

### 3. Job Description Matching
- Optional JD input for targeted analysis
- Match percentage calculation
- Keyword overlap analysis

### 4. AI Resume Builder
- User-friendly form for inputting resume data
- Generates professional PDF resumes
- Includes sections: Contact, Skills, Experience, Education

### 5. Profile Suggestions
- AI-powered job role recommendations
- Based on resume content analysis
- Top 3 best-fit roles suggested

### 6. Interactive Visualizations (Enhanced)
- Chart.js integration for comprehensive data visualization
- **7 Different Chart Types:**
  1. **Vertical Bar Chart** - Traditional score breakdown
  2. **Pie Chart** - Category distribution view
  3. **Radar Chart** - Multi-dimensional performance view
  4. **Horizontal Bar Chart** - Side-by-side comparison
  5. **Line Chart** - Performance vs Industry Average and Target Score
  6. **Doughnut Chart** - Alternative category distribution
  7. **Gauge Chart** - Visual representation of overall score
- Animated progress bars for individual metrics
- Performance level indicators (Excellent, Good, Average, Needs Improvement)

### 7. Dashboard & History
- User dashboard with evaluation history
- Statistics: total evaluations, average score, best score
- Quick access to past evaluations
- View and download previous reports

### 8. PDF Report Generation
- Downloadable evaluation reports
- Professional formatting using ReportLab
- Includes all scores, feedback, and suggestions

## Project Architecture

### Backend (Flask)
- **app.py** - Main application with all routes and business logic
- **database.py** - SQLite database initialization and connection management
- **ai_evaluator.py** - AI/NLP evaluation engine using spaCy

### Frontend (Templates)
- **base.html** - Base template with Bootstrap 5 and navigation
- **index.html** - Home page with feature showcase
- **login.html** / **signup.html** - Authentication pages
- **upload.html** - Resume upload form with JD input
- **result.html** - Evaluation results with charts
- **generate.html** - AI resume builder form
- **dashboard.html** - User dashboard with history

### Styling
- **static/css/style.css** - Custom styles with modern gradient design
- Bootstrap 5 for responsive layout
- Font Awesome icons
- Chart.js for data visualization

### Database Schema
- **users** - User accounts (id, username, email, password_hash, created_at)
- **evaluations** - Resume evaluations with scores and feedback
- **generated_resumes** - AI-generated resume data

## Dependencies

### Python Packages (installed via uv)
- flask - Web framework
- flask-login - Session management
- werkzeug - Password hashing and file handling
- spacy - NLP for resume analysis (with en_core_web_sm model)
- python-docx - DOCX file parsing
- PyPDF2 - PDF file parsing
- reportlab - PDF generation
- python-dateutil - Date handling

### Frontend Libraries (CDN)
- Bootstrap 5 - CSS framework
- Chart.js - Data visualization
- Font Awesome - Icons

## Setup Instructions

### Prerequisites
- Python 3.11 installed
- spaCy English model downloaded: `python -m spacy download en_core_web_sm`

### Running the Application
1. Install dependencies (already configured in uv)
2. Run the Flask server: `python app.py`
3. Access at http://localhost:5000
4. Create an account via signup
5. Upload resume or generate new one

### Environment Variables
- `SESSION_SECRET` - Flask session secret (configured in Replit Secrets)

## Security Features
- Password hashing using Werkzeug's secure hash functions
- Parameterized SQL queries to prevent SQL injection
- File upload validation (type, size, secure filenames)
- Protected routes with authentication required
- Session-based authentication with Flask-Login

## AI Evaluation Logic

### Scoring Components (ai_evaluator.py)
1. **ATS Compliance (0-100)** - Contact info, headers, action verbs, keywords
2. **Keyword Optimization (0-100)** - Technical and soft skills, JD matching
3. **Grammar Quality (0-100)** - Sentence structure, capitalization, language quality
4. **Structure (0-100)** - Section organization, length, bullet points
5. **Skills Assessment (0-100)** - Technical and soft skills coverage

### Overall Score Formula
```
Overall = (ATS × 0.25) + (Keywords × 0.25) + (Grammar × 0.15) + (Structure × 0.20) + (Skills × 0.15)
```

### Job Role Suggestion
Analyzes resume content against predefined role keyword sets:
- Software Developer
- Data Analyst
- Data Scientist
- DevOps Engineer
- Product Manager
- UI/UX Designer
- Marketing Manager
- Business Analyst

## Recent Changes
- **2025-10-09**: Added 12 new comprehensive features
  - **AI-Powered Improvements**: Detailed suggestions, missing keywords, action verb recommendations
  - **Resume Comparison Tool**: Side-by-side comparison with visual charts
  - **Export Options**: JSON and CSV export for evaluations
  - **Shareable Links**: Generate public links to share evaluation results
  - **Enhanced Dashboard**: Delete evaluations, bulk export, share functionality
  - **Resume Tips Page**: Comprehensive guide with ATS tips, keywords, industry-specific advice
  - **Account Settings**: Profile editing, password change, preferences management
  - **Advanced JD Matching**: Missing keywords highlighting and intelligent suggestions
  - **Batch Upload**: Process multiple resumes simultaneously
  - **Score History Tracking**: View progress over time with trend analysis
  - **Email Preferences**: Opt-in for notifications (requires SendGrid/Resend setup)
  - **Helper Modules**: Created ai_improvements.py and helpers.py for code organization
- **2025-10-09**: Enhanced visualization features
  - Added 7 different interactive chart types to results page
  - Implemented radar chart for multi-dimensional view
  - Added line chart comparing performance vs benchmarks
  - Added gauge chart for overall score visualization
  - Added performance level indicators for each metric
  - All charts fully interactive with Chart.js
- **2025-10-09**: Initial implementation completed
  - All core features implemented and tested
  - Database schema created
  - AI evaluation engine integrated
  - All templates and styling completed
  - Application successfully running and tested

## Future Enhancements (Next Phase)
1. Replace placeholder AI logic with real OpenAI API integration
2. Add batch resume processing
3. Implement resume version comparison
4. Add email notifications
5. Create admin panel for analytics
6. Add unit and integration tests
7. Deploy to production with proper WSGI server

## Notes for Developers
- Code is beginner-friendly with comprehensive comments
- All routes are documented with docstrings
- Database uses SQLite for development (consider PostgreSQL for production)
- AI evaluation uses placeholder/heuristic logic ready for OpenAI API replacement
- spaCy model (en_core_web_sm) must be downloaded for full NLP features
- Development server runs with debug mode (disable in production)

## File Structure
```
.
├── app.py                      # Main Flask application
├── database.py                 # Database initialization
├── ai_evaluator.py             # AI evaluation engine
├── resume_evaluator.db         # SQLite database
├── static/
│   ├── css/
│   │   └── style.css          # Custom styles
│   └── uploads/               # Uploaded resume files
├── templates/
│   ├── base.html              # Base template
│   ├── index.html             # Home page
│   ├── login.html             # Login page
│   ├── signup.html            # Signup page
│   ├── upload.html            # Upload page
│   ├── result.html            # Results page
│   ├── generate.html          # Resume builder
│   └── dashboard.html         # User dashboard
└── replit.md                  # This file
```