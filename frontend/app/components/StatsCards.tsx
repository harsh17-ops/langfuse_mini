import { DashboardStats } from "@/app/lib/types";

type Props = {
  stats: DashboardStats;
};

export function StatsCards({ stats }: Props) {
  const cards = [
    { label: "Total Traces", value: stats.total_traces.toString() },
    { label: "Avg Latency", value: `${stats.avg_latency_ms} ms` },
    { label: "P95 Latency", value: `${stats.p95_latency_ms} ms` },
    { label: "Total Tokens", value: stats.total_tokens.toString() },
    { label: "Total Cost", value: `$${stats.total_cost_usd.toFixed(4)}` },
    { label: "Avg Judge Score", value: stats.avg_overall_score.toFixed(3) }
  ];

  return (
    <section className="statsGrid">
      {cards.map((card) => (
        <article key={card.label} className="statCard">
          <p className="statLabel">{card.label}</p>
          <h2 className="statValue">{card.value}</h2>
        </article>
      ))}
    </section>
  );
}
