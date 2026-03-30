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

// Code blocks with highlight.js
renderer.code = function ({ text, lang }: { text: string; lang?: string }) {
  let highlighted: string;
  if (lang && hljs.getLanguage(lang)) {
    highlighted = hljs.highlight(text, { language: lang }).value;
  } else {
    highlighted = hljs.highlightAuto(text).value;
  }
  return `<pre class="code-block"><code class="hljs language-${lang || "text"}">${highlighted}</code></pre>`;
};

// Table styling — right-align numbers
renderer.tablecell = function ({
  text,
  header,
}: {
  text: string;
  header: boolean;
  align?: string | null;
}) {
  const tag = header ? "th" : "td";
  const isNumeric = /^[+\-]?\d/.test(text.replace(/<[^>]+>/g, "").trim());
  const align = isNumeric && !header ? ' style="text-align:right"' : "";
  return `<${tag}${align}>${text}</${tag}>`;
};

marked.use({ renderer });

/** Render markdown to HTML with highlighting. */
export function renderMarkdown(md: string): string {
  const html = marked.parse(md, { async: false }) as string;
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
