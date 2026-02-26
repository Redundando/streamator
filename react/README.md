# streamator-react

Frontend primitives for displaying live log streams in React. Handles SSE connection,
entry formatting, auto-scroll, and rendering.

Pairs with [`streamator`](https://pypi.org/project/streamator/) on the backend.

## Install

```bash
npm install streamator-react
```

## Usage

```jsx
import { useLogStream, LogPanel } from "streamator-react"
import "streamator-react/log.css"

const { logs, active } = useLogStream(`/api/log/${jobId}/stream`)

<LogPanel logs={logs} active={active} />
```

## `useLogStream(url, options)`

```js
const { logs, active } = useLogStream(url, {
  mode: "sse",          // "sse" (default) | "poll"
  interval: 3000,       // poll interval ms — poll mode only
  formatEvent: fn,      // (rawEvent) => string | null
})
```

- `logs` — `Array<{ text, t, level }>` — ready to render
- `active` — `true` while stream is open / polling
- Passing `null` or `undefined` as `url` is a no-op

## `LogPanel` props

```jsx
<LogPanel
  logs={logs}
  active={active}
  waitingText="⏳ Starting…"           // shown while active but no logs yet
  maxHeight="200px"                    // default: 160px
  className="my-log"                   // appended to root class
  style={{}}
  renderEntry={(entry, i) => <div />}  // fully custom row renderer
/>
```

Returns `null` when not active and no logs. Auto-scrolls to latest entry.

## `makeFormatEvent(overrides)`

Map structured backend events to display strings:

```js
import { makeFormatEvent } from "streamator-react"

const formatEvent = makeFormatEvent({
  scraping: e => `🔍 Scraping ${e.url}`,
  done:     () => `✅ Finished`,
})

const { logs } = useLogStream(url, { formatEvent })
```

Return `null` from a handler to suppress that entry entirely.

## Styling

Default styles via CSS custom properties — override any of them:

```css
--streamator-bg:            #f8f8f8;
--streamator-border:        #e0e0e0;
--streamator-color:         #444;
--streamator-time-color:    #aaa;
--streamator-radius:        6px;
--streamator-font-size:     0.8rem;
--streamator-max-height:    160px;
--streamator-success-color: #2e7d32;
--streamator-warning-color: #f59e0b;
--streamator-error-color:   #c62828;
```

Migrating from old `.log` / `.log-time` / `.log-waiting` class names?

```js
import "streamator-react/log-compat.css"
```
