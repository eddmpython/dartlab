/** 마크다운 → HTML 렌더러 (테이블, 코드블록, 숫자 하이라이트 포함) */
import hljs from "highlight.js/lib/core";
import python from "highlight.js/lib/languages/python";
import javascript from "highlight.js/lib/languages/javascript";
import json from "highlight.js/lib/languages/json";
import sql from "highlight.js/lib/languages/sql";
import bash from "highlight.js/lib/languages/bash";
import xml from "highlight.js/lib/languages/xml";

hljs.registerLanguage("python", python);
hljs.registerLanguage("javascript", javascript);
hljs.registerLanguage("js", javascript);
hljs.registerLanguage("json", json);
hljs.registerLanguage("sql", sql);
hljs.registerLanguage("bash", bash);
hljs.registerLanguage("sh", bash);
hljs.registerLanguage("html", xml);
hljs.registerLanguage("xml", xml);

/**
 * 증분 마크다운 렌더러 — 스트리밍 중 새 텍스트만 파싱.
 * 이전 완결 블록의 HTML을 캐시하고 마지막 미완결 블록만 재파싱.
 */
export function createIncrementalRenderer() {
	let prevText = "";
	let cachedHtml = "";
	let lastCompleteIdx = 0;
	let prevTail = "";
	let cachedTailHtml = "";

	return {
		/** 전체 텍스트(누적)를 받아서 HTML을 반환. 새 부분만 재파싱. */
		render(fullText) {
			if (!fullText) return "";
			const lastDoubleNewline = fullText.lastIndexOf("\n\n");
			if (lastDoubleNewline > lastCompleteIdx && lastDoubleNewline <= fullText.length - 2) {
				const completeText = fullText.slice(0, lastDoubleNewline + 2);
				if (completeText !== prevText) {
					cachedHtml = renderMarkdown(completeText);
					prevText = completeText;
					lastCompleteIdx = lastDoubleNewline;
				}
				const tail = fullText.slice(lastDoubleNewline + 2);
				if (!tail) return cachedHtml;
				if (tail === prevTail) return cachedHtml + cachedTailHtml;
				cachedTailHtml = renderMarkdown(tail);
				prevTail = tail;
				return cachedHtml + cachedTailHtml;
			}
			return renderMarkdown(fullText);
		},
		reset() {
			prevText = "";
			cachedHtml = "";
			lastCompleteIdx = 0;
			prevTail = "";
			cachedTailHtml = "";
		},
	};
}

function isNumericCell(text) {
	const s = text.replace(/<\/?strong>/g, '').replace(/\*\*/g, '').trim();
	return /^[−\-+]?[\d,]+\.?\d*[%조억만원배x]*$/.test(s) || s === '-' || s === '0';
}

export function renderMarkdown(text) {
	if (!text) return "";

	let codeBlocks = [];
	let tableBlocks = [];
	let processed = text.replace(/```(\w*)\n([\s\S]*?)```/g, (_, lang, code) => {
		const idx = codeBlocks.length;
		codeBlocks.push({ lang: lang || "", code: code.trimEnd() });
		return `\n%%CODE_${idx}%%\n`;
	});

	processed = processed.replace(/((?:^\|.+\|$\n?)+)/gm, (block) => {
		const lines = block.trim().split('\n').filter(l => l.trim());
		let headerLine = null;
		let sepIdx = -1;
		let dataLines = [];

		for (let i = 0; i < lines.length; i++) {
			const cells = lines[i].slice(1, -1).split('|').map(c => c.trim());
			if (cells.every(c => /^[\-:]+$/.test(c))) {
				sepIdx = i;
				break;
			}
		}

		if (sepIdx > 0) {
			headerLine = lines[sepIdx - 1];
			dataLines = lines.slice(sepIdx + 1);
		} else if (sepIdx === 0) {
			dataLines = lines.slice(1);
		} else {
			headerLine = lines[0];
			dataLines = lines.slice(1);
		}

		let tableHtml = '<table>';
		if (headerLine) {
			const hCells = headerLine.slice(1, -1).split('|').map(c => c.trim());
			tableHtml += '<thead><tr>' + hCells.map(c => {
				let rendered = c.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
				return `<th>${rendered}</th>`;
			}).join('') + '</tr></thead>';
		}

		if (dataLines.length > 0) {
			tableHtml += '<tbody>';
			for (const line of dataLines) {
				const cells = line.slice(1, -1).split('|').map(c => c.trim());
				tableHtml += '<tr>' + cells.map(c => {
					let rendered = c.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
					const align = isNumericCell(c) ? ' class="num"' : '';
					return `<td${align}>${rendered}</td>`;
				}).join('') + '</tr>';
			}
			tableHtml += '</tbody>';
		}
		tableHtml += '</table>';

		let idx = tableBlocks.length;
		tableBlocks.push(tableHtml);
		return `\n%%TABLE_${idx}%%\n`;
	});

	let html = processed
		.replace(/`([^`]+)`/g, '<code>$1</code>')
		.replace(/^### (.+)$/gm, '<h3>$1</h3>')
		.replace(/^## (.+)$/gm, '<h2>$1</h2>')
		.replace(/^# (.+)$/gm, '<h1>$1</h1>')
		.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
		.replace(/\*([^*]+)\*/g, '<em>$1</em>')
		.replace(/^[•\-\*] (.+)$/gm, '<li>$1</li>')
		.replace(/^\d+\. (.+)$/gm, '<li>$1</li>')
		.replace(/^> (.+)$/gm, '<blockquote>$1</blockquote>')
		.replace(/\n\n/g, '</p><p>')
		.replace(/\n/g, '<br>');
	html = html.replace(/(<li>.*?<\/li>(\s*<br>)?)+/g, m => '<ul>' + m.replace(/<br>/g, '') + '</ul>');

	for (let i = 0; i < tableBlocks.length; i++) {
		html = html.replace(`%%TABLE_${i}%%`, tableBlocks[i]);
	}

	for (let i = 0; i < codeBlocks.length; i++) {
		const { lang, code } = codeBlocks[i];
		let highlighted;
		try {
			if (lang && hljs.getLanguage(lang)) {
				highlighted = hljs.highlight(code, { language: lang }).value;
			} else {
				highlighted = hljs.highlightAuto(code).value;
			}
		} catch {
			highlighted = code.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
		}
		const langLabel = lang ? `<span class="code-lang-label">${lang}</span>` : "";
		html = html.replace(`%%CODE_${i}%%`,
			`<div class="code-block-wrap">${langLabel}<button class="code-copy-btn" data-code-idx="${i}"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"/><path d="M5 15H4a2 2 0 01-2-2V4a2 2 0 012-2h9a2 2 0 012 2v1"/></svg></button><pre><code class="hljs">${highlighted}</code></pre></div>`
		);
	}

	html = html.replace(/(?<=>|^)([^<]*?)(?=<|$)/g, (_, text) => {
		return text.replace(/(?<![a-zA-Z가-힣/\-])([−\-+]?\d[\d,]*\.?\d*)(\s*)(억원|억|만원|만|조원|조|원|천원|%|배|bps|bp)/g,
			'<span class="num-highlight">$1$2$3</span>');
	});

	// 소스 인용 각주: [1], [2] 등 → 인라인 참조 뱃지
	html = html.replace(/(?<![<\w])\[(\d{1,2})\](?![<(])/g,
		'<sup class="cite-ref" data-cite="$1">[$1]</sup>'
	);

	return '<p>' + html + '</p>';
}
