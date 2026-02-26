import { useState, useEffect, useRef } from "react";

const fmt = (t) => `${t.toFixed(1)}s`;

export function useLogStream(url, options = {}) {
  const { mode = "sse", interval = 3000, formatEvent } = options;
  const [logs, setLogs] = useState([]);
  const [active, setActive] = useState(false);
  const startRef = useRef(null);

  const toEntry = (raw, elapsed) => ({
    text: formatEvent ? formatEvent(raw) : (raw.message ?? ""),
    level: raw.level ?? "info",
    t: fmt(raw.t ?? elapsed),
  });

  useEffect(() => {
    if (!url) return;
    setLogs([]);
    setActive(true);
    startRef.current = Date.now();

    if (mode === "sse") {
      const es = new EventSource(url);
      es.onmessage = (e) => {
        const raw = JSON.parse(e.data);
        if (raw.event === "done") { setActive(false); es.close(); return; }
        const elapsed = (Date.now() - startRef.current) / 1000;
        const entry = toEntry(raw, elapsed);
        if (entry.text !== null) setLogs((l) => [...l, entry]);
      };
      es.onerror = () => { setActive(false); es.close(); };
      return () => { es.close(); setActive(false); };
    }

    if (mode === "poll") {
      let seen = 0;
      const id = setInterval(async () => {
        try {
          const res = await fetch(url);
          const { logs: all } = await res.json();
          const elapsed = (Date.now() - startRef.current) / 1000;
          const newEntries = all.slice(seen).map((raw) => toEntry(raw, elapsed));
          seen = all.length;
          if (newEntries.length) setLogs((l) => [...l, ...newEntries.filter(e => e.text !== null)]);
        } catch {}
      }, interval);
      return () => { clearInterval(id); setActive(false); };
    }
  }, [url, mode]);

  return { logs, active };
}
