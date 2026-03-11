# Phase 1: Project Setup & Foundation

## Goal
Set up the project structure, install dependencies, configure the database, and get both frontend and backend running.

## Backend Tasks

### 1.1 Initialize backend
- Create `backend/` folder structure (app/, core/, models/, routes/, services/, websocket/)
- Create all `__init__.py` files
- Create `requirements.txt`:
  ```
  fastapi==0.109.0
  uvicorn==0.27.0
  sqlalchemy==2.0.25
  pydantic==2.5.3
  python-dotenv==1.0.0
  playwright==1.41.0
  anthropic==0.18.0
  cryptography==42.0.0
  websockets==12.0
  ```
- Create `.env.example`:
  ```
  DATABASE_URL=sqlite:///./broadcaster.db
  SECRET_KEY=your-secret-key-for-encryption
  ```

### 1.2 Database setup
- `core/config.py` — Load env vars, app settings
- `core/database.py` — SQLAlchemy engine, SessionLocal, Base
- `core/security.py` — Fernet encrypt/decrypt functions for storing credentials

### 1.3 Define all models
- Settings, Page, Contact, Broadcast, MessageLog
- All with proper relationships and foreign keys

### 1.4 FastAPI entry point
- `main.py` — Create app, add CORS middleware, include routers, create tables on startup
- `run.py` — Uvicorn runner script

### 1.5 Install Playwright browsers
- Run `playwright install chromium` after pip install

## Frontend Tasks

### 1.6 Initialize frontend
- `npm create vite@latest frontend -- --template react`
- Install dependencies:
  ```
  npm install react-router-dom axios react-icons react-toastify
  npm install -D tailwindcss @tailwindcss/vite
  ```
- Configure Tailwind (tailwind.config.js, postcss.config.js, index.css)
- Configure Vite proxy to backend (vite.config.js)

### 1.7 Base layout
- `Layout.jsx` — Sidebar navigation + main content area
- `Sidebar.jsx` — Navigation links: Settings, Pages, Compose, Broadcast, History
- `App.jsx` — React Router with all routes
- Basic dark-themed styling for a clean dashboard look

## Verification
- Backend: `python run.py` → FastAPI running on http://localhost:8000
- Frontend: `npm run dev` → React app on http://localhost:5173
- Database: `broadcaster.db` created with all tables
- Visit frontend → see sidebar and empty pages rendering
