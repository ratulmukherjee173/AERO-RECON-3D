import urllib.request
import urllib.error
import urllib.parse
import json
import uuid

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

def run_tests():
    # 1. Registration
    print("Testing Registration...")
    email = f"test_{uuid.uuid4().hex[:6]}@example.com"
    password = "secure_password_123"
    
    status, data = make_request("/auth/register", method="POST", data={"email": email, "password": password})
    assert status == 201, f"Expected 201, got {status}"
    assert "access_token" in data
    assert data["user"]["email"] == email
    token = data["access_token"]
    
    # 2. Duplicate Registration
    print("Testing Duplicate Registration...")
    status, data = make_request("/auth/register", method="POST", data={"email": email, "password": password})
    assert status == 409, f"Expected 409, got {status}"
    
    # 3. Successful Login
    print("Testing Successful Login...")
    status, data = make_request("/auth/login", method="POST", data={"email": email, "password": password})
    assert status == 200, f"Expected 200, got {status}"
    assert "access_token" in data
    
    # 4. Wrong Password
    print("Testing Wrong Password...")
    status, data = make_request("/auth/login", method="POST", data={"email": email, "password": "wrong_password"})
    assert status == 401, f"Expected 401, got {status}"
    
    # 5. /auth/me with valid token
    print("Testing /auth/me with valid token...")
    headers = {"Authorization": f"Bearer {token}"}
    status, data = make_request("/auth/me", method="GET", headers=headers)
    assert status == 200, f"Expected 200, got {status}"
    assert data["email"] == email
    
    # 6. /auth/me with invalid token
    print("Testing /auth/me with invalid token...")
    headers = {"Authorization": f"Bearer invalid_token"}
    status, data = make_request("/auth/me", method="GET", headers=headers)
    assert status == 401, f"Expected 401, got {status}"
    
    print("All Auth tests passed!")

if __name__ == "__main__":
    run_tests()
