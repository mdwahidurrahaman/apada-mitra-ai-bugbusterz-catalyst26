"""
Database Service
MongoDB Atlas connection and collection helpers.
"""

import logging
import os
import threading
from typing import Optional

try:
    from pymongo import ASCENDING, MongoClient
    PYMONGO_AVAILABLE = True
except ImportError:
    ASCENDING = None
    MongoClient = None
    PYMONGO_AVAILABLE = False

logger = logging.getLogger(__name__)


class DatabaseService:
    """Small MongoDB helper used by application services."""
    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            with cls._lock:
                if not cls._instance:
                    cls._instance = super(DatabaseService, cls).__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(
        self,
        mongo_uri: Optional[str] = None,
        database_name: Optional[str] = None
    ):
        if getattr(self, '_initialized', False):
            return
            
        self.mongo_uri = mongo_uri or os.getenv("MONGO_URI")
        self.database_name = database_name or os.getenv(
            "MONGO_DB_NAME",
            "apadamitra"
        )
        self._client = None
        self._database = None
        self._initialized = True

    def is_configured(self) -> bool:
        return bool(PYMONGO_AVAILABLE and self.mongo_uri)

    def get_client(self):
        if not self.is_configured():
            raise RuntimeError(
                "MongoDB is not configured. Set MONGO_URI and install pymongo."
            )

        if self._client is None:
            with self._lock:
                if self._client is None:
                    self._client = MongoClient(
                        self.mongo_uri,
                        serverSelectionTimeoutMS=5000
                    )

        return self._client

    def get_database(self):
        if self._database is None:
            with self._lock:
                if self._database is None:
                    self._database = self.get_client()[self.database_name]

        return self._database

    def users_collection(self):
        return self.get_database()["users"]

    def alerts_collection(self):
        return self.get_database()["alerts"]

    def ping(self) -> bool:
        try:
            self.get_client().admin.command("ping")
            return True
        except Exception as e:
            logger.error("MongoDB ping failed: %s", str(e))
            return False

    def ensure_indexes(self) -> bool:
        try:
            users = self.users_collection()
            users.create_index(
                [("email", ASCENDING)],
                unique=True,
                name="unique_user_email"
            )
            users.create_index(
                [("phone", ASCENDING)],
                unique=True,
                sparse=True,
                name="unique_user_phone"
            )
            alerts = self.alerts_collection()
            alerts.create_index(
                [("created_at", ASCENDING)],
                name="alert_created_at"
            )
            alerts.create_index(
                [("user_id", ASCENDING), ("created_at", ASCENDING)],
                name="alert_user_created_at"
            )
            return True
        except Exception as e:
            logger.error("MongoDB index setup failed: %s", str(e))
            return False


db_service = DatabaseService()
