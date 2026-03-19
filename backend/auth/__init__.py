"""
Supabase JWT Authentication for FastAPI (ES256 / Asymmetric Keys).

This module verifies the Supabase access token sent by the frontend
and extracts the authenticated user_id.

Your Supabase project uses ES256 (asymmetric) JWTs, so we verify
using the public JWK — no secret needed on the backend.

Usage in routes:
  from auth.dependencies import get_current_user_id

  @router.get("/my-data")
  def my_endpoint(user_id: str = Depends(get_current_user_id)):
      # user_id is the authenticated Supabase user's UUID
      ...
"""

import json
import os
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, jwk, JWTError

# ── Supabase JWK Public Key (ES256) ────────────────────────────────
# This is the PUBLIC verification key from your Supabase project.
# It is safe to store in code because it's a public key (only verifies, can't sign).
# You can also set it via the SUPABASE_JWK env var as a JSON string.

_DEFAULT_JWK = {
    "x": "cWVCYuFrE5vEk5vO7zuzWLL58lZ1ZUO4a9Ta7W1SCb8",
    "y": "Cx4jLb1WwsyU-xxWI6qMOMEl34MqYOgqP6Kyw_O50cU",
    "alg": "ES256",
    "crv": "P-256",
    "ext": True,
    "kid": "d004b2d3-d0ac-48ca-8401-7c4377193f5d",
    "kty": "EC",
    "key_ops": ["verify"],
}

_jwk_env = os.environ.get("SUPABASE_JWK")
SUPABASE_JWK: dict = json.loads(_jwk_env) if _jwk_env else _DEFAULT_JWK

ALGORITHM = "ES256"

# Build the EC public key object from the JWK
try:
    _PUBLIC_KEY = jwk.construct(SUPABASE_JWK, algorithm=ALGORITHM)
except Exception as e:
    import warnings
    warnings.warn(f"Failed to construct JWK: {e}", stacklevel=2)
    _PUBLIC_KEY = None

# ── Bearer Token Extraction ────────────────────────────────────────
security = HTTPBearer()


# ── Dependency ──────────────────────────────────────────────────────
def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> str:
    """
    FastAPI dependency that:
      1. Extracts the Bearer token from the Authorization header
      2. Verifies & decodes the Supabase JWT using the ES256 public key
      3. Returns the user's UUID (the 'sub' claim)

    Raises 401 if the token is missing, expired, or invalid.
    """
    if _PUBLIC_KEY is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Auth not configured: JWK could not be loaded",
        )

    token = credentials.credentials

    try:
        payload = jwt.decode(
            token,
            _PUBLIC_KEY,
            algorithms=[ALGORITHM],
            options={"verify_aud": False},
        )
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid or expired token: {e}",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id: str | None = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token does not contain a user ID",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user_id