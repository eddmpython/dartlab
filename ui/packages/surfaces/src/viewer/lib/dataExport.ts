// 일반인 접근용 데이터 export · 브라우저에 이미 로드된 데이터를 CSV/Excel 로 변환·다운로드 (서버 0, 라이브러리 0).
// 공시 수평화표 = CSV(항목×기간 텍스트 격자), 재무제표 = Excel(.xls SpreadsheetML 멀티시트, 숫자).

import type { FinanceStatement } from './finance/types';
import type { PanelBundle } from './types';

// ── CSV (UTF-8 BOM → Excel/Sheets 한글 정상) ──
function csvCell(v: string): string {
	return /[",\n\r]/.test(v) ? `"${v.replace(/"/g, '""')}"` : v;
}
export function toCsv(rows: string[][]): string {
	return '﻿' + rows.map((r) => r.map(csvCell).join(',')).join('\r\n');
}

// 셀 본문(raw DART XML) → CSV 용 평문 (태그 제거·엔티티·공백 정리).
export function cellText(raw: string | undefined): string {
	if (!raw) return '';
	return raw
		.replace(/<br\s*\/?>/gi, ' ')
		.replace(/<\/(tr|p|div|table|caption)>/gi, ' ')
		.replace(/<[^>]+>/g, '')
		.replace(/&cr;/g, ' ')
		.replace(/&nbsp;/g, ' ')
		.replace(/&amp;/g, '&')
		.replace(/&lt;/g, '<')
		.replace(/&gt;/g, '>')
		.replace(/\s+/g, ' ')
		.trim();
}

// 공시 수평화표 → CSV: [구분(섹션), 항목, ...기간]. panel 의 모든 섹션×항목×기간을 한 표로(수평화 그대로).
export function panelToCsv(bundle: PanelBundle): string {
	const periods = bundle.periods;
	const rows: string[][] = [['구분', '항목', ...periods]];
	for (const [sectionKey, prows] of bundle.gridBySection) {
		const section = sectionKey.split('␟').pop() ?? sectionKey;
		for (const r of prows) rows.push([section, r.blockLeaf ?? '', ...periods.map((p) => cellText(r.cells[p]))]);
	}
	return toCsv(rows);
}

// ── Excel (SpreadsheetML 2003 .xls · 멀티시트, 라이브러리 0. Excel/Sheets 가 직접 엶) ──
function xmlEsc(s: string): string {
	return s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}
// 시트명 · Excel 제한 31자·특수문자(:\/?*[]) 불가.
function sheetName(name: string): string {
	return name.replace(/[:\\/?*[\]]/g, ' ').slice(0, 31);
}
function sheetXml(name: string, statement: FinanceStatement): string {
	const periods = statement.periods;
	const head = `<Row><Cell><Data ss:Type="String">계정</Data></Cell>${periods
		.map((p) => `<Cell><Data ss:Type="String">${xmlEsc(p)}</Data></Cell>`)
		.join('')}</Row>`;
	const body = statement.rows
		.map((row) => {
			const cells = periods
				.map((p) => {
					const v = row.values[p];
					return v == null ? '<Cell/>' : `<Cell><Data ss:Type="Number">${v}</Data></Cell>`;
				})
				.join('');
			return `<Row><Cell><Data ss:Type="String">${xmlEsc(row.label)}</Data></Cell>${cells}</Row>`;
		})
		.join('');
	return `<Worksheet ss:Name="${xmlEsc(sheetName(name))}"><Table>${head}${body}</Table></Worksheet>`;
}
export function financeToExcel(sheets: Array<{ name: string; statement: FinanceStatement }>): string {
	const ws = sheets
		.filter((s) => s.statement.rows.length > 0)
		.map((s) => sheetXml(s.name, s.statement))
		.join('');
	return `<?xml version="1.0"?>\n<?mso-application progid="Excel.Sheet"?>\n<Workbook xmlns="urn:schemas-microsoft-com:office:spreadsheet" xmlns:ss="urn:schemas-microsoft-com:office:spreadsheet">${ws}</Workbook>`;
}

// 브라우저 다운로드 트리거 (Blob) · 이름·revoke 정리 단일 출처.
function triggerDownload(blob: Blob, filename: string): void {
	const url = URL.createObjectURL(blob);
	const a = document.createElement('a');
	a.href = url;
	a.download = filename;
	document.body.appendChild(a);
	a.click();
	a.remove();
	setTimeout(() => URL.revokeObjectURL(url), 1000);
}

// 텍스트(CSV/.xls SpreadsheetML) 다운로드.
export function downloadText(content: string, filename: string, mime: string): void {
	triggerDownload(new Blob([content], { type: mime }), filename);
}

// 바이너리(진짜 .xlsx 등 Uint8Array) 다운로드 · buildWorkbook 산출 바이트용.
export function downloadBlob(bytes: Uint8Array, filename: string, mime: string): void {
	// lib.dom BlobPart 는 ArrayBufferView<ArrayBuffer> 를 요구하는데 Uint8Array 의 buffer 는 ArrayBufferLike
	// (SharedArrayBuffer 가능)로 추론돼 거부된다. slice() 로 정확히 크기맞춘 새 ArrayBuffer 사본을 만들어 그 buffer 전달.
	const copy = bytes.slice();
	triggerDownload(new Blob([copy.buffer as ArrayBuffer], { type: mime }), filename);
}
