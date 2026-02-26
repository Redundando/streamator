import { useEffect, useRef } from "react";
import "./log.css";

export function LogPanel({
  logs,
  active,
  waitingText = "⏳ Starting…",
  maxHeight,
  className,
  style,
  renderEntry,
  autoScroll = true,
}) {
  const panelRef = useRef(null);

  useEffect(() => {
    if (autoScroll && panelRef.current)
      panelRef.current.scrollTop = panelRef.current.scrollHeight;
  }, [logs, autoScroll]);

  if (!active && logs.length === 0) return null;

  const rootStyle = maxHeight
    ? { ...style, "--streamator-max-height": maxHeight }
    : style;

  return (
    <div
      ref={panelRef}
      className={["streamator-log", className].filter(Boolean).join(" ")}
      style={rootStyle}
    >
      {active && logs.length === 0 && (
        <div className="streamator-log-waiting">{waitingText}</div>
      )}
      {logs.map((entry, i) =>
        renderEntry ? (
          renderEntry(entry, i)
        ) : (
          <div
            key={i}
            className={[
              "streamator-log-entry",
              entry.level !== "info" ? `streamator-log-entry--${entry.level}` : "",
            ]
              .filter(Boolean)
              .join(" ")}
          >
            <span className="streamator-log-time">{entry.t}</span>
            <span>{entry.text}</span>
          </div>
        )
      )}
    </div>
  );
}
