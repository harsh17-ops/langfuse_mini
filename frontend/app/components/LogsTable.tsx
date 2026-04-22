import { FeedbackButtons } from "@/app/components/FeedbackButtons";
import { LogRecord } from "@/app/lib/types";

type Props = {
  logs: LogRecord[];
};

export function LogsTable({ logs }: Props) {
  return (
    <section className="panel">
      <div className="panelHeader">
        <div>
          <p className="eyebrow">Trace Explorer</p>
          <h2>LLM Request Logs</h2>
        </div>
      </div>
      <div className="tableWrap">
        <table>
          <thead>
            <tr>
              <th>Time</th>
              <th>Prompt</th>
              <th>Response</th>
              <th>Model</th>
              <th>Latency</th>
              <th>Tokens</th>
              <th>Feedback</th>
            </tr>
          </thead>
          <tbody>
            {logs.map((log) => (
              <tr key={log.id}>
                <td>{new Date(log.created_at).toLocaleString()}</td>
                <td>{log.prompt}</td>
                <td>{log.response}</td>
                <td>{log.model_name}</td>
                <td>{log.latency_ms} ms</td>
                <td>{log.total_tokens}</td>
                <td>
                  <FeedbackButtons logId={log.id} currentFeedback={log.feedback} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {logs.length === 0 ? <p className="emptyState">No logs yet. Send a request to the backend `/api/chat` endpoint first.</p> : null}
      </div>
    </section>
  );
}

