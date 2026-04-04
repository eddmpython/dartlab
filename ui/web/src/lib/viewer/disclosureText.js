/**
 * 공시 텍스트 파싱/포맷팅 유틸리티.
 * SectionsViewer와 TopicRenderer에서 공유.
 */

import { renderMarkdown } from "$lib/markdown.js";

export function escapeHtml(text) {
	return String(text)
		.replaceAll("&", "&amp;")
		.replaceAll("<", "&lt;")
		.replaceAll(">", "&gt;")
		.replaceAll('"', "&quot;")
		.replaceAll("'", "&#39;");
}

export function normalizeDisclosureLine(line) {
	return String(line || "")
		.replaceAll("\u00a0", " ")
		.replace(/\s+/g, " ")
		.trim();
}

export function isStructuralHeadingLine(line) {
	if (!line || line.length > 88) return false;
	return /^\[.+\]$/.test(line)
		|| /^【.+】$/.test(line)
		|| /^[IVX]+\.\s/.test(line)
		|| /^\d+\.\s/.test(line)
		|| /^[가-힣]\.\s/.test(line)
		|| /^\(\d+\)\s/.test(line)
		|| /^\([가-힣]\)\s/.test(line);
}

export function headingTag(line) {
	if (/^\(\d+\)\s/.test(line) || /^\([가-힣]\)\s/.test(line)) return "h5";
	return "h4";
}

export function headingClass(line) {
	if (/^\[.+\]$/.test(line) || /^【.+】$/.test(line)) return "vw-h-bracket";
	if (/^\(\d+\)\s/.test(line) || /^\([가-힣]\)\s/.test(line)) return "vw-h-sub";
	return "vw-h-section";
}

export function parseDisclosureUnits(text) {
	if (!text) return [];
	if (/^\|.+\|$/m.test(text) || /^#{1,3} /m.test(text) || /```/.test(text)) {
		return [{ kind: "markdown", text }];
	}

	const units = [];
	let paragraph = [];
	const flushParagraph = () => {
		if (paragraph.length === 0) return;
		units.push({ kind: "paragraph", text: paragraph.join(" ") });
		paragraph = [];
	};

	for (const rawLine of String(text).split("\n")) {
		const line = normalizeDisclosureLine(rawLine);
		if (!line) {
			flushParagraph();
			continue;
		}
		if (isStructuralHeadingLine(line)) {
			flushParagraph();
			units.push({ kind: "heading", text: line, tag: headingTag(line), className: headingClass(line) });
			continue;
		}
		paragraph.push(line);
	}
	flushParagraph();
	return units;
}

export function formatDisclosureText(text) {
	const units = parseDisclosureUnits(text);
	if (units.length === 0) return "";
	if (units[0]?.kind === "markdown") return renderMarkdown(text);
	let html = "";
	for (const unit of units) {
		if (unit.kind === "heading") {
			html += `<${unit.tag} class="${unit.className}">${escapeHtml(unit.text)}</${unit.tag}>`;
			continue;
		}
		html += `<p class="vw-para">${escapeHtml(unit.text)}</p>`;
	}
	return html;
}

export function formatHeadingText(text) {
	if (!text) return "";
	const lines = text.trim().split("\n").filter(l => l.trim());
	let html = "";
	for (const line of lines) {
		const t = line.trim();
		if (/^[가-힣]\.\s/.test(t) || /^\d+[-.]/.test(t))
			html += `<h4 class="vw-h-section">${t}</h4>`;
		else if (/^\(\d+\)\s/.test(t) || /^\([가-힣]\)\s/.test(t))
			html += `<h5 class="vw-h-sub">${t}</h5>`;
		else if (/^\[.+\]$/.test(t) || /^【.+】$/.test(t))
			html += `<h4 class="vw-h-bracket">${t}</h4>`;
		else
			html += `<h5 class="vw-h-sub">${t}</h5>`;
	}
	return html;
}

/** 숫자 셀 감지 */
export function isNumericCell(val) {
	if (val == null) return false;
	return /^-?[\d,.]+%?$/.test(String(val).trim().replace(/,/g, ""));
}

export function isNegative(val) {
	if (val == null) return false;
	return /^-[\d.]+/.test(String(val).trim().replace(/,/g, ""));
}

export function formatScaledCell(val, divisor) {
	if (val == null || val === "") return "";
	const num = typeof val === "number" ? val : Number(String(val).replace(/,/g, ""));
	if (isNaN(num)) return String(val);
	if (divisor <= 1) return num.toLocaleString("ko-KR");
	const scaled = num / divisor;
	return Number.isInteger(scaled) ? scaled.toLocaleString("ko-KR")
		: scaled.toFixed(1).replace(/\B(?=(\d{3})+(?!\d))/g, ",");
}

export function formatCell(val) {
	if (val == null || val === "") return "";
	const s = String(val).trim();
	if (s.includes(",")) return s;
	const m = s.match(/^(-?\d+)(\.\d+)?(%?)$/);
	if (m) return m[1].replace(/\B(?=(\d{3})+(?!\d))/g, ",") + (m[2] || "") + (m[3] || "");
	return s;
}

/** 기간 정렬키: 최신 먼저 */
export function periodSortKey(p) {
	const m = p.match(/^(\d{4})(Q([1-4]))?$/);
	if (!m) return "0000_0";
	const y = m[1];
	const q = m[3] || "5";
	return `${y}_${q}`;
}

export function sortPeriodsDesc(arr) {
	return [...arr].sort((a, b) => periodSortKey(b).localeCompare(periodSortKey(a)));
}

export function periodDisplayLabel(period) {
	if (!period) return "";
	if (period.kind === "annual") return `${period.year}Q4`;
	if (period.year && period.quarter) return `${period.year}Q${period.quarter}`;
	return period.label || "";
}

export function sectionStatusLabel(status) {
	if (status === "updated") return "최근 수정";
	if (status === "new") return "신규";
	if (status === "stale") return "과거 유지";
	return "유지";
}

export function sectionStatusClass(status) {
	if (status === "updated") return "updated";
	if (status === "new") return "new";
	if (status === "stale") return "stale";
	return "stable";
}

export function renderDiffStatus(status) {
	if (status === "updated") return "변경 있음";
	if (status === "new") return "직전 없음";
	return "직전과 동일";
}
