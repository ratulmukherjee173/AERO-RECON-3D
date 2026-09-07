import urllib.request
import urllib.parse
import json

base_url = "http://127.0.0.1:8000"

def test_get(path, token=None):
    req = urllib.request.Request(f"{base_url}{path}")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(req) as response:
            return response.status, response.read().decode()
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()
    except Exception as e:
        return None, str(e)

def test_post(path, data):
    req = urllib.request.Request(f"{base_url}{path}", method="POST")
    req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, data=json.dumps(data).encode()) as response:
            return response.status, response.read().decode()
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()
    except Exception as e:
        return None, str(e)

print("--- HEALTH ---")
print(test_get("/health"))

print("--- REGISTER ---")
test_user = {"email": "test@test.com", "password": "password123"}
print(test_post("/auth/register", test_user))

print("--- LOGIN ---")
print(test_post("/auth/login", {"email": "test@test.com", "password": "password123"}))

if token:
    print("--- ME ---")
    print(test_get("/auth/me", token))
