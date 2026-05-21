"""
User Service
Registration and login workflows backed by MongoDB.
"""

import base64
import hashlib
import hmac
import logging
import os
import re
from datetime import datetime
from typing import Dict, Any, Optional

try:
    from pymongo.errors import DuplicateKeyError
    from bson import ObjectId
except ImportError:
    class DuplicateKeyError(Exception):
        pass
    ObjectId = None

from app.services.database_service import DatabaseService

logger = logging.getLogger(__name__)


class UserService:
    """Handles registration and login for users."""

    def __init__(self, database: Optional[DatabaseService] = None):
        self.database = database or DatabaseService()

    def register_user(
        self,
        name: str,
        email: str,
        password: str,
        phone: Optional[str] = None,
        user_type: Optional[str] = None,
        location: Optional[str] = None,
        lat: Optional[float] = None,
        lon: Optional[float] = None,
        enable_sms_alerts: bool = False
    ) -> Dict[str, Any]:
        self._validate_email(email)
        self._validate_password(password)
        self._validate_phone(phone)

        normalized_email = email.strip().lower()
        normalized_phone = phone.strip() if phone else None

        self.database.ensure_indexes()
        users = self.database.users_collection()
        now = datetime.utcnow()

        duplicate_filters = [{"email": normalized_email}]

        if normalized_phone:
            duplicate_filters.append({"phone": normalized_phone})

        if users.find_one({"$or": duplicate_filters}):
            raise ValueError("A user with this email or phone already exists.")

        user_doc = {
            "name": name.strip(),
            "email": normalized_email,
            "password_hash": self._hash_password(password),
            "phone": normalized_phone,
            "user_type": user_type,
            "location": location.strip() if location else None,
            "lat": lat,
            "lon": lon,
            "enable_sms_alerts": enable_sms_alerts,
            "role": "user",
            "created_at": now,
            "updated_at": now
        }

        try:
            result = users.insert_one(user_doc)
            created = users.find_one({"_id": result.inserted_id})
            return self._serialize_user(created)

        except DuplicateKeyError:
            raise ValueError("A user with this email or phone already exists.")

    def authenticate_user(self, email: str, password: str) -> Optional[Dict[str, Any]]:
        normalized_email = email.strip().lower()
        user_doc = self.database.users_collection().find_one(
            {"email": normalized_email}
        )

        if not user_doc:
            return None

        if not self._verify_password(password, user_doc.get("password_hash", "")):
            return None

        return self._serialize_user(user_doc)

    def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        user_doc = self.database.users_collection().find_one(
            {"email": email.strip().lower()}
        )
        return self._serialize_user(user_doc) if user_doc else None

    def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        if ObjectId is None:
            return None

        user_doc = self.database.users_collection().find_one(
            {"_id": ObjectId(user_id)}
        )
        return self._serialize_user(user_doc) if user_doc else None

    def list_users(self, limit: int = 100, skip: int = 0) -> Dict[str, Any]:
        users = self.database.users_collection()
        total = users.count_documents({})
        cursor = (
            users.find({})
            .sort("created_at", -1)
            .skip(skip)
            .limit(limit)
        )

        return {
            "users": [self._serialize_user(user_doc) for user_doc in cursor],
            "total": total,
            "limit": limit,
            "skip": skip
        }

    def list_users_for_alerts(self, limit: int = 100) -> list:
        cursor = self.database.users_collection().find(
            {
                "enable_sms_alerts": True,
                "phone": {"$ne": None},
                "lat": {"$ne": None},
                "lon": {"$ne": None}
            }
        ).limit(limit)
        return [self._serialize_user(user_doc) for user_doc in cursor]

    def seed_demo_users(self) -> Dict[str, int]:
        demo_users = [
            {
                "name": "Amit Sharma",
                "email": "amit.sharma@example.com",
                "password": "DemoPass123",
                "phone": "+919800000001",
                "user_type": "farmer",
                "location": "Malda",
                "lat": 25.01,
                "lon": 88.14,
                "enable_sms_alerts": True
            },
            {
                "name": "Priya Das",
                "email": "priya.das@example.com",
                "password": "DemoPass123",
                "phone": "+919800000002",
                "user_type": "student",
                "location": "Kolkata",
                "lat": 22.57,
                "lon": 88.36,
                "enable_sms_alerts": False
            },
            {
                "name": "Rahul Verma",
                "email": "rahul.verma@example.com",
                "password": "DemoPass123",
                "phone": "+919800000003",
                "user_type": "worker",
                "location": "Patna",
                "lat": 25.59,
                "lon": 85.14,
                "enable_sms_alerts": True
            },
            {
                "name": "Sunita Roy",
                "email": "sunita.roy@example.com",
                "password": "DemoPass123",
                "phone": "+919800000004",
                "user_type": "elderly",
                "location": "Bhubaneswar",
                "lat": 20.30,
                "lon": 85.82,
                "enable_sms_alerts": True
            },
            {
                "name": "Vikram Singh",
                "email": "vikram.singh@example.com",
                "password": "DemoPass123",
                "phone": "+919800000005",
                "user_type": "industry",
                "location": "Visakhapatnam",
                "lat": 17.69,
                "lon": 83.22,
                "enable_sms_alerts": False
            },
            {
                "name": "Neha Gupta",
                "email": "neha.gupta@example.com",
                "password": "DemoPass123",
                "phone": "+919800000006",
                "user_type": "student",
                "location": "Guwahati",
                "lat": 26.14,
                "lon": 91.73,
                "enable_sms_alerts": True
            },
            {
                "name": "Sanjay Mandal",
                "email": "sanjay.mandal@example.com",
                "password": "DemoPass123",
                "phone": "+919800000007",
                "user_type": "farmer",
                "location": "Cuttack",
                "lat": 20.46,
                "lon": 85.88,
                "enable_sms_alerts": True
            },
            {
                "name": "Ananya Sen",
                "email": "ananya.sen@example.com",
                "password": "DemoPass123",
                "phone": "+919800000008",
                "user_type": "worker",
                "location": "Ranchi",
                "lat": 23.34,
                "lon": 85.31,
                "enable_sms_alerts": False
            },
            {
                "name": "Ramesh Yadav",
                "email": "ramesh.yadav@example.com",
                "password": "DemoPass123",
                "phone": "+919800000009",
                "user_type": "elderly",
                "location": "Varanasi",
                "lat": 25.32,
                "lon": 82.97,
                "enable_sms_alerts": True
            },
            {
                "name": "Meera Nair",
                "email": "meera.nair@example.com",
                "password": "DemoPass123",
                "phone": "+919800000010",
                "user_type": "industry",
                "location": "Chennai",
                "lat": 13.08,
                "lon": 80.27,
                "enable_sms_alerts": True
            },
            {
                "name": "Arjun Paul",
                "email": "arjun.paul@example.com",
                "password": "DemoPass123",
                "phone": "+919800000011",
                "user_type": "student",
                "location": "Durgapur",
                "lat": 23.55,
                "lon": 87.32,
                "enable_sms_alerts": False
            },
            {
                "name": "Kavita Kumari",
                "email": "kavita.kumari@example.com",
                "password": "DemoPass123",
                "phone": "+919800000012",
                "user_type": "farmer",
                "location": "Purnia",
                "lat": 25.78,
                "lon": 87.48,
                "enable_sms_alerts": True
            },
            {
                "name": "Mohit Agarwal",
                "email": "mohit.agarwal@example.com",
                "password": "DemoPass123",
                "phone": "+919800000013",
                "user_type": "worker",
                "location": "Siliguri",
                "lat": 26.73,
                "lon": 88.40,
                "enable_sms_alerts": True
            },
            {
                "name": "Farida Khan",
                "email": "farida.khan@example.com",
                "password": "DemoPass123",
                "phone": "+919800000014",
                "user_type": "elderly",
                "location": "Howrah",
                "lat": 22.59,
                "lon": 88.26,
                "enable_sms_alerts": False
            },
            {
                "name": "Ishaan Bose",
                "email": "ishaan.bose@example.com",
                "password": "DemoPass123",
                "phone": "+919800000015",
                "user_type": "industry",
                "location": "Haldia",
                "lat": 22.06,
                "lon": 88.11,
                "enable_sms_alerts": True
            }
        ]

        created = 0
        skipped = 0

        for user in demo_users:
            if self.get_user_by_email(user["email"]):
                skipped += 1
                continue

            self.register_user(**user)
            created += 1

        return {
            "created": created,
            "skipped": skipped,
            "total": len(demo_users)
        }

    def ensure_admin_user(self) -> bool:
        admin_email = os.getenv("ADMIN_EMAIL")
        admin_password = os.getenv("ADMIN_PASSWORD")

        if not admin_email or not admin_password:
            return False

        users = self.database.users_collection()
        existing = users.find_one({"email": admin_email.strip().lower()})
        now = datetime.utcnow()

        if existing:
            users.update_one(
                {"_id": existing["_id"]},
                {
                    "$set": {
                        "role": "admin",
                        "updated_at": now
                    }
                }
            )
            return False

        self._validate_email(admin_email)
        self._validate_password(admin_password)
        users.insert_one(
            {
                "name": os.getenv("ADMIN_NAME", "ApadaMitra Admin"),
                "email": admin_email.strip().lower(),
                "password_hash": self._hash_password(admin_password),
                "phone": os.getenv("ADMIN_PHONE"),
                "user_type": None,
                "location": None,
                "lat": None,
                "lon": None,
                "enable_sms_alerts": False,
                "role": "admin",
                "created_at": now,
                "updated_at": now
            }
        )
        return True

    def _serialize_user(self, user_doc: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "id": str(user_doc["_id"]),
            "name": user_doc.get("name"),
            "email": user_doc.get("email"),
            "phone": user_doc.get("phone"),
            "user_type": user_doc.get("user_type"),
            "location": user_doc.get("location"),
            "lat": user_doc.get("lat"),
            "lon": user_doc.get("lon"),
            "enable_sms_alerts": user_doc.get("enable_sms_alerts", False),
            "role": user_doc.get("role", "user"),
            "created_at": user_doc.get("created_at").isoformat()
            if user_doc.get("created_at")
            else None
        }

    def _validate_email(self, email: str) -> None:
        if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email or ""):
            raise ValueError("A valid email address is required.")

    def _validate_password(self, password: str) -> None:
        if len(password or "") < 8:
            raise ValueError("Password must be at least 8 characters long.")

    def _validate_phone(self, phone: Optional[str]) -> None:
        if phone and not re.match(r"^\+[1-9]\d{7,14}$", phone):
            raise ValueError("Phone number must use E.164 format, for example +919876543210.")

    def _hash_password(self, password: str) -> str:
        iterations = 260000
        salt = os.urandom(16)
        password_hash = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt,
            iterations
        )
        salt_text = base64.urlsafe_b64encode(salt).decode("ascii")
        hash_text = base64.urlsafe_b64encode(password_hash).decode("ascii")
        return f"pbkdf2_sha256${iterations}${salt_text}${hash_text}"

    def _verify_password(self, password: str, stored_hash: str) -> bool:
        try:
            algorithm, iterations_text, salt_text, hash_text = stored_hash.split("$")

            if algorithm != "pbkdf2_sha256":
                return False

            salt = base64.urlsafe_b64decode(salt_text.encode("ascii"))
            expected_hash = base64.urlsafe_b64decode(hash_text.encode("ascii"))
            actual_hash = hashlib.pbkdf2_hmac(
                "sha256",
                password.encode("utf-8"),
                salt,
                int(iterations_text)
            )
            return hmac.compare_digest(actual_hash, expected_hash)

        except Exception:
            return False
