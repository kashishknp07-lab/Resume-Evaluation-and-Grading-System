from flask import (
    Flask, render_template, request, redirect, url_for,
    flash, send_file, jsonify, make_response
)
from flask_login import (
    LoginManager, UserMixin, login_user, login_required,
    logout_user, current_user
)
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from pymongo import MongoClient
from bson import ObjectId
import os
from datetime import datetime
from statistics import mean

# Import AI evaluator
from utils.ai_evaluator import evaluate_resume as ai_evaluate_resume

# PDF generation imports (ReportLab)
try:
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.units import inch
    from reportlab.pdfgen import canvas
    REPORTLAB_AVAILABLE = True
except Exception:
    REPORTLAB_AVAILABLE = False

# ========================================================
# 🚀 FLASK APP CONFIGURATION
# ========================================================

app = Flask(__name__, template_folder='templates', static_folder='static')
app.secret_key = os.environ.get('SESSION_SECRET', 'dev-secret-key-change-in-production')

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'uploads')
GENERATED_FOLDER = os.path.join(BASE_DIR, 'static', 'generated')
ALLOWED_EXTENSIONS = {'pdf', 'docx'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['GENERATED_FOLDER'] = GENERATED_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(GENERATED_FOLDER, exist_ok=True)

# ========================================================
# 🔹 MONGODB CONNECTION (LOCAL)
# ========================================================

# Local MongoDB connection settings
MONGO_HOST = os.environ.get('MONGO_HOST', 'localhost')
MONGO_PORT = int(os.environ.get('MONGO_PORT', 27017))
DATABASE_NAME = 'resume_evaluator'

# Build local MongoDB URI
MONGO_URI = f"mongodb://{MONGO_HOST}:{MONGO_PORT}/{DATABASE_NAME}"

# Global MongoDB connection variables
_client = None
_db = None
_users_col = None
_evaluations_col = None
_generated_col = None
_connection_status = False

def is_connection_alive():
    """Check if MongoDB connection exists and is alive"""
    global _client, _connection_status
    if _client is None:
        return False
    try:
        # Try to ping the database
        _client.admin.command('ping')
        _connection_status = True
        return True
    except Exception:
        _connection_status = False
        return False

def create_mongo_connection():
    """Create a new MongoDB connection to local MongoDB"""
    global _client, _db, _users_col, _evaluations_col, _generated_col, _connection_status
    try:
        print(f"Creating MongoDB connection to {MONGO_HOST}:{MONGO_PORT}...")
        _client = MongoClient(
            MONGO_URI,
            serverSelectionTimeoutMS=5000,
            connectTimeoutMS=5000
        )
        
        # Test the connection
        _client.admin.command('ping')
        print("MongoDB connection successful!")
        
        # Initialize database and collections
        _db = _client[DATABASE_NAME]
        _users_col = _db['users']
        _evaluations_col = _db['evaluations']
        _generated_col = _db['generated_resumes']
        
        # Create indexes for better performance
        try:
            _users_col.create_index("username", unique=True)
            _users_col.create_index("email", unique=True)
            _evaluations_col.create_index("user_id")
            _evaluations_col.create_index("created_at")
            print("Database indexes created/verified")
        except Exception as e:
            print(f"Index creation warning: {e}")
        
        _connection_status = True
        return True
    except Exception as e:
        print(f"MongoDB connection failed: {e}")
        print(f"Please make sure MongoDB is running on {MONGO_HOST}:{MONGO_PORT}")
        _connection_status = False
        _client = None
        _db = None
        _users_col = None
        _evaluations_col = None
        _generated_col = None
        return False

def get_mongo_client():
    """Get or create MongoDB client - checks if connection exists, creates if not"""
    global _client, _connection_status
    
    # Check if connection exists and is alive
    if is_connection_alive():
        return _client
    
    # Connection doesn't exist or is dead, create new one
    if create_mongo_connection():
        return _client
    else:
        print("MongoDB connection unavailable. Some features may not work.")
        return None

def get_users_col():
    """Get users collection - creates connection if needed"""
    get_mongo_client()
    return _users_col

def get_evaluations_col():
    """Get evaluations collection - creates connection if needed"""
    get_mongo_client()
    return _evaluations_col

def get_generated_col():
    """Get generated resumes collection - creates connection if needed"""
    get_mongo_client()
    return _generated_col

def check_db_connection():
    """Check if database connection is available"""
    return _connection_status and _users_col is not None

def initialize_database():
    """Initialize MongoDB connection on startup"""
    print("Initializing database connection...")
    if get_mongo_client():
        print("Database initialized and ready!")
        return True
    else:
        print("Database initialization failed. App will continue but DB features may not work.")
        return False

# Initialize database connection on module load
initialize_database()

# ========================================================
# 🔹 CUSTOM JINJA FILTER
# ========================================================

@app.template_filter('average')
def average_filter(numbers):
    try:
        nums = [float(n) for n in numbers if n is not None]
        return mean(nums) if nums else 0
    except Exception:
        return 0

# ========================================================
# 👤 USER MANAGEMENT
# ========================================================

class User(UserMixin):
    def __init__(self, id, username, email):
        self.id = str(id)
        self.username = username
        self.email = email

@login_manager.user_loader
def load_user(user_id):
    try:
        users_col = get_users_col()
        if users_col is None:
            return None
        user = users_col.find_one({"_id": ObjectId(user_id)})
        if user:
            return User(user['_id'], user['username'], user['email'])
    except Exception:
        pass
    return None

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# ========================================================
# 🔑 AUTH ROUTES
# ========================================================

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        if not check_db_connection():
            flash('Database connection unavailable. Please try again later.', 'error')
            return redirect(url_for('signup'))
            
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        if not username or not email or not password:
            flash('सभी फ़ील्ड भरना आवश्यक है!', 'error')
            return redirect(url_for('signup'))

        users_col = get_users_col()
        if users_col is None:
            flash('Database connection unavailable. Please try again later.', 'error')
            return redirect(url_for('signup'))
            
        existing_user = users_col.find_one({"$or": [{"username": username}, {"email": email}]})
        if existing_user:
            flash('Username या Email पहले से मौजूद है!', 'error')
            return redirect(url_for('signup'))

        password_hash = generate_password_hash(password)
        users_col.insert_one({
            "username": username,
            "email": email,
            "password_hash": password_hash,
            "created_at": datetime.utcnow()
        })
        flash('रजिस्ट्रेशन सफल रहा! कृपया लॉगिन करें।', 'success')
        return redirect(url_for('login'))

    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if not check_db_connection():
            flash('Database connection unavailable. Please try again later.', 'error')
            return redirect(url_for('login'))
            
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        
        users_col = get_users_col()
        if users_col is None:
            flash('Database connection unavailable. Please try again later.', 'error')
            return redirect(url_for('login'))
            
        user = users_col.find_one({"username": username})
        if user and check_password_hash(user['password_hash'], password):
            login_user(User(user['_id'], user['username'], user['email']))
            flash('लॉगिन सफल!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('गलत Username या Password!', 'error')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('आप सफलतापूर्वक लॉगआउट हो गए हैं!', 'success')
    return redirect(url_for('index'))

# ========================================================
# 🌍 ROUTES
# ========================================================

@app.route('/')
def index():
    return render_template('index.html', current_user=current_user)

@app.route('/tips')
@login_required
def tips():
    return render_template('tips.html')

@app.route('/dashboard')
@login_required
def dashboard():
    if not check_db_connection():
        flash('Database connection unavailable. Please try again later.', 'error')
        return render_template('dashboard.html', evaluations=[])
        
    evaluations_col = get_evaluations_col()
    if evaluations_col is None:
        flash('Database connection unavailable. Please try again later.', 'error')
        return render_template('dashboard.html', evaluations=[])
        
    evaluations = list(evaluations_col.find({"user_id": current_user.id}).sort("created_at", -1))
    # Convert MongoDB _id to id for templates
    for eval in evaluations:
        eval['id'] = str(eval['_id'])
    return render_template('dashboard.html', evaluations=evaluations)

# ========================================================
# 📥 UPLOAD & EVALUATE
# ========================================================

@app.route('/upload', methods=['GET', 'POST'])
@login_required
def upload():
    if request.method == 'POST':
        file = request.files.get('resume')
        job_description = request.form.get('job_description', '').strip()
        if not file or not file.filename:
            flash('कृपया फ़ाइल चुनें!', 'error')
            return redirect(url_for('upload'))

        if allowed_file(file.filename):
            filename = secure_filename(file.filename)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{current_user.id}_{timestamp}_{filename}"
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)

            evaluation_result = ai_evaluate_resume(file_path, job_description)
            
            # Handle case where evaluation fails
            if not evaluation_result:
                flash('Resume evaluation failed. Please check the file format.', 'error')
                return redirect(url_for('upload'))

            if not check_db_connection():
                flash('Database connection unavailable. Please try again later.', 'error')
                return redirect(url_for('upload'))
                
            evaluations_col = get_evaluations_col()
            if evaluations_col is None:
                flash('Database connection unavailable. Please try again later.', 'error')
                return redirect(url_for('upload'))

            evaluation_doc = {
                "user_id": current_user.id,
                "filename": filename,
                "file_path": file_path,
                **evaluation_result,
                "job_description": job_description,
                "created_at": datetime.utcnow()
            }

            result = evaluations_col.insert_one(evaluation_doc)
            flash('Resume सफलतापूर्वक विश्लेषित हुआ!', 'success')
            return redirect(url_for('result', eval_id=result.inserted_id))
        else:
            flash('केवल PDF या DOCX फ़ाइलें अनुमति हैं।', 'error')

    return render_template('upload.html')

@app.route('/result/<eval_id>')
@login_required
def result(eval_id):
    if not check_db_connection():
        flash('Database connection unavailable. Please try again later.', 'error')
        return redirect(url_for('dashboard'))
        
    evaluations_col = get_evaluations_col()
    if evaluations_col is None:
        flash('Database connection unavailable. Please try again later.', 'error')
        return redirect(url_for('dashboard'))
        
    try:
        eval_obj = evaluations_col.find_one({"_id": ObjectId(eval_id), "user_id": current_user.id})
    except:
        flash('Evaluation ID invalid!', 'error')
        return redirect(url_for('dashboard'))

    if not eval_obj:
        flash('Evaluation नहीं मिली!', 'error')
        return redirect(url_for('dashboard'))

    suggested_roles = eval_obj.get('suggested_roles', [])
    chart_data = {
        'ats': eval_obj.get('ats_score', 0),
        'keywords': eval_obj.get('keyword_score', 0),
        'grammar': eval_obj.get('grammar_score', 0),
        'structure': eval_obj.get('structure_score', 0),
        'skills': eval_obj.get('skills_score', 0)
    }

    feedback = eval_obj.get('detailed_feedback') or ''
    suggestions = [line.strip() for line in feedback.splitlines() if line.strip()][:6] or [
        "Use clear achievements with metrics.",
        "Include relevant keywords from job description.",
        "Ensure contact info is visible at top."
    ]

    # Convert MongoDB _id to id for templates
    eval_obj['id'] = str(eval_obj['_id'])

    return render_template('result.html', evaluation=eval_obj,
                           suggested_roles=suggested_roles,
                           suggestions=suggestions,
                           chart_data=chart_data)

# ========================================================
# 🔹 DOWNLOAD / PDF
# ========================================================

@app.route('/download/<eval_id>')
@login_required
def download_report(eval_id):
    if not check_db_connection():
        flash('Database connection unavailable. Please try again later.', 'error')
        return redirect(url_for('dashboard'))
        
    evaluations_col = get_evaluations_col()
    if evaluations_col is None:
        flash('Database connection unavailable. Please try again later.', 'error')
        return redirect(url_for('dashboard'))
        
    try:
        eval_obj = evaluations_col.find_one({"_id": ObjectId(eval_id), "user_id": current_user.id})
    except:
        eval_obj = None

    if not eval_obj:
        flash('Report नहीं मिली!', 'error')
        return redirect(url_for('dashboard'))

    file_path = eval_obj.get('file_path')
    if not file_path or not os.path.exists(file_path):
        flash('Original file not found.', 'error')
        return redirect(url_for('dashboard'))

    return send_file(file_path, as_attachment=True)

def _create_pdf_from_evaluation(evaluation_row):
    if not REPORTLAB_AVAILABLE:
        raise RuntimeError("ReportLab not installed")
    eval_dict = dict(evaluation_row)
    eval_id = str(eval_dict.get('_id', 'unknown'))
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_filename = f"evaluation_{eval_id}_{timestamp}.pdf"
    out_path = os.path.join(app.config['GENERATED_FOLDER'], out_filename)
    c = canvas.Canvas(out_path, pagesize=letter)
    width, height = letter
    margin = 0.6 * inch
    x = margin
    y = height - margin
    c.setFont("Helvetica-Bold", 16)
    c.drawString(x, y, "Resume Evaluation Report")
    c.save()
    return out_path

@app.route('/download_report_pdf/<eval_id>')
@login_required
def download_report_pdf(eval_id):
    if not check_db_connection():
        flash('Database connection unavailable. Please try again later.', 'error')
        return redirect(url_for('dashboard'))
        
    evaluations_col = get_evaluations_col()
    if evaluations_col is None:
        flash('Database connection unavailable. Please try again later.', 'error')
        return redirect(url_for('dashboard'))
        
    try:
        eval_obj = evaluations_col.find_one({"_id": ObjectId(eval_id), "user_id": current_user.id})
    except:
        eval_obj = None

    if not eval_obj:
        flash('Evaluation नहीं मिली!', 'error')
        return redirect(url_for('dashboard'))

    try:
        pdf_path = _create_pdf_from_evaluation(eval_obj)
    except Exception as e:
        flash('PDF जनरेट करने में समस्या हुई।', 'error')
        return redirect(url_for('result', eval_id=eval_id))

    return send_file(pdf_path, as_attachment=True)

# ========================================================
# 🔹 MISSING ROUTES - PLACEHOLDERS
# ========================================================

@app.route('/generate_resume', methods=['GET', 'POST'])
@login_required
def generate_resume():
    """Generate new resume route"""
    if request.method == 'POST':
        flash('Resume generation feature coming soon!', 'info')
        return redirect(url_for('dashboard'))
    return render_template('generate.html')

@app.route('/score_history')
@login_required
def score_history():
    """Score history route"""
    if not check_db_connection():
        flash('Database connection unavailable. Please try again later.', 'error')
        return render_template('history.html', evaluations=[])
        
    evaluations_col = get_evaluations_col()
    if evaluations_col is None:
        flash('Database connection unavailable. Please try again later.', 'error')
        return render_template('history.html', evaluations=[])
        
    evaluations = list(evaluations_col.find({"user_id": current_user.id}).sort("created_at", -1))
    # Convert MongoDB _id to id for templates
    for eval in evaluations:
        eval['id'] = str(eval['_id'])
    return render_template('history.html', evaluations=evaluations)

@app.route('/skill_gap', methods=['GET', 'POST'])
@login_required
def skill_gap():
    """Skill gap analyzer route"""
    if request.method == 'POST':
        flash('Skill gap analysis feature coming soon!', 'info')
        return redirect(url_for('dashboard'))
    return render_template('skill_gap.html')

@app.route('/batch_upload', methods=['GET', 'POST'])
@login_required
def batch_upload():
    """Batch upload route"""
    if request.method == 'POST':
        flash('Batch upload feature coming soon!', 'info')
        return redirect(url_for('dashboard'))
    return render_template('batch_upload.html')

@app.route('/compare_resumes', methods=['GET', 'POST'])
@login_required
def compare_resumes():
    """Compare resumes route"""
    if request.method == 'POST':
        flash('Resume comparison feature coming soon!', 'info')
        return redirect(url_for('dashboard'))
    return render_template('compare.html')

@app.route('/delete_evaluation/<eval_id>', methods=['POST'])
@login_required
def delete_evaluation(eval_id):
    """Delete evaluation route"""
    if not check_db_connection():
        flash('Database connection unavailable. Please try again later.', 'error')
        return redirect(url_for('dashboard'))
        
    evaluations_col = get_evaluations_col()
    if evaluations_col is None:
        flash('Database connection unavailable. Please try again later.', 'error')
        return redirect(url_for('dashboard'))
        
    try:
        result = evaluations_col.delete_one({"_id": ObjectId(eval_id), "user_id": current_user.id})
        if result.deleted_count > 0:
            flash('Evaluation deleted successfully!', 'success')
        else:
            flash('Evaluation not found!', 'error')
    except Exception as e:
        flash('Error deleting evaluation!', 'error')
    
    return redirect(url_for('dashboard'))

@app.route('/share/<eval_id>')
@login_required
def share(eval_id):
    """Share evaluation route"""
    # Placeholder - returns JSON with share URL
    return jsonify({"share_url": f"{request.host_url}shared/{eval_id}"})

@app.route('/download_generated/<filename>')
@login_required
def download_generated(filename):
    """Download generated resume route"""
    file_path = os.path.join(app.config['GENERATED_FOLDER'], filename)
    if os.path.exists(file_path):
        return send_file(file_path, as_attachment=True)
    flash('File not found!', 'error')
    return redirect(url_for('dashboard'))

@app.route('/update_profile', methods=['POST'])
@login_required
def update_profile():
    """Update user profile route"""
    flash('Profile update feature coming soon!', 'info')
    return redirect(url_for('dashboard'))

@app.route('/change_password', methods=['POST'])
@login_required
def change_password():
    """Change password route"""
    flash('Password change feature coming soon!', 'info')
    return redirect(url_for('dashboard'))

@app.route('/update_preferences', methods=['POST'])
@login_required
def update_preferences():
    """Update user preferences route"""
    flash('Preferences update feature coming soon!', 'info')
    return redirect(url_for('dashboard'))

# ========================================================
# ✅ MAIN ENTRY POINT
# ========================================================

if __name__ == '__main__':
    print("Starting Flask server...")
    # Ensure database connection is ready
    if initialize_database():
        print("Database connection ready!")
    else:
        print("Starting without database connection")
    print("Server starting on http://127.0.0.1:5000")
    app.run(host='127.0.0.1', port=5000, debug=True)
