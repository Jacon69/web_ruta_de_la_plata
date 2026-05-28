import requests

BASE_URL = 'http://localhost:5000/api'

def run_tests():
    print("=== STARTING INTEGRATION TESTS ===")
    
    # Create a session to keep cookies
    session = requests.Session()
    
    # 1. Login as Profesor
    print("\n1. Logging in as 'profesor'...")
    res = session.post(f"{BASE_URL}/auth/login", json={'username': 'profesor', 'password': 'plata2026'})
    assert res.status_code == 200, f"Login failed: {res.text}"
    user = res.json()['user']
    print(f"Logged in successfully: {user['username']} ({user['role']})")
    
    # 2. Try to fetch activity logs (should fail for Profesor)
    print("\n2. Trying to fetch system logs as 'profesor' (should be forbidden)...")
    res = session.get(f"{BASE_URL}/admin/logs")
    print(f"Response status: {res.status_code}")
    assert res.status_code == 403, "Access to logs should be forbidden for teachers"
    print("Success: Forbidden as expected!")
    
    # 3. Create news as Profesor (should succeed)
    print("\n3. Creating news as 'profesor'...")
    data = {'type': 'news', 'title': 'Noticia de Prueba Docente', 'body': 'Cuerpo de la noticia de prueba.'}
    res = session.post(f"{BASE_URL}/admin/contents", data=data)
    assert res.status_code == 200, f"News creation failed: {res.text}"
    print(f"Success: {res.json()['success']}")
    
    # 4. Try to create document as Profesor (should fail)
    print("\n4. Trying to create document as 'profesor' (should be forbidden)...")
    data = {'type': 'document', 'title': 'Documento No Autorizado', 'body': 'Doc.'}
    res = session.post(f"{BASE_URL}/admin/contents", data=data)
    print(f"Response status: {res.status_code}")
    assert res.status_code == 403, "Creating documents should be forbidden for teachers"
    print("Success: Forbidden as expected!")
    
    # Logout Profesor
    session.post(f"{BASE_URL}/auth/logout")
    
    # 5. Login as Dirección
    print("\n5. Logging in as 'director'...")
    session = requests.Session()
    res = session.post(f"{BASE_URL}/auth/login", json={'username': 'director', 'password': 'plata2026'})
    assert res.status_code == 200, f"Login failed: {res.text}"
    user = res.json()['user']
    print(f"Logged in: {user['username']} ({user['role']})")
    
    # 6. Fetch activity logs (should succeed for Dirección)
    print("\n6. Fetching system logs as 'director'...")
    res = session.get(f"{BASE_URL}/admin/logs")
    assert res.status_code == 200, f"Fetch logs failed: {res.text}"
    logs = res.json()
    print(f"Fetched {len(logs)} logs successfully!")
    print("Last 3 logs in system:")
    for log in logs[:3]:
        print(f" - {log['timestamp']} | {log['username']} | {log['action']} | {log['details']}")
        
    print("\n=== ALL TESTS PASSED SUCCESSFULLY ===")

if __name__ == '__main__':
    run_tests()
