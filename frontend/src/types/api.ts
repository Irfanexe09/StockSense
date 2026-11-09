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
