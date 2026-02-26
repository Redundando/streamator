# Streamator — Product Overview

## Purpose
Streamator is a monorepo providing paired backend and frontend libraries for streaming
real-time log output from long-running async jobs to a browser UI. It solves the common
pattern of "start a job, watch its progress live" without requiring WebSockets or custom
infrastructure.

## Value Proposition
- Zero-boilerplate SSE streaming from Python async jobs to React UIs
- Two storage backends: in-memory (single-process) or DynamoDB (distributed/persistent)
- Drop-in replacement for inline log streaming code duplicated across projects
- Part of the `*rator` family: `dynamorator`, `searcherator`, `cacherator`, `logorator`

## Packages

### `streamator` (PyPI)
Backend logging primitive for long-running async jobs.
- `JobLogger` — creates a job ID, appends timestamped log entries to a store
- `MemoryStore` — asyncio.Queue-backed, SSE push model, zero dependencies
- `DynamoStore` — DynamoDB-backed via `dynamorator`, persists across restarts
- `streamator.fastapi` — optional FastAPI route helpers for SSE and snapshot endpoints

### `streamator-react` (npm)
Frontend primitives for displaying live log streams.
- `useLogStream(url, options)` — React hook, supports SSE and polling modes
- `LogPanel` — pre-built component with auto-scroll, level styling, waiting state
- `makeFormatEvent(overrides)` — utility to map structured events to display strings
- `BASE_EVENT_LABELS` — built-in labels for common audible-toolkit events
- `log.css` — default styles via CSS custom properties, fully overridable

## Key Features
- SSE streaming (EventSource) and polling modes in the React hook
- Log levels: `info`, `success`, `warning`, `error` with per-level CSS classes
- Elapsed time (`t`) on every entry — computed server-side for SSE, client-side fallback for poll
- `formatEvent` override to suppress or reformat individual log entries
- `LogPanel` renders null when idle, shows pulse animation while waiting
- CSS custom properties for theming (`--streamator-bg`, `--streamator-border`, etc.)
- Compat CSS (`log-compat.css`) for projects migrating from old class names

## Target Users
Developers in the `audible-toolkit` / `*rator` ecosystem building FastAPI backends with
React frontends that run long async jobs (scraping, LLM calls, batch processing) and need
to surface progress to users in real time.

## Primary Use Case
```python
# Backend
logger = JobLogger()
asyncio.create_task(my_job(logger))
return {"log_job_id": logger.job_id}
```
```jsx
// Frontend
const { logs, active } = useLogStream(`/api/log/${jobId}/stream`)
<LogPanel logs={logs} active={active} />
```
