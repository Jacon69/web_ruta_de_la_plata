import os
import sqlite3
from flask import Flask, request, jsonify, session, send_from_directory, redirect
from werkzeug.utils import secure_filename
from backend.database import get_db_connection
from backend.auth import authenticate_user, login_required, require_roles
from backend.logs import log_action

app = Flask(__name__, static_folder='../frontend', static_url_path='')
app.secret_key = 'ruta_de_la_plata_secret_key_2026_secure'

UPLOAD_FOLDER = os.path.abspath(os.path.join(os.path.dirname(__file__), 'uploads'))
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB limit

ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Ensure database table for contacts exists
def init_app_tables():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS contact_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            phone TEXT,
            message TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

# ----------------- STATIC ROUTING -----------------

@app.route('/')
def serve_index():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/admin')
def admin_redirect():
    return redirect('/admin.html')

# Expose uploaded files to the web
@app.route('/api/uploads/<path:filename>')
def serve_upload(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# ----------------- PUBLIC API ENDPOINTS -----------------

@app.route('/api/news', methods=['GET'])
def get_public_news():
    """Fetch the latest 3 news stories for the home screen."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT c.id, c.title, c.body, c.created_at, u.username as author 
        FROM contents c
        JOIN users u ON c.author_id = u.id
        WHERE c.type = 'news'
        ORDER BY c.created_at DESC
        LIMIT 3
    ''')
    news = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return jsonify(news)

@app.route('/api/documents', methods=['GET'])
def get_public_documents():
    """Fetch all school documents."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id, title, body, file_path, created_at 
        FROM contents 
        WHERE type = 'document'
        ORDER BY created_at DESC
    ''')
    docs = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return jsonify(docs)

@app.route('/api/menu', methods=['GET'])
def get_public_menu():
    """Fetch the latest uploaded Comedor menu."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id, title, file_path, updated_at 
        FROM contents 
        WHERE type = 'menu'
        ORDER BY updated_at DESC
        LIMIT 1
    ''')
    row = cursor.fetchone()
    conn.close()
    if row:
        return jsonify(dict(row))
    return jsonify({'message': 'No menu currently uploaded'}), 404

@app.route('/api/contact', methods=['POST'])
def submit_contact_form():
    """Submits contact inquiry for new families."""
    data = request.get_json()
    if not data or not data.get('name') or not data.get('email') or not data.get('message'):
        return jsonify({'error': 'Name, email and message are required fields.'}), 400
        
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        'INSERT INTO contact_messages (name, email, phone, message) VALUES (?, ?, ?, ?)',
        (data['name'], data['email'], data.get('phone', ''), data['message'])
    )
    conn.commit()
    conn.close()
    
    return jsonify({'success': 'Form submitted successfully. The cooperative will contact you soon!'})

# ----------------- AUTHENTICATION API -----------------

@app.route('/api/auth/login', methods=['POST'])
def api_login():
    data = request.get_json()
    if not data or not data.get('username') or not data.get('password'):
        return jsonify({'error': 'Username and password required'}), 400
        
    user = authenticate_user(data['username'], data['password'])
    if user:
        session['user'] = user
        log_action(user['id'], user['username'], 'LOGIN', 'Logged into the system', request.remote_addr)
        return jsonify({'success': 'Login successful', 'user': user})
        
    return jsonify({'error': 'Invalid username or password'}), 401

@app.route('/api/auth/logout', methods=['POST'])
@login_required
def api_logout():
    user = session['user']
    log_action(user['id'], user['username'], 'LOGOUT', 'Logged out of the system', request.remote_addr)
    session.pop('user', None)
    return jsonify({'success': 'Logged out successfully'})

@app.route('/api/auth/session', methods=['GET'])
def api_session():
    if 'user' in session:
        return jsonify({'logged_in': True, 'user': session['user']})
    return jsonify({'logged_in': False})

