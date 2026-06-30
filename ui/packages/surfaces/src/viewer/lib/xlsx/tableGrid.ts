// table-export 격자기 · 엔진 `providers/dart/parse/htmlTableParser.py::cellGrid` 의 TS 포팅.
// 입력 = `cell.ts::normalizeDartXml` 가 만든 표준 소문자 HTML(<table><tr><td|th colspan rowspan align>).
// 출력 = rowspan/colspan 을 모두 펼친 직사각 격자. 병합셀은 *같은 GridCell 인스턴스* 가 여러 좌표에 등장
// (엔진과 동일 · id() dedup 으로 merge 범위 추출 가능). *.grid.json 골든 스키마와 셀별 일치.
//
// DOM 0 (DOMParser 미사용) · node 패리티 스크립트와 브라우저가 바이트 동일 로직을 탄다. DART 정규화 HTML 은
// 잘 형성된 td/th/tr 구조라 정규식 state 파서로 충분(엔진도 lxml recover 로 같은 구조만 읽음).

export interface GridCell {
	text: string;
	colspan: number;
	rowspan: number;
	align: string; // "right" / "center" / "left" / ""
	isHeader: boolean; // th 인지 td 인지
}

interface ParsedRow {
	cells: GridCell[];
}

interface ParsedTable {
	rows: ParsedRow[];
	maxCols: number;
}

// 셀 안 내부 마크업(span/div/br/…) 제거 후 텍스트만 · lxml `itertext().strip()` 대응.
// <br> 는 텍스트 노드가 없어 공백 삽입 없이 사라진다(엔진과 동일). 그 외 태그도 텍스트만 남긴다.
function cellInnerText(inner: string): string {
	return inner.replace(/<[^>]*>/g, '').trim();
}

