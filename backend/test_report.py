import urllib.request
import urllib.parse
import json

url = "http://127.0.0.1:8000"

def run_tests():
    # 1. Get a job that exists
    req = urllib.request.Request(f"{url}/jobs")
    with urllib.request.urlopen(req) as response:
        jobs = json.loads(response.read().decode())
        
    if not jobs:
        print("No jobs in database to test with.")
        return
        
    success_jobs = [j for j in jobs if j.get('status') == 'SUCCESS']
    if not success_jobs:
        print("No SUCCESS jobs found.")
        return
        
    job_id = success_jobs[0]['job_id']
    
    # 2. Test PDF Generation
    print(f"Generating report for {job_id}...")
    req = urllib.request.Request(f"{url}/reports/{job_id}/generate", method="POST")
    try:
        with urllib.request.urlopen(req) as response:
            print(response.status, json.loads(response.read().decode()))
    except Exception as e:
        print(f"Generate failed: {e}")
        return
    
    # 3. Test Metadata Fetch
    print("Fetching report metadata...")
    req = urllib.request.Request(f"{url}/reports/{job_id}")
    with urllib.request.urlopen(req) as response:
        print(response.status, json.loads(response.read().decode()))
    
    # 4. Test Download
    print("Downloading report...")
    req = urllib.request.Request(f"{url}/reports/{job_id}/download")
    with urllib.request.urlopen(req) as response:
        content = response.read()
        print(response.status, f"Downloaded {len(content)} bytes")
        assert len(content) > 1000, "PDF seems too small"
    
    print("All backend tests passed!")

if __name__ == "__main__":
    run_tests()
