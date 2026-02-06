"""
Helper functions for the Resume Evaluator application
Handles evaluation sharing, export, user preferences, and score trends.
"""
import secrets
import json
from datetime import datetime, timedelta
import csv
import io

# Import database connection from the utils package
from .database import get_db_connection


def generate_share_token():
    """Generate a unique share token for sharing evaluations"""
    return secrets.token_urlsafe(32)


def create_shared_link(evaluation_id, expires_days=30):
    """
    Create a shareable link for a specific evaluation.

    Args:
        evaluation_id (int): ID of the evaluation.
        expires_days (int): Number of days before the link expires (default 30).

    Returns:
        str: Generated share token.
    """
    conn = get_db_connection()
    token = generate_share_token()
    expires_at = datetime.now() + timedelta(days=expires_days)

    conn.execute(
        '''
        INSERT INTO shared_links (evaluation_id, share_token, expires_at)
        VALUES (?, ?, ?)
        ''',
        (evaluation_id, token, expires_at)
    )
    conn.commit()
    conn.close()

    return token


def get_evaluation_by_share_token(token):
    """
    Fetch evaluation by share token and update view count.

    Args:
        token (str): The share token.

    Returns:
        sqlite3.Row or None: Evaluation data including views and expiry info.
    """
    conn = get_db_connection()

    # Increment view count
    conn.execute(
        'UPDATE shared_links SET views = views + 1 WHERE share_token = ?',
        (token,)
    )
    conn.commit()

    # Fetch evaluation details
    result = conn.execute(
        '''
        SELECT e.*, s.views, s.expires_at
        FROM evaluations e
        JOIN shared_links s ON e.id = s.evaluation_id
        WHERE s.share_token = ? AND (s.expires_at IS NULL OR s.expires_at > datetime('now'))
        ''',
        (token,)
    ).fetchone()

    conn.close()
    return result


def export_to_json(evaluation):
    """
    Export a single evaluation to JSON format.

    Args:
        evaluation (sqlite3.Row): The evaluation record.

    Returns:
        str: JSON string representation of the evaluation.
    """
    return json.dumps(
        {
            'id': evaluation['id'],
            'filename': evaluation['filename'],
            'overall_score': evaluation['overall_score'],
            'ats_score': evaluation['ats_score'],
            'keyword_score': evaluation['keyword_score'],
            'grammar_score': evaluation['grammar_score'],
            'structure_score': evaluation['structure_score'],
            'skills_score': evaluation['skills_score'],
            'jd_match_percentage': evaluation['jd_match_percentage'],
            'suggested_roles': json.loads(evaluation['suggested_roles']) if evaluation['suggested_roles'] else [],
            'detailed_feedback': evaluation['detailed_feedback'],
            'missing_keywords': evaluation.get('missing_keywords'),
            'improvement_suggestions': evaluation.get('improvement_suggestions'),
            'created_at': evaluation['created_at']
        },
        indent=2
    )


def export_to_csv(evaluations):
    """
    Export multiple evaluations to CSV format.

    Args:
        evaluations (list[sqlite3.Row]): List of evaluation records.

    Returns:
        str: CSV formatted string of evaluations.
    """
    output = io.StringIO()
    writer = csv.writer(output)

    # CSV Header
    writer.writerow([
        'Date', 'Filename', 'Overall Score', 'ATS Score', 'Keyword Score',
        'Grammar Score', 'Structure Score', 'Skills Score', 'JD Match %'
    ])

    # Write data rows
    for eval in evaluations:
        writer.writerow([
            eval['created_at'],
            eval['filename'],
            eval['overall_score'],
            eval['ats_score'],
            eval['keyword_score'],
            eval['grammar_score'],
            eval['structure_score'],
            eval['skills_score'],
            eval['jd_match_percentage']
        ])

    return output.getvalue()


def get_user_preferences(user_id):
    """
    Retrieve user preferences; create defaults if not exists.

    Args:
        user_id (int): ID of the user.

    Returns:
        sqlite3.Row: User preferences record.
    """
    conn = get_db_connection()
    prefs = conn.execute(
        'SELECT * FROM user_preferences WHERE user_id = ?',
        (user_id,)
    ).fetchone()

    if not prefs:
        # Create default preferences
        conn.execute(
            '''
            INSERT INTO user_preferences (user_id, dark_mode, email_notifications, weekly_tips)
            VALUES (?, 0, 1, 1)
            ''',
            (user_id,)
        )
        conn.commit()
        prefs = conn.execute(
            'SELECT * FROM user_preferences WHERE user_id = ?',
            (user_id,)
        ).fetchone()

    conn.close()
    return prefs


def update_user_preferences(user_id, dark_mode=None, email_notifications=None, weekly_tips=None):
    """
    Update user preferences with provided values.

    Args:
        user_id (int): ID of the user.
        dark_mode (bool | None): Enable/disable dark mode.
        email_notifications (bool | None): Enable/disable email notifications.
        weekly_tips (bool | None): Enable/disable weekly tips.
    """
    conn = get_db_connection()
    updates = []
    params = []

    if dark_mode is not None:
        updates.append('dark_mode = ?')
        params.append(1 if dark_mode else 0)
    if email_notifications is not None:
        updates.append('email_notifications = ?')
        params.append(1 if email_notifications else 0)
    if weekly_tips is not None:
        updates.append('weekly_tips = ?')
        params.append(1 if weekly_tips else 0)

    if updates:
        params.append(user_id)
        query = f"UPDATE user_preferences SET {', '.join(updates)} WHERE user_id = ?"
        conn.execute(query, params)
        conn.commit()

    conn.close()


def calculate_score_trend(evaluations):
    """
    Calculate the trend of overall scores over time.

    Args:
        evaluations (list[sqlite3.Row]): List of recent evaluation records, ordered by newest first.

    Returns:
        dict: {'trend': 'improving'|'declining'|'stable'|'neutral', 'change': float}
    """
    if not evaluations or len(evaluations) < 2:
        return {'trend': 'neutral', 'change': 0}

    # Take last 3 evaluations as recent
    recent_scores = [e['overall_score'] for e in evaluations[:3]]
    avg_recent = sum(recent_scores) / len(recent_scores)

    # Take next 3 evaluations as older
    older_scores = [e['overall_score'] for e in evaluations[3:6]] if len(evaluations) > 3 else []
    if older_scores:
        avg_older = sum(older_scores) / len(older_scores)
        change = avg_recent - avg_older

        if change > 5:
            return {'trend': 'improving', 'change': round(change, 1)}
        elif change < -5:
            return {'trend': 'declining', 'change': round(change, 1)}

    return {'trend': 'stable', 'change': round(avg_recent, 1)}
