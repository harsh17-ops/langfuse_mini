"use client";

import { useState, useTransition } from "react";
import { useRouter } from "next/navigation";

import { createPrompt, createPromptVersion, promotePrompt } from "@/app/lib/api";

export function PromptManager() {
  const router = useRouter();
  const [isPending, startTransition] = useTransition();
  const [name, setName] = useState("");
  const [content, setContent] = useState("Answer the user request clearly: {input}");
  const [label, setLabel] = useState<"staging" | "production">("staging");
  const [versionName, setVersionName] = useState("");
  const [versionContent, setVersionContent] = useState("");
  const [promoteName, setPromoteName] = useState("");
  const [promoteVersion, setPromoteVersion] = useState("1");

  function onCreatePrompt() {
    startTransition(async () => {
      await createPrompt(name, content, label);
      router.refresh();
    });
  }

  function onCreateVersion() {
    startTransition(async () => {
      await createPromptVersion(versionName, versionContent);
      router.refresh();
    });
  }

  function onPromote() {
    startTransition(async () => {
      await promotePrompt(promoteName, Number(promoteVersion));
      router.refresh();
    });
  }

  return (
    <div className="managerGrid">
      <div className="detailCard">
        <h3>Create Prompt</h3>
        <input onChange={(event) => setName(event.target.value)} placeholder="prompt name" value={name} />
        <textarea onChange={(event) => setContent(event.target.value)} rows={4} value={content} />
        <select onChange={(event) => setLabel(event.target.value as "staging" | "production")} value={label}>
          <option value="staging">staging</option>
          <option value="production">production</option>
        </select>
        <button disabled={isPending || !name || !content} onClick={onCreatePrompt} type="button">Create</button>
      </div>
      <div className="detailCard">
        <h3>New Version</h3>
        <input onChange={(event) => setVersionName(event.target.value)} placeholder="prompt name" value={versionName} />
        <textarea onChange={(event) => setVersionContent(event.target.value)} placeholder="new version content" rows={4} value={versionContent} />
        <button disabled={isPending || !versionName || !versionContent} onClick={onCreateVersion} type="button">Add Version</button>
      </div>
      <div className="detailCard">
        <h3>Promote Version</h3>
        <input onChange={(event) => setPromoteName(event.target.value)} placeholder="prompt name" value={promoteName} />
        <input onChange={(event) => setPromoteVersion(event.target.value)} placeholder="version" type="number" value={promoteVersion} />
        <button disabled={isPending || !promoteName || !promoteVersion} onClick={onPromote} type="button">Promote</button>
      </div>
    </div>
  );
}

