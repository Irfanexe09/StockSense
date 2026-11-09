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
