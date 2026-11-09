# StockSense

**Inventory management platform for small retail businesses.**

StockSense helps small retailers manage products, track stock levels, record sales and purchases, monitor expiry dates, and view analytics — all from a clean web interface.

## The Problem

Small retail shops often track inventory manually with notebooks or spreadsheets. This leads to:
- Stock-outs when popular items run out unexpectedly.
- Expired products sitting unnoticed on shelves.
- No visibility into which products sell well and which don't.
- Difficulty knowing when and how much to reorder.

StockSense solves these problems with a purpose-built, free, and open-source platform.

## Technology Stack

| Layer     | Technology                         |
| --------- | ---------------------------------- |
| Frontend  | Next.js 16, React 19, TypeScript, Tailwind CSS 4 |
| Backend   | Python 3.13, FastAPI, Pydantic     |
| Database  | PostgreSQL 16, SQLAlchemy 2, Alembic |
| Dev Tools | Docker Compose, ESLint, Pytest     |

## Architecture

```
Browser  ──HTTP/JSON──►  FastAPI  ──SQLAlchemy──►  PostgreSQL
(Next.js)                (Python)                  (Docker)
Port 3000                Port 8000                 Port 5432
```

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for details.

## Prerequisites

- Python 3.13+
- Node.js 26+
- npm 12+
- Git
- Docker Desktop

## Quick Start

```bash
# 1. Start the database
cp .env.example .env          # then edit .env to set a real password
docker compose up -d

# 2. Start the backend
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # then edit .env with your DB password
uvicorn app.main:app --reload --port 8000

# 3. Start the frontend (in a new terminal)
cd frontend
npm install
cp .env.example .env.local
npm run dev
```

Open http://localhost:3000 in your browser.

## Running Tests

```bash
# Backend
cd backend && source .venv/bin/activate && pytest

# Frontend
cd frontend && npm run lint && npm run build
```

## Current Status

### ✅ Phase 1 — Project Foundation (Complete)
- Git repository initialized
- Backend: FastAPI with health check endpoint (`GET /api/v1/health`)
- Frontend: Next.js shell with dashboard placeholder
- Docker Compose: PostgreSQL 16 configuration
- Documentation: Architecture and development guides

### 🔲 Phase 2 — Product & Category Management
### 🔲 Phase 3 — Batches, Expiry Tracking & Low-Stock Alerts
### 🔲 Phase 4 — Point of Sale & Inventory Transactions
### 🔲 Phase 5 — Supplier Purchases & Restocking
### 🔲 Phase 6 — Sales & Inventory Analytics
### 🔲 Phase 7 — Demand Forecasting
### 🔲 Phase 8 — Deployment

## Development Guide

See [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md) for detailed setup instructions.

## License

This project is for educational and personal use.
