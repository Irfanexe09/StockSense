/**
 * Shared TypeScript types for StockSense.
 *
 * These types mirror the backend Pydantic schemas so the frontend
 * and backend always agree on the shape of data.
 */

/** Response from GET /api/v1/health */
export interface HealthResponse {
  status: string;
  service: string;
  version: string;
  timestamp: string;
}

/** A product category. */
export interface Category {
  id: number;
  name: string;
  description: string | null;
}

/** Payload to create a category. */
export interface CategoryCreate {
  name: string;
  description?: string | null;
}

/** A product in the inventory. */
export interface Product {
  id: number;
  sku: string;
  name: string;
  description: string | null;
  cost_price: number;
  selling_price: number;
  stock_quantity: number;
  reorder_level: number;
  is_low_stock: boolean;
  category_id: number | null;
}

/** Payload to create a product. */
export interface ProductCreate {
  sku: string;
  name: string;
  description?: string | null;
  cost_price: number;
  selling_price: number;
  stock_quantity?: number;
  reorder_level?: number;
  category_id?: number | null;
}

/** Payload to update a product (all fields optional). */
export interface ProductUpdate {
  sku?: string;
  name?: string;
  description?: string | null;
  cost_price?: number;
  selling_price?: number;
  stock_quantity?: number;
  reorder_level?: number;
  category_id?: number | null;
}

/** Paginated product list response from the API. */
export interface PaginatedProducts {
  items: Product[];
  total: number;
}

/** A product lot/batch. */
export interface Batch {
  id: number;
  product_id: number;
  batch_number: string;
  initial_quantity: number;
  quantity: number;
  expiry_date: string | null;
  received_date: string;
  created_at: string;
  is_expired: boolean;
  days_until_expiry: number | null;
  product_name?: string | null;
  product_sku?: string | null;
}

/** Payload to create a batch. */
export interface BatchCreate {
  product_id: number;
  batch_number: string;
  quantity: number;
  expiry_date?: string | null;
  received_date?: string | null;
}

/** Payload to update a batch. */
export interface BatchUpdate {
  batch_number?: string;
  quantity?: number;
  expiry_date?: string | null;
  received_date?: string | null;
}

/** Request payload to deduct stock using FIFO. */
export interface StockDeductRequest {
  quantity: number;
  reason?: string | null;
}

export interface BatchDeductionDetail {
  batch_id: number;
  batch_number: string;
  deducted_quantity: number;
  remaining_in_batch: number;
  expiry_date: string | null;
}

export interface StockDeductResponse {
  product_id: number;
  requested_quantity: number;
  deducted_quantity: number;
  remaining_stock: number;
  batches_affected: BatchDeductionDetail[];
}

export interface AlertsSummaryCounts {
  low_stock_products_count: number;
  expiring_batches_count: number;
  expired_batches_count: number;
}

export interface AlertsSummaryResponse {
  counts: AlertsSummaryCounts;
  low_stock_products: Product[];
  expiring_batches: Batch[];
  expired_batches: Batch[];
}

// ── Sales / Point of Sale ──

/** A single item in a checkout request. */
export interface CheckoutItem {
  product_id: number;
  quantity: number;
  unit_price: number;
}

/** Payload for POST /api/v1/sales/checkout. */
export interface CheckoutRequest {
  items: CheckoutItem[];
}

/** A line item within a completed sale. */
export interface SaleItem {
  id: number;
  product_id: number | null;
  product_name: string;
  product_sku: string;
  quantity: number;
  unit_price: number;
  line_total: number;
}

/** A completed sale with full line-item detail. */
export interface SaleResponse {
  id: number;
  receipt_number: string;
  created_at: string;
  total_amount: number;
  item_count: number;
  items: SaleItem[];
}

/** A sale summary (without line items) for list views. */
export interface SaleListItem {
  id: number;
  receipt_number: string;
  created_at: string;
  total_amount: number;
  item_count: number;
}
