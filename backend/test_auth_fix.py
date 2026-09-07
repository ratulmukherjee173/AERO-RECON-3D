import json
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

def run_tests():
    # We will test against the existing account "test_user_9e4657@example.com"
    email_correct = "test_user_9e4657@example.com"
    email_caps = "Test_User_9e4657@Example.COM"
    email_whitespace = "  test_user_9e4657@example.com  "
    password = "secure_password_123"
    wrong_password = "wrong_password_123"

    print("--- 1. Existing account login with correct password ---")
    status, data = make_request("/auth/login", method="POST", data={"email": email_correct, "password": password})
    assert status == 200, f"Expected 200, got {status}"
    
    print("--- 2. Same existing email with different capitalization ---")
    status, data = make_request("/auth/login", method="POST", data={"email": email_caps, "password": password})
    assert status == 200, f"Expected 200, got {status}"

    print("--- 3. Email with surrounding whitespace ---")
    status, data = make_request("/auth/login", method="POST", data={"email": email_whitespace, "password": password})
    assert status == 200, f"Expected 200, got {status}"
    token = data["access_token"]

    print("--- 4. Wrong password ---")
    status, data = make_request("/auth/login", method="POST", data={"email": email_correct, "password": wrong_password})
    assert status == 401, f"Expected 401, got {status}"

    print("--- 5. Duplicate normalized email registration ---")
    status, data = make_request("/auth/register", method="POST", data={"email": email_caps, "password": password})
    assert status == 409, f"Expected 409, got {status}"

    print("--- 6. /auth/me with returned JWT ---")
    headers = {"Authorization": f"Bearer {token}"}
    status, data = make_request("/auth/me", method="GET", headers=headers)
    assert status == 200, f"Expected 200, got {status}"
    assert data["email"] == email_correct, f"Expected {email_correct}, got {data.get('email')}"

    print("ALL FIX TESTS PASSED!")

if __name__ == "__main__":
    run_tests()
