import { LogsTable } from "@/app/components/LogsTable";
import { StatsCards } from "@/app/components/StatsCards";
import { fetchLogs, fetchStats } from "@/app/lib/api";

export default async function HomePage() {
  const [stats, logs] = await Promise.all([fetchStats(), fetchLogs()]);

  return (
    <main className="pageShell">
      <section className="hero">
        <div>
          <p className="eyebrow">Interview Mini Project</p>
          <h1>Mini Langfuse Clone</h1>
          <p className="heroCopy">
            This dashboard shows LLM request traces, latency, token usage, and end-user feedback.
            It is intentionally simple, but the architecture mirrors real observability platforms.
          </p>
        </div>
      </section>
      <StatsCards stats={stats} />
      <LogsTable logs={logs} />
    </main>
  );
}

