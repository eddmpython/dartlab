/** 마크다운 → HTML 렌더러 (VSCode 확장 수준: 테이블, 코드 접기, 숫자 하이라이트) */
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
 */
export function createIncrementalRenderer() {
	let prevText = "";
	let cachedHtml = "";
	let lastCompleteIdx = 0;
	let prevTail = "";
	let cachedTailHtml = "";

	return {
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

// ── 숫자 유틸 ──

function isNumericCell(text) {
	const s = text.replace(/<\/?strong>/g, '').replace(/\*\*/g, '').trim();
	return /^[−\-+]?[\d,]+\.?\d*[%조억만원배x배]*$/.test(s) || s === '-' || s === '0' || s === 'N/A';
}

/** 5자리 이상 정수에 콤마 추가: 12345 → 12,345 */
function formatLargeNumbers(s) {
	return s.replace(/(?<![.\d])(-?\d{5,})(?!\.\d)/g, (m) => {
		const n = parseInt(m, 10);
		if (isNaN(n)) return m;
		return n.toLocaleString();
	});
}

/** Polars 유니코드 박스 테이블 → GFM 마크다운 변환 */
function polarsToGfm(text) {
	return text.replace(/(┌[\s\S]*?└[─┘]+)/g, (block) => {
		const lines = block.split('\n').filter(l => l.trim());
		const dataRows = lines.filter(l => l.startsWith('│'));
		if (dataRows.length < 2) return block;

		const parse = (row) => row.split('│').slice(1, -1).map(c => c.trim());
		const header = parse(dataRows[0]);
		const sep = header.map(() => '---').join(' | ');
		const rows = dataRows.slice(1).map(r => '| ' + parse(r).join(' | ') + ' |');
		return `| ${header.join(' | ')} |\n| ${sep} |\n${rows.join('\n')}`;
	});
}

// ── 코드 블록 접기 ──

const CODE_FOLD_ICON = '<svg width="10" height="10" viewBox="0 0 16 16" fill="currentColor"><path d="M6 4l4 4-4 4"/></svg>';
const COPY_ICON = '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"/><path d="M5 15H4a2 2 0 01-2-2V4a2 2 0 012-2h9a2 2 0 012 2v1"/></svg>';

function renderCodeBlock(lang, code) {
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

	const lineCount = code.split('\n').length;
	const shouldCollapse = lang === "python" && lineCount > 3;

	if (shouldCollapse) {
		// 첫 번째 의미 있는 줄을 미리보기로 표시
		const preview = code.split('\n').find(l => l.trim() && !l.trim().startsWith('#') && !l.trim().startsWith('import')) || code.split('\n')[0];
		const escapedPreview = preview.trim().replace(/</g, '&lt;').replace(/>/g, '&gt;');
		return `<details class="code-fold"><summary class="code-fold-summary"><span class="code-fold-icon">${CODE_FOLD_ICON}</span><span class="code-fold-label">${lang || 'code'}</span><span class="code-fold-hint">${escapedPreview}</span></summary><div class="code-block-wrap"><button class="code-copy-btn">${COPY_ICON}</button><pre><code class="hljs">${highlighted}</code></pre></div></details>`;
	}

	const langLabel = lang ? `<span class="code-lang-label">${lang}</span>` : "";
	return `<div class="code-block-wrap">${langLabel}<button class="code-copy-btn">${COPY_ICON}</button><pre><code class="hljs">${highlighted}</code></pre></div>`;
}

// ── 테이블 렌더링 ──

function renderTable(block) {
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

	// 헤더 파싱 + 종목코드 컬럼 감지
	const hCells = headerLine ? headerLine.slice(1, -1).split('|').map(c => c.trim()) : [];
	const codeColSet = new Set();
	const skipCols = new Set();
	hCells.forEach((c, i) => {
		const h = c.toLowerCase();
		if (h.includes("종목코드") || h.includes("stockcode") || h === "code") codeColSet.add(i);
		if (c.trim() === "…" || c.trim() === "...") skipCols.add(i);
	});

	let tableHtml = '<div class="table-wrap"><table>';
	if (headerLine) {
		tableHtml += '<thead><tr>';
		hCells.forEach((c, i) => {
			if (skipCols.has(i)) return;
			let rendered = c.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
			tableHtml += `<th>${rendered}</th>`;
		});
		tableHtml += '</tr></thead>';
	}

	if (dataLines.length > 0) {
		tableHtml += '<tbody>';
		for (const line of dataLines) {
			const cells = line.slice(1, -1).split('|').map(c => c.trim());
			tableHtml += '<tr>';
			cells.forEach((c, i) => {
				if (skipCols.has(i)) return;
				let rendered = c.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
				// 숫자 셀: 우측 정렬 + 콤마 포맷 (종목코드 컬럼 제외)
				if (isNumericCell(c) && !codeColSet.has(i)) {
					rendered = formatLargeNumbers(rendered);
					tableHtml += `<td class="num">${rendered}</td>`;
				} else {
					tableHtml += `<td>${rendered}</td>`;
				}
			});
			tableHtml += '</tr>';
		}
		tableHtml += '</tbody>';
	}
	tableHtml += '</table></div>';
	return tableHtml;
}

// ── 메인 렌더러 ──

export function renderMarkdown(text) {
	if (!text) return "";

	// Polars 유니코드 테이블 → GFM 변환
	text = polarsToGfm(text);

	let codeBlocks = [];
	let tableBlocks = [];

	// 코드 블록 추출
	let processed = text.replace(/```(\w*)\n([\s\S]*?)```/g, (_, lang, code) => {
		const idx = codeBlocks.length;
		codeBlocks.push({ lang: lang || "", code: code.trimEnd() });
		return `\n%%CODE_${idx}%%\n`;
	});

	// 테이블 추출
	processed = processed.replace(/((?:^\|.+\|$\n?)+)/gm, (block) => {
		const idx = tableBlocks.length;
		tableBlocks.push(renderTable(block));
		return `\n%%TABLE_${idx}%%\n`;
	});

	// 인라인 마크다운
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

	// 테이블 복원
	for (let i = 0; i < tableBlocks.length; i++) {
		html = html.replace(`%%TABLE_${i}%%`, tableBlocks[i]);
	}

	// 코드 블록 복원
	for (let i = 0; i < codeBlocks.length; i++) {
		const { lang, code } = codeBlocks[i];
		html = html.replace(`%%CODE_${i}%%`, renderCodeBlock(lang, code));
	}

	// 숫자 하이라이트 (테이블/코드 외 텍스트)
	html = html.replace(/(?<=>|^)([^<]*?)(?=<|$)/g, (_, text) => {
		return text.replace(/(?<![a-zA-Z가-힣/\-])([−\-+]?\d[\d,]*\.?\d*)(\s*)(억원|억|만원|만|조원|조|원|천원|%|배|bps|bp)/g,
			'<span class="num-highlight">$1$2$3</span>');
	});

	// 소스 인용 각주
	html = html.replace(/(?<![<\w])\[(\d{1,2})\](?![<(])/g,
		'<sup class="cite-ref" data-cite="$1">[$1]</sup>'
	);

	return '<p>' + html + '</p>';
}
