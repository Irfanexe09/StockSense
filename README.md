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

### ✅ Phase 2 — Product & Category Management (Complete)
- Database models: Category and Product with SQLAlchemy 2
- Full CRUD API endpoints for categories and products
- Search by name/SKU, filter by category, low-stock filter
- Pydantic schema validation on all inputs
- Frontend: Products page with table, search, filters, and add form
- Frontend: Categories page with list and add/delete
- Sidebar navigation between Dashboard, Products, and Categories
- 21 automated backend tests (SQLite in-memory)

### ✅ Phase 3 — Batches, Expiry Tracking & Low-Stock Alerts (Complete)
- Database model: Batch with quantity, initial_quantity, received_date, and optional expiry_date
- Alembic database migration with automatic backfill for existing stock
- Full CRUD API for batches and expiry status calculation
- FIFO stock deduction engine prioritizing earliest-expiring batches, followed by non-expiring batches by receipt date
- Atomic stock deduction and strict insufficient stock validation (HTTP 400 error rollback)
- Inventory alerts summary API (`/api/v1/alerts/`) detecting low-stock products and expiring/expired batches
- Frontend: Real-time dashboard with active KPI badges, low-stock alerts table, and expiry warnings
- Frontend: Dedicated Batches & Expiry page with filtering, new batch creation, and FIFO deduction tool
- 30 automated backend tests with 100% pass rate

### ✅ Phase 4 — Point of Sale & Inventory Transactions (Complete)
- Database models: Sale (with unique receipt numbers) and SaleItem (with product snapshots)
- Alembic migration `0002_add_sales` for sales and sale_items tables
- Atomic checkout API (`POST /api/v1/sales/checkout`): validates cart, verifies prices, deducts stock via FIFO, records sale — full rollback on any failure
- Backward-compatible refactor of `deduct_stock_fifo` with `commit` parameter for transactional multi-item deductions
- Sale retrieval: `GET /api/v1/sales/` (list) and `GET /api/v1/sales/{id}` (detail with line items)
- Frontend: Point of Sale page with product search, cart management, quantity controls, live totals, checkout confirmation, and success receipt display
- Frontend: Sales History page with sortable list and receipt detail modal
- Sidebar navigation updated with Point of Sale and Sales History
- 45 automated backend tests (15 new: checkout success, multi-item, FIFO, rollback, validation, totals, history)

### ✅ Phase 5 — Supplier Purchases & Restocking (Complete)
- Database models: Supplier, PurchaseOrder (unique PO number), PurchaseOrderItem, PurchaseOrderReceipt, and PurchaseOrderReceiptItem
- Alembic migration `0003_add_suppliers_and_purchases`
- Purchase order lifecycle: DRAFT, ORDERED, PARTIALLY_RECEIVED, RECEIVED, and CANCELLED
- Atomic inventory receiving: creates Batches with received quantities, costs, and optional expiry dates; synchronizes `Product.stock_quantity`
- Strict receiving safeguards: prevents over-receiving, blocks receiving cancelled/draft orders, prohibits cancellation once stock is received
- Suppliers API (`/api/v1/suppliers/`) and Purchase Orders API (`/api/v1/purchase-orders/`)
- Frontend: Suppliers management page (vendor directory, active/inactive toggle, register modal)
- Frontend: Purchases page with status filter tabs, new PO creation modal, detailed PO inspection, and receipt modal
- Sidebar navigation updated with Suppliers and Purchases
- 66 automated backend tests (21 new: supplier validation, PO totals, partial/full receiving, over-receipt rejection, batch creation, status transitions)

### 🔲 Phase 6 — Sales & Inventory Analytics
### 🔲 Phase 6 — Sales & Inventory Analytics
### 🔲 Phase 7 — Demand Forecasting
### 🔲 Phase 8 — Deployment

## Development Guide

See [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md) for detailed setup instructions.

## License

This project is for educational and personal use.
