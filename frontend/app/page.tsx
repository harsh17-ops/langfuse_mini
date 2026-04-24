import { AnalyticsPanel } from "@/app/components/AnalyticsPanel";
import { PlaygroundPanel } from "@/app/components/PlaygroundPanel";
import { PromptPanel } from "@/app/components/PromptPanel";
import { ScoreFilterPanel } from "@/app/components/ScoreFilterPanel";
import { StatsCards } from "@/app/components/StatsCards";
import { TraceDetail } from "@/app/components/TraceDetail";
import { TraceTable } from "@/app/components/TraceTable";
import { fetchPromptMetrics, fetchPrompts, fetchScoreFilter, fetchStats, fetchTrace, fetchTraces } from "@/app/lib/api";

type SearchParams = {
  traceId?: string;
  search?: string;
  scoreName?: string;
  minValue?: string;
  promptName?: string;
};

export default async function HomePage({ searchParams }: { searchParams: SearchParams }) {
  const selectedTraceId = searchParams.traceId ? Number(searchParams.traceId) : undefined;
  const selectedPromptName = searchParams.promptName ?? null;

  const [stats, traces, prompts, trace, scoreFilter, promptMetrics] = await Promise.all([
    fetchStats(),
    fetchTraces(searchParams.search),
    fetchPrompts(),
    selectedTraceId ? fetchTrace(selectedTraceId) : Promise.resolve(null),
    searchParams.scoreName ? fetchScoreFilter(searchParams.scoreName, searchParams.minValue) : Promise.resolve(null),
    selectedPromptName ? fetchPromptMetrics(selectedPromptName) : Promise.resolve([])
  ]);

  return (
    <main className="pageShell">
      <section className="hero">
        <div>
          <p className="eyebrow">NLP / Transformers Interview Build</p>
          <h1>Mini Langfuse Observability Platform</h1>
          <p className="heroCopy">
            This dashboard now mirrors the Langfuse-style hierarchy of traces, spans, generations, scores,
            and prompt templates. It also adds NLP-specific evaluation with semantic similarity, classifier
            scores, and LLM-as-judge metrics.
          </p>
        </div>
      </section>
      <StatsCards stats={stats} />
      <section className="panel">
        <div className="panelHeader">
          <div>
            <p className="eyebrow">Search</p>
            <h2>Trace Explorer</h2>
          </div>
          <form className="inlineForm">
            <input defaultValue={searchParams.search ?? ""} name="search" placeholder="search traces" />
            <button type="submit">Search</button>
          </form>
        </div>
      </section>
      <TraceTable selectedTraceId={selectedTraceId} traces={traces} />
      <TraceDetail trace={trace} />
      <AnalyticsPanel stats={stats} traces={traces} />
      <ScoreFilterPanel result={scoreFilter} />
      <PromptPanel metrics={promptMetrics} prompts={prompts} selectedPromptName={selectedPromptName} />
      <PlaygroundPanel prompts={prompts} />
    </main>
  );
}
