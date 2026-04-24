import { TraceRecord } from "@/app/lib/types";

type Props = {
  trace: TraceRecord | null;
};

export function TraceDetail({ trace }: Props) {
  if (!trace) {
    return (
      <section className="panel">
        <div className="panelHeader">
          <div>
            <p className="eyebrow">Trace Detail</p>
            <h2>Select a Trace</h2>
          </div>
        </div>
        <div className="detailBody">
          <p className="emptyState">Click a trace row to inspect spans, generations, and attached scores.</p>
        </div>
      </section>
    );
  }

  return (
    <section className="panel">
      <div className="panelHeader">
        <div>
          <p className="eyebrow">View 2</p>
          <h2>Trace #{trace.id}</h2>
        </div>
      </div>
      <div className="detailBody">
        <div className="detailGrid">
          <article className="detailCard">
            <h3>Trace</h3>
            <p><strong>Name:</strong> {trace.name}</p>
            <p><strong>Status:</strong> {trace.status}</p>
            <p><strong>Session:</strong> {trace.session_id ?? "n/a"}</p>
            <p><strong>User:</strong> {trace.user_id ?? "n/a"}</p>
          </article>
          <article className="detailCard">
            <h3>Input</h3>
            <pre>{trace.input}</pre>
          </article>
          <article className="detailCard">
            <h3>Output</h3>
            <pre>{trace.output ?? "n/a"}</pre>
          </article>
        </div>

        <div className="detailGrid">
          <article className="detailCard wide">
            <h3>Spans & Generations</h3>
            {trace.spans.map((span) => (
              <div key={span.id} className="spanBlock">
                <p>
                  <strong>{span.name}</strong> - {span.type} - {span.latency_ms} ms
                </p>
                {span.generations.map((generation) => (
                  <div key={generation.id} className="generationBlock">
                    <p>
                      <strong>{generation.model}</strong> - {generation.total_tokens} tokens - ${generation.cost_usd}
                    </p>
                    <pre>{generation.response}</pre>
                  </div>
                ))}
              </div>
            ))}
          </article>

          <article className="detailCard">
            <h3>Scores</h3>
            <div className="scoreList">
              {trace.scores.map((score) => (
                <div key={score.id} className="scoreRow">
                  <span>{score.name}</span>
                  <strong>{String(score.value)}</strong>
                </div>
              ))}
            </div>
          </article>
        </div>
      </div>
    </section>
  );
}
