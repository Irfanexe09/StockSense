"use client";

import { useEffect, useState } from "react";
import { apiFetch } from "@/lib/api";
import type {
  Batch,
  BatchCreate,
  PaginatedProducts,
  Product,
  StockDeductRequest,
  StockDeductResponse,
} from "@/types/api";

export default function BatchesPage() {
  const [batches, setBatches] = useState<Batch[]>([]);
  const [products, setProducts] = useState<Product[]>([]);
  const [selectedProductFilter, setSelectedProductFilter] = useState<string>("");
  const [filterExpiringSoon, setFilterExpiringSoon] = useState(false);
  const [filterExpired, setFilterExpired] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showAddForm, setShowAddForm] = useState(false);
  const [showDeductModal, setShowDeductModal] = useState(false);
  const [deductSuccessMessage, setDeductSuccessMessage] = useState<string | null>(null);
  const [refreshKey, setRefreshKey] = useState(0);

  // Load products list for dropdown filters and forms
  useEffect(() => {
    let cancelled = false;
    async function loadProducts() {
      try {
        const data = await apiFetch<PaginatedProducts>("/api/v1/products/?limit=200");
        if (!cancelled) setProducts(data.items);
      } catch {
        // Non-critical
      }
    }
    loadProducts();
    return () => {
      cancelled = true;
    };
  }, []);

  // Load batches based on active filters
  useEffect(() => {
    let cancelled = false;

    async function loadBatches() {
      setLoading(true);
      setError(null);
      try {
        const params = new URLSearchParams();
        if (selectedProductFilter) params.set("product_id", selectedProductFilter);
        if (filterExpired) {
          params.set("expired_only", "true");
        } else if (filterExpiringSoon) {
          params.set("expiring_within_days", "30");
        }

        const query = params.toString();
        const data = await apiFetch<Batch[]>(
          `/api/v1/batches/${query ? `?${query}` : ""}`
        );
        if (!cancelled) {
          setBatches(data);
        }
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : "Failed to load batches");
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    loadBatches();
    return () => {
      cancelled = true;
    };
  }, [selectedProductFilter, filterExpiringSoon, filterExpired, refreshKey]);

  const handleDeleteBatch = async (batchId: number) => {
    if (!confirm("Are you sure you want to delete this batch? Product stock will decrease accordingly.")) {
      return;
    }
    try {
      await apiFetch(`/api/v1/batches/${batchId}`, { method: "DELETE" });
      setRefreshKey((k) => k + 1);
    } catch (err) {
      alert(err instanceof Error ? err.message : "Failed to delete batch");
    }
  };

  return (
    <div className="p-6 sm:p-10">
      <div className="mx-auto max-w-5xl space-y-6">
        {/* Page Header */}
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h1 className="text-3xl font-bold tracking-tight text-zinc-900 dark:text-zinc-50">
              Batches & Expiry Tracking
            </h1>
            <p className="mt-1 text-sm text-zinc-500 dark:text-zinc-400">
              Track lots, monitor expiry dates, and execute FIFO stock deductions.
            </p>
          </div>
          <div className="flex gap-2">
            <button
              onClick={() => setShowDeductModal(true)}
              className="inline-flex items-center gap-1.5 rounded-md border border-zinc-300 bg-white px-3.5 py-2 text-sm font-medium text-zinc-700 hover:bg-zinc-50 dark:border-zinc-700 dark:bg-zinc-800 dark:text-zinc-200 dark:hover:bg-zinc-700"
            >
              FIFO Stock Deduct
            </button>
            <button
              onClick={() => setShowAddForm(!showAddForm)}
              className="inline-flex items-center gap-1.5 rounded-md bg-emerald-600 px-4 py-2 text-sm font-medium text-white hover:bg-emerald-700"
            >
              {showAddForm ? "Cancel" : "+ New Batch"}
            </button>
          </div>
        </div>

        {/* Deduct Success Notification */}
        {deductSuccessMessage && (
          <div className="flex items-center justify-between rounded-md border border-emerald-200 bg-emerald-50 p-4 text-sm text-emerald-800 dark:border-emerald-900/50 dark:bg-emerald-950/40 dark:text-emerald-300">
            <span>{deductSuccessMessage}</span>
            <button onClick={() => setDeductSuccessMessage(null)} className="font-bold">
              ✕
            </button>
          </div>
        )}

        {/* Add Batch Form */}
        {showAddForm && (
          <AddBatchForm
            products={products}
            onCreated={() => {
              setShowAddForm(false);
              setRefreshKey((k) => k + 1);
            }}
          />
        )}

        {/* FIFO Deduct Modal / Panel */}
        {showDeductModal && (
          <FifoDeductForm
            products={products}
            onClose={() => setShowDeductModal(false)}
            onSuccess={(result) => {
              setShowDeductModal(false);
              setDeductSuccessMessage(
                `Successfully deducted ${result.deducted_quantity} units using FIFO across ${result.batches_affected.length} batch(es). Remaining stock: ${result.remaining_stock} units.`
              );
              setRefreshKey((k) => k + 1);
            }}
          />
        )}

        {/* Filter Controls */}
        <div className="flex flex-col gap-3 rounded-lg border border-zinc-200 bg-white p-4 dark:border-zinc-800 dark:bg-zinc-900 sm:flex-row sm:items-center">
          <select
            value={selectedProductFilter}
            onChange={(e) => setSelectedProductFilter(e.target.value)}
            className="rounded-md border border-zinc-300 bg-white px-3 py-1.5 text-sm text-zinc-900 focus:border-emerald-500 focus:outline-none dark:border-zinc-700 dark:bg-zinc-800 dark:text-zinc-50"
          >
            <option value="">All Products</option>
            {products.map((p) => (
              <option key={p.id} value={p.id}>
                {p.sku} — {p.name}
              </option>
            ))}
          </select>

          <label className="flex items-center gap-2 text-sm text-zinc-700 dark:text-zinc-300">
            <input
              type="checkbox"
              checked={filterExpiringSoon}
              onChange={(e) => {
                setFilterExpiringSoon(e.target.checked);
                if (e.target.checked) setFilterExpired(false);
              }}
              className="rounded border-zinc-300 text-emerald-600 focus:ring-emerald-500"
            />
            Expiring in 30 days
          </label>

          <label className="flex items-center gap-2 text-sm text-zinc-700 dark:text-zinc-300">
            <input
              type="checkbox"
              checked={filterExpired}
              onChange={(e) => {
                setFilterExpired(e.target.checked);
                if (e.target.checked) setFilterExpiringSoon(false);
              }}
              className="rounded border-zinc-300 text-red-600 focus:ring-red-500"
            />
            Expired only
          </label>

          <div className="ml-auto text-xs text-zinc-500">
            Showing {batches.length} batch{batches.length !== 1 ? "es" : ""}
          </div>
        </div>

        {/* Error message */}
        {error && (
          <div className="rounded-md border border-red-200 bg-red-50 p-4 text-sm text-red-700 dark:border-red-900 dark:bg-red-950 dark:text-red-400">
            {error}
          </div>
        )}

        {/* Batches Table */}
        {loading ? (
          <p className="text-sm text-zinc-500">Loading batches…</p>
        ) : batches.length === 0 ? (
          <div className="rounded-lg border border-zinc-200 bg-white p-10 text-center dark:border-zinc-800 dark:bg-zinc-900">
            <p className="text-zinc-500 dark:text-zinc-400">
              No batches found matching the filters. Click &quot;+ New Batch&quot; to add stock.
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto rounded-lg border border-zinc-200 bg-white dark:border-zinc-800 dark:bg-zinc-900">
            <table className="min-w-full divide-y divide-zinc-200 dark:divide-zinc-800">
              <thead className="bg-zinc-50 dark:bg-zinc-950">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-zinc-500">Batch #</th>
                  <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-zinc-500">Product</th>
                  <th className="px-4 py-3 text-right text-xs font-medium uppercase tracking-wider text-zinc-500">Remaining / Initial</th>
                  <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-zinc-500">Received</th>
                  <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-zinc-500">Expiry Date</th>
                  <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-zinc-500">Status</th>
                  <th className="px-4 py-3 text-right text-xs font-medium uppercase tracking-wider text-zinc-500">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-zinc-200 dark:divide-zinc-800">
                {batches.map((b) => (
                  <tr key={b.id} className="hover:bg-zinc-50 dark:hover:bg-zinc-800/50">
                    <td className="whitespace-nowrap px-4 py-3 font-mono text-sm font-semibold text-zinc-800 dark:text-zinc-200">
                      {b.batch_number}
                    </td>
                    <td className="px-4 py-3 text-sm text-zinc-900 dark:text-zinc-100">
                      {b.product_name ?? `Product #${b.product_id}`}
                      {b.product_sku && (
                        <span className="ml-1.5 font-mono text-xs text-zinc-400">
                          ({b.product_sku})
                        </span>
                      )}
                    </td>
                    <td className="whitespace-nowrap px-4 py-3 text-right text-sm">
                      <span className="font-semibold text-zinc-900 dark:text-zinc-100">
                        {b.quantity}
                      </span>
                      <span className="text-zinc-400 text-xs"> / {b.initial_quantity}</span>
                    </td>
                    <td className="whitespace-nowrap px-4 py-3 text-xs text-zinc-500 dark:text-zinc-400">
                      {b.received_date}
                    </td>
                    <td className="whitespace-nowrap px-4 py-3 text-sm text-zinc-700 dark:text-zinc-300">
                      {b.expiry_date ?? <span className="text-zinc-400 text-xs italic">No Expiry</span>}
                    </td>
                    <td className="whitespace-nowrap px-4 py-3 text-sm">
                      {b.is_expired ? (
                        <span className="inline-flex rounded-full bg-red-100 px-2 py-0.5 text-xs font-semibold text-red-800 dark:bg-red-900 dark:text-red-200">
                          Expired
                        </span>
                      ) : b.days_until_expiry !== null && b.days_until_expiry <= 30 ? (
                        <span className="inline-flex rounded-full bg-amber-100 px-2 py-0.5 text-xs font-semibold text-amber-800 dark:bg-amber-900 dark:text-amber-200">
                          {b.days_until_expiry === 0
                            ? "Expires Today"
                            : `${b.days_until_expiry}d left`}
                        </span>
                      ) : (
                        <span className="inline-flex rounded-full bg-emerald-100 px-2 py-0.5 text-xs font-medium text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300">
                          Healthy
                        </span>
                      )}
                    </td>
                    <td className="whitespace-nowrap px-4 py-3 text-right text-sm">
                      <button
                        onClick={() => handleDeleteBatch(b.id)}
                        className="text-xs text-red-600 hover:text-red-800 dark:text-red-400 dark:hover:text-red-300"
                      >
                        Delete
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}

/* ------------------------------------------------------------------ */
/*  Add Batch Form                                                    */
/* ------------------------------------------------------------------ */

function AddBatchForm({
  products,
  onCreated,
}: {
  products: Product[];
  onCreated: () => void;
}) {
  const [form, setForm] = useState<BatchCreate>({
    product_id: products[0]?.id ?? 0,
    batch_number: "",
    quantity: 10,
    expiry_date: null,
    received_date: new Date().toISOString().split("T")[0],
  });
  const [submitting, setSubmitting] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!form.product_id) {
      setFormError("Please select a product.");
      return;
    }
    setSubmitting(true);
    setFormError(null);
    try {
      await apiFetch("/api/v1/batches/", {
        method: "POST",
        body: JSON.stringify(form),
      });
      onCreated();
    } catch (err) {
      setFormError(err instanceof Error ? err.message : "Failed to create batch");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <form
      onSubmit={handleSubmit}
      className="space-y-4 rounded-lg border border-zinc-200 bg-white p-6 dark:border-zinc-800 dark:bg-zinc-900"
    >
      <h2 className="text-lg font-semibold text-zinc-900 dark:text-zinc-50">
        Record New Product Batch
      </h2>

      {formError && (
        <p className="text-sm text-red-600 dark:text-red-400">{formError}</p>
      )}

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        <div>
          <label className="block text-sm font-medium text-zinc-700 dark:text-zinc-300">
            Product *
          </label>
          <select
            required
            value={form.product_id}
            onChange={(e) => setForm({ ...form, product_id: parseInt(e.target.value) })}
            className="mt-1 w-full rounded-md border border-zinc-300 bg-white px-3 py-2 text-sm text-zinc-900 focus:border-emerald-500 focus:outline-none dark:border-zinc-700 dark:bg-zinc-800 dark:text-zinc-50"
          >
            {products.map((p) => (
              <option key={p.id} value={p.id}>
                {p.sku} — {p.name}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-zinc-700 dark:text-zinc-300">
            Batch / Lot Number *
          </label>
          <input
            required
            type="text"
            placeholder="e.g. LOT-2026-01"
            value={form.batch_number}
            onChange={(e) => setForm({ ...form, batch_number: e.target.value })}
            className="mt-1 w-full rounded-md border border-zinc-300 bg-white px-3 py-2 text-sm text-zinc-900 focus:border-emerald-500 focus:outline-none dark:border-zinc-700 dark:bg-zinc-800 dark:text-zinc-50"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-zinc-700 dark:text-zinc-300">
            Received Quantity *
          </label>
          <input
            required
            type="number"
            min="1"
            value={form.quantity}
            onChange={(e) => setForm({ ...form, quantity: parseInt(e.target.value) || 1 })}
            className="mt-1 w-full rounded-md border border-zinc-300 bg-white px-3 py-2 text-sm text-zinc-900 focus:border-emerald-500 focus:outline-none dark:border-zinc-700 dark:bg-zinc-800 dark:text-zinc-50"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-zinc-700 dark:text-zinc-300">
            Expiry Date (Optional)
          </label>
          <input
            type="date"
            value={form.expiry_date ?? ""}
            onChange={(e) => setForm({ ...form, expiry_date: e.target.value || null })}
            className="mt-1 w-full rounded-md border border-zinc-300 bg-white px-3 py-2 text-sm text-zinc-900 focus:border-emerald-500 focus:outline-none dark:border-zinc-700 dark:bg-zinc-800 dark:text-zinc-50"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-zinc-700 dark:text-zinc-300">
            Received Date
          </label>
          <input
            type="date"
            value={form.received_date ?? ""}
            onChange={(e) => setForm({ ...form, received_date: e.target.value })}
            className="mt-1 w-full rounded-md border border-zinc-300 bg-white px-3 py-2 text-sm text-zinc-900 focus:border-emerald-500 focus:outline-none dark:border-zinc-700 dark:bg-zinc-800 dark:text-zinc-50"
          />
        </div>
      </div>

      <div className="flex justify-end gap-2">
        <button
          type="submit"
          disabled={submitting}
          className="rounded-md bg-emerald-600 px-4 py-2 text-sm font-medium text-white hover:bg-emerald-700 disabled:opacity-50"
        >
          {submitting ? "Saving…" : "Save Batch"}
        </button>
      </div>
    </form>
  );
}

/* ------------------------------------------------------------------ */
/*  FIFO Deduct Modal Form                                            */
/* ------------------------------------------------------------------ */

function FifoDeductForm({
  products,
  onClose,
  onSuccess,
}: {
  products: Product[];
  onClose: () => void;
  onSuccess: (result: StockDeductResponse) => void;
}) {
  const [productId, setProductId] = useState<number>(products[0]?.id ?? 0);
  const [quantity, setQuantity] = useState<number>(1);
  const [reason, setReason] = useState<string>("sale");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const selectedProduct = products.find((p) => p.id === productId);

  const handleDeduct = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!productId) return;
    setSubmitting(true);
    setError(null);
    try {
      const payload: StockDeductRequest = { quantity, reason };
      const res = await apiFetch<StockDeductResponse>(
        `/api/v1/products/${productId}/deduct`,
        {
          method: "POST",
          body: JSON.stringify(payload),
        }
      );
      onSuccess(res);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to deduct stock");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
      <div className="w-full max-w-md rounded-lg border border-zinc-200 bg-white p-6 shadow-xl dark:border-zinc-800 dark:bg-zinc-900">
        <h2 className="text-lg font-bold text-zinc-900 dark:text-zinc-50">
          FIFO Stock Deduction
        </h2>
        <p className="mt-1 text-xs text-zinc-500">
          Deducts stock automatically starting from the earliest expiring batch.
        </p>

        {error && (
          <p className="mt-3 rounded bg-red-50 p-2.5 text-xs font-semibold text-red-600 dark:bg-red-950 dark:text-red-400">
            {error}
          </p>
        )}

        <form onSubmit={handleDeduct} className="mt-4 space-y-4">
          <div>
            <label className="block text-sm font-medium text-zinc-700 dark:text-zinc-300">
              Select Product
            </label>
            <select
              value={productId}
              onChange={(e) => setProductId(parseInt(e.target.value))}
              className="mt-1 w-full rounded-md border border-zinc-300 bg-white px-3 py-2 text-sm text-zinc-900 focus:border-emerald-500 focus:outline-none dark:border-zinc-700 dark:bg-zinc-800 dark:text-zinc-50"
            >
              {products.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.sku} — {p.name} ({p.stock_quantity} available)
                </option>
              ))}
            </select>
            {selectedProduct && (
              <p className="mt-1 text-xs text-zinc-500">
                Available Stock: <strong>{selectedProduct.stock_quantity} units</strong>
              </p>
            )}
          </div>

          <div>
            <label className="block text-sm font-medium text-zinc-700 dark:text-zinc-300">
              Quantity to Deduct *
            </label>
            <input
              required
              type="number"
              min="1"
              value={quantity}
              onChange={(e) => setQuantity(parseInt(e.target.value) || 1)}
              className="mt-1 w-full rounded-md border border-zinc-300 bg-white px-3 py-2 text-sm text-zinc-900 focus:border-emerald-500 focus:outline-none dark:border-zinc-700 dark:bg-zinc-800 dark:text-zinc-50"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-zinc-700 dark:text-zinc-300">
              Reason / Reference
            </label>
            <select
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              className="mt-1 w-full rounded-md border border-zinc-300 bg-white px-3 py-2 text-sm text-zinc-900 focus:border-emerald-500 focus:outline-none dark:border-zinc-700 dark:bg-zinc-800 dark:text-zinc-50"
            >
              <option value="sale">Sale (Customer purchase)</option>
              <option value="damage">Damaged item</option>
              <option value="spoilage">Expired / Spoiled stock</option>
              <option value="adjustment">Manual inventory adjustment</option>
            </select>
          </div>

          <div className="flex justify-end gap-2 pt-2">
            <button
              type="button"
              onClick={onClose}
              className="rounded-md border border-zinc-300 px-3 py-1.5 text-sm font-medium text-zinc-700 hover:bg-zinc-50 dark:border-zinc-700 dark:text-zinc-300 dark:hover:bg-zinc-800"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={submitting}
              className="rounded-md bg-emerald-600 px-4 py-1.5 text-sm font-medium text-white hover:bg-emerald-700 disabled:opacity-50"
            >
              {submitting ? "Processing…" : "Confirm FIFO Deduction"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
