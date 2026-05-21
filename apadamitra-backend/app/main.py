import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from app.database import Base, engine, get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.routers import auth, alerts, chat
from app.services.weather import fetch_weather, reverse_geocode
from scheduler import start_scheduler, scheduler

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    start_scheduler()
    yield
    scheduler.shutdown()


app = FastAPI(
    title="Apadamitra — Weather Alert System",
    description="AI-powered hyperlocal weather alerts for West Bengal",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/auth", tags=["Auth"])
app.include_router(alerts.router, prefix="/alerts", tags=["Alerts"])
app.include_router(chat.router, prefix="/chat", tags=["Chat"])


@app.get("/health", tags=["Health"])
def health():
    return {"status": "ok", "service": "Apadamitra"}


@app.get("/weather/current", tags=["Weather"])
async def current_weather(current_user: User = Depends(get_current_user)):
    weather = await fetch_weather(current_user.lat, current_user.lon)
    district = await reverse_geocode(current_user.lat, current_user.lon)
    return {
        "user": current_user.name,
        "occupation": current_user.occupation.value,
        "district": district,
        "weather": weather,
    }
