// OOXML 부품 emit · [Content_Types].xml · _rels/.rels · xl/workbook.xml · xl/_rels/workbook.xml.rels ·
// xl/styles.xml(최소) · xl/worksheets/sheetN.xml. inlineStr(텍스트)·t="n"(숫자) 셀 + <mergeCells>.
// sharedStrings 대신 inlineStr · 표가 좁고 쓰기 전용이라 dedup 이득 < 복잡도(feedback_always_check_clutter).
//
// styleId 고정 테이블 (xl/styles.xml 의 cellXfs 순서와 정확히 일치):
//   0 = 기본            1 = 헤더 볼드(가운데)
//   2 = #,##0           3 = #,##0;[Red]-#,##0
//   4 = @ 텍스트(좌)    5 = wrapText 텍스트(좌·줄바꿈)
//   6 = 우측정렬 텍스트 7 = 가운데정렬 텍스트   8 = 노트(회색 이탤릭)

export const STYLE = {
	DEFAULT: 0,
	HEADER: 1,
	NUMBER: 2,
	NUMBER_NEG: 3,
	TEXT: 4,
	TEXT_WRAP: 5,
	TEXT_RIGHT: 6,
	TEXT_CENTER: 7,
	NOTE: 8
} as const;

export function xmlEsc(s: string): string {
	return s
		.replace(/&/g, '&amp;')
		.replace(/</g, '&lt;')
		.replace(/>/g, '&gt;')
		.replace(/"/g, '&quot;')
		.replace(/'/g, '&apos;');
}

// A1 표기 · col(0-base) → "A".."Z","AA".. ; row(0-base) → 1-base 숫자.
export function colLetter(col: number): string {
	let n = col;
	let s = '';
	do {
		s = String.fromCharCode(65 + (n % 26)) + s;
		n = Math.floor(n / 26) - 1;
	} while (n >= 0);
	return s;
}

export function cellRef(row: number, col: number): string {
	return `${colLetter(col)}${row + 1}`;
}

const CONTENT_TYPES = `<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/><Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>__SHEET_OVERRIDES__</Types>`;

const ROOT_RELS = `<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/></Relationships>`;

// 최소 styles.xml · numFmt(custom 164/165) + fonts(기본·볼드·노트) + cellXfs(위 STYLE 순서).
const STYLES = `<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><numFmts count="2"><numFmt numFmtId="164" formatCode="#,##0"/><numFmt numFmtId="165" formatCode="#,##0;[Red]-#,##0"/></numFmts><fonts count="3"><font><sz val="11"/><name val="Calibri"/></font><font><b/><sz val="11"/><name val="Calibri"/></font><font><i/><sz val="9"/><color rgb="FF808080"/><name val="Calibri"/></font></fonts><fills count="2"><fill><patternFill patternType="none"/></fill><fill><patternFill patternType="gray125"/></fill></fills><borders count="1"><border><left/><right/><top/><bottom/><diagonal/></border></borders><cellStyleXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0"/></cellStyleXfs><cellXfs count="9"><xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0"/><xf numFmtId="0" fontId="1" fillId="0" borderId="0" xfId="0" applyFont="1" applyAlignment="1"><alignment horizontal="center" vertical="center"/></xf><xf numFmtId="164" fontId="0" fillId="0" borderId="0" xfId="0" applyNumberFormat="1"/><xf numFmtId="165" fontId="0" fillId="0" borderId="0" xfId="0" applyNumberFormat="1"/><xf numFmtId="49" fontId="0" fillId="0" borderId="0" xfId="0" applyNumberFormat="1" applyAlignment="1"><alignment horizontal="left" vertical="center"/></xf><xf numFmtId="49" fontId="0" fillId="0" borderId="0" xfId="0" applyNumberFormat="1" applyAlignment="1"><alignment horizontal="left" vertical="center" wrapText="1"/></xf><xf numFmtId="49" fontId="0" fillId="0" borderId="0" xfId="0" applyNumberFormat="1" applyAlignment="1"><alignment horizontal="right" vertical="center"/></xf><xf numFmtId="49" fontId="0" fillId="0" borderId="0" xfId="0" applyNumberFormat="1" applyAlignment="1"><alignment horizontal="center" vertical="center"/></xf><xf numFmtId="0" fontId="2" fillId="0" borderId="0" xfId="0" applyFont="1"/></cellXfs><cellStyles count="1"><cellStyle name="Normal" xfId="0" builtinId="0"/></cellStyles></styleSheet>`;

export interface SheetCell {
	row: number; // 0-base 행
	col: number; // 0-base 열
	value: number | string;
	styleId: number;
}

export interface SheetPart {
	name: string; // 시트 표시 이름 (이미 정규화됨)
	cells: SheetCell[];
	merges: string[]; // ["A1:B1", ...]
}

function sheetXml(sheet: SheetPart): string {
	// 행별 그룹화 (오름차순).
	const byRow = new Map<number, SheetCell[]>();
	for (const c of sheet.cells) {
		const arr = byRow.get(c.row);
		if (arr) arr.push(c);
		else byRow.set(c.row, [c]);
	}
	const rowNums = [...byRow.keys()].sort((a, b) => a - b);

	const rowsXml = rowNums
		.map((r) => {
			const cells = byRow.get(r)!.slice().sort((a, b) => a.col - b.col);
			const cellsXml = cells
				.map((c) => {
					const ref = cellRef(c.row, c.col);
					if (typeof c.value === 'number') {
						return `<c r="${ref}" s="${c.styleId}" t="n"><v>${c.value}</v></c>`;
					}
					return `<c r="${ref}" s="${c.styleId}" t="inlineStr"><is><t xml:space="preserve">${xmlEsc(c.value)}</t></is></c>`;
				})
				.join('');
			return `<row r="${r + 1}">${cellsXml}</row>`;
		})
		.join('');

	const mergeXml =
		sheet.merges.length > 0
			? `<mergeCells count="${sheet.merges.length}">${sheet.merges.map((m) => `<mergeCell ref="${m}"/>`).join('')}</mergeCells>`
			: '';

	return `<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData>${rowsXml}</sheetData>${mergeXml}</worksheet>`;
}

function workbookXml(sheets: SheetPart[]): string {
	const tabs = sheets
		.map((s, i) => `<sheet name="${xmlEsc(s.name)}" sheetId="${i + 1}" r:id="rId${i + 1}"/>`)
		.join('');
	return `<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets>${tabs}</sheets></workbook>`;
}

function workbookRels(sheets: SheetPart[]): string {
	const rels = sheets
		.map(
			(_s, i) =>
				`<Relationship Id="rId${i + 1}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet${i + 1}.xml"/>`
		)
		.join('');
	const stylesId = sheets.length + 1;
	return `<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">${rels}<Relationship Id="rId${stylesId}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/></Relationships>`;
}

export interface OoxmlParts {
	[path: string]: string;
}

/** 시트 부품 목록 → OOXML 파트 dict (path → XML 문자열). zipStore 가 각 path 를 addEntry. */
export function emitOoxmlParts(sheets: SheetPart[]): OoxmlParts {
	const sheetOverrides = sheets
		.map(
			(_s, i) =>
				`<Override PartName="/xl/worksheets/sheet${i + 1}.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>`
		)
		.join('');

	const parts: OoxmlParts = {
		'[Content_Types].xml': CONTENT_TYPES.replace('__SHEET_OVERRIDES__', sheetOverrides),
		'_rels/.rels': ROOT_RELS,
		'xl/workbook.xml': workbookXml(sheets),
		'xl/_rels/workbook.xml.rels': workbookRels(sheets),
		'xl/styles.xml': STYLES
	};
	sheets.forEach((s, i) => {
		parts[`xl/worksheets/sheet${i + 1}.xml`] = sheetXml(s);
	});
	return parts;
}