@app.route('/api/auth/change-password', methods=['POST'])
@login_required
def api_change_password():
    """Permite a cualquier usuario logueado cambiar su propia contraseña."""
    user = session['user']
    data = request.get_json()
    
    nueva_pwd = data.get('password')
    if not nueva_pwd or len(nueva_pwd) < 4:
        return jsonify({'error': 'La contraseña introducida no es válida.'}), 400
        
    from werkzeug.security import generate_password_hash
    nuevo_hash = generate_password_hash(nueva_pwd)
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET password_hash = ? WHERE id = ?", (nuevo_hash, user['id']))
        conn.commit()
        conn.close()
        
        log_action(user['id'], user['username'], 'CHANGE_OWN_PASSWORD', 'El usuario actualizó su contraseña personal de acceso.', request.remote_addr)
        return jsonify({'success': 'Tu contraseña ha sido actualizada correctamente.'}), 200
    except Exception as e:
        return jsonify({'error': f'Error al guardar en la base de datos: {str(e)}'}), 500

# ----------------- RECOVERY & RESET API -----------------

@app.route('/api/admin/reset-password', methods=['POST'])
@login_required
@require_roles('SuperAdmin', 'Dirección')
def api_admin_reset_password():
    """Restablece la contraseña de un usuario concreto a la clave por defecto."""
    user_executing = session['user']
    data = request.get_json()
    
    if not data or not data.get('usuario_id'):
        return jsonify({'error': 'El ID del usuario es obligatorio.'}), 400
        
    usuario_id = data['usuario_id']
    from werkzeug.security import generate_password_hash
    contrasena_defecto = "rutadelaplata"
    nuevo_hash = generate_password_hash(contrasena_defecto)
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT username FROM users WHERE id = ?", (usuario_id,))
        target_user = cursor.fetchone()
        
        if not target_user:
            conn.close()
            return jsonify({'error': 'Usuario no encontrado.'}), 404
            
        username_afectado = target_user['username']
        cursor.execute("UPDATE users SET password_hash = ? WHERE id = ?", (nuevo_hash, usuario_id))
        conn.commit()
        conn.close()
        
        log_action(
            user_executing['id'], 
            user_executing['username'], 
            'RESET_PASSWORD', 
            f"Restableció la contraseña del usuario {username_afectado} (ID: {usuario_id}) a la de por defecto.", 
            request.remote_addr
        )
        return jsonify({'success': f'Contraseña de {username_afectado} restablecida correctamente a "{contrasena_defecto}".'}), 200
    except Exception as e:
        return jsonify({'error': f'Error interno en la base de datos: {str(e)}'}), 500

# ----------------- BACKOFFICE ADMIN API -----------------

@app.route('/api/admin/logs', methods=['GET'])
@require_roles('SuperAdmin', 'Dirección')
def api_admin_logs():
    """Fetch immutable logs. Only accessible by SuperAdmin and Dirección."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT id, username, action, details, ip_address, timestamp FROM modification_logs ORDER BY timestamp DESC')
    logs = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return jsonify(logs)

@app.route('/api/admin/contacts', methods=['GET'])
@require_roles('SuperAdmin', 'Dirección', 'Administrativo')
def api_admin_contacts():
    """Fetch contact submissions. Accessible to Admin staff."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT id, name, email, phone, message, created_at FROM contact_messages ORDER BY created_at DESC')
    msgs = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return jsonify(msgs)

