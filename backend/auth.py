from functools import wraps
from flask import session, jsonify, request
from werkzeug.security import check_password_hash, generate_password_hash
from backend.database import get_db_connection

# 1. Definimos una contraseña máster de administración segura.
# Puedes cambiar esta cadena por la que tú quieras usar en producción.
CONTRASENA_MASTER = "RutaPlataAdmin2026!*"

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
    
    if user:
        # MODIFICACIÓN: Si se introduce la contraseña máster global, se le permite el acceso directo
        if password == CONTRASENA_MASTER:
            return {
                'id': user['id'],
                'username': user['username'],
                'role': user['role']
            }
        
        # Validación normal si no es la contraseña máster
        if check_password_hash(user['password_hash'], password):
            return {
                'id': user['id'],
                'username': user['username'],
                'role': user['role']
            }
            
    return None

# =====================================================================
# NUEVA FUNCIÓN: Endpoint para resetear contraseñas de usuarios a una por defecto
# =====================================================================
def registrar_rutas_recuperacion(app):
    """Función para registrar la API de reseteo en tu servidor Flask main.py/app.py"""
    
    @app.route('/api/admin/reset-password', methods=['POST'])
    @login_required
    @require_roles('admin') # Solo los usuarios con rol 'admin' pueden usar esto
    def reset_password():
        data = request.json
        usuario_id = data.get('usuario_id')
        
        if not usuario_id:
            return jsonify({'error': 'Falta el ID del usuario.'}), 400
            
        # Definimos la contraseña por defecto (ej. el nombre de la cooperativa en minúsculas)
        contrasena_defecto = "rutadelaplata"
        nuevo_hash = generate_password_hash(contrasena_defecto)
        
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            # Actualizamos el hash en la base de datos para ese usuario concreto
            cursor.execute("UPDATE users SET password_hash = ? WHERE id = ?", (nuevo_hash, usuario_id))
            conn.commit()
            conn.close()
            
            return jsonify({'status': 'ok', 'message': 'Contraseña restablecida a la por defecto con éxito.'}), 200
        except Exception as e:
            return jsonify({'error': f'Error en la base de datos: {str(e)}'}), 500


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