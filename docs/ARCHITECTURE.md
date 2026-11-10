# StockSense Architecture

## Overview

StockSense is a three-tier web application for small retail inventory management.

```
┌─────────────────┐     HTTP/JSON     ┌─────────────────┐     SQL      ┌──────────────┐
│                 │  ◄──────────────► │                 │ ◄──────────► │              │
│   Next.js App   │   REST API (v1)   │  FastAPI Server │  SQLAlchemy  │  PostgreSQL  │
│   (Frontend)    │                   │  (Backend)      │              │  (Database)  │
│   Port 3000     │                   │  Port 8000      │              │  Port 5432   │
└─────────────────┘                   └─────────────────┘              └──────────────┘
```

## Frontend (Next.js)

- **Framework**: Next.js 16 with App Router
- **Language**: TypeScript (strict mode)
- **Styling**: Tailwind CSS 4
- **Directory**: `frontend/`

The frontend runs in the user's browser. It sends HTTP requests to the backend API and renders the responses. It never talks to the database directly.

## Backend (FastAPI)

- **Framework**: FastAPI
- **Language**: Python 3.13
- **ORM**: SQLAlchemy 2.0
- **Migrations**: Alembic
- **Directory**: `backend/`

The backend receives HTTP requests, validates input with Pydantic schemas, applies business rules, and reads/writes data through SQLAlchemy.

### API Versioning

All endpoints are prefixed with `/api/v1/`. This allows us to introduce `/api/v2/` in the future without breaking existing clients.

## Database (PostgreSQL)

- **Version**: PostgreSQL 16
- **Local setup**: Docker Compose (`docker-compose.yml`)

PostgreSQL stores all persistent data: products, batches, sales, purchases, and audit logs.

## Key Design Decisions

1. **Monorepo structure** — Frontend and backend live in the same repository for easy version tracking, but they are fully independent applications.
2. **Environment variables** — All secrets and configuration are read from `.env` files, never hardcoded.
3. **CORS middleware** — The backend explicitly allows requests from the frontend origin to avoid browser security blocks.
4. **Lot/Batch Inventory & FIFO** — Products track total inventory, but stock is physically organized in lots/batches (`batches` table). When stock is deducted, the system consumes the earliest-expiring batch first (FEFO/FIFO). If no expiry date is set, the oldest batch by receipt date is used. `Product.stock_quantity` is kept in sync with the sum of batch quantities.
5. **Atomic Checkout** — The Point-of-Sale checkout validates every cart item, deducts stock via FIFO for each product, and records the sale with line items in a single database transaction. If any item fails (insufficient stock, invalid product, price mismatch), the entire transaction is rolled back — no partial sales occur. The `deduct_stock_fifo` function accepts a `commit=False` parameter so the checkout service can defer the commit until all items have been processed.
6. **Product Snapshots in Sales** — Each `SaleItem` stores a copy of the product name, SKU, and unit price at the time of purchase. This means sale records remain accurate even if a product is later renamed, repriced, or deleted.
