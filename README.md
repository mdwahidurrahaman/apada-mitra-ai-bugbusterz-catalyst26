# 🌪️ Apadamitra — AI-Powered Disaster Alert System

> **আপদামিত্র** (*Apadamitra*) — *"Disaster Friend"* in Bengali.  
> Apadamitra goes beyond alerts. By combining AI-driven disaster prediction with personalized mitigation strategies, it helps people know not only **what is coming** — but exactly **what to do next**.

---

## 📌 Table of Contents

- [Overview](#overview)
- [Key Features](#key-features)
- [Architecture](#architecture)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Getting Started](#getting-started)
- [Environment Variables](#environment-variables)
- [API Reference](#api-reference)
- [ML Models](#ml-models)
- [Demo Guide](#demo-guide)
- [Team](#team)

---

## Overview

Apadamitra is a real-time, hyperlocal weather alert system built for West Bengal, India. It predicts natural disasters — **cyclones, floods, and heatwaves** — using custom-trained ML models, and delivers **personalized, AI-generated SMS alerts** tailored to each user's occupation (farmer, fisherman, construction worker, citizen, disaster relief worker).

Users also get access to **Apadamitra Chat**, an AI assistant powered by Gemini that answers weather-related questions with full awareness of the user's location, occupation, and active alerts — in English or Bengali.

---

## Key Features

| Feature | Description |
|--------|-------------|
| 🔮 **Disaster Prediction** | Custom ML models predict cyclone, flood, and heatwave probability from live weather data |
| 📍 **Hyperlocal Alerts** | Alerts are tied to each user's GPS location — district-level precision |
| 🧑‍🌾 **Occupation-Aware SMS** | Gemini generates unique SMS messages for farmers, fishermen, construction workers, citizens, and relief workers |
| 🤖 **Apadamitra Chat** | AI chat assistant with real-time weather context and active alert awareness |
| ⏰ **Automated Cron Pipeline** | Background scheduler fetches weather → runs ML → sends alerts at configurable intervals |
| 🚀 **Manual Demo Trigger** | `/alerts/trigger` endpoint fires the full pipeline on demand |

---

## Architecture

```
┌─────────────────────────────────────────┐
│             CLIENT LAYER                │
│     React Frontend  +  Browser GPS     │
└──────────────────┬──────────────────────┘
                   │ REST API
┌──────────────────▼──────────────────────┐
│            FASTAPI BACKEND              │
│                                         │
│  /auth    /alerts    /chat    /weather  │
│                                         │
│         APScheduler (Cron Job)          │
└──────┬──────────┬──────────┬────────────┘
       │          │          │
  ┌────▼───┐  ┌───▼────┐  ┌──▼──────────────────┐
  │  PostgreSQL│  ML Layer│  External Services    │
  │  Database  │  3 .pkl  │  Open-Meteo (weather) │
  │            │  models  │  Gemini API (SMS+chat)│
  └────────┘  └─────────┘  │  Twilio (SMS delivery│
                            └──────────────────────┘
```

### Alert Pipeline Flow

```
Cron fires (every N minutes) or POST /alerts/trigger
         │
         ▼
  Fetch all users from DB
         │
         ▼  (per user)
  Open-Meteo API → live weather at user's lat/lon
         │
         ▼
  3 ML models → cyclone / flood / heatwave probability
         │
         ▼
  Threshold check → LOW / MEDIUM / HIGH / skip
         │
         ▼
  Gemini → personalized SMS for user's name + occupation
         │
         ▼
  Twilio → SMS delivered + saved to DB
```

---

## Tech Stack

### Backend
| Layer | Technology |
|-------|-----------|
| Framework | FastAPI |
| Language | Python 3.11+ |
| Database | PostgreSQL + SQLAlchemy |
| Auth | JWT (python-jose) + bcrypt |
| Scheduler | APScheduler |
| HTTP Client | httpx (async) |

### AI / ML
| Component | Technology |
|-----------|-----------|
| Disaster Prediction | scikit-learn (.pkl models) |
| SMS Generation | Google Gemini 1.5 Flash |
| Chat Assistant | Google Gemini 1.5 Flash |

### External APIs
| Service | Purpose |
|---------|---------|
| Open-Meteo | Free real-time weather data (no API key required) |
| OpenStreetMap Nominatim | Reverse geocoding (lat/lon → district name) |
| Twilio | SMS delivery |

### Frontend *(separate repo)*
| Technology | Purpose |
|-----------|---------|
| React | UI |
| Browser Geolocation API | Capture user lat/lon at registration |

---

## Project Structure

```
apadamitra/
├── apadamitra-backend/
│   ├── app/
│   │   ├── main.py                  # FastAPI app + lifespan + CORS
│   │   ├── config.py                # Pydantic settings from .env
│   │   ├── database.py              # SQLAlchemy engine + session
│   │   ├── dependencies.py          # JWT auth dependency injection
│   │   ├── models/
│   │   │   ├── user.py              # User model + Occupation enum
│   │   │   └── alert.py             # Alert, UserAlert, ChatMessage models
│   │   ├── schemas/
│   │   │   ├── user.py              # Register/Login/Token Pydantic schemas
│   │   │   ├── alert.py             # Alert response schemas
│   │   │   └── chat.py              # Chat request/response schemas
│   │   ├── routers/
│   │   │   ├── auth.py              # POST /auth/register, /login, GET /me
│   │   │   ├── alerts.py            # GET /alerts/me, POST /alerts/trigger
│   │   │   └── chat.py              # POST /chat/message
│   │   └── services/
│   │       ├── weather.py           # Open-Meteo fetch + Nominatim geocode
│   │       ├── ml.py                # Load .pkl models + predict
│   │       ├── sms.py               # Gemini SMS generation + Twilio send
│   │       ├── alert_engine.py      # Full pipeline orchestration
│   │       └── chat.py              # Gemini chat with user context
│   ├── scheduler.py                 # APScheduler cron job
│   ├── requirements.txt
│   ├── .env                         # Secrets (gitignored)
│   └── .env.example
│
├── models/                          # ML model files
│   ├── apadamitra_cyclone_model.pkl
│   ├── apadamitra_cyclone_scaler.pkl
│   ├── apadamitra_flood_model.pkl        (coming)
│   ├── apadamitra_flood_scaler.pkl       (coming)
│   ├── apadamitra_heatwave_model.pkl     (coming)
│   └── apadamitra_heatwave_scaler.pkl    (coming)
│
├── model_dataset/                   # Training data
│   └── apadamitra_cyclone_dataset.csv
│
├── model_notebooks/                 # Model training notebooks
│   └── cyclone_prediction_model.ipynb
│
└── README.md
```

---

## Getting Started

### Prerequisites

- Python 3.11+
- PostgreSQL running locally or a cloud instance (Supabase, Render, etc.)
- Google AI Studio API key (free at [aistudio.google.com](https://aistudio.google.com))
- Twilio account (free trial works for prototype)

### 1. Clone the repository

```bash
git clone https://github.com/your-org/apadamitra.git
cd apadamitra/apadamitra-backend
```

### 2. Create and activate virtual environment

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS/Linux or WSL2
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Set up environment variables

```bash
cp .env.example .env
# Open .env and fill in all values (see Environment Variables section)
```

### 5. Create the database

```bash
# Connect to PostgreSQL and create the database
psql -U postgres
CREATE DATABASE apadamitra;
\q
```

> Tables are auto-created on first server startup via SQLAlchemy `create_all`.

### 6. Run the server

```bash
uvicorn app.main:app --reload
```

Server starts at `http://localhost:8000`  
Interactive API docs at `http://localhost:8000/docs`

---

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `DATABASE_URL` | ✅ | PostgreSQL connection string e.g. `postgresql://user:pass@localhost:5432/apadamitra` |
| `SECRET_KEY` | ✅ | JWT signing secret — use a long random string |
| `ALGORITHM` | ❌ | JWT algorithm, default `HS256` |
| `ACCESS_TOKEN_EXPIRE_HOURS` | ❌ | JWT expiry, default `24` |
| `GEMINI_API_KEY` | ✅ | Google AI Studio API key |
| `TWILIO_ACCOUNT_SID` | ✅ | Twilio Account SID |
| `TWILIO_AUTH_TOKEN` | ✅ | Twilio Auth Token |
| `TWILIO_PHONE_NUMBER` | ✅ | Twilio sender number in E.164 format e.g. `+1xxxxxxxxxx` |
| `CRON_INTERVAL_MINUTES` | ❌ | How often the alert pipeline runs, default `30` |
| `THRESHOLD_LOW` | ❌ | Minimum probability for LOW alert, default `0.20` |
| `THRESHOLD_MEDIUM` | ❌ | Minimum probability for MEDIUM alert, default `0.40` |
| `THRESHOLD_HIGH` | ❌ | Minimum probability for HIGH alert, default `0.70` |
| `SITE_URL` | ❌ | Site URL appended to SMS messages, default `https://apadamitra.com` |
| `MODEL_DIR` | ❌ | Path to ML model files, default `../models` |

---

## API Reference

Base URL: `http://localhost:8000`  
Full interactive docs: `http://localhost:8000/docs`

---

### Auth

#### `POST /auth/register`
Register a new user. Frontend sends lat/lon from browser GPS.

**Request body:**
```json
{
  "name": "Ravi Das",
  "phone": "+919876543210",
  "password": "securepassword",
  "occupation": "fisherman",
  "lat": 21.9242,
  "lon": 88.1318
}
```

**Occupation values:** `farmer` | `fisherman` | `construction_worker` | `citizen` | `disaster_relief_worker`

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

---

#### `POST /auth/login`

**Request body:**
```json
{
  "phone": "+919876543210",
  "password": "securepassword"
}
```

**Response:** Same as register — JWT token.

---

#### `GET /auth/me`
🔒 *Requires Bearer token*

Returns the authenticated user's profile.

---

### Alerts

#### `GET /alerts/me`
🔒 *Requires Bearer token*

Returns the last 20 alerts for the authenticated user.

**Response:**
```json
[
  {
    "id": 1,
    "alert_type": "cyclone",
    "severity": "high",
    "district": "South 24 Parganas",
    "probability": 0.82,
    "created_at": "2025-05-22T14:30:00+05:30",
    "sms_sent": true
  }
]
```

---

#### `POST /alerts/trigger`
Manually fires the full alert pipeline. **Use this button during demo.**

No request body needed.

**Response:**
```json
{
  "message": "Alert pipeline executed successfully",
  "alerts_triggered": 3
}
```

---

### Chat

#### `POST /chat/message`
🔒 *Requires Bearer token*

Send a message to the Apadamitra AI assistant. The assistant has full context of the user's occupation, location, current weather, and active alerts.

**Request body:**
```json
{
  "message": "Should I go fishing today?"
}
```

**Response:**
```json
{
  "response": "Ravi, with wind speeds at 62 km/h and an active HIGH cyclone warning near Digha, it is strongly advised not to venture into the sea today. Secure your boat on shore and stay in a safe location until the alert is lifted.",
  "role": "assistant"
}
```

> Responds in English or Bengali based on the user's message language.

---

### Weather

#### `GET /weather/current`
🔒 *Requires Bearer token*

Returns live weather conditions at the user's registered location.

**Response:**
```json
{
  "user": "Ravi Das",
  "occupation": "fisherman",
  "district": "South 24 Parganas",
  "weather": {
    "temperature_2m": 34.2,
    "relative_humidity_2m": 78,
    "surface_pressure": 1008.4,
    "wind_speed_10m": 62.1,
    "wind_direction_10m": 180,
    "precipitation": 12.4,
    "cloud_cover": 95,
    "apparent_temperature": 41.3,
    "time": "2025-05-22T14:00"
  }
}
```

---

### Health

#### `GET /health`
No auth required. Returns server status.

```json
{
  "status": "ok",
  "service": "Apadamitra"
}
```

---

## ML Models

The prediction layer uses three separate scikit-learn models, each with a corresponding feature scaler.

| Disaster | Model File | Scaler File |
|----------|-----------|-------------|
| Cyclone | `apadamitra_cyclone_model.pkl` | `apadamitra_cyclone_scaler.pkl` |
| Flood | `apadamitra_flood_model.pkl` | `apadamitra_flood_scaler.pkl` |
| Heatwave | `apadamitra_heatwave_model.pkl` | `apadamitra_heatwave_scaler.pkl` |

All models are placed in the `models/` directory at the project root.

**Input features** (in order):
```
temperature_2m, relative_humidity_2m, surface_pressure,
wind_speed_10m, wind_direction_10m, precipitation,
cloud_cover, apparent_temperature
```

**Output:** Probability score between `0.0` and `1.0`

**Threshold logic:**

| Probability | Severity |
|-------------|----------|
| ≥ 0.70 | 🔴 HIGH |
| 0.40 – 0.69 | 🟠 MEDIUM |
| 0.20 – 0.39 | 🟡 LOW |
| < 0.20 | ✅ No alert |

> If a model file is missing, the system logs a warning and gracefully skips that disaster type. The server will not crash.

---

## Demo Guide

### Step-by-step for judges

**1. Start the server**
```bash
cd apadamitra-backend
uvicorn app.main:app --reload
```

**2. Open Swagger docs**  
Navigate to `http://localhost:8000/docs`

**3. Register a test user**  
`POST /auth/register` — use coordinates within West Bengal:
```json
{
  "name": "Arjun Das",
  "phone": "+919000000001",
  "password": "test1234",
  "occupation": "fisherman",
  "lat": 21.9242,
  "lon": 88.1318
}
```

**4. Copy the JWT token** from the response and click **Authorize** in Swagger docs (top right).

**5. Check current weather**  
`GET /weather/current` — shows live conditions at the user's location.

**6. Fire the alert pipeline**  
`POST /alerts/trigger` — runs ML prediction → generates personalized SMS → logs it to console.

**7. See alerts**  
`GET /alerts/me` — shows all alerts generated for this user.

**8. Chat with Apadamitra**  
`POST /chat/message` — send `"Should I go out to sea today?"` — AI responds with occupation-aware weather advice.

---

### Console output during demo trigger

```
INFO | [PIPELINE] Arjun Das (fisherman) | cyclone=0.82 flood=0.31 heatwave=0.04
INFO | [ALERT] CYCLONE [HIGH] → Arjun Das | SMS: ✓
INFO | [MOCK SMS] To: +919000000001
      Arjun, a severe cyclone is approaching South 24 Parganas with winds
      at 62 km/h. As a fisherman, do not venture into the sea — return to
      shore immediately and secure your boat.

      Stay informed: https://apadamitra.com
INFO | [PIPELINE DONE] Total alerts: 1
```

---

### Enabling live SMS (Twilio)

1. Uncomment the Twilio block in `app/services/sms.py`
2. Uncomment `twilio==9.10.9` in `requirements.txt` and run `pip install twilio`
3. Verify the recipient phone number in your Twilio console (free tier requirement)
4. Ensure `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, `TWILIO_PHONE_NUMBER` are set in `.env`

---

## Team

| Role | Responsibility |
|------|---------------|
| 🔧 Backend | FastAPI, alert pipeline, Gemini integration, cron scheduler |
| 🤖 ML | Cyclone, flood, heatwave prediction models (scikit-learn) |
| 🎨 Frontend | React UI, geolocation, alert dashboard, chat interface |

---

*Built for Catalyst '26 Hackathon — Team BugBusterz*