import Link from "next/link";

import { FeedbackButtons } from "@/app/components/FeedbackButtons";
import { TraceSummary } from "@/app/lib/types";

type Props = {
  traces: TraceSummary[];
  selectedTraceId?: number;
};

export function TraceTable({ traces, selectedTraceId }: Props) {
  return (
    <section className="panel">
      <div className="panelHeader">
        <div>
          <p className="eyebrow">View 1</p>
          <h2>Traces</h2>
        </div>
      </div>
      <div className="tableWrap">
        <table>
          <thead>
            <tr>
              <th>Trace</th>
              <th>Input</th>
              <th>Model</th>
              <th>Latency</th>
              <th>Tokens</th>
              <th>Judge</th>
              <th>Semantic</th>
              <th>Feedback</th>
            </tr>
          </thead>
          <tbody>
            {traces.map((trace) => (
              <tr key={trace.id} className={selectedTraceId === trace.id ? "selectedRow" : undefined}>
                <td>
                  <Link className="traceLink" href={`/?traceId=${trace.id}`}>
                    #{trace.id} {trace.name}
                  </Link>
                  <div className="subtle">{new Date(trace.created_at).toLocaleString()}</div>
                </td>
                <td>{trace.input}</td>
                <td>{trace.latest_generation_model ?? "n/a"}</td>
                <td>{trace.latest_generation_latency_ms ? `${trace.latest_generation_latency_ms} ms` : "n/a"}</td>
                <td>{trace.latest_generation_total_tokens ?? "n/a"}</td>
                <td>{trace.overall_score?.toFixed(3) ?? "pending"}</td>
                <td>{trace.semantic_similarity?.toFixed(3) ?? "n/a"}</td>
                <td>
                  <FeedbackButtons traceId={trace.id} currentFeedback={trace.human_feedback} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {traces.length === 0 ? <p className="emptyState">No traces yet. Use the generation endpoint or playground first.</p> : null}
      </div>
    </section>
  );
}

