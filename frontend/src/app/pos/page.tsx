"use client";

import { useEffect, useState } from "react";
import { apiFetch } from "@/lib/api";
import type { Product, PaginatedProducts } from "@/types/api";
import type { CheckoutRequest, SaleResponse } from "@/types/api";

interface CartItem {
  product: Product;
  quantity: number;
}

export default function POSPage() {
  // ── Product search state ──
  const [products, setProducts] = useState<Product[]>([]);
  const [searchQuery, setSearchQuery] = useState("");
  const [loadingProducts, setLoadingProducts] = useState(true);
  const [productError, setProductError] = useState<string | null>(null);

  // ── Cart state ──
  const [cart, setCart] = useState<CartItem[]>([]);

  // ── Checkout state ──
  const [checkingOut, setCheckingOut] = useState(false);
  const [checkoutError, setCheckoutError] = useState<string | null>(null);
  const [lastSale, setLastSale] = useState<SaleResponse | null>(null);

  // ── Refresh trigger ──
  const [refreshKey, setRefreshKey] = useState(0);

  // ── Load products ──
  useEffect(() => {
    let cancelled = false;

    async function loadProducts() {
      setLoadingProducts(true);
      setProductError(null);
      try {
        const params = new URLSearchParams({ limit: "200" });
        if (searchQuery.trim()) {
          params.set("search", searchQuery.trim());
        }
        const data = await apiFetch<PaginatedProducts>(
          `/api/v1/products/?${params.toString()}`
        );
        if (!cancelled) {
          setProducts(data.items);
        }
      } catch (err) {
        if (!cancelled) {
          setProductError(
            err instanceof Error ? err.message : "Failed to load products"
          );
        }
      } finally {
        if (!cancelled) setLoadingProducts(false);
      }
    }

    loadProducts();
    return () => {
      cancelled = true;
    };
  }, [searchQuery, refreshKey]);

  // ── Cart helpers ──
  function addToCart(product: Product) {
    setCheckoutError(null);
    setLastSale(null);
    setCart((prev) => {
      const existing = prev.find((c) => c.product.id === product.id);
      if (existing) {
        return prev.map((c) =>
          c.product.id === product.id
            ? { ...c, quantity: c.quantity + 1 }
            : c
        );
      }
      return [...prev, { product, quantity: 1 }];
    });
  }

  function updateCartQty(productId: number, qty: number) {
    if (qty <= 0) {
      removeFromCart(productId);
      return;
    }
    setCart((prev) =>
      prev.map((c) =>
        c.product.id === productId ? { ...c, quantity: qty } : c
      )
    );
  }

  function removeFromCart(productId: number) {
    setCart((prev) => prev.filter((c) => c.product.id !== productId));
  }

  function clearCart() {
    setCart([]);
    setCheckoutError(null);
  }

  const cartTotal = cart.reduce(
    (sum, c) => sum + c.product.selling_price * c.quantity,
    0
  );

  // ── Checkout ──
  async function handleCheckout() {
    if (cart.length === 0) return;
    setCheckingOut(true);
    setCheckoutError(null);
    setLastSale(null);

    const request: CheckoutRequest = {
      items: cart.map((c) => ({
        product_id: c.product.id,
        quantity: c.quantity,
        unit_price: c.product.selling_price,
      })),
    };

    try {
      const sale = await apiFetch<SaleResponse>("/api/v1/sales/checkout", {
        method: "POST",
        body: JSON.stringify(request),
      });
      setLastSale(sale);
      setCart([]);
      setRefreshKey((k) => k + 1); // refresh stock levels
    } catch (err) {
      if (err instanceof Error) {
        // Try to extract the detail from the API error response
        const match = err.message.match(/API error: (\d+)/);
        if (match) {
          try {
            // Re-fetch to get the error detail
            const resp = await fetch(
              `${process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"}/api/v1/sales/checkout`,
              {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(request),
              }
            );
            const data = await resp.json();
            setCheckoutError(data.detail || err.message);
          } catch {
            setCheckoutError(err.message);
          }
        } else {
          setCheckoutError(err.message);
        }
      } else {
        setCheckoutError("Checkout failed. Please try again.");
      }
    } finally {
      setCheckingOut(false);
    }
  }

  return (
    <div className="p-6 sm:p-10">
      <div className="mx-auto max-w-6xl space-y-6">
        {/* Header */}
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-zinc-900 dark:text-zinc-50">
            Point of Sale
          </h1>
          <p className="text-zinc-600 dark:text-zinc-400">
            Search for products, add them to the cart, and complete the checkout.
          </p>
        </div>

        {/* Success Receipt */}
        {lastSale && (
          <div className="rounded-lg border border-emerald-200 bg-emerald-50/60 p-6 dark:border-emerald-900/40 dark:bg-emerald-950/20">
            <div className="flex items-start gap-3">
              <svg
                xmlns="http://www.w3.org/2000/svg"
                className="h-6 w-6 shrink-0 text-emerald-600"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
              <div className="flex-1">
                <h3 className="font-semibold text-emerald-800 dark:text-emerald-300">
                  Sale Complete!
                </h3>
                <p className="mt-1 text-sm text-emerald-700 dark:text-emerald-400">
                  Receipt: <span className="font-mono font-bold">{lastSale.receipt_number}</span>
                </p>
                <p className="text-sm text-emerald-700 dark:text-emerald-400">
                  Total: <span className="font-bold">${Number(lastSale.total_amount).toFixed(2)}</span>
                  {" · "}
                  {lastSale.item_count} item{lastSale.item_count !== 1 && "s"}
                </p>
                <div className="mt-3 space-y-1">
                  {lastSale.items.map((item) => (
                    <p key={item.id} className="text-xs text-emerald-600 dark:text-emerald-400">
                      {item.product_name} ({item.product_sku}) × {item.quantity} @ ${Number(item.unit_price).toFixed(2)} = ${Number(item.line_total).toFixed(2)}
                    </p>
                  ))}
                </div>
                <button
                  onClick={() => setLastSale(null)}
                  className="mt-3 text-xs font-medium text-emerald-700 underline hover:text-emerald-900 dark:text-emerald-400"
                >
                  Dismiss
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Checkout Error */}
        {checkoutError && (
          <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-red-700 dark:border-red-900 dark:bg-red-950 dark:text-red-400">
            <h3 className="font-semibold">Checkout Failed</h3>
            <p className="mt-1 text-sm">{checkoutError}</p>
            <button
              onClick={() => setCheckoutError(null)}
              className="mt-2 text-xs font-medium underline"
            >
              Dismiss
            </button>
          </div>
        )}

        <div className="grid gap-6 lg:grid-cols-5">
          {/* ── Product List (Left) ── */}
          <div className="lg:col-span-3 space-y-4">
            <div>
              <input
                type="text"
                placeholder="Search products by name or SKU…"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full rounded-md border border-zinc-300 bg-white px-3 py-2 text-sm shadow-sm placeholder:text-zinc-400 focus:border-emerald-500 focus:outline-none focus:ring-1 focus:ring-emerald-500 dark:border-zinc-700 dark:bg-zinc-800 dark:text-zinc-100 dark:placeholder:text-zinc-500"
              />
            </div>

            {loadingProducts && (
              <div className="space-y-2">
                {[1, 2, 3].map((i) => (
                  <div
                    key={i}
                    className="h-16 animate-pulse rounded-lg border border-zinc-200 bg-zinc-100 dark:border-zinc-800 dark:bg-zinc-900"
                  />
                ))}
              </div>
            )}

            {productError && (
              <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700 dark:border-red-900 dark:bg-red-950 dark:text-red-400">
                {productError}
              </div>
            )}

            {!loadingProducts && !productError && products.length === 0 && (
              <div className="rounded-lg border border-zinc-200 bg-zinc-50 p-6 text-center text-sm text-zinc-500 dark:border-zinc-800 dark:bg-zinc-900 dark:text-zinc-400">
                No products found. {searchQuery && "Try a different search term."}
              </div>
            )}

            {!loadingProducts && !productError && products.length > 0 && (
              <div className="overflow-x-auto rounded-lg border border-zinc-200 bg-white dark:border-zinc-800 dark:bg-zinc-900">
                <table className="min-w-full divide-y divide-zinc-200 dark:divide-zinc-800">
                  <thead className="bg-zinc-50 dark:bg-zinc-950">
                    <tr>
                      <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-zinc-500">Product</th>
                      <th className="px-4 py-3 text-right text-xs font-medium uppercase tracking-wider text-zinc-500">Price</th>
                      <th className="px-4 py-3 text-right text-xs font-medium uppercase tracking-wider text-zinc-500">Stock</th>
                      <th className="px-4 py-3 text-right text-xs font-medium uppercase tracking-wider text-zinc-500">Action</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-zinc-200 dark:divide-zinc-800">
                    {products.map((p) => (
                      <tr key={p.id} className="hover:bg-zinc-50 dark:hover:bg-zinc-800/50">
                        <td className="px-4 py-3">
                          <div className="text-sm font-medium text-zinc-900 dark:text-zinc-100">{p.name}</div>
                          <div className="font-mono text-xs text-zinc-500">{p.sku}</div>
                        </td>
                        <td className="whitespace-nowrap px-4 py-3 text-right text-sm font-semibold text-zinc-900 dark:text-zinc-100">
                          ${Number(p.selling_price).toFixed(2)}
                        </td>
                        <td className="whitespace-nowrap px-4 py-3 text-right text-sm">
                          <span
                            className={`inline-flex rounded-full px-2 py-0.5 text-xs font-semibold ${
                              p.stock_quantity <= 0
                                ? "bg-red-100 text-red-700 dark:bg-red-900 dark:text-red-300"
                                : p.is_low_stock
                                  ? "bg-amber-100 text-amber-700 dark:bg-amber-900 dark:text-amber-300"
                                  : "bg-emerald-100 text-emerald-700 dark:bg-emerald-900 dark:text-emerald-300"
                            }`}
                          >
                            {p.stock_quantity}
                          </span>
                        </td>
                        <td className="whitespace-nowrap px-4 py-3 text-right">
                          <button
                            onClick={() => addToCart(p)}
                            disabled={p.stock_quantity <= 0}
                            className="rounded bg-emerald-600 px-3 py-1 text-xs font-medium text-white hover:bg-emerald-700 disabled:cursor-not-allowed disabled:opacity-40"
                          >
                            + Add
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>

          {/* ── Cart (Right) ── */}
          <div className="lg:col-span-2">
            <div className="sticky top-6 space-y-4 rounded-lg border border-zinc-200 bg-white p-5 shadow-sm dark:border-zinc-800 dark:bg-zinc-900">
              <div className="flex items-center justify-between">
                <h2 className="text-lg font-bold text-zinc-900 dark:text-zinc-50">
                  Cart ({cart.length})
                </h2>
                {cart.length > 0 && (
                  <button
                    onClick={clearCart}
                    className="text-xs font-medium text-red-600 hover:text-red-700 dark:text-red-400"
                  >
                    Clear All
                  </button>
                )}
              </div>

              {cart.length === 0 ? (
                <div className="py-8 text-center text-sm text-zinc-400">
                  Cart is empty. Add products to get started.
                </div>
              ) : (
                <div className="space-y-3">
                  {cart.map((item) => (
                    <div
                      key={item.product.id}
                      className="flex items-center gap-3 rounded-md border border-zinc-100 bg-zinc-50 p-3 dark:border-zinc-800 dark:bg-zinc-800/50"
                    >
                      <div className="flex-1 min-w-0">
                        <p className="truncate text-sm font-medium text-zinc-900 dark:text-zinc-100">
                          {item.product.name}
                        </p>
                        <p className="text-xs text-zinc-500">
                          ${Number(item.product.selling_price).toFixed(2)} each
                        </p>
                      </div>
                      <div className="flex items-center gap-1">
                        <button
                          onClick={() =>
                            updateCartQty(item.product.id, item.quantity - 1)
                          }
                          className="flex h-7 w-7 items-center justify-center rounded border border-zinc-300 text-sm hover:bg-zinc-100 dark:border-zinc-600 dark:hover:bg-zinc-700"
                        >
                          −
                        </button>
                        <input
                          type="number"
                          min={1}
                          value={item.quantity}
                          onChange={(e) =>
                            updateCartQty(
                              item.product.id,
                              parseInt(e.target.value) || 0
                            )
                          }
                          className="h-7 w-12 rounded border border-zinc-300 bg-white text-center text-sm dark:border-zinc-600 dark:bg-zinc-800 dark:text-zinc-100"
                        />
                        <button
                          onClick={() =>
                            updateCartQty(item.product.id, item.quantity + 1)
                          }
                          className="flex h-7 w-7 items-center justify-center rounded border border-zinc-300 text-sm hover:bg-zinc-100 dark:border-zinc-600 dark:hover:bg-zinc-700"
                        >
                          +
                        </button>
                      </div>
                      <p className="w-16 text-right text-sm font-semibold text-zinc-900 dark:text-zinc-100">
                        ${(Number(item.product.selling_price) * item.quantity).toFixed(2)}
                      </p>
                      <button
                        onClick={() => removeFromCart(item.product.id)}
                        className="text-red-400 hover:text-red-600"
                        title="Remove"
                      >
                        <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2}>
                          <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
                        </svg>
                      </button>
                    </div>
                  ))}
                </div>
              )}

              {/* Total & Checkout */}
              {cart.length > 0 && (
                <div className="space-y-3 border-t border-zinc-200 pt-4 dark:border-zinc-700">
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium text-zinc-600 dark:text-zinc-400">
                      Subtotal ({cart.reduce((s, c) => s + c.quantity, 0)} items)
                    </span>
                    <span className="text-xl font-bold text-zinc-900 dark:text-zinc-50">
                      ${cartTotal.toFixed(2)}
                    </span>
                  </div>
                  <button
                    onClick={handleCheckout}
                    disabled={checkingOut}
                    className="w-full rounded-md bg-emerald-600 py-2.5 text-sm font-semibold text-white shadow hover:bg-emerald-700 disabled:opacity-50"
                  >
                    {checkingOut ? "Processing…" : `Checkout — $${cartTotal.toFixed(2)}`}
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
