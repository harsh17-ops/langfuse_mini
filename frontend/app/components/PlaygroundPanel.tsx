"use client";

import { useState, useTransition } from "react";

import { comparePlayground } from "@/app/lib/api";
import { PlaygroundCompareResponse, PromptTemplate } from "@/app/lib/types";

type Props = {
  prompts: PromptTemplate[];
};

export function PlaygroundPanel({ prompts }: Props) {
  const [isPending, startTransition] = useTransition();
  const [prompt, setPrompt] = useState("Explain retrieval augmented generation for an NLP interview.");
  const [primaryModel, setPrimaryModel] = useState("llama-3.1-8b-instant");
  const [secondaryModel, setSecondaryModel] = useState("llama-3.3-70b-versatile");
  const [templateName, setTemplateName] = useState("");
  const [result, setResult] = useState<PlaygroundCompareResponse | null>(null);

  function runCompare() {
    startTransition(async () => {
      const response = await comparePlayground({
        prompt,
        primary_model: primaryModel,
        secondary_model: secondaryModel,
        prompt_template_name: templateName || undefined
      });
      setResult(response);
    });
  }

  const uniquePromptNames = Array.from(new Set(prompts.map((promptTemplate) => promptTemplate.name)));

  return (
    <section className="panel">
      <div className="panelHeader">
        <div>
          <p className="eyebrow">Playground</p>
          <h2>Model Comparison</h2>
        </div>
      </div>
      <div className="detailBody">
        <div className="managerGrid">
          <div className="detailCard wide">
            <textarea onChange={(event) => setPrompt(event.target.value)} rows={4} value={prompt} />
            <div className="managerGrid compact">
              <select onChange={(event) => setPrimaryModel(event.target.value)} value={primaryModel}>
                <option value="llama-3.1-8b-instant">llama-3.1-8b-instant</option>
                <option value="llama-3.3-70b-versatile">llama-3.3-70b-versatile</option>
              </select>
              <select onChange={(event) => setSecondaryModel(event.target.value)} value={secondaryModel}>
                <option value="llama-3.1-8b-instant">llama-3.1-8b-instant</option>
                <option value="llama-3.3-70b-versatile">llama-3.3-70b-versatile</option>
              </select>
              <select onChange={(event) => setTemplateName(event.target.value)} value={templateName}>
                <option value="">no prompt template</option>
                {uniquePromptNames.map((name) => (
                  <option key={name} value={name}>{name}</option>
                ))}
              </select>
              <button disabled={isPending} onClick={runCompare} type="button">Compare</button>
            </div>
          </div>
        </div>

        {result ? (
          <div className="detailGrid">
            {result.results.map((item) => (
              <article key={item.model_name} className="detailCard">
                <h3>{item.model_name}</h3>
                <p>{item.latency_ms} ms - {item.total_tokens} tokens - ${item.cost_usd}</p>
                <p>Semantic similarity: {item.semantic_similarity?.toFixed(3) ?? "n/a"}</p>
                <pre>{item.response}</pre>
              </article>
            ))}
          </div>
        ) : null}
      </div>
    </section>
  );
}
