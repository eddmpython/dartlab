/**
 * CSV export · BOM + 한글 Excel 호환.
 *
 * 사용:
 *   downloadCsv('prices.csv', ['stockCode', 'currentPrice'], rows);
 *
 * row 의 array / object 컬럼은 JSON.stringify 로 직렬화.
 */

const BOM = '﻿';

function escapeCell(v: unknown): string {
	if (v === null || v === undefined) return '';
	let s: string;
	if (typeof v === 'string') s = v;
	else if (typeof v === 'number' || typeof v === 'boolean') s = String(v);
	else if (Array.isArray(v) || typeof v === 'object') s = JSON.stringify(v);
	else s = String(v);
	// 큰따옴표/쉼표/개행 있으면 quoted + 큰따옴표 escape
	if (/["\n\r,]/.test(s)) {
		return `"${s.replace(/"/g, '""')}"`;
	}
	return s;
}

/** rows 배열 + columns 순서 → CSV 문자열 (BOM 포함). */
export function toCsv(columns: string[], rows: Array<Record<string, unknown>>): string {
	const head = columns.map(escapeCell).join(',');
	const body = rows
		.map((row) => columns.map((c) => escapeCell(row[c])).join(','))
		.join('\n');
	return BOM + head + '\n' + body;
}

/** CSV 즉시 다운로드. browser only. */
export function downloadCsv(
	filename: string,
	columns: string[],
	rows: Array<Record<string, unknown>>
): void {
	if (typeof window === 'undefined') return;
	const csv = toCsv(columns, rows);
	const blob = new Blob([csv], { type: 'text/csv;charset=utf-8' });
	const url = URL.createObjectURL(blob);
	const a = document.createElement('a');
	a.href = url;
	a.download = filename.endsWith('.csv') ? filename : `${filename}.csv`;
	document.body.appendChild(a);
	a.click();
	document.body.removeChild(a);
	URL.revokeObjectURL(url);
}
