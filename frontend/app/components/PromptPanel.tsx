import { PromptMetric, PromptTemplate } from "@/app/lib/types";

import { PromptManager } from "@/app/components/PromptManager";

type Props = {
  prompts: PromptTemplate[];
  metrics: PromptMetric[];
  selectedPromptName: string | null;
};

export function PromptPanel({ prompts, metrics, selectedPromptName }: Props) {
  const grouped = prompts.reduce<Record<string, PromptTemplate[]>>((acc, prompt) => {
    acc[prompt.name] = [...(acc[prompt.name] ?? []), prompt];
    return acc;
  }, {});

  return (
    <section className="panel">
      <div className="panelHeader">
        <div>
          <p className="eyebrow">Prompt Management</p>
          <h2>Versioned Prompts</h2>
        </div>
      </div>
      <div className="detailBody">
        <PromptManager />
        <div className="detailGrid">
          <article className="detailCard wide">
            <h3>Templates</h3>
            {Object.entries(grouped).map(([name, versions]) => (
              <div key={name} className="spanBlock">
                <p>
                  <a className="traceLink" href={`/?promptName=${encodeURIComponent(name)}`}>{name}</a>
                </p>
                {versions.map((version) => (
                  <div key={version.id} className="scoreRow">
                    <span>v{version.version} - {version.label}</span>
                    <strong>{version.content.slice(0, 70)}</strong>
                  </div>
                ))}
              </div>
            ))}
          </article>
          <article className="detailCard">
            <h3>{selectedPromptName ? `${selectedPromptName} Metrics` : "Prompt Metrics"}</h3>
            {metrics.length === 0 ? (
              <p className="emptyState">Select a prompt family to compare version performance.</p>
            ) : (
              metrics.map((metric) => (
                <div key={metric.version} className="scoreRow">
                  <span>v{metric.version} - {metric.label}</span>
                  <strong>{metric.avg_overall_score.toFixed(3)} judge</strong>
                </div>
              ))
            )}
          </article>
        </div>
      </div>
    </section>
  );
}
