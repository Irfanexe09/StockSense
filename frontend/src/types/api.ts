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

// ── Suppliers ──

export interface Supplier {
  id: number;
  name: string;
  contact_name: string | null;
  email: string | null;
  phone: string | null;
  address: string | null;
  is_active: boolean;
  created_at: string;
}

export interface SupplierCreate {
  name: string;
  contact_name?: string | null;
  email?: string | null;
  phone?: string | null;
  address?: string | null;
  is_active?: boolean;
}

export interface SupplierUpdate {
  name?: string;
  contact_name?: string | null;
  email?: string | null;
  phone?: string | null;
  address?: string | null;
  is_active?: boolean;
}

// ── Purchase Orders & Receiving ──

export interface PurchaseOrderItemCreate {
  product_id: number;
  quantity: number;
  unit_cost: number;
}

export interface PurchaseOrderItem {
  id: number;
  purchase_order_id: number;
  product_id: number | null;
  product_name: string;
  product_sku: string;
  quantity: number;
  received_quantity: number;
  remaining_quantity: number;
  unit_cost: number;
  line_total: number;
  is_fully_received: boolean;
}

export interface ReceiveItemInput {
  purchase_order_item_id: number;
  quantity_received: number;
  batch_number: string;
  expiry_date?: string | null;
}

export interface ReceiveOrderRequest {
  notes?: string | null;
  items: ReceiveItemInput[];
}

export interface ReceiptItem {
  id: number;
  purchase_order_item_id: number;
  batch_id: number | null;
  quantity_received: number;
  batch_number: string;
  expiry_date: string | null;
}

export interface ReceiptResponse {
  id: number;
  purchase_order_id: number;
  receipt_number: string;
  received_at: string;
  notes: string | null;
  items: ReceiptItem[];
}

export interface PurchaseOrderListItem {
  id: number;
  order_number: string;
  supplier_id: number;
  supplier_name: string | null;
  status: "DRAFT" | "ORDERED" | "PARTIALLY_RECEIVED" | "RECEIVED" | "CANCELLED";
  order_date: string;
  expected_delivery_date: string | null;
  total_amount: number;
  item_count: number;
  created_at: string;
}

export interface PurchaseOrder {
  id: number;
  order_number: string;
  supplier_id: number;
  supplier_name: string | null;
  status: "DRAFT" | "ORDERED" | "PARTIALLY_RECEIVED" | "RECEIVED" | "CANCELLED";
  order_date: string;
  expected_delivery_date: string | null;
  notes: string | null;
  total_amount: number;
  item_count: number;
  created_at: string;
  updated_at: string;
  items: PurchaseOrderItem[];
  receipts: ReceiptResponse[];
}

export interface PurchaseOrderCreate {
  supplier_id: number;
  order_date?: string | null;
  expected_delivery_date?: string | null;
  notes?: string | null;
  submit_now?: boolean;
  items: PurchaseOrderItemCreate[];
}

// ── Sales & Inventory Analytics ──

export interface SalesSummaryKPIs {
  total_revenue: number;
  order_count: number;
  units_sold: number;
  average_order_value: number;
}

export interface DailySalesTrend {
  date: string;
  revenue: number;
  order_count: number;
  units_sold: number;
}

export interface TopSellingProduct {
  product_id: number | null;
  product_name: string;
  product_sku: string;
  units_sold: number;
  total_revenue: number;
  order_count: number;
}

export interface CategorySalesShare {
  category_id: number | null;
  category_name: string;
  units_sold: number;
  total_revenue: number;
  revenue_percentage: number;
}

export interface SalesAnalyticsResponse {
  start_date: string;
  end_date: string;
  summary: SalesSummaryKPIs;
  daily_trends: DailySalesTrend[];
  top_products: TopSellingProduct[];
  category_breakdown: CategorySalesShare[];
}

export interface InventoryValuationSummary {
  total_products_count: number;
  total_stock_units: number;
  total_cost_value: number;
  total_retail_value: number;
  potential_margin_value: number;
  potential_margin_percent: number;
}

export interface LowStockExposure {
  low_stock_products_count: number;
  total_units_deficit: number;
  estimated_restock_cost: number;
}

export interface ExpiryRiskExposure {
  expired_batches_count: number;
  expired_units: number;
  expired_cost_value: number;
  expiring_soon_batches_count: number;
  expiring_soon_units: number;
  expiring_soon_cost_value: number;
}

export interface InventoryAnalyticsResponse {
  valuation: InventoryValuationSummary;
  low_stock_exposure: LowStockExposure;
  expiry_risk: ExpiryRiskExposure;
}
