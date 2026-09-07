import json
import uuid
import urllib.request
import urllib.error

url = "http://127.0.0.1:8000"

def make_request(path, method="GET", data=None, headers=None):
    if headers is None:
        headers = {}
    if data:
        data = json.dumps(data).encode("utf-8")
        headers["Content-Type"] = "application/json"
    
    req = urllib.request.Request(f"{url}{path}", data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as response:
            return response.status, json.loads(response.read().decode())
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        try:
            body = json.loads(body)
        except:
            pass
        return e.code, body

def run_debug():
    print("--- 1. Testing Registration with Mixed Case Email ---")
    test_id = uuid.uuid4().hex[:6]
    email = f"  Test_User_{test_id}@Example.COM  "
    password = "secure_password_123"
    
    status, data = make_request("/auth/register", method="POST", data={"email": email, "password": password})
    print(f"Register status: {status}")
    print(f"Register response: {data}")
    
    if status == 201:
        print("\n--- 2. Testing Login with Lowercase Email ---")
        login_email = f"test_user_{test_id}@example.com"
        status2, data2 = make_request("/auth/login", method="POST", data={"email": login_email, "password": password})
        print(f"Login status: {status2}")
        print(f"Login response: {data2}")
        
if __name__ == "__main__":
    run_debug()
