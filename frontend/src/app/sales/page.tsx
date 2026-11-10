"use client";

import { useEffect, useState } from "react";
import { apiFetch } from "@/lib/api";
import type { SaleListItem, SaleResponse } from "@/types/api";

export default function SalesPage() {
  const [sales, setSales] = useState<SaleListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [refreshKey, setRefreshKey] = useState(0);

  // Detail modal state
  const [selectedSale, setSelectedSale] = useState<SaleResponse | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);

  useEffect(() => {
    let cancelled = false;

    async function loadSales() {
      setLoading(true);
      setError(null);
      try {
        const data = await apiFetch<SaleListItem[]>("/api/v1/sales/?limit=100");
        if (!cancelled) setSales(data);
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : "Failed to load sales");
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    loadSales();
    return () => {
      cancelled = true;
    };
  }, [refreshKey]);

  async function viewSaleDetail(saleId: number) {
    setDetailLoading(true);
    try {
      const sale = await apiFetch<SaleResponse>(`/api/v1/sales/${saleId}`);
      setSelectedSale(sale);
    } catch {
      // silently ignore; user can retry
    } finally {
      setDetailLoading(false);
    }
  }

  return (
    <div className="p-6 sm:p-10">
      <div className="mx-auto max-w-5xl space-y-6">
        {/* Header */}
        <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h1 className="text-3xl font-bold tracking-tight text-zinc-900 dark:text-zinc-50">
              Sales History
            </h1>
            <p className="text-zinc-600 dark:text-zinc-400">
              View completed sales transactions and receipts.
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

        {/* Loading skeleton */}
        {loading && (
          <div className="space-y-2">
            {[1, 2, 3].map((i) => (
              <div
                key={i}
                className="h-14 animate-pulse rounded-lg border border-zinc-200 bg-zinc-100 dark:border-zinc-800 dark:bg-zinc-900"
              />
            ))}
          </div>
        )}

        {/* Error */}
        {error && (
          <div className="rounded-lg border border-red-200 bg-red-50 p-6 text-red-700 dark:border-red-900 dark:bg-red-950 dark:text-red-400">
            <h3 className="font-semibold">Unable to load sales data</h3>
            <p className="mt-1 text-sm">{error}</p>
            <button
              onClick={() => setRefreshKey((k) => k + 1)}
              className="mt-3 rounded bg-red-600 px-3 py-1.5 text-xs font-medium text-white hover:bg-red-700"
            >
              Retry
            </button>
          </div>
        )}

        {/* Empty state */}
        {!loading && !error && sales.length === 0 && (
          <div className="rounded-lg border border-zinc-200 bg-zinc-50 p-8 text-center dark:border-zinc-800 dark:bg-zinc-900">
            <p className="text-sm text-zinc-500 dark:text-zinc-400">
              No sales recorded yet. Complete a checkout from the{" "}
              <a href="/pos" className="font-medium text-emerald-600 underline hover:text-emerald-700">
                Point of Sale
              </a>{" "}
              page.
            </p>
          </div>
        )}

        {/* Sales Table */}
        {!loading && !error && sales.length > 0 && (
          <div className="overflow-x-auto rounded-lg border border-zinc-200 bg-white dark:border-zinc-800 dark:bg-zinc-900">
            <table className="min-w-full divide-y divide-zinc-200 dark:divide-zinc-800">
              <thead className="bg-zinc-50 dark:bg-zinc-950">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-zinc-500">Receipt #</th>
                  <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-zinc-500">Date & Time</th>
                  <th className="px-4 py-3 text-right text-xs font-medium uppercase tracking-wider text-zinc-500">Items</th>
                  <th className="px-4 py-3 text-right text-xs font-medium uppercase tracking-wider text-zinc-500">Total</th>
                  <th className="px-4 py-3 text-right text-xs font-medium uppercase tracking-wider text-zinc-500">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-zinc-200 dark:divide-zinc-800">
                {sales.map((sale) => (
                  <tr key={sale.id} className="hover:bg-zinc-50 dark:hover:bg-zinc-800/50">
                    <td className="whitespace-nowrap px-4 py-3 font-mono text-sm font-semibold text-zinc-800 dark:text-zinc-200">
                      {sale.receipt_number}
                    </td>
                    <td className="whitespace-nowrap px-4 py-3 text-sm text-zinc-600 dark:text-zinc-400">
                      {new Date(sale.created_at).toLocaleString()}
                    </td>
                    <td className="whitespace-nowrap px-4 py-3 text-right text-sm text-zinc-900 dark:text-zinc-100">
                      {sale.item_count}
                    </td>
                    <td className="whitespace-nowrap px-4 py-3 text-right text-sm font-bold text-zinc-900 dark:text-zinc-100">
                      ${Number(sale.total_amount).toFixed(2)}
                    </td>
                    <td className="whitespace-nowrap px-4 py-3 text-right">
                      <button
                        onClick={() => viewSaleDetail(sale.id)}
                        disabled={detailLoading}
                        className="text-xs font-medium text-emerald-600 hover:text-emerald-700 dark:text-emerald-400"
                      >
                        View Details
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* Sale Detail Modal */}
        {selectedSale && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
            <div className="w-full max-w-lg rounded-lg border border-zinc-200 bg-white p-6 shadow-xl dark:border-zinc-700 dark:bg-zinc-900">
              <div className="flex items-center justify-between">
                <h3 className="text-lg font-bold text-zinc-900 dark:text-zinc-50">
                  Receipt {selectedSale.receipt_number}
                </h3>
                <button
                  onClick={() => setSelectedSale(null)}
                  className="text-zinc-400 hover:text-zinc-600"
                >
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>
              <p className="mt-1 text-xs text-zinc-500">
                {new Date(selectedSale.created_at).toLocaleString()}
              </p>

              <div className="mt-4 overflow-x-auto rounded-lg border border-zinc-200 dark:border-zinc-700">
                <table className="min-w-full divide-y divide-zinc-200 dark:divide-zinc-700">
                  <thead className="bg-zinc-50 dark:bg-zinc-800">
                    <tr>
                      <th className="px-3 py-2 text-left text-xs font-medium uppercase text-zinc-500">Product</th>
                      <th className="px-3 py-2 text-right text-xs font-medium uppercase text-zinc-500">Qty</th>
                      <th className="px-3 py-2 text-right text-xs font-medium uppercase text-zinc-500">Price</th>
                      <th className="px-3 py-2 text-right text-xs font-medium uppercase text-zinc-500">Total</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-zinc-200 dark:divide-zinc-700">
                    {selectedSale.items.map((item) => (
                      <tr key={item.id}>
                        <td className="px-3 py-2 text-sm">
                          <div className="text-zinc-900 dark:text-zinc-100">{item.product_name}</div>
                          <div className="font-mono text-xs text-zinc-500">{item.product_sku}</div>
                        </td>
                        <td className="px-3 py-2 text-right text-sm text-zinc-900 dark:text-zinc-100">{item.quantity}</td>
                        <td className="px-3 py-2 text-right text-sm text-zinc-600 dark:text-zinc-400">${Number(item.unit_price).toFixed(2)}</td>
                        <td className="px-3 py-2 text-right text-sm font-semibold text-zinc-900 dark:text-zinc-100">${Number(item.line_total).toFixed(2)}</td>
                      </tr>
                    ))}
                  </tbody>
                  <tfoot>
                    <tr className="bg-zinc-50 dark:bg-zinc-800">
                      <td colSpan={3} className="px-3 py-2 text-right text-sm font-bold text-zinc-900 dark:text-zinc-50">Grand Total</td>
                      <td className="px-3 py-2 text-right text-sm font-bold text-emerald-600 dark:text-emerald-400">${Number(selectedSale.total_amount).toFixed(2)}</td>
                    </tr>
                  </tfoot>
                </table>
              </div>

              <button
                onClick={() => setSelectedSale(null)}
                className="mt-4 w-full rounded-md border border-zinc-300 bg-white py-2 text-sm font-medium text-zinc-700 hover:bg-zinc-50 dark:border-zinc-600 dark:bg-zinc-800 dark:text-zinc-300"
              >
                Close
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
