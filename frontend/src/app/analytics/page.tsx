"use client";

import { useEffect, useState } from "react";
import { apiFetch } from "@/lib/api";
import { StatusCard } from "@/components/status-card";
import type {
  InventoryAnalyticsResponse,
  SalesAnalyticsResponse,
} from "@/types/api";

export default function AnalyticsPage() {
  const [salesData, setSalesData] = useState<SalesAnalyticsResponse | null>(null);
  const [inventoryData, setInventoryData] = useState<InventoryAnalyticsResponse | null>(null);

  const [preset, setPreset] = useState<string>("30d");
  const [customStart, setCustomStart] = useState<string>("");
  const [customEnd, setCustomEnd] = useState<string>("");

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [refreshKey, setRefreshKey] = useState(0);

  const [trendViewMode, setTrendViewMode] = useState<"chart" | "table">("chart");

  useEffect(() => {
    let cancelled = false;

    async function loadAnalytics() {
      setLoading(true);
      setError(null);
      try {
        const salesParams = new URLSearchParams({ preset });
        if (preset === "custom") {
          if (!customStart || !customEnd) {
            setLoading(false);
            return;
          }
          salesParams.set("start_date", customStart);
          salesParams.set("end_date", customEnd);
        }

        const [salesRes, invRes] = await Promise.all([
          apiFetch<SalesAnalyticsResponse>(`/api/v1/analytics/sales?${salesParams.toString()}`),
          apiFetch<InventoryAnalyticsResponse>("/api/v1/analytics/inventory"),
        ]);

        if (!cancelled) {
          setSalesData(salesRes);
          setInventoryData(invRes);
        }
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : "Failed to load analytics");
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    loadAnalytics();
    return () => {
      cancelled = true;
    };
  }, [preset, customStart, customEnd, refreshKey]);

  // Find max daily revenue for chart scaling
  const maxDailyRevenue = salesData?.daily_trends
    ? Math.max(...salesData.daily_trends.map((t) => Number(t.revenue)), 1)
    : 1;

  return (
    <div className="p-6 sm:p-10">
      <div className="mx-auto max-w-6xl space-y-8">
        {/* Header and Controls */}
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h1 className="text-3xl font-bold tracking-tight text-zinc-900 dark:text-zinc-50">
              Sales & Inventory Analytics
            </h1>
            <p className="text-zinc-600 dark:text-zinc-400">
              Revenue metrics, order trends, product performance, and stock valuation.
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-2">
            <button
              onClick={() => setRefreshKey((k) => k + 1)}
              disabled={loading}
              className="rounded-md border border-zinc-300 bg-white px-3 py-1.5 text-xs font-medium text-zinc-700 hover:bg-zinc-50 disabled:opacity-50 dark:border-zinc-700 dark:bg-zinc-800 dark:text-zinc-300 dark:hover:bg-zinc-700"
            >
              {loading ? "Refreshing…" : "↻ Refresh"}
            </button>
          </div>
        </div>

        {/* Date Range Presets */}
        <div className="flex flex-wrap items-center gap-2 rounded-lg border border-zinc-200 bg-white p-3 dark:border-zinc-800 dark:bg-zinc-900">
          <span className="text-xs font-medium text-zinc-500 dark:text-zinc-400">Date Range:</span>
          {[
            { label: "Today", value: "today" },
            { label: "Last 7 Days", value: "7d" },
            { label: "Last 30 Days", value: "30d" },
            { label: "Last 90 Days", value: "90d" },
            { label: "All Time", value: "all" },
            { label: "Custom", value: "custom" },
          ].map((tab) => (
            <button
              key={tab.value}
              onClick={() => setPreset(tab.value)}
              className={`rounded-full px-3 py-1 text-xs font-medium transition-colors ${
                preset === tab.value
                  ? "bg-emerald-600 text-white"
                  : "bg-zinc-100 text-zinc-600 hover:bg-zinc-200 dark:bg-zinc-800 dark:text-zinc-300"
              }`}
            >
              {tab.label}
            </button>
          ))}

          {preset === "custom" && (
            <div className="mt-2 flex flex-wrap items-center gap-2 sm:ml-4 sm:mt-0">
              <input
                type="date"
                value={customStart}
                onChange={(e) => setCustomStart(e.target.value)}
                className="rounded border border-zinc-300 bg-white px-2 py-1 text-xs dark:border-zinc-700 dark:bg-zinc-800 dark:text-zinc-100"
              />
              <span className="text-xs text-zinc-400">to</span>
              <input
                type="date"
                value={customEnd}
                onChange={(e) => setCustomEnd(e.target.value)}
                className="rounded border border-zinc-300 bg-white px-2 py-1 text-xs dark:border-zinc-700 dark:bg-zinc-800 dark:text-zinc-100"
              />
            </div>
          )}

          {salesData && (
            <span className="ml-auto text-xs text-zinc-400">
              Period: {salesData.start_date} → {salesData.end_date}
            </span>
          )}
        </div>

        {/* Loading state */}
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

        {/* Error state */}
        {error && (
          <div className="rounded-lg border border-red-200 bg-red-50 p-6 text-red-700 dark:border-red-900 dark:bg-red-950 dark:text-red-400">
            <h3 className="font-semibold">Unable to load analytics</h3>
            <p className="mt-1 text-sm">{error}</p>
            <button
              onClick={() => setRefreshKey((k) => k + 1)}
              className="mt-3 rounded bg-red-600 px-3 py-1.5 text-xs font-medium text-white hover:bg-red-700"
            >
              Retry
            </button>
          </div>
        )}

        {!loading && !error && salesData && (
          <>
            {/* Sales Summary KPI Cards */}
            <section className="space-y-3">
              <h2 className="text-lg font-bold text-zinc-900 dark:text-zinc-50">
                Sales Overview
              </h2>
              <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
                <StatusCard
                  title="Total Revenue"
                  value={`$${Number(salesData.summary.total_revenue).toFixed(2)}`}
                  description="Gross sales across completed transactions"
                />
                <StatusCard
                  title="Completed Orders"
                  value={String(salesData.summary.order_count)}
                  description="Number of POS sales receipts"
                />
                <StatusCard
                  title="Units Sold"
                  value={String(salesData.summary.units_sold)}
                  description="Total individual product items sold"
                />
                <StatusCard
                  title="Average Order Value"
                  value={`$${Number(salesData.summary.average_order_value).toFixed(2)}`}
                  description="Mean revenue per transaction"
                />
              </div>
            </section>

            {/* Daily Trends Section */}
            <section className="space-y-3 rounded-lg border border-zinc-200 bg-white p-5 shadow-sm dark:border-zinc-800 dark:bg-zinc-900">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-base font-bold text-zinc-900 dark:text-zinc-50">
                    Daily Sales Trends
                  </h3>
                  <p className="text-xs text-zinc-500">
                    Revenue and transaction volume over the selected timeframe.
                  </p>
                </div>
                <div className="flex items-center gap-1 rounded bg-zinc-100 p-0.5 dark:bg-zinc-800">
                  <button
                    onClick={() => setTrendViewMode("chart")}
                    className={`rounded px-2.5 py-1 text-xs font-medium transition-colors ${
                      trendViewMode === "chart"
                        ? "bg-white text-zinc-900 shadow dark:bg-zinc-700 dark:text-zinc-50"
                        : "text-zinc-500 hover:text-zinc-800 dark:text-zinc-400"
                    }`}
                  >
                    Chart
                  </button>
                  <button
                    onClick={() => setTrendViewMode("table")}
                    className={`rounded px-2.5 py-1 text-xs font-medium transition-colors ${
                      trendViewMode === "table"
                        ? "bg-white text-zinc-900 shadow dark:bg-zinc-700 dark:text-zinc-50"
                        : "text-zinc-500 hover:text-zinc-800 dark:text-zinc-400"
                    }`}
                  >
                    Table
                  </button>
                </div>
              </div>

              {salesData.daily_trends.length === 0 ? (
                <div className="py-8 text-center text-sm text-zinc-400">
                  No sales recorded in this period.
                </div>
              ) : trendViewMode === "chart" ? (
                <div className="space-y-2 pt-4">
                  {/* Visual Bar Chart */}
                  <div className="flex h-48 items-end gap-1 overflow-x-auto border-b border-zinc-200 pb-2 pt-6 dark:border-zinc-800">
                    {salesData.daily_trends.map((t) => {
                      const heightPercent =
                        Number(t.revenue) > 0
                          ? Math.max(8, (Number(t.revenue) / maxDailyRevenue) * 100)
                          : 4;
                      return (
                        <div
                          key={t.date}
                          className="group relative flex min-w-[28px] flex-1 flex-col items-center justify-end"
                        >
                          {/* Tooltip */}
                          <div className="pointer-events-none absolute -top-12 z-20 hidden flex-col items-center rounded bg-zinc-900 px-2 py-1 text-[11px] text-white shadow-lg group-hover:flex dark:bg-zinc-100 dark:text-zinc-900">
                            <span className="font-semibold">${Number(t.revenue).toFixed(2)}</span>
                            <span className="text-[10px] opacity-80">{t.units_sold} units · {t.order_count} orders</span>
                          </div>

                          <div
                            style={{ height: `${heightPercent}%` }}
                            className={`w-full max-w-[40px] rounded-t transition-all ${
                              Number(t.revenue) > 0
                                ? "bg-emerald-500 hover:bg-emerald-600 dark:bg-emerald-600 dark:hover:bg-emerald-500"
                                : "bg-zinc-200 dark:bg-zinc-800"
                            }`}
                          />
                          <span className="mt-1 text-[10px] text-zinc-400">
                            {t.date.slice(5)}
                          </span>
                        </div>
                      );
                    })}
                  </div>
                  <div className="flex justify-between text-xs text-zinc-400">
                    <span>{salesData.start_date}</span>
                    <span>Daily Volume</span>
                    <span>{salesData.end_date}</span>
                  </div>
                </div>
              ) : (
                <div className="max-h-64 overflow-y-auto">
                  <table className="min-w-full divide-y divide-zinc-200 text-xs dark:divide-zinc-800">
                    <thead className="bg-zinc-50 dark:bg-zinc-950">
                      <tr>
                        <th className="px-3 py-2 text-left font-medium text-zinc-500">Date</th>
                        <th className="px-3 py-2 text-right font-medium text-zinc-500">Orders</th>
                        <th className="px-3 py-2 text-right font-medium text-zinc-500">Units Sold</th>
                        <th className="px-3 py-2 text-right font-medium text-zinc-500">Revenue</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-zinc-200 dark:divide-zinc-800">
                      {salesData.daily_trends.map((t) => (
                        <tr key={t.date}>
                          <td className="px-3 py-1.5 font-medium text-zinc-800 dark:text-zinc-200">{t.date}</td>
                          <td className="px-3 py-1.5 text-right text-zinc-600 dark:text-zinc-400">{t.order_count}</td>
                          <td className="px-3 py-1.5 text-right text-zinc-600 dark:text-zinc-400">{t.units_sold}</td>
                          <td className="px-3 py-1.5 text-right font-semibold text-zinc-900 dark:text-zinc-100">
                            ${Number(t.revenue).toFixed(2)}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </section>

            {/* Top Products & Category Breakdown */}
            <div className="grid gap-6 lg:grid-cols-2">
              {/* Top Products Leaderboard */}
              <div className="space-y-3 rounded-lg border border-zinc-200 bg-white p-5 shadow-sm dark:border-zinc-800 dark:bg-zinc-900">
                <h3 className="text-base font-bold text-zinc-900 dark:text-zinc-50">
                  Top-Selling Products
                </h3>
                {salesData.top_products.length === 0 ? (
                  <p className="py-6 text-center text-xs text-zinc-400">
                    No sales recorded in this period.
                  </p>
                ) : (
                  <div className="overflow-x-auto">
                    <table className="min-w-full divide-y divide-zinc-200 text-xs dark:divide-zinc-800">
                      <thead>
                        <tr>
                          <th className="px-3 py-2 text-left font-medium text-zinc-500">Product</th>
                          <th className="px-3 py-2 text-right font-medium text-zinc-500">Units</th>
                          <th className="px-3 py-2 text-right font-medium text-zinc-500">Revenue</th>
                          <th className="px-3 py-2 text-right font-medium text-zinc-500">Orders</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-zinc-200 dark:divide-zinc-800">
                        {salesData.top_products.map((p, idx) => (
                          <tr key={idx} className="hover:bg-zinc-50 dark:hover:bg-zinc-800/40">
                            <td className="px-3 py-2">
                              <div className="font-semibold text-zinc-900 dark:text-zinc-100">{p.product_name}</div>
                              <div className="font-mono text-[11px] text-zinc-400">{p.product_sku}</div>
                            </td>
                            <td className="px-3 py-2 text-right font-semibold text-emerald-600 dark:text-emerald-400">
                              {p.units_sold}
                            </td>
                            <td className="px-3 py-2 text-right font-bold text-zinc-900 dark:text-zinc-100">
                              ${Number(p.total_revenue).toFixed(2)}
                            </td>
                            <td className="px-3 py-2 text-right text-zinc-500">
                              {p.order_count}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>

              {/* Category Revenue Breakdown */}
              <div className="space-y-3 rounded-lg border border-zinc-200 bg-white p-5 shadow-sm dark:border-zinc-800 dark:bg-zinc-900">
                <h3 className="text-base font-bold text-zinc-900 dark:text-zinc-50">
                  Category Breakdown
                </h3>
                {salesData.category_breakdown.length === 0 ? (
                  <p className="py-6 text-center text-xs text-zinc-400">
                    No sales recorded in this period.
                  </p>
                ) : (
                  <div className="space-y-4 pt-1">
                    {salesData.category_breakdown.map((cat, idx) => (
                      <div key={idx} className="space-y-1">
                        <div className="flex items-center justify-between text-xs">
                          <span className="font-semibold text-zinc-800 dark:text-zinc-200">
                            {cat.category_name}
                          </span>
                          <span className="text-zinc-500">
                            ${Number(cat.total_revenue).toFixed(2)} ({cat.revenue_percentage}%)
                          </span>
                        </div>
                        <div className="h-2 w-full overflow-hidden rounded-full bg-zinc-100 dark:bg-zinc-800">
                          <div
                            style={{ width: `${Math.min(100, cat.revenue_percentage)}%` }}
                            className="h-full rounded-full bg-emerald-500"
                          />
                        </div>
                        <div className="text-[11px] text-zinc-400">
                          {cat.units_sold} units sold
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>

            {/* Inventory Valuation & Exposure Section */}
            {inventoryData && (
              <section className="space-y-4 pt-2">
                <div className="flex flex-col gap-1 sm:flex-row sm:items-center sm:justify-between">
                  <div>
                    <h2 className="text-lg font-bold text-zinc-900 dark:text-zinc-50">
                      Inventory Valuation & Exposure
                    </h2>
                    <p className="text-xs text-zinc-500">
                      Calculated from current on-hand units and catalog pricing.
                    </p>
                  </div>
                </div>

                <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
                  <StatusCard
                    title="Total Stock Units"
                    value={String(inventoryData.valuation.total_stock_units)}
                    description={`Across ${inventoryData.valuation.total_products_count} catalog products`}
                  />
                  <StatusCard
                    title="Stock Cost Value"
                    value={`$${Number(inventoryData.valuation.total_cost_value).toFixed(2)}`}
                    description="Current cost investment in on-hand inventory"
                  />
                  <StatusCard
                    title="Stock Retail Value"
                    value={`$${Number(inventoryData.valuation.total_retail_value).toFixed(2)}`}
                    description="Expected revenue at current selling prices"
                  />
                  <StatusCard
                    title="Potential Gross Margin"
                    value={`${inventoryData.valuation.potential_margin_percent}%`}
                    description={`$${Number(inventoryData.valuation.potential_margin_value).toFixed(2)} projected spread`}
                  />
                </div>

                {/* Exposure Cards */}
                <div className="grid gap-4 sm:grid-cols-2">
                  <div className="rounded-lg border border-amber-200 bg-amber-50/50 p-4 dark:border-amber-900/40 dark:bg-amber-950/20">
                    <h4 className="text-sm font-bold text-amber-900 dark:text-amber-300">
                      Low-Stock Restock Exposure
                    </h4>
                    <p className="mt-1 text-xs text-amber-800 dark:text-amber-400">
                      {inventoryData.low_stock_exposure.low_stock_products_count} product(s) at or below reorder threshold.
                    </p>
                    <div className="mt-3 flex items-center justify-between border-t border-amber-200 pt-2 text-xs text-amber-900 dark:border-amber-900 dark:text-amber-200">
                      <span>Total Deficit Units: <b>{inventoryData.low_stock_exposure.total_units_deficit}</b></span>
                      <span>Estimated Restock Cost: <b>${Number(inventoryData.low_stock_exposure.estimated_restock_cost).toFixed(2)}</b></span>
                    </div>
                  </div>

                  <div className="rounded-lg border border-red-200 bg-red-50/50 p-4 dark:border-red-900/40 dark:bg-red-950/20">
                    <h4 className="text-sm font-bold text-red-900 dark:text-red-300">
                      Batch Expiry Exposure
                    </h4>
                    <p className="mt-1 text-xs text-red-800 dark:text-red-400">
                      Expired: {inventoryData.expiry_risk.expired_units} units (${Number(inventoryData.expiry_risk.expired_cost_value).toFixed(2)} at cost).
                    </p>
                    <div className="mt-3 flex items-center justify-between border-t border-red-200 pt-2 text-xs text-red-900 dark:border-red-900 dark:text-red-200">
                      <span>Expiring in 30d: <b>{inventoryData.expiry_risk.expiring_soon_units} units</b></span>
                      <span>At-Risk Cost: <b>${Number(inventoryData.expiry_risk.expiring_soon_cost_value).toFixed(2)}</b></span>
                    </div>
                  </div>
                </div>
              </section>
            )}
          </>
        )}
      </div>
    </div>
  );
}
