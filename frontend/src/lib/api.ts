/**
 * Central API configuration.
 *
 * The backend URL is read from the NEXT_PUBLIC_API_URL environment variable.
 * In local development this defaults to http://localhost:8000.
 *
 * Usage:
 *   import { apiUrl } from "@/lib/api";
 *   const res = await fetch(`${apiUrl}/api/v1/health`);
 */

export const apiUrl: string =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

/**
 * Typed wrapper around fetch that calls the StockSense backend.
 * Automatically prepends the API base URL.
 */
export async function apiFetch<T>(
  path: string,
  options?: RequestInit,
): Promise<T> {
  const url = `${apiUrl}${path}`;
  const response = await fetch(url, {
    headers: { "Content-Type": "application/json", ...options?.headers },
    ...options,
  });

  if (!response.ok) {
    throw new Error(`API error: ${response.status} ${response.statusText}`);
  }

  return response.json() as Promise<T>;
}
