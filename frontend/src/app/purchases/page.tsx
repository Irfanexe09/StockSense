"use client";

import { useEffect, useState } from "react";
import { apiFetch } from "@/lib/api";
import type {
  PaginatedProducts,
  Product,
  PurchaseOrder,
  PurchaseOrderCreate,
  PurchaseOrderItemCreate,
  PurchaseOrderListItem,
  ReceiveItemInput,
  ReceiveOrderRequest,
  Supplier,
} from "@/types/api";

export default function PurchasesPage() {
  const [orders, setOrders] = useState<PurchaseOrderListItem[]>([]);
  const [statusFilter, setStatusFilter] = useState<string>("ALL");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [refreshKey, setRefreshKey] = useState(0);

  // Active suppliers and products for creating PO
  const [suppliers, setSuppliers] = useState<Supplier[]>([]);
  const [products, setProducts] = useState<Product[]>([]);

  // Modals
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [selectedPO, setSelectedPO] = useState<PurchaseOrder | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const [showReceiveModal, setShowReceiveModal] = useState(false);

  // Create Form State
  const [formSupplierId, setFormSupplierId] = useState<number | "">("");
  const [formExpectedDate, setFormExpectedDate] = useState("");
  const [formNotes, setFormNotes] = useState("");
  const [formItems, setFormItems] = useState<
    { product_id: number | ""; quantity: number; unit_cost: number }[]
  >([{ product_id: "", quantity: 1, unit_cost: 0 }]);
  const [createSubmitting, setCreateSubmitting] = useState(false);
  const [createError, setCreateError] = useState<string | null>(null);

  // Receive Form State
  const [receiveInputs, setReceiveInputs] = useState<
    Record<
      number,
      { quantity_received: number; batch_number: string; expiry_date: string }
    >
  >({});
  const [receiveNotes, setReceiveNotes] = useState("");
  const [receiveSubmitting, setReceiveSubmitting] = useState(false);
  const [receiveError, setReceiveError] = useState<string | null>(null);

  // ── Load Orders List ──
  useEffect(() => {
    let cancelled = false;

    async function loadOrders() {
      setLoading(true);
      setError(null);
      try {
        const params = new URLSearchParams({ limit: "100" });
        if (statusFilter !== "ALL") {
          params.set("status", statusFilter);
        }
        const data = await apiFetch<PurchaseOrderListItem[]>(
          `/api/v1/purchase-orders/?${params.toString()}`
        );
        if (!cancelled) setOrders(data);
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : "Failed to load purchase orders");
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    loadOrders();
    return () => {
      cancelled = true;
    };
  }, [statusFilter, refreshKey]);

  // ── Load Suppliers and Products when opening Create Modal ──
  async function openCreateModal() {
    setShowCreateModal(true);
    setCreateError(null);
    try {
      const [supData, prodData] = await Promise.all([
        apiFetch<Supplier[]>("/api/v1/suppliers/?active_only=true"),
        apiFetch<PaginatedProducts>("/api/v1/products/?limit=200"),
      ]);
      setSuppliers(supData);
      setProducts(prodData.items);
      if (supData.length > 0) setFormSupplierId(supData[0].id);
    } catch (err) {
      setCreateError(
        err instanceof Error ? err.message : "Failed to load suppliers/products"
      );
    }
  }

  // ── View PO Detail ──
  async function viewPODetail(poId: number) {
    setDetailLoading(true);
    try {
      const data = await apiFetch<PurchaseOrder>(`/api/v1/purchase-orders/${poId}`);
      setSelectedPO(data);
    } catch {
      // ignore
    } finally {
      setDetailLoading(false);
    }
  }

  // ── Form Helpers ──
  function addFormItem() {
    setFormItems((prev) => [
      ...prev,
      { product_id: "", quantity: 1, unit_cost: 0 },
    ]);
  }

  function updateFormItem(
    index: number,
    field: "product_id" | "quantity" | "unit_cost",
    val: number | ""
  ) {
    setFormItems((prev) => {
      const copy = [...prev];
      copy[index] = { ...copy[index], [field]: val };
      if (field === "product_id" && typeof val === "number") {
        const prod = products.find((p) => p.id === val);
        if (prod) {
          copy[index].unit_cost = Number(prod.cost_price);
        }
      }
      return copy;
    });
  }

  function removeFormItem(index: number) {
    setFormItems((prev) => prev.filter((_, i) => i !== index));
  }

  async function handleCreatePO(submitNow: boolean) {
    if (!formSupplierId) {
      setCreateError("Please select a supplier.");
      return;
    }

    const validItems: PurchaseOrderItemCreate[] = [];
    for (const item of formItems) {
      if (typeof item.product_id !== "number") {
        setCreateError("Please select a product for all line items.");
        return;
      }
      if (item.quantity <= 0) {
        setCreateError("Quantities must be greater than zero.");
        return;
      }
      validItems.push({
        product_id: item.product_id,
        quantity: item.quantity,
        unit_cost: item.unit_cost,
      });
    }

    if (validItems.length === 0) {
      setCreateError("Please add at least one line item.");
      return;
    }

    setCreateSubmitting(true);
    setCreateError(null);

    const payload: PurchaseOrderCreate = {
      supplier_id: Number(formSupplierId),
      expected_delivery_date: formExpectedDate || null,
      notes: formNotes.trim() || null,
      submit_now: submitNow,
      items: validItems,
    };

    try {
      await apiFetch<PurchaseOrder>("/api/v1/purchase-orders/", {
        method: "POST",
        body: JSON.stringify(payload),
      });
      setShowCreateModal(false);
      setFormItems([{ product_id: "", quantity: 1, unit_cost: 0 }]);
      setFormNotes("");
      setFormExpectedDate("");
      setRefreshKey((k) => k + 1);
    } catch (err) {
      setCreateError(
        err instanceof Error ? err.message : "Failed to create purchase order"
      );
    } finally {
      setCreateSubmitting(false);
    }
  }

  // ── Status Action Helpers ──
  async function submitOrder(poId: number) {
    try {
      const updated = await apiFetch<PurchaseOrder>(
        `/api/v1/purchase-orders/${poId}/order`,
        { method: "POST" }
      );
      setSelectedPO(updated);
      setRefreshKey((k) => k + 1);
    } catch (err) {
      alert(err instanceof Error ? err.message : "Failed to submit order");
    }
  }

  async function cancelOrder(poId: number) {
    if (!confirm("Are you sure you want to cancel this purchase order?")) return;
    try {
      const updated = await apiFetch<PurchaseOrder>(
        `/api/v1/purchase-orders/${poId}/cancel`,
        { method: "POST" }
      );
      setSelectedPO(updated);
      setRefreshKey((k) => k + 1);
    } catch (err) {
      alert(err instanceof Error ? err.message : "Failed to cancel order");
    }
  }

  // ── Open Receive Modal ──
  function openReceiveModal(po: PurchaseOrder) {
    const initialInputs: Record<
      number,
      { quantity_received: number; batch_number: string; expiry_date: string }
    > = {};
    const defaultBatchPrefix = `LOT-${new Date().toISOString().slice(0, 10).replace(/-/g, "")}`;

    po.items.forEach((item, idx) => {
      if (item.remaining_quantity > 0) {
        initialInputs[item.id] = {
          quantity_received: item.remaining_quantity,
          batch_number: `${defaultBatchPrefix}-${idx + 1}`,
          expiry_date: "",
        };
      }
    });

    setReceiveInputs(initialInputs);
    setReceiveNotes("");
    setReceiveError(null);
    setShowReceiveModal(true);
  }

  async function handleReceiveSubmit() {
    if (!selectedPO) return;

    const itemsToReceive: ReceiveItemInput[] = [];
    for (const [itemIdStr, val] of Object.entries(receiveInputs)) {
      const itemId = Number(itemIdStr);
      if (val.quantity_received > 0) {
        if (!val.batch_number.trim()) {
          setReceiveError("Batch number is required for all received items.");
          return;
        }
        itemsToReceive.push({
          purchase_order_item_id: itemId,
          quantity_received: val.quantity_received,
          batch_number: val.batch_number.trim(),
          expiry_date: val.expiry_date ? val.expiry_date : null,
        });
      }
    }

    if (itemsToReceive.length === 0) {
      setReceiveError("Please specify a quantity to receive for at least one item.");
      return;
    }

    setReceiveSubmitting(true);
    setReceiveError(null);

    const payload: ReceiveOrderRequest = {
      notes: receiveNotes.trim() || null,
      items: itemsToReceive,
    };

    try {
      await apiFetch(
        `/api/v1/purchase-orders/${selectedPO.id}/receive`,
        {
          method: "POST",
          body: JSON.stringify(payload),
        }
      );
      setShowReceiveModal(false);
      // Reload PO details
      await viewPODetail(selectedPO.id);
      setRefreshKey((k) => k + 1);
    } catch (err) {
      setReceiveError(
        err instanceof Error ? err.message : "Failed to receive items"
      );
    } finally {
      setReceiveSubmitting(false);
    }
  }

  function getStatusBadge(status: string) {
    switch (status) {
      case "DRAFT":
        return "bg-zinc-100 text-zinc-700 dark:bg-zinc-800 dark:text-zinc-300";
      case "ORDERED":
        return "bg-sky-100 text-sky-800 dark:bg-sky-950 dark:text-sky-300";
      case "PARTIALLY_RECEIVED":
        return "bg-amber-100 text-amber-800 dark:bg-amber-950 dark:text-amber-300";
      case "RECEIVED":
        return "bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300";
      case "CANCELLED":
        return "bg-red-100 text-red-800 dark:bg-red-950 dark:text-red-300";
      default:
        return "bg-zinc-100 text-zinc-600";
    }
  }

  const calculatedTotal = formItems.reduce(
    (sum, item) => sum + (item.quantity > 0 ? item.quantity * item.unit_cost : 0),
    0
  );

  return (
    <div className="p-6 sm:p-10">
      <div className="mx-auto max-w-6xl space-y-6">
        {/* Header */}
        <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h1 className="text-3xl font-bold tracking-tight text-zinc-900 dark:text-zinc-50">
              Purchases & Restocking
            </h1>
            <p className="text-zinc-600 dark:text-zinc-400">
              Create supplier purchase orders, track order fulfillment, and receive stock into batches.
            </p>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={() => setRefreshKey((k) => k + 1)}
              disabled={loading}
              className="rounded-md border border-zinc-300 bg-white px-3 py-1.5 text-xs font-medium text-zinc-700 hover:bg-zinc-50 disabled:opacity-50 dark:border-zinc-700 dark:bg-zinc-800 dark:text-zinc-300 dark:hover:bg-zinc-700"
            >
              {loading ? "Refreshing…" : "↻ Refresh"}
            </button>
            <button
              onClick={openCreateModal}
              className="rounded-md bg-emerald-600 px-3 py-1.5 text-xs font-semibold text-white shadow hover:bg-emerald-700"
            >
              + New Purchase Order
            </button>
          </div>
        </div>

        {/* Filter Tabs */}
        <div className="flex flex-wrap gap-2 border-b border-zinc-200 pb-3 dark:border-zinc-800">
          {[
            { label: "All Orders", value: "ALL" },
            { label: "Draft", value: "DRAFT" },
            { label: "Ordered", value: "ORDERED" },
            { label: "Partially Received", value: "PARTIALLY_RECEIVED" },
            { label: "Received", value: "RECEIVED" },
            { label: "Cancelled", value: "CANCELLED" },
          ].map((tab) => (
            <button
              key={tab.value}
              onClick={() => setStatusFilter(tab.value)}
              className={`rounded-full px-3 py-1 text-xs font-medium transition-colors ${
                statusFilter === tab.value
                  ? "bg-emerald-600 text-white"
                  : "bg-zinc-100 text-zinc-600 hover:bg-zinc-200 dark:bg-zinc-800 dark:text-zinc-300"
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {/* Loading */}
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
            <h3 className="font-semibold">Unable to load purchase orders</h3>
            <p className="mt-1 text-sm">{error}</p>
          </div>
        )}

        {/* Empty */}
        {!loading && !error && orders.length === 0 && (
          <div className="rounded-lg border border-zinc-200 bg-zinc-50 p-8 text-center dark:border-zinc-800 dark:bg-zinc-900">
            <p className="text-sm text-zinc-500 dark:text-zinc-400">
              No purchase orders found for this status. Click &quot;+ New Purchase Order&quot; to order stock.
            </p>
          </div>
        )}

        {/* Orders Table */}
        {!loading && !error && orders.length > 0 && (
          <div className="overflow-x-auto rounded-lg border border-zinc-200 bg-white dark:border-zinc-800 dark:bg-zinc-900">
            <table className="min-w-full divide-y divide-zinc-200 dark:divide-zinc-800">
              <thead className="bg-zinc-50 dark:bg-zinc-950">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-zinc-500">Order #</th>
                  <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-zinc-500">Supplier</th>
                  <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-zinc-500">Order Date</th>
                  <th className="px-4 py-3 text-center text-xs font-medium uppercase tracking-wider text-zinc-500">Status</th>
                  <th className="px-4 py-3 text-right text-xs font-medium uppercase tracking-wider text-zinc-500">Items</th>
                  <th className="px-4 py-3 text-right text-xs font-medium uppercase tracking-wider text-zinc-500">Total</th>
                  <th className="px-4 py-3 text-right text-xs font-medium uppercase tracking-wider text-zinc-500">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-zinc-200 dark:divide-zinc-800">
                {orders.map((po) => (
                  <tr key={po.id} className="hover:bg-zinc-50 dark:hover:bg-zinc-800/50">
                    <td className="whitespace-nowrap px-4 py-3 font-mono text-sm font-semibold text-zinc-900 dark:text-zinc-100">
                      {po.order_number}
                    </td>
                    <td className="px-4 py-3 text-sm text-zinc-800 dark:text-zinc-200">
                      {po.supplier_name || `Supplier #${po.supplier_id}`}
                    </td>
                    <td className="whitespace-nowrap px-4 py-3 text-sm text-zinc-600 dark:text-zinc-400">
                      {po.order_date}
                    </td>
                    <td className="whitespace-nowrap px-4 py-3 text-center">
                      <span
                        className={`inline-flex rounded-full px-2.5 py-0.5 text-xs font-semibold ${getStatusBadge(po.status)}`}
                      >
                        {po.status.replace("_", " ")}
                      </span>
                    </td>
                    <td className="whitespace-nowrap px-4 py-3 text-right text-sm text-zinc-600 dark:text-zinc-400">
                      {po.item_count}
                    </td>
                    <td className="whitespace-nowrap px-4 py-3 text-right text-sm font-bold text-zinc-900 dark:text-zinc-100">
                      ${Number(po.total_amount).toFixed(2)}
                    </td>
                    <td className="whitespace-nowrap px-4 py-3 text-right">
                      <button
                        onClick={() => viewPODetail(po.id)}
                        disabled={detailLoading}
                        className="text-xs font-medium text-emerald-600 hover:text-emerald-700 dark:text-emerald-400"
                      >
                        Manage →
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* ── Purchase Order Detail Modal ── */}
        {selectedPO && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
            <div className="max-h-[90vh] w-full max-w-3xl overflow-y-auto rounded-lg border border-zinc-200 bg-white p-6 shadow-xl dark:border-zinc-700 dark:bg-zinc-900">
              {/* Header */}
              <div className="flex items-start justify-between">
                <div>
                  <div className="flex items-center gap-3">
                    <h2 className="text-xl font-bold text-zinc-900 dark:text-zinc-50">
                      Order {selectedPO.order_number}
                    </h2>
                    <span
                      className={`inline-flex rounded-full px-2.5 py-0.5 text-xs font-semibold ${getStatusBadge(selectedPO.status)}`}
                    >
                      {selectedPO.status.replace("_", " ")}
                    </span>
                  </div>
                  <p className="mt-1 text-sm text-zinc-600 dark:text-zinc-400">
                    Supplier: <span className="font-semibold text-zinc-900 dark:text-zinc-100">{selectedPO.supplier_name}</span>
                    {" · "}Ordered: {selectedPO.order_date}
                    {selectedPO.expected_delivery_date && ` · Expected: ${selectedPO.expected_delivery_date}`}
                  </p>
                </div>
                <button
                  onClick={() => setSelectedPO(null)}
                  className="text-zinc-400 hover:text-zinc-600"
                >
                  ✕
                </button>
              </div>

              {selectedPO.notes && (
                <div className="mt-3 rounded bg-zinc-50 p-2.5 text-xs text-zinc-600 dark:bg-zinc-800 dark:text-zinc-300">
                  <span className="font-semibold">Notes:</span> {selectedPO.notes}
                </div>
              )}

              {/* Items Table */}
              <div className="mt-5 space-y-2">
                <h3 className="text-sm font-bold text-zinc-900 dark:text-zinc-50">
                  Ordered Line Items
                </h3>
                <div className="overflow-x-auto rounded border border-zinc-200 dark:border-zinc-700">
                  <table className="min-w-full divide-y divide-zinc-200 text-xs dark:divide-zinc-700">
                    <thead className="bg-zinc-50 dark:bg-zinc-800">
                      <tr>
                        <th className="px-3 py-2 text-left font-medium text-zinc-500">Product</th>
                        <th className="px-3 py-2 text-right font-medium text-zinc-500">Ordered</th>
                        <th className="px-3 py-2 text-right font-medium text-zinc-500">Received</th>
                        <th className="px-3 py-2 text-right font-medium text-zinc-500">Outstanding</th>
                        <th className="px-3 py-2 text-right font-medium text-zinc-500">Cost</th>
                        <th className="px-3 py-2 text-right font-medium text-zinc-500">Total</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-zinc-200 dark:divide-zinc-700">
                      {selectedPO.items.map((item) => (
                        <tr key={item.id}>
                          <td className="px-3 py-2">
                            <div className="font-medium text-zinc-900 dark:text-zinc-100">{item.product_name}</div>
                            <div className="font-mono text-zinc-500">{item.product_sku}</div>
                          </td>
                          <td className="px-3 py-2 text-right font-semibold text-zinc-900 dark:text-zinc-100">{item.quantity}</td>
                          <td className="px-3 py-2 text-right text-emerald-600 dark:text-emerald-400">{item.received_quantity}</td>
                          <td className="px-3 py-2 text-right">
                            <span className={item.remaining_quantity > 0 ? "font-bold text-amber-600" : "text-zinc-400"}>
                              {item.remaining_quantity}
                            </span>
                          </td>
                          <td className="px-3 py-2 text-right text-zinc-600 dark:text-zinc-400">${Number(item.unit_cost).toFixed(2)}</td>
                          <td className="px-3 py-2 text-right font-semibold text-zinc-900 dark:text-zinc-100">${Number(item.line_total).toFixed(2)}</td>
                        </tr>
                      ))}
                    </tbody>
                    <tfoot>
                      <tr className="bg-zinc-50 dark:bg-zinc-800 font-semibold">
                        <td colSpan={5} className="px-3 py-2 text-right text-zinc-900 dark:text-zinc-50">Grand Total</td>
                        <td className="px-3 py-2 text-right text-emerald-600 dark:text-emerald-400 font-bold">${Number(selectedPO.total_amount).toFixed(2)}</td>
                      </tr>
                    </tfoot>
                  </table>
                </div>
              </div>

              {/* Receipts Log */}
              {selectedPO.receipts && selectedPO.receipts.length > 0 && (
                <div className="mt-5 space-y-2">
                  <h3 className="text-sm font-bold text-zinc-900 dark:text-zinc-50">
                    Receipt History
                  </h3>
                  <div className="space-y-2">
                    {selectedPO.receipts.map((rcv) => (
                      <div
                        key={rcv.id}
                        className="rounded border border-emerald-100 bg-emerald-50/40 p-3 text-xs dark:border-emerald-950 dark:bg-emerald-950/20"
                      >
                        <div className="flex items-center justify-between">
                          <span className="font-mono font-bold text-emerald-900 dark:text-emerald-300">{rcv.receipt_number}</span>
                          <span className="text-zinc-500">{new Date(rcv.received_at).toLocaleString()}</span>
                        </div>
                        {rcv.notes && <p className="mt-1 text-zinc-600 dark:text-zinc-400">{rcv.notes}</p>}
                        <div className="mt-2 flex flex-wrap gap-2">
                          {rcv.items.map((ri) => (
                            <span
                              key={ri.id}
                              className="rounded bg-white px-2 py-1 font-mono text-[11px] shadow-sm dark:bg-zinc-800"
                            >
                              Batch {ri.batch_number}: +{ri.quantity_received} units {ri.expiry_date && `(exp: ${ri.expiry_date})`}
                            </span>
                          ))}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Actions Footer */}
              <div className="mt-6 flex flex-wrap items-center justify-between gap-3 border-t border-zinc-200 pt-4 dark:border-zinc-700">
                <div className="flex items-center gap-2">
                  {selectedPO.status === "DRAFT" && (
                    <button
                      onClick={() => submitOrder(selectedPO.id)}
                      className="rounded bg-sky-600 px-3 py-1.5 text-xs font-semibold text-white hover:bg-sky-700"
                    >
                      Submit Order to Supplier
                    </button>
                  )}
                  {(selectedPO.status === "ORDERED" || selectedPO.status === "PARTIALLY_RECEIVED") && (
                    <button
                      onClick={() => openReceiveModal(selectedPO)}
                      className="rounded bg-emerald-600 px-3 py-1.5 text-xs font-semibold text-white hover:bg-emerald-700"
                    >
                      Receive Stock Items
                    </button>
                  )}
                  {(selectedPO.status === "DRAFT" || selectedPO.status === "ORDERED") &&
                    selectedPO.items.every((i) => i.received_quantity === 0) && (
                      <button
                        onClick={() => cancelOrder(selectedPO.id)}
                        className="rounded border border-red-200 bg-red-50 px-3 py-1.5 text-xs font-semibold text-red-700 hover:bg-red-100 dark:border-red-900 dark:bg-red-950 dark:text-red-400"
                      >
                        Cancel Order
                      </button>
                    )}
                </div>
                <button
                  onClick={() => setSelectedPO(null)}
                  className="rounded border border-zinc-300 bg-white px-4 py-1.5 text-xs font-medium text-zinc-700 hover:bg-zinc-50 dark:border-zinc-700 dark:bg-zinc-800 dark:text-zinc-300"
                >
                  Close
                </button>
              </div>
            </div>
          </div>
        )}

        {/* ── Create Purchase Order Modal ── */}
        {showCreateModal && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
            <div className="max-h-[90vh] w-full max-w-2xl overflow-y-auto rounded-lg border border-zinc-200 bg-white p-6 shadow-xl dark:border-zinc-700 dark:bg-zinc-900">
              <h3 className="text-lg font-bold text-zinc-900 dark:text-zinc-50">
                New Purchase Order
              </h3>
              <p className="mt-1 text-xs text-zinc-500 dark:text-zinc-400">
                Select a supplier and products to order inventory restocking.
              </p>

              {createError && (
                <div className="mt-3 rounded bg-red-50 p-3 text-xs text-red-700 dark:bg-red-950 dark:text-red-400">
                  {createError}
                </div>
              )}

              <div className="mt-4 space-y-4">
                <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
                  <div>
                    <label className="block text-xs font-medium text-zinc-700 dark:text-zinc-300">
                      Supplier *
                    </label>
                    <select
                      value={formSupplierId}
                      onChange={(e) => setFormSupplierId(Number(e.target.value))}
                      className="mt-1 w-full rounded-md border border-zinc-300 bg-white px-3 py-1.5 text-sm dark:border-zinc-700 dark:bg-zinc-800 dark:text-zinc-100"
                    >
                      {suppliers.length === 0 && <option value="">No active suppliers</option>}
                      {suppliers.map((s) => (
                        <option key={s.id} value={s.id}>
                          {s.name}
                        </option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <label className="block text-xs font-medium text-zinc-700 dark:text-zinc-300">
                      Expected Delivery Date
                    </label>
                    <input
                      type="date"
                      value={formExpectedDate}
                      onChange={(e) => setFormExpectedDate(e.target.value)}
                      className="mt-1 w-full rounded-md border border-zinc-300 bg-white px-3 py-1.5 text-sm dark:border-zinc-700 dark:bg-zinc-800 dark:text-zinc-100"
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-xs font-medium text-zinc-700 dark:text-zinc-300">
                    Order Notes
                  </label>
                  <input
                    type="text"
                    value={formNotes}
                    onChange={(e) => setFormNotes(e.target.value)}
                    placeholder="e.g. Weekly reorder, priority shipment"
                    className="mt-1 w-full rounded-md border border-zinc-300 bg-white px-3 py-1.5 text-sm dark:border-zinc-700 dark:bg-zinc-800 dark:text-zinc-100"
                  />
                </div>

                {/* Line items list */}
                <div className="space-y-2 border-t border-zinc-200 pt-3 dark:border-zinc-800">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-bold text-zinc-700 dark:text-zinc-300">
                      Line Items ({formItems.length})
                    </span>
                    <button
                      type="button"
                      onClick={addFormItem}
                      className="text-xs font-medium text-emerald-600 hover:text-emerald-700 dark:text-emerald-400"
                    >
                      + Add Item
                    </button>
                  </div>

                  {formItems.map((item, idx) => (
                    <div
                      key={idx}
                      className="flex items-center gap-2 rounded border border-zinc-100 bg-zinc-50 p-2 dark:border-zinc-800 dark:bg-zinc-800/60"
                    >
                      <div className="flex-1">
                        <select
                          value={item.product_id}
                          onChange={(e) =>
                            updateFormItem(
                              idx,
                              "product_id",
                              e.target.value ? Number(e.target.value) : ""
                            )
                          }
                          className="w-full rounded border border-zinc-300 bg-white px-2 py-1 text-xs dark:border-zinc-700 dark:bg-zinc-800 dark:text-zinc-100"
                        >
                          <option value="">Select a product…</option>
                          {products.map((p) => (
                            <option key={p.id} value={p.id}>
                              {p.name} ({p.sku})
                            </option>
                          ))}
                        </select>
                      </div>
                      <div className="w-20">
                        <input
                          type="number"
                          min={1}
                          placeholder="Qty"
                          value={item.quantity}
                          onChange={(e) =>
                            updateFormItem(
                              idx,
                              "quantity",
                              parseInt(e.target.value) || 0
                            )
                          }
                          className="w-full rounded border border-zinc-300 bg-white px-2 py-1 text-right text-xs dark:border-zinc-700 dark:bg-zinc-800 dark:text-zinc-100"
                        />
                      </div>
                      <div className="w-24">
                        <input
                          type="number"
                          step="0.01"
                          min={0}
                          placeholder="Unit Cost"
                          value={item.unit_cost}
                          onChange={(e) =>
                            updateFormItem(
                              idx,
                              "unit_cost",
                              parseFloat(e.target.value) || 0
                            )
                          }
                          className="w-full rounded border border-zinc-300 bg-white px-2 py-1 text-right text-xs dark:border-zinc-700 dark:bg-zinc-800 dark:text-zinc-100"
                        />
                      </div>
                      <div className="w-20 text-right font-mono text-xs font-semibold text-zinc-900 dark:text-zinc-100">
                        ${(item.quantity * item.unit_cost).toFixed(2)}
                      </div>
                      <button
                        type="button"
                        onClick={() => removeFormItem(idx)}
                        disabled={formItems.length === 1}
                        className="text-red-400 hover:text-red-600 disabled:opacity-30"
                      >
                        ✕
                      </button>
                    </div>
                  ))}
                </div>

                {/* Subtotal */}
                <div className="flex items-center justify-between border-t border-zinc-200 pt-3 dark:border-zinc-800">
                  <span className="text-sm font-semibold text-zinc-700 dark:text-zinc-300">
                    Order Total
                  </span>
                  <span className="text-lg font-bold text-zinc-900 dark:text-zinc-50">
                    ${calculatedTotal.toFixed(2)}
                  </span>
                </div>

                {/* Submit buttons */}
                <div className="flex justify-end gap-2 pt-2">
                  <button
                    type="button"
                    onClick={() => setShowCreateModal(false)}
                    className="rounded border border-zinc-300 bg-white px-3 py-1.5 text-xs font-medium text-zinc-700 hover:bg-zinc-50 dark:border-zinc-700 dark:bg-zinc-800 dark:text-zinc-300"
                  >
                    Cancel
                  </button>
                  <button
                    type="button"
                    disabled={createSubmitting}
                    onClick={() => handleCreatePO(false)}
                    className="rounded border border-zinc-300 bg-zinc-100 px-3 py-1.5 text-xs font-semibold text-zinc-800 hover:bg-zinc-200 disabled:opacity-50 dark:border-zinc-700 dark:bg-zinc-800 dark:text-zinc-200"
                  >
                    Save as Draft
                  </button>
                  <button
                    type="button"
                    disabled={createSubmitting}
                    onClick={() => handleCreatePO(true)}
                    className="rounded bg-emerald-600 px-3 py-1.5 text-xs font-semibold text-white shadow hover:bg-emerald-700 disabled:opacity-50"
                  >
                    {createSubmitting ? "Placing…" : "Place Order Now"}
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* ── Receive Items Modal ── */}
        {showReceiveModal && selectedPO && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
            <div className="max-h-[90vh] w-full max-w-2xl overflow-y-auto rounded-lg border border-zinc-200 bg-white p-6 shadow-xl dark:border-zinc-700 dark:bg-zinc-900">
              <h3 className="text-lg font-bold text-zinc-900 dark:text-zinc-50">
                Receive Stock — {selectedPO.order_number}
              </h3>
              <p className="mt-1 text-xs text-zinc-500 dark:text-zinc-400">
                Record incoming shipments. Created batches will immediately increase product stock.
              </p>

              {receiveError && (
                <div className="mt-3 rounded bg-red-50 p-3 text-xs text-red-700 dark:bg-red-950 dark:text-red-400">
                  {receiveError}
                </div>
              )}

              <div className="mt-4 space-y-3">
                {selectedPO.items
                  .filter((item) => item.remaining_quantity > 0)
                  .map((item) => {
                    const input = receiveInputs[item.id] || {
                      quantity_received: 0,
                      batch_number: "",
                      expiry_date: "",
                    };
                    return (
                      <div
                        key={item.id}
                        className="rounded border border-zinc-200 bg-zinc-50/50 p-3 text-xs dark:border-zinc-700 dark:bg-zinc-800/40"
                      >
                        <div className="flex items-center justify-between font-semibold text-zinc-900 dark:text-zinc-100">
                          <span>{item.product_name} ({item.product_sku})</span>
                          <span className="text-zinc-500 font-normal">
                            Outstanding: <b className="text-amber-600">{item.remaining_quantity}</b> of {item.quantity}
                          </span>
                        </div>

                        <div className="mt-2 grid grid-cols-1 gap-2 sm:grid-cols-3">
                          <div>
                            <label className="block font-medium text-zinc-600 dark:text-zinc-400">
                              Qty Receiving (max {item.remaining_quantity})
                            </label>
                            <input
                              type="number"
                              min={0}
                              max={item.remaining_quantity}
                              value={input.quantity_received}
                              onChange={(e) =>
                                setReceiveInputs((prev) => ({
                                  ...prev,
                                  [item.id]: {
                                    ...prev[item.id],
                                    quantity_received: parseInt(e.target.value) || 0,
                                  },
                                }))
                              }
                              className="mt-1 w-full rounded border border-zinc-300 bg-white px-2 py-1 text-xs dark:border-zinc-700 dark:bg-zinc-800 dark:text-zinc-100"
                            />
                          </div>

                          <div>
                            <label className="block font-medium text-zinc-600 dark:text-zinc-400">
                              Batch Number *
                            </label>
                            <input
                              type="text"
                              required
                              placeholder="e.g. LOT-2026-01"
                              value={input.batch_number}
                              onChange={(e) =>
                                setReceiveInputs((prev) => ({
                                  ...prev,
                                  [item.id]: {
                                    ...prev[item.id],
                                    batch_number: e.target.value,
                                  },
                                }))
                              }
                              className="mt-1 w-full rounded border border-zinc-300 bg-white px-2 py-1 text-xs dark:border-zinc-700 dark:bg-zinc-800 dark:text-zinc-100"
                            />
                          </div>

                          <div>
                            <label className="block font-medium text-zinc-600 dark:text-zinc-400">
                              Expiry Date (Optional)
                            </label>
                            <input
                              type="date"
                              value={input.expiry_date}
                              onChange={(e) =>
                                setReceiveInputs((prev) => ({
                                  ...prev,
                                  [item.id]: {
                                    ...prev[item.id],
                                    expiry_date: e.target.value,
                                  },
                                }))
                              }
                              className="mt-1 w-full rounded border border-zinc-300 bg-white px-2 py-1 text-xs dark:border-zinc-700 dark:bg-zinc-800 dark:text-zinc-100"
                            />
                          </div>
                        </div>
                      </div>
                    );
                  })}

                <div>
                  <label className="block text-xs font-medium text-zinc-700 dark:text-zinc-300">
                    Receipt Notes (e.g. Invoice #, Carrier)
                  </label>
                  <input
                    type="text"
                    value={receiveNotes}
                    onChange={(e) => setReceiveNotes(e.target.value)}
                    placeholder="e.g. Received via DHL, invoice #98231"
                    className="mt-1 w-full rounded border border-zinc-300 bg-white px-3 py-1.5 text-xs dark:border-zinc-700 dark:bg-zinc-800 dark:text-zinc-100"
                  />
                </div>

                <div className="flex justify-end gap-2 pt-3">
                  <button
                    type="button"
                    onClick={() => setShowReceiveModal(false)}
                    className="rounded border border-zinc-300 bg-white px-3 py-1.5 text-xs font-medium text-zinc-700 hover:bg-zinc-50 dark:border-zinc-700 dark:bg-zinc-800 dark:text-zinc-300"
                  >
                    Cancel
                  </button>
                  <button
                    type="button"
                    disabled={receiveSubmitting}
                    onClick={handleReceiveSubmit}
                    className="rounded bg-emerald-600 px-4 py-1.5 text-xs font-semibold text-white shadow hover:bg-emerald-700 disabled:opacity-50"
                  >
                    {receiveSubmitting ? "Processing…" : "Confirm Receipt"}
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
