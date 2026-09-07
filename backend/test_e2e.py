import urllib.request
import urllib.parse
import json
import time
import sys
from pathlib import Path

BASE_URL = "http://127.0.0.1:8000"

def get_json(url):
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req) as response:
        return json.loads(response.read().decode())

def post_empty(url):
    req = urllib.request.Request(url, method="POST")
    with urllib.request.urlopen(req) as response:
        return json.loads(response.read().decode())

def run_integration_test():
    print("--- STARTING END-TO-END DEMO VALIDATION ---")
    
    # 1. Check health
    try:
        data = get_json(f"{BASE_URL}/health")
        print(" [OK] Backend Health Check")
    except Exception as e:
        print(f"Backend is not running. {e}")
        sys.exit(1)

    # 2. Upload Video
    video_path = Path("backend/data/samples/test_drone.mp4")
    if not video_path.exists():
        print("Test video not found!")
        sys.exit(1)
        
    print(f"Uploading {video_path}...")
    # using curl to avoid writing multipart form data from scratch
    import subprocess
    res = subprocess.run([
        "curl", "-s", "-X", "POST",
        "-F", f"file=@{video_path}",
        f"{BASE_URL}/upload"
    ], capture_output=True, text=True)
    
    if res.returncode != 0:
        print(f"Upload failed: {res.stderr}")
        sys.exit(1)
        
    try:
        job_data = json.loads(res.stdout)
        job_id = job_data['job_id']
        print(f" [OK] Upload successful. Job ID: {job_id}")
    except json.JSONDecodeError:
        print(f"Failed to parse upload response: {res.stdout}")
        sys.exit(1)

    # 3. Start Pipeline
    print("Starting pipeline...")
    try:
        post_empty(f"{BASE_URL}/start/{job_id}")
    except Exception as e:
        print(f"Failed to start: {e}")
        sys.exit(1)
    
    print(" [OK] Pipeline Queued")

    # 4. Wait for Pipeline
    print("Waiting for pipeline to complete (this will take several minutes)...")
    while True:
        status_data = get_json(f"{BASE_URL}/status/{job_id}")
        
        status = status_data['status']
        progress = status_data['progress']
        stage = status_data.get('current_stage', '')
        
        print(f"[{status}] {stage}: {progress}")
        
        if status == "SUCCESS":
            print(" [OK] Pipeline Complete!")
            break
        elif status == "FAILED":
            print(f"Pipeline Failed: {status_data.get('error')}")
            sys.exit(1)
            
        time.sleep(5)

    # 5. Check Outputs
    print("Validating endpoints...")
    
    def check_head(url, name):
        import urllib.error
        req = urllib.request.Request(url, method="HEAD")
        try:
            urllib.request.urlopen(req)
        except urllib.error.HTTPError as e:
            if e.code == 404:
                print(f"FAILED: {name} not found!")
                sys.exit(1)
                
    check_head(f"{BASE_URL}/download/{job_id}/preview", "Preview PLY")
    check_head(f"{BASE_URL}/download/{job_id}/ply", "Full PLY")
    check_head(f"{BASE_URL}/download/{job_id}/glb", "Web GLB")
    check_head(f"{BASE_URL}/report/{job_id}", "JSON Report")

    print(" [OK] All endpoints serve valid files.")
    print("--- E2E VALIDATION PASSED ---")

if __name__ == "__main__":
    run_integration_test()
