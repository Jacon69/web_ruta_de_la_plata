from functools import wraps
from flask import session, jsonify, request
from werkzeug.security import check_password_hash
from backend.database import get_db_connection

def authenticate_user(username, password):
    """
    Checks user credentials.
    Returns the user Row if successful, None otherwise.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, password_hash, role FROM users WHERE username = ?", (username,))
    user = cursor.fetchone()
    conn.close()
    
    if user and check_password_hash(user['password_hash'], password):
        return {
            'id': user['id'],
            'username': user['username'],
            'role': user['role']
        }
    return None

def login_required(f):
    """Decorator to require login for a route."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            return jsonify({'error': 'Authentication required. Please log in.'}), 401
        return f(*args, **kwargs)
    return decorated_function

def require_roles(*roles):
    """Decorator to require specific roles for a route."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user' not in session:
                return jsonify({'error': 'Authentication required. Please log in.'}), 401
            
            user_role = session['user'].get('role')
            if user_role not in roles:
                return jsonify({'error': f'Unauthorized. This action requires one of the following roles: {", ".join(roles)}.'}), 403
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator
