import { Header } from "@/components/header";
import { StatusCard } from "@/components/status-card";

export default function Home() {
  return (
    <div className="flex flex-col flex-1 bg-zinc-50 font-sans dark:bg-zinc-950">
      <Header />

      <main className="flex flex-1 flex-col items-center px-6 py-12 sm:px-12">
        <div className="w-full max-w-4xl space-y-8">
          {/* Welcome section */}
          <section className="space-y-2">
            <h1 className="text-3xl font-bold tracking-tight text-zinc-900 dark:text-zinc-50">
              Dashboard
            </h1>
            <p className="text-zinc-600 dark:text-zinc-400">
              Welcome to StockSense. The application foundation is being
              developed — features will appear here as they are built.
            </p>
          </section>

          {/* Status overview */}
          <section className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            <StatusCard
              title="Products"
              value="—"
              description="Coming in Phase 2"
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
              Phase 1 — Project foundation is complete. The backend API and
              frontend shell are running.
            </p>
          </section>
        </div>
      </main>
    </div>
  );
}
