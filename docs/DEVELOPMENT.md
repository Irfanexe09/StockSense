# StockSense Development Guide

## Prerequisites

| Tool       | Required Version | Check Command       |
| ---------- | ---------------- | ------------------- |
| Python     | 3.13+            | `python3 --version` |
| Node.js    | 26+              | `node -v`           |
| npm        | 12+              | `npm -v`            |
| Git        | 2.40+            | `git --version`     |
| Docker     | 20+              | `docker --version`  |

## Initial Setup

### 1. Clone the repository

```bash
cd ~/Desktop
git clone <repository-url> StockSense
cd StockSense
```

### 2. Start the database

Make sure Docker Desktop is running, then:

```bash
# Copy the environment file and set a real password
cp .env.example .env
# Edit .env and change POSTGRES_PASSWORD

# Start PostgreSQL
docker compose up -d

# Verify it's healthy
docker compose ps
```

### 3. Set up the backend

```bash
cd backend

# Create a Python virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Copy and configure backend environment
cp .env.example .env
# Edit .env and update DATABASE_URL with your password

# Apply database migrations
alembic upgrade head
```

> **Migration history:**
>
> | Revision | Description |
> |---|---|
> | `0001_initial_and_batches` | Creates categories, products, and batches tables with stock backfill |
> | `0002_add_sales` | Creates sales and sale_items tables for POS checkout |

### 4. Set up the frontend

```bash
cd frontend

# Install Node.js dependencies
npm install

# Copy environment file
cp .env.example .env.local
```

## Running the Application

### Backend

```bash
cd backend
source .venv/bin/activate
uvicorn app.main:app --reload --port 8000
```

The API will be available at http://localhost:8000.
Interactive API docs: http://localhost:8000/docs

### Frontend

```bash
cd frontend
npm run dev
```

The app will be available at http://localhost:3000.

## Running Tests

### Backend

```bash
cd backend
source .venv/bin/activate
pytest
```

### Frontend

```bash
cd frontend
npm run lint
npm run build
```

## Stopping the Database

```bash
# Stop PostgreSQL but keep data
docker compose down

# Stop and DELETE all data (use with caution)
docker compose down -v
```

## Project Structure

```
StockSense/
├── backend/          Python FastAPI application
│   ├── app/          Application source code
│   │   ├── api/      API endpoint routers
│   │   ├── core/     Configuration and shared setup
│   │   ├── models/   SQLAlchemy database models
│   │   ├── schemas/  Pydantic validation schemas
│   │   ├── services/ Business logic
│   │   └── utils/    Helper utilities
│   └── tests/        Automated test suite
├── frontend/         Next.js application
│   └── src/
│       ├── app/       Next.js App Router pages
│       ├── components/ Reusable React components
│       ├── lib/       Utility functions and API client
│       └── types/     TypeScript type definitions
└── docs/             Project documentation
```
