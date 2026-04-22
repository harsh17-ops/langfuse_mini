import { DashboardStats } from "@/app/lib/types";

type Props = {
  stats: DashboardStats;
};

export function StatsCards({ stats }: Props) {
  const cards = [
    { label: "Total Requests", value: stats.total_requests.toString() },
    { label: "Avg Latency", value: `${stats.avg_latency_ms} ms` },
    { label: "Total Tokens", value: stats.total_tokens.toString() },
    { label: "Positive Feedback", value: stats.positive_feedback.toString() },
    { label: "Negative Feedback", value: stats.negative_feedback.toString() }
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

