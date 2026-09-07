import sys
import os
from pathlib import Path
import time

sys.path.append('.')

from fastapi.testclient import TestClient
from app.main import app, on_startup
from app.db.database import Base, engine, SessionLocal
from app.db.models import Job, Project

def test_flow():
    # Trigger startup
    on_startup()
    
    client = TestClient(app)
    
    print("1. Creating Project...")
    res = client.post("/projects", json={"name": "Test Project 1", "description": "Persistent DB Test"})
    assert res.status_code == 200, res.text
    proj_id = res.json()["id"]
    print(f"Project created: {proj_id}")
    
    print("2. Uploading Video...")
    test_video = Path("data/samples/drone_flight_01.mp4")
    if not test_video.exists():
        print(f"Skipping video upload, file not found: {test_video}")
        return
        
    with open(test_video, "rb") as f:
        res = client.post("/upload", files={"file": ("video.mp4", f, "video/mp4")}, data={"project_id": proj_id})
    assert res.status_code == 200, res.text
    job_id = res.json()["job_id"]
    print(f"Job created: {job_id}")
    
    print("3. Starting Job...")
    res = client.post(f"/start/{job_id}")
    assert res.status_code == 200, res.text
    
    print("4. Verifying DB persistence...")
    res = client.get(f"/status/{job_id}")
    assert res.status_code == 200, res.text
    status = res.json()["status"]
    print(f"API Job status: {status}")
    
    db = SessionLocal()
    job = db.query(Job).filter(Job.job_id == job_id).first()
    assert job is not None
    assert job.project_id == proj_id
    
    # Test restart behavior (orphan job cleanup)
    print("5. Testing Restart Behavior...")
    # Manually make a fake running job
    fake_job_id = "orphan12"
    fake_job = Job(job_id=fake_job_id, status="RUNNING", progress="Stuck")
    db.add(fake_job)
    db.commit()
    db.close()
    
    # Re-run startup
    on_startup()
    
    db = SessionLocal()
    orphaned = db.query(Job).filter(Job.job_id == fake_job_id).first()
    assert orphaned.status == "FAILED"
    assert orphaned.error == "Backend stopped unexpectedly before completion."
    db.close()
    
    print("Restart cleanup successful!")

if __name__ == "__main__":
    test_flow()
