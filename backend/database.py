import sqlite3
import os
from werkzeug.security import generate_password_hash

DB_PATH = os.path.join(os.path.dirname(__file__), 'db', 'school.db')

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    # Ensure the db directory exists
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 1. Users Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT CHECK(role IN ('SuperAdmin', 'Dirección', 'Administrativo', 'Profesor')) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 2. Contents Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS contents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            type TEXT CHECK(type IN ('news', 'menu', 'document')) NOT NULL,
            title TEXT NOT NULL,
            body TEXT,
            file_path TEXT,
            author_id INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(author_id) REFERENCES users(id)
        )
    ''')
    
    # 3. Immutable logs table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS modification_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            username TEXT NOT NULL,
            action TEXT NOT NULL,
            details TEXT NOT NULL,
            ip_address TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()

def seed_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Seed default users
    default_users = [
        ('admin', 'plata2026', 'SuperAdmin'),
        ('director', 'plata2026', 'Dirección'),
        ('staff', 'plata2026', 'Administrativo'),
        ('profesor', 'plata2026', 'Profesor')
    ]
    
    for username, password, role in default_users:
        cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
        if not cursor.fetchone():
            p_hash = generate_password_hash(password)
            cursor.execute(
                "INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)",
                (username, p_hash, role)
            )
            print(f"Seeded user: {username} ({role})")
            
    conn.commit()
    
    # Get admin ID for content authoring
    cursor.execute("SELECT id FROM users WHERE username = 'admin'")
    admin_id = cursor.fetchone()[0]
    
    # Seed 3 sample news for the homepage
    sample_news = [
        (
            'news', 
            'Comienzo del Curso Escolar 2024/2025', 
            'El Colegio Ruta de la Plata da la bienvenida a todo el alumnado de Educación Infantil y Primaria. Afrontamos este nuevo año académico con el compromiso cooperativo que nos caracteriza, potenciando la convivencia y el aprendizaje competencial de nuestros niños.', 
            None, 
            admin_id
        ),
        (
            'news', 
            'Proyecto Vía Verde Sevilla-Mina de Cala', 
            'Nuestros alumnos de Educación Primaria han iniciado un proyecto de investigación y difusión sobre la Vía Verde. Esta actividad tiene como objetivo poner en valor el antiguo trazado ferroviario y el patrimonio minero de nuestra comarca, colaborando con los organismos locales.', 
            None, 
            admin_id
        ),
        (
            'news', 
            'Talleres de Aprendizaje Dialógico y Mediación', 
            'En el marco de nuestro Plan de Convivencia, el profesorado y el alumnado participan en talleres semanales para potenciar el diálogo y la resolución pacífica de conflictos. La mediación escolar sigue siendo nuestro pilar fundamental para garantizar un ambiente seguro y lúdico.', 
            None, 
            admin_id
        )
    ]
    
    for c_type, title, body, file_path, author_id in sample_news:
        cursor.execute("SELECT id FROM contents WHERE title = ?", (title,))
        if not cursor.fetchone():
            cursor.execute(
                "INSERT INTO contents (type, title, body, file_path, author_id) VALUES (?, ?, ?, ?, ?)",
                (c_type, title, body, file_path, author_id)
            )
            print(f"Seeded content: {title}")
            
    # Seed default document (Plan Convivencia) if not present
    cursor.execute("SELECT id FROM contents WHERE type = 'document'")
    if not cursor.fetchone():
        cursor.execute(
            "INSERT INTO contents (type, title, body, file_path, author_id) VALUES (?, ?, ?, ?, ?)",
            (
                'document',
                'Plan de Convivencia: Normas y Sanciones',
                'Documento oficial que regula las normas de convivencia, conductas perjudiciales, mediación y el catálogo de sanciones del centro.',
                'PlanConviven_NORMASySANCIONES.pdf',
                admin_id
            )
        )
        print("Seeded default document: Plan de Convivencia")
        
    conn.commit()
    conn.close()

if __name__ == '__main__':
    init_db()
    seed_db()
    print("Database initialization and seeding completed successfully.")
