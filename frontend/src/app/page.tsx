"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { apiFetch } from "@/lib/api";
import { StatusCard } from "@/components/status-card";
import type { AlertsSummaryResponse, PaginatedProducts } from "@/types/api";

export default function DashboardPage() {
  const [alerts, setAlerts] = useState<AlertsSummaryResponse | null>(null);
  const [totalProducts, setTotalProducts] = useState<number>(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [refreshKey, setRefreshKey] = useState(0);

  useEffect(() => {
    let cancelled = false;

    async function loadDashboardData() {
      setLoading(true);
      setError(null);
      try {
        const [alertsData, productsData] = await Promise.all([
          apiFetch<AlertsSummaryResponse>("/api/v1/alerts/"),
          apiFetch<PaginatedProducts>("/api/v1/products/?limit=1"),
        ]);

        if (!cancelled) {
          setAlerts(alertsData);
          setTotalProducts(productsData.total);
        }
      } catch (err) {
        if (!cancelled) {
          setError(
            err instanceof Error ? err.message : "Failed to load dashboard metrics"
          );
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    loadDashboardData();
    return () => {
      cancelled = true;
    };
  }, [refreshKey]);

  return (
    <div className="p-6 sm:p-10">
      <div className="mx-auto max-w-5xl space-y-8">
        {/* Welcome section */}
        <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h1 className="text-3xl font-bold tracking-tight text-zinc-900 dark:text-zinc-50">
              Dashboard
            </h1>
            <p className="text-zinc-600 dark:text-zinc-400">
              Real-time inventory levels, low-stock alerts, and batch expiry tracking.
            </p>
          </div>
          <button
            onClick={() => setRefreshKey((k) => k + 1)}
            disabled={loading}
            className="self-start rounded-md border border-zinc-300 bg-white px-3 py-1.5 text-xs font-medium text-zinc-700 hover:bg-zinc-50 disabled:opacity-50 dark:border-zinc-700 dark:bg-zinc-800 dark:text-zinc-300 dark:hover:bg-zinc-700"
          >
            {loading ? "Refreshing…" : "↻ Refresh"}
          </button>
        </div>

        {/* Loading State Skeleton */}
        {loading && (
          <div className="space-y-4">
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
              {[1, 2, 3, 4].map((i) => (
                <div
                  key={i}
                  className="h-28 animate-pulse rounded-lg border border-zinc-200 bg-zinc-100 dark:border-zinc-800 dark:bg-zinc-900"
                />
              ))}
            </div>
            <div className="h-64 animate-pulse rounded-lg border border-zinc-200 bg-zinc-100 dark:border-zinc-800 dark:bg-zinc-900" />
          </div>
        )}

        {/* Error State */}
        {error && (
          <div className="rounded-lg border border-red-200 bg-red-50 p-6 text-red-700 dark:border-red-900 dark:bg-red-950 dark:text-red-400">
            <h3 className="font-semibold">Unable to load dashboard data</h3>
            <p className="mt-1 text-sm">{error}</p>
            <button
              onClick={() => setRefreshKey((k) => k + 1)}
              className="mt-3 rounded bg-red-600 px-3 py-1.5 text-xs font-medium text-white hover:bg-red-700"
            >
              Retry
            </button>
          </div>
        )}

        {/* Dashboard Content */}
        {!loading && !error && alerts && (
          <>
            {/* KPI Overview Cards */}
            <section className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
              <StatusCard
                title="Total Products"
                value={String(totalProducts)}
                description="Active catalog items"
              />
              <StatusCard
                title="Low Stock"
                value={String(alerts.counts.low_stock_products_count)}
                description={
                  alerts.counts.low_stock_products_count > 0
                    ? "Items at or below reorder level"
                    : "All items well-stocked"
                }
              />
              <StatusCard
                title="Expiring Soon (30d)"
                value={String(alerts.counts.expiring_batches_count)}
                description={
                  alerts.counts.expiring_batches_count > 0
                    ? "Batches near expiry date"
                    : "No batches expiring soon"
                }
              />
              <StatusCard
                title="Expired Batches"
                value={String(alerts.counts.expired_batches_count)}
                description={
                  alerts.counts.expired_batches_count > 0
                    ? "Action required: quarantine/dispose"
                    : "Zero expired stock"
                }
              />
            </section>

            {/* Low-Stock Alerts Section */}
            <section className="space-y-3">
              <div className="flex items-center justify-between">
                <div>
                  <h2 className="text-xl font-bold text-zinc-900 dark:text-zinc-50">
                    Low-Stock Alerts
                  </h2>
                  <p className="text-xs text-zinc-500 dark:text-zinc-400">
                    Products where remaining stock has fallen to or below the reorder threshold.
                  </p>
                </div>
                <Link
                  href="/products"
                  className="text-xs font-medium text-emerald-600 hover:text-emerald-700 dark:text-emerald-400"
                >
                  Manage Products →
                </Link>
              </div>

              {alerts.low_stock_products.length === 0 ? (
                <div className="flex items-center gap-3 rounded-lg border border-emerald-200 bg-emerald-50/60 p-5 text-emerald-800 dark:border-emerald-900/40 dark:bg-emerald-950/20 dark:text-emerald-300">
                  <svg
                    xmlns="http://www.w3.org/2000/svg"
                    className="h-5 w-5 shrink-0 text-emerald-600"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                  >
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                  <p className="text-sm">
                    All product stock levels are healthy! No items are currently below their reorder threshold.
                  </p>
                </div>
              ) : (
                <div className="overflow-x-auto rounded-lg border border-zinc-200 bg-white dark:border-zinc-800 dark:bg-zinc-900">
                  <table className="min-w-full divide-y divide-zinc-200 dark:divide-zinc-800">
                    <thead className="bg-zinc-50 dark:bg-zinc-950">
                      <tr>
                        <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-zinc-500">SKU</th>
                        <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-zinc-500">Product Name</th>
                        <th className="px-4 py-3 text-right text-xs font-medium uppercase tracking-wider text-zinc-500">Current Stock</th>
                        <th className="px-4 py-3 text-right text-xs font-medium uppercase tracking-wider text-zinc-500">Reorder Level</th>
                        <th className="px-4 py-3 text-right text-xs font-medium uppercase tracking-wider text-zinc-500">Action</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-zinc-200 dark:divide-zinc-800">
                      {alerts.low_stock_products.map((p) => (
                        <tr key={p.id} className="hover:bg-zinc-50 dark:hover:bg-zinc-800/50">
                          <td className="whitespace-nowrap px-4 py-3 font-mono text-sm font-semibold text-zinc-800 dark:text-zinc-200">{p.sku}</td>
                          <td className="px-4 py-3 text-sm text-zinc-900 dark:text-zinc-100">{p.name}</td>
                          <td className="whitespace-nowrap px-4 py-3 text-right text-sm">
                            <span className="inline-flex rounded-full bg-red-100 px-2 py-0.5 text-xs font-semibold text-red-700 dark:bg-red-900 dark:text-red-300">
                              {p.stock_quantity} units
                            </span>
                          </td>
                          <td className="whitespace-nowrap px-4 py-3 text-right text-sm text-zinc-500">{p.reorder_level} units</td>
                          <td className="whitespace-nowrap px-4 py-3 text-right text-sm">
                            <Link
                              href="/batches"
                              className="text-xs font-medium text-emerald-600 hover:text-emerald-700 dark:text-emerald-400"
                            >
                              + Add Batch
                            </Link>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </section>

            {/* Expiry Tracking Alerts Section */}
            <section className="space-y-3">
              <div className="flex items-center justify-between">
                <div>
                  <h2 className="text-xl font-bold text-zinc-900 dark:text-zinc-50">
                    Expiry Tracking Alerts
                  </h2>
                  <p className="text-xs text-zinc-500 dark:text-zinc-400">
                    Batches that have expired or will expire within the next 30 days.
                  </p>
                </div>
                <Link
                  href="/batches"
                  className="text-xs font-medium text-emerald-600 hover:text-emerald-700 dark:text-emerald-400"
                >
                  View All Batches →
                </Link>
              </div>

              {alerts.expired_batches.length === 0 && alerts.expiring_batches.length === 0 ? (
                <div className="flex items-center gap-3 rounded-lg border border-emerald-200 bg-emerald-50/60 p-5 text-emerald-800 dark:border-emerald-900/40 dark:bg-emerald-950/20 dark:text-emerald-300">
                  <svg
                    xmlns="http://www.w3.org/2000/svg"
                    className="h-5 w-5 shrink-0 text-emerald-600"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                  >
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                  <p className="text-sm">
                    No batches are expiring soon or expired! All batch expiration dates are in good standing.
                  </p>
                </div>
              ) : (
                <div className="overflow-x-auto rounded-lg border border-zinc-200 bg-white dark:border-zinc-800 dark:bg-zinc-900">
                  <table className="min-w-full divide-y divide-zinc-200 dark:divide-zinc-800">
                    <thead className="bg-zinc-50 dark:bg-zinc-950">
                      <tr>
                        <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-zinc-500">Batch Number</th>
                        <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-zinc-500">Product</th>
                        <th className="px-4 py-3 text-right text-xs font-medium uppercase tracking-wider text-zinc-500">Remaining Qty</th>
                        <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-zinc-500">Expiry Date</th>
                        <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-zinc-500">Status</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-zinc-200 dark:divide-zinc-800">
                      {/* Expired Batches */}
                      {alerts.expired_batches.map((b) => (
                        <tr key={`exp-${b.id}`} className="bg-red-50/40 hover:bg-red-50/80 dark:bg-red-950/20">
                          <td className="whitespace-nowrap px-4 py-3 font-mono text-sm font-semibold text-red-900 dark:text-red-300">{b.batch_number}</td>
                          <td className="px-4 py-3 text-sm text-zinc-900 dark:text-zinc-100">{b.product_name ?? `Product #${b.product_id}`}</td>
                          <td className="whitespace-nowrap px-4 py-3 text-right text-sm font-semibold text-zinc-900 dark:text-zinc-100">{b.quantity} units</td>
                          <td className="whitespace-nowrap px-4 py-3 text-sm text-red-700 dark:text-red-400">{b.expiry_date}</td>
                          <td className="whitespace-nowrap px-4 py-3 text-sm">
                            <span className="inline-flex items-center rounded-full bg-red-100 px-2.5 py-0.5 text-xs font-bold text-red-800 dark:bg-red-900 dark:text-red-200">
                              Expired {b.days_until_expiry !== null ? `(${Math.abs(b.days_until_expiry)}d ago)` : ""}
                            </span>
                          </td>
                        </tr>
                      ))}

                      {/* Expiring Soon Batches */}
                      {alerts.expiring_batches.map((b) => (
                        <tr key={`soon-${b.id}`} className="hover:bg-amber-50/30 dark:hover:bg-amber-950/20">
                          <td className="whitespace-nowrap px-4 py-3 font-mono text-sm font-medium text-zinc-800 dark:text-zinc-200">{b.batch_number}</td>
                          <td className="px-4 py-3 text-sm text-zinc-900 dark:text-zinc-100">{b.product_name ?? `Product #${b.product_id}`}</td>
                          <td className="whitespace-nowrap px-4 py-3 text-right text-sm text-zinc-900 dark:text-zinc-100">{b.quantity} units</td>
                          <td className="whitespace-nowrap px-4 py-3 text-sm text-amber-800 dark:text-amber-300">{b.expiry_date}</td>
                          <td className="whitespace-nowrap px-4 py-3 text-sm">
                            <span className="inline-flex items-center rounded-full bg-amber-100 px-2.5 py-0.5 text-xs font-semibold text-amber-800 dark:bg-amber-900 dark:text-amber-200">
                              {b.days_until_expiry === 0
                                ? "Expires Today"
                                : `Expires in ${b.days_until_expiry} days`}
                            </span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </section>
          </>
        )}
      </div>
    </div>
  );
}
