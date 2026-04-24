"use client";

import { useTransition } from "react";
import { useRouter } from "next/navigation";

import { submitFeedback } from "@/app/lib/api";

type Props = {
  traceId: number;
  currentFeedback: "up" | "down" | null;
};

export function FeedbackButtons({ traceId, currentFeedback }: Props) {
  const router = useRouter();
  const [isPending, startTransition] = useTransition();

  function handleClick(feedback: "up" | "down") {
    startTransition(async () => {
      await submitFeedback(traceId, feedback);
      router.refresh();
    });
  }

  return (
    <div className="feedbackActions">
      <button
        className={currentFeedback === "up" ? "feedbackButton active" : "feedbackButton"}
        disabled={isPending}
        onClick={() => handleClick("up")}
        type="button"
      >
        👍
      </button>
      <button
        className={currentFeedback === "down" ? "feedbackButton active negative" : "feedbackButton"}
        disabled={isPending}
        onClick={() => handleClick("down")}
        type="button"
      >
        👎
      </button>
    </div>
  );
}
