# Trading Engine UI Dashboard

Company: Deccan Research Capital
Role: Full Stack Developer Intern

This repository contains a full-stack real-time trading dashboard with:
- Backend: FastAPI (Python) with REST APIs and WebSocket streaming
- Frontend: React + Vite + TailwindCSS
- Database: SQLite (for local testing)

## Features
- Live Orders table (auto-updates via WebSocket)
- Live Trades table (new trades append via WebSocket)
- Live Ticker panel with second-by-second price updates
- Manual refresh buttons for Orders and Trades
- WebSocket status indicator (connected/disconnected)

## Project Structure
- `backend/` — FastAPI app with REST + WebSocket, SQLite models and seed data
- `frontend/` — React app with TailwindCSS and WebSocket client

## Quickstart

### Backend
1. Create and activate a Python environment (any method is fine; venv/conda).
2. Install dependencies.
3. Run the server.

Example commands (PowerShell):

```powershell
# 1) Create venv (optional but recommended)
python -m venv .venv
. .venv/Scripts/Activate.ps1

# 2) Install deps
pip install -r backend/requirements.txt

# 3) Run FastAPI (auto-reload for dev)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 --app-dir backend
```

FastAPI docs: http://localhost:8000/docs

### Frontend
We'll scaffold a Vite + React + Tailwind app in `frontend/`.

```powershell
# From repository root
cd frontend
npm install
npm run dev
```

Vite dev server: http://localhost:5174

Environment variables (already provided in `frontend/.env`):

```
VITE_API_BASE=http://localhost:8000
VITE_WS_URL=ws://localhost:8000/ws/live
```

If you need to change ports, update these values accordingly.

### Environment and CORS
The backend allows CORS from `http://localhost:5173` (Vite default). Adjust in `backend/app/main.py` if you use a different port.

## REST API Summary
- `GET /orders/open` — list active/open orders
- `GET /trades/recent` — most recent 100 trades
- `GET /tickers` — list of tickers
- `WS /ws/live` — streams events: `price_update`, `order_update`, `new_trade`

## Notes
- Data is seeded with mock records on startup if DB is empty.
- WebSocket simulates price ticks every second and occasional order/trade events.
- For a production DB, switch the SQLAlchemy URL in `backend/app/database.py`.

## Run both servers (TL;DR)

```powershell
# From repo root

# Backend
python -m venv .venv
. .venv/Scripts/Activate.ps1
pip install -r backend/requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 --app-dir backend

# In a new PowerShell window
cd frontend
npm install
npm run dev
```

## Bonus (optional)
- Add order entry form
- Small sparkline for ticker prices
- Docker Compose for one-command startup

### Docker (optional)

Build and run both services with one command:

```powershell
docker compose up --build
```

- Backend: http://localhost:8000 (docs at /docs)
- Frontend: http://localhost:5173

The frontend in Docker uses env vars to call the backend service by name.

```
backend/
  app/
    main.py
    database.py
    models.py
    schemas.py
    crud.py
    __init__.py
  requirements.txt
frontend/
  ... (Vite + React + Tailwind)
```
