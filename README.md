# 🐾 Haven Pet — AI-Powered Pet Care Assistant

Haven Pet helps pet owners monitor their pets' daily routines, get personalized care recommendations, receive proactive health reminders, log and analyze pet behavior, and chat with an AI assistant for pet-care guidance.

## Architecture

```
React SPA (Vite)  ──HTTP/JSON──>  FastAPI (REST /api/v1)
                                       │
                           ┌───────────┼──────────────┐
                           │           │              │
                    SQLite/PostgreSQL  Agent          APScheduler
                    (SQLAlchemy 2.0)   Orchestrator   (reminder cron)
                           │           │              │
                           │     ┌─────┴──────┐      │
                           │     │  Claude API │      │
                           │     │  (chat,     │      │
                           │     │   recommend,│      │
                           │     │   tools)    │      │
                           └─────┴─────────────┴──────┘
```

### AI Agent Architecture
- **Intelligent Pet Care Agent (orchestrator)** — routes requests to sub-agents
- **Conversational AI Agent** — free-form chat with pet context
- **Personalized Recommendation Agent** — diet/exercise/enrichment advice
- **Tool-Using Agent** — function-calling for backend operations
- **Proactive Health Reminder Agent** — scheduled vaccination/medication alerts

## Tech Stack
| Layer | Technology |
|-------|-----------|
| Frontend | React 18 + Vite, React Router, Axios, CSS Modules |
| Backend | Python 3.13, FastAPI, Pydantic v2, SQLAlchemy 2.0 (async) |
| Database | SQLite (dev) / PostgreSQL (prod) |
| AI | Anthropic Claude API |
| Auth | JWT (access + refresh tokens), bcrypt |
| Scheduler | APScheduler |
| Containerization | Docker + docker-compose (optional) |

## Quick Start (Local Development)

### Prerequisites
- Python 3.11+
- Node.js 18+
- (Optional) PostgreSQL 15+

### 1. Clone & configure environment
```bash
cp .env.example .env
# Edit .env with your settings (JWT_SECRET is required, ANTHROPIC_API_KEY optional)
```

### 2. Start Both Backend & Frontend (One Command)
```bash
npm run dev
# Or double-click start-dev.bat (Windows)
```
This automatically boots both:
- Backend: `http://localhost:8000` (FastAPI)
- Frontend: `http://localhost:5173` (Vite SPA with auto-proxy)

### 3. (Alternative) Run Individually
**Backend:**
```bash
cd backend
uvicorn app.main:app --reload --port 8000
```

**Frontend:**
```bash
cd frontend
npm run dev
```

### 4. (Optional) Docker
```bash
docker-compose up --build     # Runs everything with PostgreSQL
```

### 5. Seed demo data
```bash
cd backend
python -m app.seed            # Creates demo user + pet
```

**Demo credentials:** `demo@havenpet.com` / `password123`

## API Documentation
Once the backend is running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Project Structure
```
haven-pet/
├── backend/
│   ├── app/
│   │   ├── agents/       # AI agent layer
│   │   ├── api/v1/       # Route modules
│   │   ├── core/         # Config, security, deps
│   │   ├── models/       # SQLAlchemy ORM models
│   │   ├── schemas/      # Pydantic request/response schemas
│   │   ├── services/     # Business logic
│   │   └── main.py       # FastAPI app entry
│   ├── alembic/          # Database migrations
│   ├── uploads/          # Pet photo uploads
│   ├── tests/
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/   # Reusable UI components
│   │   ├── pages/        # Route pages
│   │   ├── services/     # API client
│   │   ├── context/      # React contexts
│   │   └── App.jsx
│   └── package.json
├── docker-compose.yml
├── .env.example
└── README.md
```

## License
MIT
