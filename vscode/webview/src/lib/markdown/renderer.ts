/** Markdown renderer — ported from ui/src/lib/markdown.js */
import { marked } from "marked";
import hljs from "highlight.js/lib/core";
import python from "highlight.js/lib/languages/python";
import javascript from "highlight.js/lib/languages/javascript";
import json from "highlight.js/lib/languages/json";
import bash from "highlight.js/lib/languages/bash";
import sql from "highlight.js/lib/languages/sql";
import xml from "highlight.js/lib/languages/xml";

hljs.registerLanguage("python", python);
hljs.registerLanguage("javascript", javascript);
hljs.registerLanguage("json", json);
hljs.registerLanguage("bash", bash);
hljs.registerLanguage("sql", sql);
hljs.registerLanguage("xml", xml);

// Number highlighting regex (Korean financial units)
const NUM_RE =
  /(?<![a-zA-Z\d])([+\-]?\d[\d,]*\.?\d*)\s*(원|억|만|조|%|배|bps)/g;

function highlightNumbers(html: string): string {
  return html.replace(
    NUM_RE,
    '<span class="num-highlight">$1 $2</span>',
  );
}

// Configure marked
marked.setOptions({
  breaks: true,
  gfm: true,
});

const renderer = new marked.Renderer();

// Extract first meaningful line for code fold summary
function codeSummary(text: string): string {
  const lines = text.split("\n").filter((l) => l.trim() && !l.trim().startsWith("#"));
  const first = lines[0] || text.split("\n")[0] || "";
  return first.length > 60 ? first.slice(0, 57) + "..." : first;
}

// Code blocks -- collapsed by default (Claude Code style)
renderer.code = function ({ text, lang }: { text: string; lang?: string }) {
  let highlighted: string;
  if (lang && hljs.getLanguage(lang)) {
    highlighted = hljs.highlight(text, { language: lang }).value;
  } else {
    highlighted = hljs.highlightAuto(text).value;
  }
  const summary = codeSummary(text);
  const label = lang === "python" ? "Python" : lang || "Code";
  const lineCount = text.split("\n").length;

  // Only collapse Python code (AI-written). Results/output stay visible.
  const shouldCollapse = lang === "python" && lineCount > 3;

  if (!shouldCollapse) {
    return `<pre class="code-block"><code class="hljs language-${lang || "text"}">${highlighted}</code></pre>`;
  }

  // Python code -- collapsed by default
  return `<details class="code-fold">
<summary class="code-fold-summary"><span class="code-fold-icon">▸</span> <span class="code-fold-label">${label}</span> <span class="code-fold-hint">${escapeHtml(summary)}</span></summary>
<pre class="code-block"><code class="hljs language-${lang || "text"}">${highlighted}</code></pre>
</details>`;
};

function escapeHtml(s: string): string {
  return s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}

// Format large numbers with commas for readability
function formatNumber(s: string): string {
  return s.replace(/(?<![.\d])(-?\d{5,})(?!\.\d)/g, (m) => {
    const n = parseInt(m, 10);
    if (isNaN(n)) return m;
    return n.toLocaleString();
  });
}

// Table styling — right-align numbers + format large numbers
renderer.tablecell = function ({
  text,
  header,
}: {
  text: string;
  header: boolean;
  align?: string | null;
}) {
  const tag = header ? "th" : "td";
  const plain = text.replace(/<[^>]+>/g, "").trim();
  const isNumeric = /^[+\-]?\d/.test(plain);
  const align = isNumeric && !header ? ' style="text-align:right"' : "";
  // Format large numbers in non-header cells
  const formatted = !header ? formatNumber(text) : text;
  return `<${tag}${align}>${formatted}</${tag}>`;
};

// Wrap tables with download button
let tableCounter = 0;
renderer.table = function ({ header, rows }: { header: string; rows: string }) {
  const id = `tbl-${++tableCounter}`;
  return `<div class="table-wrap" data-table-id="${id}">
<button class="table-dl-btn" onclick="(function(){var t=document.querySelector('[data-table-id=\\'${id}\\'] table');if(!t)return;var r=[],h=t.querySelectorAll('th');var hr=[];h.forEach(function(c){hr.push(c.textContent)});r.push(hr.join(','));t.querySelectorAll('tbody tr').forEach(function(tr){var row=[];tr.querySelectorAll('td').forEach(function(c){row.push(c.textContent.replace(/,/g,''))});r.push(row.join(','))});var b=new Blob([r.join('\\n')],{type:'text/csv'});var a=document.createElement('a');a.href=URL.createObjectURL(b);a.download='dartlab-table.csv';a.click()})()">CSV</button>
<table><thead>${header}</thead><tbody>${rows}</tbody></table></div>`;
};

marked.use({ renderer });

/** Convert Polars unicode box tables (┌──┬──┐) to GFM markdown tables. */
function polarsToMarkdown(text: string): string {
  if (!text.includes("┌")) return text;
  const lines = text.split("\n");
  const result: string[] = [];
  let inTable = false;
  let headerEmitted = false;
  let colCount = 0;

  for (const line of lines) {
    const s = line.trim();
    if (s.startsWith("┌") && s.endsWith("┐")) { inTable = true; headerEmitted = false; continue; }
    if (s.startsWith("└") && s.endsWith("┘")) { inTable = false; continue; }
    if (!inTable) { result.push(line); continue; }
    if (s.startsWith("╞") || s.startsWith("├")) {
      if (!headerEmitted && colCount > 0) {
        result.push("| " + Array(colCount).fill("---").join(" | ") + " |");
        headerEmitted = true;
      }
      continue;
    }
    if (s.includes("│") || s.includes("┆")) {
      const cells = s.split(/[│┆]/).map(c => c.trim()).filter(c => c);
      if (cells.every(c => ["---", "str", "f64", "i64", "i32", "u32", "u64", "bool", "cat", "date", "datetime"].includes(c))) continue;
      if (cells.length) {
        colCount = Math.max(colCount, cells.length);
        result.push("| " + cells.join(" | ") + " |");
      }
    }
  }
  return result.join("\n");
}

/** Render markdown to HTML with highlighting. */
export function renderMarkdown(md: string): string {
  const preprocessed = polarsToMarkdown(md);
  const html = marked.parse(preprocessed, { async: false }) as string;
  return highlightNumbers(html);
}

/** Incremental renderer for streaming. Caches completed blocks. */
export function createIncrementalRenderer() {
  let lastCompleteIndex = 0;
  let cachedHtml = "";

  return function render(fullText: string): string {
    // Find last complete block boundary (double newline)
    const lastBreak = fullText.lastIndexOf("\n\n");
    if (lastBreak <= lastCompleteIndex) {
      // No new complete blocks — render everything
      return renderMarkdown(fullText);
    }

    // Cache completed portion
    const completePart = fullText.slice(0, lastBreak);
    const remainder = fullText.slice(lastBreak);

    if (lastBreak > lastCompleteIndex) {
      cachedHtml = renderMarkdown(completePart);
      lastCompleteIndex = lastBreak;
    }

    // Render only the trailing portion
    const trailingHtml = renderMarkdown(remainder);
    return cachedHtml + trailingHtml;
  };
}
