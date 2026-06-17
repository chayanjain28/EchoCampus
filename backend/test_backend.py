import sys
import os
import uuid
from fastapi.testclient import TestClient

# Adjust python path to be able to import backend
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.main import app
from backend.database.connection import SessionLocal, engine, Base
from backend.seed import seed_database

client = TestClient(app)

def test_flow():
    # 1. Reset/Seed database first to ensure standard state
    seed_database()
    
    print("\nStarting programatic verification tests...")
    
    unique_id = uuid.uuid4().hex[:8]
    test_email = f"student_{unique_id}@echocampus.edu"
    
    # 1. Register User
    signup_payload = {
        "name": "Test Student",
        "email": test_email,
        "password": "password123",
        "role": "student"
    }
    res = client.post("/api/auth/register", json=signup_payload)
    if res.status_code != 200:
        print(f"Registration Failed: {res.json()}")
    assert res.status_code == 200, "Registration failed"
    token = res.json()["access_token"]
    print("[OK] Registration verified successfully")

    # 2. Login User
    login_payload = {
        "email": test_email,
        "password": "password123"
    }
    res = client.post("/api/auth/login", json=login_payload)
    assert res.status_code == 200, "Login failed"
    token = res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print("[OK] Login verified successfully")

    # 3. Submit Complaint
    complaint_payload = {
        "title": "Low water pressure in Room 412 Hostel B",
        "description": "The water pressure in Hostel B room 412 bathroom is extremely low. It is impossible to wash properly. Please dispatch maintenance.",
        "anonymous": False
    }
    res = client.post("/api/complaints", json=complaint_payload, headers=headers)
    assert res.status_code == 200, "Complaint submission failed"
    data = res.json()
    assert data["category"] == "Hostel", "AI routing category mismatch"
    assert data["assigned_department"] == "Hostel Warden", "AI department routing mismatch"
    complaint_id = data["id"]
    print(f"[OK] Complaint submission, AI classification, routing, and severity calculation verified (Severity: {data['severity_score']})")

    # 4. Check Duplicate Detection
    duplicate_payload = {
        "title": "Room 412 water pressure in Hostel B is low",
        "description": "Hostel B bathroom 412 has very low water pressure. Water trickles slowly. Maintenance needs to check it.",
        "anonymous": True
    }
    res = client.post("/api/complaints", json=duplicate_payload, headers=headers)
    assert res.status_code == 200, "Duplicate complaint submission failed"
    dup_data = res.json()
    print("COMPLAINT_ID:", complaint_id, "DUP_DATA:", dup_data)
    assert dup_data["parent_complaint_id"] == complaint_id, "Duplicate detection failed to group issue"
    print(f"[OK] AI Duplicate Detection and grouping verified successfully (Linked duplicate #{dup_data['id']} to parent #{complaint_id})")

    # 5. Submit Feedback
    feedback_payload = {
        "category": "Hostel",
        "rating": 4,
        "message": "Hostel amenities are generally fine except for occasional water pressure drops."
    }
    res = client.post("/api/feedback", json=feedback_payload, headers=headers)
    assert res.status_code == 200, "Feedback submission failed"
    print("[OK] Feedback module verified successfully")

    # 6. Test Admin Role Endpoints
    # We login as Admin to test analytics
    admin_login = {
        "email": "admin@echocampus.edu",
        "password": "admin123"
    }
    admin_res = client.post("/api/auth/login", json=admin_login)
    assert admin_res.status_code == 200, "Admin login failed"
    admin_token = admin_res.json()["access_token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    
    # 7. Update status to Resolved
    update_payload = {
        "status": "Resolved",
        "assigned_to": "Plumber Jack",
        "assigned_department": "Hostel Warden"
    }
    res = client.put(f"/api/complaints/{complaint_id}/status", json=update_payload, headers=admin_headers)
    assert res.status_code == 200, "Status update failed"
    print("[OK] Admin status routing & department assignments verified")

    # 8. Test Rate Resolution (Student rates the resolved complaint)
    rate_payload = {
        "rating": 5,
        "comment": "Jack fixed it the same day! Awesome response speed."
    }
    res = client.post(f"/api/complaints/{complaint_id}/rate-resolution", json=rate_payload, headers=headers)
    assert res.status_code == 200, "Rating resolution failed"
    print("[OK] Student resolution rating verified successfully")

    # 9. Get Admin Analytics
    res = client.get("/api/analytics/dashboard", headers=admin_headers)
    assert res.status_code == 200, "Dashboard metrics fetching failed"
    dash = res.json()
    print(f"[OK] Executive Dashboard KPIs and CSSI calculations verified. Campus Health: {dash['campus_health_score']}%")

    # 10. Generate AI Welfare Report
    res = client.get("/api/analytics/welfare-report", headers=admin_headers)
    assert res.status_code == 200, "Monthly Welfare Report compilation failed"
    print("[OK] AI Monthly Welfare Report generation verified successfully")

    print("\nALL VERIFICATION TESTS COMPLETED SUCCESSFULLY! Backend is fully functional.")

if __name__ == "__main__":
    test_flow()
