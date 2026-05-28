from backend.database import get_db_connection

def log_action(user_id, username, action, details, ip_address=None):
    """
    Logs an admin action in the modification_logs table.
    This database table is write-only/immutable from the application's perspective (no delete/update routes).
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            INSERT INTO modification_logs (user_id, username, action, details, ip_address)
            VALUES (?, ?, ?, ?, ?)
            """,
            (user_id, username, action, details, ip_address)
        )
        conn.commit()
    except Exception as e:
        print(f"Error logging action: {e}")
    finally:
        conn.close()
