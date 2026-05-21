"""
Auth Service
Small signed access-token helper using the Python standard library.
"""

import base64
import hashlib
import hmac
import json
import os
import time
from typing import Dict, Any


class AuthService:
    """Creates and verifies signed bearer tokens."""

    def __init__(self):
        self.secret = os.getenv("JWT_SECRET_KEY", "change-this-dev-secret")
        self.expiry_minutes = int(os.getenv("JWT_EXPIRE_MINUTES", "1440"))

    def create_access_token(self, user: Dict[str, Any]) -> str:
        now = int(time.time())
        payload = {
            "sub": user["id"],
            "email": user["email"],
            "role": user.get("role", "user"),
            "iat": now,
            "exp": now + (self.expiry_minutes * 60)
        }
        header = {
            "alg": "HS256",
            "typ": "JWT"
        }
        encoded_header = self._b64_json(header)
        encoded_payload = self._b64_json(payload)
        signature = self._sign(f"{encoded_header}.{encoded_payload}")
        return f"{encoded_header}.{encoded_payload}.{signature}"

    def verify_access_token(self, token: str) -> Dict[str, Any]:
        try:
            encoded_header, encoded_payload, signature = token.split(".")
            expected_signature = self._sign(f"{encoded_header}.{encoded_payload}")

            if not hmac.compare_digest(signature, expected_signature):
                raise ValueError("Invalid token signature.")

            payload = self._decode_json(encoded_payload)

            if int(payload.get("exp", 0)) < int(time.time()):
                raise ValueError("Token expired.")

            return payload

        except ValueError:
            raise
        except Exception as e:
            raise ValueError(f"Invalid token: {str(e)}")

    def _sign(self, value: str) -> str:
        digest = hmac.new(
            self.secret.encode("utf-8"),
            value.encode("utf-8"),
            hashlib.sha256
        ).digest()
        return self._b64_bytes(digest)

    def _b64_json(self, value: Dict[str, Any]) -> str:
        return self._b64_bytes(
            json.dumps(value, separators=(",", ":")).encode("utf-8")
        )

    def _decode_json(self, value: str) -> Dict[str, Any]:
        return json.loads(self._b64_decode(value).decode("utf-8"))

    def _b64_bytes(self, value: bytes) -> str:
        return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")

    def _b64_decode(self, value: str) -> bytes:
        padding = "=" * (-len(value) % 4)
        return base64.urlsafe_b64decode((value + padding).encode("ascii"))