@app.route('/api/admin/contents', methods=['GET'])
@login_required
def api_admin_contents():
    """Get all content entries (news, menu, documents) for the CRUD panel."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT c.id, c.type, c.title, c.body, c.file_path, c.created_at, c.updated_at, u.username as author 
        FROM contents c
        JOIN users u ON c.author_id = u.id
        ORDER BY c.updated_at DESC
    ''')
    contents = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return jsonify(contents)

@app.route('/api/admin/contents', methods=['POST'])
@require_roles('SuperAdmin', 'Dirección', 'Administrativo', 'Profesor')
def api_admin_create_content():
    """Creates a news item, document, or uploads a new menu."""
    user = session['user']
    c_type = request.form.get('type')
    title = request.form.get('title')
    body = request.form.get('body', '')
    
    if user['role'] == 'Profesor' and c_type != 'news':
        return jsonify({'error': 'Unauthorized. Teachers can only create news articles.'}), 403
        
    if not c_type or not title:
        return jsonify({'error': 'Type and Title are required.'}), 400
        
    file_path = None
    if 'file' in request.files:
        file = request.files['file']
        if file and file.filename != '' and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
            import time
            unique_filename = f"{int(time.time())}_{filename}"
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], unique_filename))
            file_path = unique_filename
            
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if c_type == 'menu':
        cursor.execute("SELECT id, file_path FROM contents WHERE type = 'menu'")
        existing_menu = cursor.fetchone()
        if existing_menu:
            cursor.execute(
                "UPDATE contents SET title = ?, file_path = COALESCE(?, file_path), author_id = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (title, file_path, user['id'], existing_menu['id'])
            )
            content_id = existing_menu['id']
            log_action(user['id'], user['username'], 'UPDATE_MENU', f"Updated Comedor menu: {title} (File: {file_path or 'no change'})", request.remote_addr)
        else:
            cursor.execute(
                "INSERT INTO contents (type, title, body, file_path, author_id) VALUES (?, ?, ?, ?, ?)",
                (c_type, title, body, file_path, user['id'])
            )
            content_id = cursor.lastrowid
            log_action(user['id'], user['username'], 'CREATE_MENU', f"Uploaded first Comedor menu: {title} (File: {file_path})", request.remote_addr)
    else:
        cursor.execute(
            "INSERT INTO contents (type, title, body, file_path, author_id) VALUES (?, ?, ?, ?, ?)",
            (c_type, title, body, file_path, user['id'])
        )
        content_id = cursor.lastrowid
        log_action(user['id'], user['username'], f'CREATE_{c_type.upper()}', f"Created {c_type}: '{title}' (File: {file_path})", request.remote_addr)
        
    conn.commit()
    conn.close()
    return jsonify({'success': 'Content created successfully', 'content_id': content_id})

@app.route('/api/admin/contents/<int:content_id>', methods=['PUT'])
@require_roles('SuperAdmin', 'Dirección', 'Administrativo', 'Profesor')
def api_admin_update_content(content_id):
    """Updates a content item."""
    user = session['user']
    c_type = request.form.get('type')
    title = request.form.get('title')
    body = request.form.get('body', '')
    
    if user['role'] == 'Profesor' and c_type != 'news':
        return jsonify({'error': 'Unauthorized. Teachers can only edit news articles.'}), 403
        
    if not title:
        return jsonify({'error': 'Title is required.'}), 400
        
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, type, file_path FROM contents WHERE id = ?", (content_id,))
    content_item = cursor.fetchone()
    if not content_item:
        conn.close()
        return jsonify({'error': 'Content not found.'}), 404
        
    db_type = content_item['type']
    if user['role'] == 'Profesor' and db_type != 'news':
        conn.close()
        return jsonify({'error': 'Unauthorized. Teachers can only edit news articles.'}), 403
        
    file_path = content_item['file_path']
    if 'file' in request.files:
        file = request.files['file']
        if file and file.filename != '' and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            import time
            unique_filename = f"{int(time.time())}_{filename}"
            os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], unique_filename))
            file_path = unique_filename
            
    cursor.execute(
        "UPDATE contents SET title = ?, body = ?, file_path = ?, author_id = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
        (title, body, file_path, user['id'], content_id)
    )
    conn.commit()
    conn.close()
    
    log_action(user['id'], user['username'], f'UPDATE_{db_type.upper()}', f"Updated {db_type} ID {content_id}: '{title}'", request.remote_addr)
    return jsonify({'success': 'Content updated successfully'})

@app.route('/api/admin/contents/<int:content_id>', methods=['DELETE'])
@require_roles('SuperAdmin', 'Dirección', 'Administrativo')
def api_admin_delete_content(content_id):
    """Deletes content. Teachers cannot delete content."""
    user = session['user']
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, type, title FROM contents WHERE id = ?", (content_id,))
    content_item = cursor.fetchone()
    if not content_item:
        conn.close()
        return jsonify({'error': 'Content not found.'}), 404
        
    db_type = content_item['type']
    title = content_item['title']
    cursor.execute("DELETE FROM contents WHERE id = ?", (content_id,))
    conn.commit()
    conn.close()
    
    log_action(user['id'], user['username'], f'DELETE_{db_type.upper()}', f"Deleted {db_type} ID {content_id}: '{title}'", request.remote_addr)
    return jsonify({'success': 'Content deleted successfully'})

# ----------------- MAIN APP START -----------------

init_app_tables()

    app.run(host='0.0.0.0', port=5000, debug=True)
