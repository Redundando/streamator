export const BASE_EVENT_LABELS = {
  page_loaded:       () => "📄 Page loaded",
  batch_started:     () => "📦 Batch started",
  loading_strategy:  e  => `⚙️ Loading strategy: ${e.strategy ?? ""}`,
  llm_started:       () => "🤖 LLM started",
  llm_done:          () => "🤖 LLM done",
  cache_hit:         () => "⚡ Cache hit",
  search_started:    () => "🔍 Search started",
  search_done:       () => "🔍 Search done",
  browser_ready:     () => "🌐 Browser ready",
  retry:             e  => `🔄 Retry ${e.attempt ?? ""}`,
};

export function makeFormatEvent(overrides = {}) {
  const labels = { ...BASE_EVENT_LABELS, ...overrides };
  return (raw) => {
    const fn = labels[raw.event];
    if (fn) return fn(raw);
    return raw.message ?? null;
  };
}