function decodeEntities(s: string): string {
	if (s.indexOf('&') < 0) return s;
	return s
		.replace(/&lt;/g, '<')
		.replace(/&gt;/g, '>')
		.replace(/&quot;/g, '"')
		.replace(/&#39;/g, "'")
		.replace(/&apos;/g, "'")
		.replace(/&nbsp;/g, ' ')
		.replace(/&amp;/g, '&');
}

function intAttr(attrs: string, name: string, fallback: number): number {
	const m = new RegExp(`\\b${name}\\s*=\\s*("([^"]*)"|'([^']*)'|(\\S+))`, 'i').exec(attrs);
	if (!m) return fallback;
	const raw = (m[2] ?? m[3] ?? m[4] ?? '').trim();
	if (!raw) return fallback;
	const n = parseInt(raw, 10);
	return Number.isFinite(n) ? n : fallback;
}

function strAttr(attrs: string, name: string): string {
	const m = new RegExp(`\\b${name}\\s*=\\s*("([^"]*)"|'([^']*)'|(\\S+))`, 'i').exec(attrs);
	if (!m) return '';
	return (m[2] ?? m[3] ?? m[4] ?? '').trim();
}

// 정규화 HTML 의 첫 <table>...</table> 블록을 rows 구조로 · td/th 만, colspan/rowspan/align/isHeader 보존.
function parseHtmlTable(html: string): ParsedTable | null {
	if (!html || html.indexOf('<table') < 0) return null;
	// XML line-ending 정규화 (\r\n / \r → \n) · XML 파서 의무 규칙. 엔진 lxml 과 셀 텍스트 패리티 보장.
	html = html.replace(/\r\n?/g, '\n');
	const tableM = /<table\b[^>]*>([\s\S]*?)<\/table>/i.exec(html);
	if (!tableM) return null;
	const body = tableM[1];

	const rows: ParsedRow[] = [];
	let maxCols = 0;

	// tr 단위 분리. thead/tbody/tfoot 래퍼는 무시(엔진 _findTrs 와 동치 · tr 만 yield).
	const trRe = /<tr\b[^>]*>([\s\S]*?)<\/tr>/gi;
	let trM: RegExpExecArray | null;
	while ((trM = trRe.exec(body)) !== null) {
		const rowInner = trM[1];
		const cells: GridCell[] = [];
		// 셀 = 여는 td/th 태그 단위. 내용은 *다음 셀 여는 태그* 까지 (HTML 의 td 암묵 종료 규칙).
		// normalizeDartXml 이 self-close `<td/>` → `<td>` (닫는태그 없는 빈 셀)로 만들고, 명시 `</td>` 도
		// 있을 수 있다 · 어느 경우든 다음 셀 시작 전까지가 내용이고, 셀 내부 마크업/잔여 닫는태그는 strip.
		// 셀 경계만 매칭 (셀 내부의 span/div 닫는 태그는 경계 아님).
		const cellOpenRe = /<(td|th)\b([^>]*?)\/?>/gi;
		const opens: Array<{ tag: string; attrs: string; matchStart: number; contentStart: number }> = [];
		let oM: RegExpExecArray | null;
		while ((oM = cellOpenRe.exec(rowInner)) !== null) {
			opens.push({
				tag: oM[1].toLowerCase(),
				attrs: oM[2] ?? '',
				matchStart: oM.index,
				contentStart: oM.index + oM[0].length
			});
		}
		for (let i = 0; i < opens.length; i += 1) {
			const o = opens[i];
			// 내용 = 이 셀 여는 태그 끝 ~ 다음 셀 여는 태그 시작 (없으면 row 끝). 잔여 닫는태그/내부 마크업은 strip.
			const contentEnd = i + 1 < opens.length ? opens[i + 1].matchStart : rowInner.length;
			const inner = rowInner.slice(o.contentStart, contentEnd);
			cells.push({
				text: decodeEntities(cellInnerText(inner)),
				colspan: intAttr(o.attrs, 'colspan', 1),
				rowspan: intAttr(o.attrs, 'rowspan', 1),
				align: strAttr(o.attrs, 'align').toLowerCase(),
				isHeader: o.tag === 'th'
			});
		}
		if (cells.length > 0) {
			rows.push({ cells });
			let cols = 0;
			for (const c of cells) cols += c.colspan;
			if (cols > maxCols) maxCols = cols;
		}
	}

	return rows.length > 0 ? { rows, maxCols } : null;
}

/**
 * rowspan/colspan 을 모두 펼친 직사각 cell 격자 · 엔진 `cellGrid` 포팅.
 *
 * 병합셀은 같은 GridCell 인스턴스가 격자의 여러 좌표에 등장한다(엔진과 동일 · 병합 범위 추출용).
 *
 * @param html `normalizeDartXml` 가 만든 표준 소문자 HTML.
 * @returns `grid[row][col]` 2D 배열. parse 실패 시 빈 배열.
 *
 * @example
 * const g = tableGrid('<table><tr><td colspan="2">병합</td></tr><tr><td>a</td><td>b</td></tr></table>');
 * g[0][0] === g[0][1]; // true · colspan 으로 같은 인스턴스가 두 좌표에
 */
export function tableGrid(html: string): GridCell[][] {
	const parsed = parseHtmlTable(html);
	if (parsed === null) return [];

	const grid: GridCell[][] = [];
	// rowspan tracking · 각 col 의 (cell, 남은 row span).
	const spanCarry = new Map<number, { cell: GridCell; remaining: number }>();

	for (const row of parsed.rows) {
		const outRow: GridCell[] = [];
		let col = 0;
		let cellIdx = 0;
		while (col < parsed.maxCols || cellIdx < row.cells.length) {
			// 이전 row 의 rowspan carry.
			const carried = spanCarry.get(col);
			if (carried) {
				outRow.push(carried.cell);
				if (carried.remaining > 1) {
					spanCarry.set(col, { cell: carried.cell, remaining: carried.remaining - 1 });
				} else {
					spanCarry.delete(col);
				}
				col += 1;
				continue;
			}
			if (cellIdx < row.cells.length) {
				const cell = row.cells[cellIdx];
				cellIdx += 1;
				for (let offset = 0; offset < cell.colspan; offset += 1) outRow.push(cell);
				if (cell.rowspan > 1) {
					for (let offset = 0; offset < cell.colspan; offset += 1) {
						spanCarry.set(col + offset, { cell, remaining: cell.rowspan - 1 });
					}
				}
				col += cell.colspan;
			} else {
				break;
			}
		}
		grid.push(outRow);
	}

	return grid;
}
