// table-export 공유 순수 로직 · public·local 어댑터가 동일 사용(03 §3 "동일 순수 함수(공유 모듈)").
// 네트워크 0·DOM 0. listExportableTables(이미 로드된 PanelBundle 추출) + selection DTO → 엔진 ExcelTemplate 변환.
// 엔진 `viz/export/template.py` 의 SheetSpec/PanelTableSource 스키마와 동형(public↔local 패리티 토대).

import type {
	ExcelTemplate,
	ExportableTable,
	ExportBundleLike,
	ExportInput,
	PanelTableSource,
	SheetSelectionDTO,
	SheetSpec
} from '@dartlab/ui-contracts';

/** sectionKey = `${chapter}␟${sectionLeaf}` · 엔진 PanelTableSource 는 chapter·sectionLeaf 분리 보유. */
const SECTION_SEP = '␟'; // ␟

function splitSectionKey(sectionKey: string): { chapter: string; sectionLeaf: string } {
	const idx = sectionKey.indexOf(SECTION_SEP);
	if (idx < 0) return { chapter: '', sectionLeaf: sectionKey };
	return { chapter: sectionKey.slice(0, idx), sectionLeaf: sectionKey.slice(idx + 1) };
}

/**
 * 이미 로드된 PanelBundle 에서 내보내기 가능한 표 목록 추출 · 순수 함수(fetch 0, 03 §4).
 * gridBySection 순회로 (sectionKey, blockLeaf, disclosureKey, scope) 별 행을 수집. 같은 (sectionKey,blockLeaf)
 * 가 여러 행이면 섹션 내 ordinal 로 id 를 유일화(`${sectionKey}|${blockLeaf}#${seq}`).
 *
 * @param bundle 현재 회사 PanelBundle (구조적 최소면 ExportBundleLike).
 * @returns 내보내기 가능한 표 목록(text 블록 narrative 포함, hasTable 로 구분).
 *
 * @example
 * const tables = listExportableTables(bundle);
 */
export function listExportableTables(bundle: ExportBundleLike): ExportableTable[] {
	const out: ExportableTable[] = [];
	const periods = bundle.periods;
	for (const [sectionKey, rows] of bundle.gridBySection) {
		const seen = new Map<string, number>(); // blockLeaf → 누적 카운트(동일 blockLeaf 다중행 디스앰비그)
		for (const row of rows) {
			const base = `${sectionKey}|${row.blockLeaf}`;
			const seq = seen.get(row.blockLeaf) ?? 0;
			seen.set(row.blockLeaf, seq + 1);
			const id = seq === 0 ? base : `${base}#${seq}`;
			const hasPeriods = periods.filter((p) => {
				const v = row.cells[p];
				return v != null && v !== '';
			});
			out.push({
				id,
				sectionKey,
				blockLeaf: row.blockLeaf,
				disclosureKey: row.disclosureKey,
				scope: row.scope,
				hasTable: row.blockType === 'table',
				periods: hasPeriods
			});
		}
	}
	return out;
}

/** 한 selection DTO → 엔진 PanelTableSource(공시 표). leafSeq 는 surface 가 미보유라 null(섹션 첫 매칭). */
function selectionToPanelSource(sel: SheetSelectionDTO): PanelTableSource {
	const { chapter, sectionLeaf } = splitSectionKey(sel.sectionKey);
	const periodMode = sel.mode;
	const period =
		periodMode === 'asFiled' && Array.isArray(sel.periods) && sel.periods.length
			? (sel.periods[0] ?? null)
			: null;
	return {
		kind: 'panelTable',
		chapter,
		sectionLeaf,
		blockLeaf: sel.blockLeaf,
		leafType: 'table',
		disclosureKey: sel.disclosureKey,
		scope: sel.scope,
		leafSeq: null,
		periodMode,
		period
	};
}

/**
 * 선택 DTO 목록 → 엔진 ExcelTemplate(임시 양식). local 어댑터가 POST /api/export/excel 의 `template` 으로 전송.
 * order 순 정렬. 각 시트 = PanelTableSource. 엔진 fromDict 가 그대로 흡수(하위호환 정규화).
 *
 * @param input ExportInput(code·selections·옵션).
 * @returns ExcelTemplate(JSON-safe) · /api/export/excel 전송용.
 *
 * @example
 * const tmpl = selectionsToTemplate(input);
 */
export function selectionsToTemplate(input: ExportInput): ExcelTemplate {
	const ordered = [...input.selections].sort((a, b) => a.order - b.order);
	const sheets: SheetSpec[] = ordered.map((sel) => ({
		source: selectionToPanelSource(sel),
		label: sel.label
	}));
	return { name: '선택', sheets };
}
