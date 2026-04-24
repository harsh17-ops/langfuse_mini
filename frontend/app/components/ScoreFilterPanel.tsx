import { ScoreFilterResponse } from "@/app/lib/types";

type Props = {
  result: ScoreFilterResponse | null;
};

export function ScoreFilterPanel({ result }: Props) {
  return (
    <section className="panel">
      <div className="panelHeader">
        <div>
          <p className="eyebrow">View 4</p>
          <h2>Scores Filter</h2>
        </div>
        <form className="inlineForm">
          <input defaultValue={result?.score_name ?? "hallucinated"} name="scoreName" placeholder="score name" />
          <input defaultValue={result?.min_value ?? 0.5} name="minValue" placeholder="min value" step="0.1" type="number" />
          <button type="submit">Filter</button>
        </form>
      </div>
      <div className="detailBody">
        {result ? (
          <div className="scoreList">
            {result.traces.map((trace) => (
              <div key={trace.id} className="scoreRow">
                <span>Trace #{trace.id}</span>
                <strong>{trace.input.slice(0, 80)}</strong>
              </div>
            ))}
          </div>
        ) : (
          <p className="emptyState">Use the filter to inspect traces where a specific score crosses a threshold.</p>
        )}
      </div>
    </section>
  );
}

