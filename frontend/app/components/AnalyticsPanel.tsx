import { DashboardStats, TraceSummary } from "@/app/lib/types";

type Props = {
  stats: DashboardStats;
  traces: TraceSummary[];
};

export function AnalyticsPanel({ stats, traces }: Props) {
  const topModels = traces.reduce<Record<string, number>>((acc, trace) => {
    const model = trace.latest_generation_model ?? "unknown";
    acc[model] = (acc[model] ?? 0) + 1;
    return acc;
  }, {});
  const modelRows = Object.entries(topModels).sort((a, b) => b[1] - a[1]).slice(0, 5);

  return (
    <section className="panel">
      <div className="panelHeader">
        <div>
          <p className="eyebrow">View 3</p>
          <h2>Analytics</h2>
        </div>
      </div>
      <div className="detailBody analyticsGrid">
        <article className="detailCard">
          <h3>Feedback Split</h3>
          <p>Positive: {stats.positive_feedback}</p>
          <p>Negative: {stats.negative_feedback}</p>
        </article>
        <article className="detailCard">
          <h3>Model Comparison</h3>
          {modelRows.map(([model, count]) => (
            <div key={model} className="scoreRow">
              <span>{model}</span>
              <strong>{count}</strong>
            </div>
          ))}
        </article>
        <article className="detailCard">
          <h3>Latency Story</h3>
          <p>P50: approximated from recent traces in the backend analytics service.</p>
          <p>P95: {stats.p95_latency_ms} ms</p>
          <p>Average: {stats.avg_latency_ms} ms</p>
        </article>
      </div>
    </section>
  );
}

