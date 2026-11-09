import { StatusCard } from "@/components/status-card";

export default function DashboardPage() {
  return (
    <div className="p-6 sm:p-10">
      <div className="mx-auto max-w-4xl space-y-8">
        {/* Welcome section */}
        <section className="space-y-2">
          <h1 className="text-3xl font-bold tracking-tight text-zinc-900 dark:text-zinc-50">
            Dashboard
          </h1>
          <p className="text-zinc-600 dark:text-zinc-400">
            Welcome to StockSense. Manage your inventory from the sidebar
            navigation.
          </p>
        </section>

        {/* Status overview */}
        <section className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          <StatusCard
            title="Products"
            value="—"
            description="View in Products page"
          />
          <StatusCard
            title="Low Stock Alerts"
            value="—"
            description="Coming in Phase 3"
          />
          <StatusCard
            title="Sales Today"
            value="—"
            description="Coming in Phase 4"
          />
        </section>

        {/* System status */}
        <section className="rounded-lg border border-zinc-200 bg-white p-6 dark:border-zinc-800 dark:bg-zinc-900">
          <h2 className="text-lg font-semibold text-zinc-900 dark:text-zinc-50">
            System Status
          </h2>
          <p className="mt-1 text-sm text-zinc-500 dark:text-zinc-400">
            Phase 2 — Product and category management is available. Use the
            Products and Categories pages to manage your inventory catalog.
          </p>
        </section>
      </div>
    </div>
  );
}
