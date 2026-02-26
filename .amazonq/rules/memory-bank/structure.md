# Streamator — Project Structure

## Repository Layout
```
streamator/
├── python/                        ← PyPI package: streamator
│   ├── streamator/
│   │   ├── __init__.py            ← Public API: exports JobLogger only
│   │   ├── logger.py              ← JobLogger class
│   │   ├── store.py               ← MemoryStore, DynamoStore
│   │   └── fastapi.py             ← Optional FastAPI route helpers
│   ├── tests/
│   │   ├── __init__.py
│   │   └── test_backend.py
│   ├── .ai-docs/                  ← AI context docs for dependencies
│   │   ├── dynamorator.md
│   │   ├── fastapi.md
│   │   ├── pytest-asyncio.md
│   │   └── pytest.md
│   ├── main.py                    ← Local dev/test entrypoint
│   ├── pyproject.toml
│   └── requirements.txt
├── react/                         ← npm package: streamator-react
│   ├── src/
│   │   ├── index.js               ← Public API: re-exports everything
│   │   ├── useLogStream.js        ← React hook (SSE + poll modes)
│   │   ├── LogPanel.jsx           ← Pre-built log display component
│   │   ├── formatEvent.js         ← makeFormatEvent + BASE_EVENT_LABELS
│   │   └── log.css                ← Default styles (CSS custom properties)
│   ├── package.json
│   └── rollup.config.js           ← Builds CJS + ESM + CSS to dist/
├── demo/                          ← Local dev demo app (private, not published)
│   ├── src/
│   │   ├── main.jsx               ← React entry point
│   │   └── App.jsx                ← Demo app component
│   ├── index.html
│   ├── package.json               ← Links to react/ via file: dependency
│   └── vite.config.js
├── .amazonq/rules/memory-bank/    ← AI memory bank documentation
├── specs.md                       ← Full package specification
├── EC2_SETUP.md                   ← EC2 deployment guide
├── deploy.ps1                     ← Deployment script
├── start.ps1 / start.sh           ← Dev startup scripts
└── setup_ec2*.ps1                 ← EC2 environment setup scripts
```

## Core Components

### Python: `JobLogger` (logger.py)
Central class. On construction: generates `job_id` (UUID4), records `start_t`
(monotonic), instantiates the chosen store, registers itself in `fastapi._loggers`
if fastapi module is available (try/except import).

### Python: Storage Layer (store.py)
Two store classes with a shared informal interface:
- `append(entry: dict)` — write a log entry
- `snapshot() -> list` — read all entries so far
- `close()` — signal end of stream
- `stream()` — async generator (MemoryStore only, yields until None sentinel)

`MemoryStore` uses `asyncio.Queue` for push-based SSE. Maintains a `_log` list for
snapshot access alongside the queue.

`DynamoStore` delegates entirely to `dynamorator.DynamoDBStore`. Each `append` does a
read-modify-write on the DynamoDB item's `logs` list.

### Python: FastAPI Integration (fastapi.py)
Module-level `_loggers` dict maps `job_id → JobLogger`. Populated automatically by
`JobLogger.__init__` via try/except import. Provides:
- `make_stream_response(job_id)` — returns `StreamingResponse` (SSE) or 404
- `add_log_routes(app, prefix)` — registers GET `/{prefix}/{job_id}/stream` and
  GET `/{prefix}/{job_id}` on a FastAPI app

### React: `useLogStream` (useLogStream.js)
Hook managing EventSource or polling lifecycle. Returns `{ logs, active }`.
Cleans up on unmount or URL change. Accepts `formatEvent` override to transform
or suppress entries.

### React: `LogPanel` (LogPanel.jsx)
Presentational component. Renders null when idle+empty. Shows pulse when active+empty.
Auto-scrolls via ref on logs change. Applies `streamator-log-entry--{level}` classes.

### React: `formatEvent` (formatEvent.js)
`makeFormatEvent(overrides)` merges caller overrides with `BASE_EVENT_LABELS` map.
Returns a function `(rawEvent) => string | null`.

## Architectural Patterns

- Thin public API: `__init__.py` exports only `JobLogger`; `index.js` re-exports all
- Optional dependency pattern: `fastapi.py` and `DynamoStore` guard imports with
  try/except or lazy imports inside methods
- Store abstraction: `JobLogger` is store-agnostic; store is injected by string key
- SSE push model (MemoryStore) vs. poll model (DynamoStore) — same frontend hook handles both
- Demo app consumes the react package via `file:../react` local dependency for live dev
