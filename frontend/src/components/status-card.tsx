/**
 * A simple card displaying a metric title, value, and description.
 * Used on the dashboard to show placeholder KPIs.
 */

interface StatusCardProps {
  title: string;
  value: string;
  description: string;
}

export function StatusCard({ title, value, description }: StatusCardProps) {
  return (
    <div className="rounded-lg border border-zinc-200 bg-white p-6 dark:border-zinc-800 dark:bg-zinc-900">
      <p className="text-sm font-medium text-zinc-500 dark:text-zinc-400">
        {title}
      </p>
      <p className="mt-2 text-3xl font-bold text-zinc-900 dark:text-zinc-50">
        {value}
      </p>
      <p className="mt-1 text-xs text-zinc-400 dark:text-zinc-500">
        {description}
      </p>
    </div>
  );
}
