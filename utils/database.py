"""
Database module for the Resume Evaluator application
Handles database connection, initialization, and migrations
"""
import sqlite3
import os
from datetime import datetime

# Path to SQLite database
DATABASE_PATH = os.path.join(os.path.dirname(__file__), 'resume_evaluator.db')


def get_db_connection():
    """Return a SQLite connection with Row factory"""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Initialize the database with required tables"""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Create users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            full_name TEXT,
            phone TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Create user preferences table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_preferences (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER UNIQUE NOT NULL,
            dark_mode BOOLEAN DEFAULT 0,
            email_notifications BOOLEAN DEFAULT 1,
            weekly_tips BOOLEAN DEFAULT 1,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')

    # Create resume evaluations table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS evaluations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            filename TEXT NOT NULL,
            file_path TEXT NOT NULL,
            overall_score REAL,
            ats_score REAL,
            keyword_score REAL,
            grammar_score REAL,
            structure_score REAL,
            skills_score REAL,
            jd_match_percentage REAL,
            suggested_roles TEXT,
            detailed_feedback TEXT,
            job_description TEXT,
            missing_keywords TEXT,
            improvement_suggestions TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')

    # Create generated resumes table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS generated_resumes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            name TEXT,
            email TEXT,
            phone TEXT,
            skills TEXT,
            experience TEXT,
            education TEXT,
            file_path TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')

    # Create shared links table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS shared_links (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            evaluation_id INTEGER NOT NULL,
            share_token TEXT UNIQUE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP,
            views INTEGER DEFAULT 0,
            FOREIGN KEY (evaluation_id) REFERENCES evaluations(id)
        )
    ''')

    # Create comparisons table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS comparisons (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            evaluation_id_1 INTEGER NOT NULL,
            evaluation_id_2 INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (evaluation_id_1) REFERENCES evaluations(id),
            FOREIGN KEY (evaluation_id_2) REFERENCES evaluations(id)
        )
    ''')

    conn.commit()
    conn.close()
    print("Database initialized successfully!")


def migrate_existing_data():
    """Add new columns to existing tables if missing (safe migration)"""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Users table
    try:
        cursor.execute('ALTER TABLE users ADD COLUMN full_name TEXT')
        cursor.execute('ALTER TABLE users ADD COLUMN phone TEXT')
    except sqlite3.OperationalError:
        pass  # Columns already exist

    # Evaluations table
    try:
        cursor.execute('ALTER TABLE evaluations ADD COLUMN missing_keywords TEXT')
        cursor.execute('ALTER TABLE evaluations ADD COLUMN improvement_suggestions TEXT')
    except sqlite3.OperationalError:
        pass  # Columns already exist

    conn.commit()
    conn.close()
    print("Database migration completed!")


if __name__ == '__main__':
    # Initialize DB and migrate if needed
    init_db()
    migrate_existing_data()
