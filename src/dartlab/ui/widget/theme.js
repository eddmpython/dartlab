/**
 * DartLab Embed — 라이트/다크 테마 CSS.
 * Shadow DOM 내부에 주입되는 스타일.
 */

export const WIDGET_CSS = `
:host {
  display: block;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
  font-size: 14px;
  line-height: 1.5;
  --dl-bg: #ffffff;
  --dl-bg-subtle: #f8fafc;
  --dl-text: #1e293b;
  --dl-text-muted: #64748b;
  --dl-border: #e2e8f0;
  --dl-accent: #ea4647;
  --dl-grade-a: #10b981;
  --dl-grade-b: #3b82f6;
  --dl-grade-c: #f59e0b;
  --dl-grade-d: #f97316;
  --dl-grade-f: #ef4444;
}

:host([data-theme="dark"]) {
  --dl-bg: #0f172a;
  --dl-bg-subtle: #1e293b;
  --dl-text: #e2e8f0;
  --dl-text-muted: #94a3b8;
  --dl-border: #334155;
}

@media (prefers-color-scheme: dark) {
  :host(:not([data-theme="light"])) {
    --dl-bg: #0f172a;
    --dl-bg-subtle: #1e293b;
    --dl-text: #e2e8f0;
    --dl-text-muted: #94a3b8;
    --dl-border: #334155;
  }
}

.dl-card {
  background: var(--dl-bg);
  color: var(--dl-text);
  border: 1px solid var(--dl-border);
  border-radius: 12px;
  padding: 16px;
  max-width: 420px;
  box-sizing: border-box;
  cursor: pointer;
  transition: box-shadow 0.2s;
}
.dl-card:hover {
  box-shadow: 0 4px 12px rgba(0,0,0,0.08);
}

.dl-header {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  margin-bottom: 12px;
}
.dl-name {
  font-weight: 700;
  font-size: 16px;
  color: var(--dl-text);
}
.dl-code {
  font-size: 12px;
  color: var(--dl-text-muted);
  margin-left: 6px;
}
.dl-market {
  font-size: 11px;
  color: var(--dl-text-muted);
  background: var(--dl-bg-subtle);
  padding: 2px 8px;
  border-radius: 4px;
}

.dl-divider {
  border: none;
  border-top: 1px solid var(--dl-border);
  margin: 10px 0;
}

.dl-metrics {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 6px 16px;
  margin-bottom: 12px;
}
.dl-metric {
  display: flex;
  justify-content: space-between;
  font-size: 13px;
}
.dl-metric-label {
  color: var(--dl-text-muted);
}
.dl-metric-value {
  font-weight: 600;
}

.dl-grades {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-bottom: 12px;
}
.dl-grade {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  padding: 3px 8px;
  border-radius: 6px;
  background: var(--dl-bg-subtle);
  font-weight: 500;
}
.dl-grade-pill {
  display: inline-block;
  width: 18px;
  height: 18px;
  border-radius: 4px;
  text-align: center;
  line-height: 18px;
  font-size: 11px;
  font-weight: 700;
  color: #fff;
}
.dl-grade-A { background: var(--dl-grade-a); }
.dl-grade-B { background: var(--dl-grade-b); }
.dl-grade-C { background: var(--dl-grade-c); }
.dl-grade-D { background: var(--dl-grade-d); }
.dl-grade-F { background: var(--dl-grade-f); }

.dl-footer {
  text-align: right;
  font-size: 11px;
  color: var(--dl-text-muted);
}
.dl-footer a {
  color: var(--dl-accent);
  text-decoration: none;
}

.dl-skeleton {
  background: linear-gradient(90deg, var(--dl-bg-subtle) 25%, var(--dl-border) 50%, var(--dl-bg-subtle) 75%);
  background-size: 200% 100%;
  animation: dl-shimmer 1.5s infinite;
  border-radius: 6px;
  height: 14px;
  margin: 6px 0;
}
.dl-skeleton-wide { width: 80%; }
.dl-skeleton-med { width: 60%; }
.dl-skeleton-short { width: 40%; }

@keyframes dl-shimmer {
  0% { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}

.dl-error {
  color: var(--dl-accent);
  font-size: 13px;
  text-align: center;
  padding: 24px 16px;
}
`;
