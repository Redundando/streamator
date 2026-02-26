import { useState } from "react";
import { useLogStream, LogPanel } from "streamator-react";
import "streamator-react/log.css";

export default function App() {
  const [jobId, setJobId] = useState(null);
  const { logs, active } = useLogStream(
    jobId ? `/api/log/${jobId}/stream` : null
  );

  async function start() {
    const res = await fetch("/api/start", { method: "POST" });
    const { log_job_id } = await res.json();
    setJobId(log_job_id);
  }

  return (
    <div style={{ maxWidth: 600, margin: "60px auto", fontFamily: "sans-serif" }}>
      <h2>Streamator Demo</h2>
      <button onClick={start} disabled={active}>
        {active ? "Running…" : "Start job"}
      </button>
      <div style={{ marginTop: 16 }}>
        <LogPanel logs={logs} active={active} waitingText="⏳ Starting…" />
      </div>
    </div>
  );
}
