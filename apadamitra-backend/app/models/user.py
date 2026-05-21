import enum
from sqlalchemy import Column, Integer, String, Float, DateTime, Enum as SAEnum
from sqlalchemy.sql import func
from app.database import Base


class Occupation(str, enum.Enum):
    farmer = "farmer"
    fisherman = "fisherman"
    construction_worker = "construction_worker"
    citizen = "citizen"
    disaster_relief_worker = "disaster_relief_worker"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    phone = Column(String, unique=True, nullable=False, index=True)
    password_hash = Column(String, nullable=False)
    occupation = Column(SAEnum(Occupation), nullable=False)
    lat = Column(Float, nullable=False)
    lon = Column(Float, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
