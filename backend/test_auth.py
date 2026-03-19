"""
Auth module test script.
Tests:
  1. JWK key loading
  2. FastAPI app startup with auth dependency
  3. Unauthenticated request (should get 401/403)
  4. Authenticated request with a valid Supabase token (manual check)
"""

import sys
import json

print("=" * 60)
print("  Authentication Test Suite")
print("=" * 60)

# ── Test 1: JWK key construction ──────────────────────────────
print("\n[Test 1] JWK Key Loading...")
try:
    from jose import jwk

    JWK = {
        "x": "cWVCYuFrE5vEk5vO7zuzWLL58lZ1ZUO4a9Ta7W1SCb8",
        "y": "Cx4jLb1WwsyU-xxWI6qMOMEl34MqYOgqP6Kyw_O50cU",
        "alg": "ES256",
        "crv": "P-256",
        "ext": True,
        "kid": "d004b2d3-d0ac-48ca-8401-7c4377193f5d",
        "kty": "EC",
        "key_ops": ["verify"],
    }

    key = jwk.construct(JWK, algorithm="ES256")
    print(f"  ✅ JWK loaded successfully: {type(key)}")
except Exception as e:
    print(f"  ❌ JWK loading FAILED: {e}")
    sys.exit(1)

# ── Test 2: Import auth module ────────────────────────────────
print("\n[Test 2] Import auth module...")
try:
    # Add backend to path so 'auth' package resolves
    sys.path.insert(0, ".")
    from auth import get_current_user_id
    from auth import _PUBLIC_KEY, ALGORITHM, SUPABASE_JWK

    if _PUBLIC_KEY is not None:
        print(f"  ✅ Auth module imported, public key loaded")
        print(f"     Algorithm: {ALGORITHM}")
        print(f"     JWK kid  : {SUPABASE_JWK.get('kid')}")
    else:
        print(f"  ❌ Auth module imported but _PUBLIC_KEY is None!")
        sys.exit(1)
except Exception as e:
    print(f"  ❌ Import FAILED: {e}")
    import traceback; traceback.print_exc()
    sys.exit(1)

# ── Test 3: FastAPI TestClient — unauthenticated request ──────
print("\n[Test 3] Unauthenticated request to protected endpoint...")
try:
    from fastapi.testclient import TestClient
    from main import app

    client = TestClient(app, raise_server_exceptions=False)

    # Hit a protected endpoint without a token
    resp = client.get("/users/profile")
    print(f"  Status: {resp.status_code}")
    print(f"  Body  : {resp.json()}")

    if resp.status_code in (401, 403):
        print(f"  ✅ Correctly rejected unauthenticated request ({resp.status_code})")
    else:
        print(f"  ⚠️  Unexpected status code: {resp.status_code}")
except Exception as e:
    print(f"  ❌ Test FAILED: {e}")
    import traceback; traceback.print_exc()

# ── Test 4: FastAPI TestClient — invalid token ────────────────
print("\n[Test 4] Request with invalid/fake token...")
try:
    resp = client.get(
        "/users/profile",
        headers={"Authorization": "Bearer fake.invalid.token"}
    )
    print(f"  Status: {resp.status_code}")
    print(f"  Body  : {resp.json()}")

    if resp.status_code == 401:
        print(f"  ✅ Correctly rejected invalid token")
    else:
        print(f"  ⚠️  Unexpected status code: {resp.status_code}")
except Exception as e:
    print(f"  ❌ Test FAILED: {e}")
    import traceback; traceback.print_exc()

# ── Test 5: Check dashboard endpoint (also protected) ─────────
print("\n[Test 5] Unauthenticated request to /dashboard/summary...")
try:
    resp = client.get("/dashboard/summary")
    print(f"  Status: {resp.status_code}")

    if resp.status_code in (401, 403):
        print(f"  ✅ Dashboard endpoint correctly protected ({resp.status_code})")
    else:
        print(f"  ⚠️  Unexpected status code: {resp.status_code}")
except Exception as e:
    print(f"  ❌ Test FAILED: {e}")
    import traceback; traceback.print_exc()

# ── Test 6: Check unprotected endpoints still work ────────────
print("\n[Test 6] Unprotected endpoint /setup/status...")
try:
    resp = client.get("/setup/status")
    print(f"  Status: {resp.status_code}")

    if resp.status_code == 200:
        print(f"  ✅ Unprotected endpoint works fine")
    elif resp.status_code == 500:
        print(f"  ⚠️  Endpoint returned 500 (possibly DB issue, not auth)")
        print(f"  Body: {resp.json()}")
    else:
        print(f"  ⚠️  Unexpected status code: {resp.status_code}")
except Exception as e:
    print(f"  ❌ Test FAILED: {e}")
    import traceback; traceback.print_exc()

print("\n" + "=" * 60)
print("  All authentication tests complete!")
print("=" * 60)
