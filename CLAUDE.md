# FB Page Broadcaster

## What This Project Does
A web app that broadcasts AI-rephrased messages to Facebook page contacts via Playwright browser automation. Users compose one message, the AI creates unique variants, and they are sent to page contacts with configurable delays.

## Tech Stack
| Layer      | Technology                              |
|------------|----------------------------------------|
| Frontend   | React 19 + Vite + TailwindCSS          |
| Backend    | Python FastAPI + SQLAlchemy + SQLite    |
| Automation | Playwright (headless Chromium)          |
| AI         | Google GenAI (`google-genai` package)   |
| Real-time  | WebSockets                              |

## Project Structure
```
backend/
  app/
    main.py              # FastAPI app entry point
    routes/              # API endpoints (settings, pages, compose, broadcast, history)
    services/            # Business logic (facebook.py, broadcast.py, message.py)
    models/              # SQLAlchemy models (settings, page, contact, broadcast, message_log)
    core/                # Config, database setup
    websocket/           # WebSocket handlers
  run.py                 # Server runner
  requirements.txt
  broadcaster.db         # SQLite database (gitignored)

frontend/
  src/
    App.jsx              # Router setup
    main.jsx             # Entry point
    pages/               # Settings, Pages, Compose, Broadcast, History
    components/          # Layout, Sidebar, ProgressBar, StatusBadge, MessagePreview
    api/                 # API client (axios)
    hooks/               # Custom React hooks
  vite.config.js
  tailwind.config.js
```

## Commands
```bash
# Backend
cd backend
pip install -r requirements.txt
python run.py              # Starts FastAPI on http://localhost:8000

# Frontend
cd frontend
npm install
npm run dev                # Starts Vite on http://localhost:5173
npm run build              # Production build → dist/
```

## Key Patterns
- Backend routes are in `backend/app/routes/`, services in `backend/app/services/`
- Frontend pages map 1:1 to sidebar nav: Settings, Pages, Compose, Broadcast, History
- Real-time broadcast progress is sent via WebSocket
- Facebook automation uses Playwright with cookie persistence for session reuse
- AI rephrasing uses Google GenAI (not Claude API despite PROJECT_PLAN.md mentioning it)
- Credentials are encrypted via `cryptography` package

## Coding Conventions
- Backend: Python with FastAPI, async/await, Pydantic models for validation
- Frontend: React functional components with hooks, TailwindCSS for styling
- API communication: axios from frontend to FastAPI backend
- Code comments in English
