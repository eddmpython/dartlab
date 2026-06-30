// table-export 선택 스토어 (Svelte 5 runes) · "뷰어 격자 = 미리보기" 선택 바구니의 상태 + buildWorkbook 입력 파생.
//
// 선택 원자 = (테이블 정체성 + 기간 범위). 정체성은 (sectionKey, indexInSection) · bundle.gridBySection 의
// 섹션 배열 절대 인덱스. PRD 의 `${sectionKey}|${blockLeaf}` 보다 견고(같은 blockLeaf 가 한 섹션에 여러 행일 때
// blockLeaf 만으론 충돌). PanelMatrix data-cell 키(rowIndex)는 현재 표시 필터 상대값이라, 선택 시 ViewerStudio 가
// 섹션 절대 인덱스로 환산해 add 한다.
//
// 파생: 각 선택 → bundle 에서 raw XML 해석 → cell.ts normalizeDartXml → splitHtmlAndText → tableGrid →
// SheetInput{ label, grid, unit?, note? }. as-filed=그 표 구조 그대로(병합 보존). horizontalized=행 라벨×기간 격자
// (표 행은 라벨 정렬 불확실 → as-filed 자동 폴백 + 시트 노트, honest-gap).

import { normalizeDartXml, splitHtmlAndText, stripInlineTags } from '../cell';
import { tableGrid, buildWorkbook, type GridCell, type SheetInput } from '../xlsx';
import { detectUnit } from '../xlsx/tableExtract';
import type { PanelBundle, PanelRow } from '../types';
import type { ExportInput, SheetSelectionDTO } from '@dartlab/ui-contracts';

export type ExportMode = 'asFiled' | 'horizontalized';

export interface SheetSelection {
	/** 안정 키 = `${sectionKey}|${indexInSection}` (섹션 절대 인덱스). */
	id: string;
	sectionKey: string;
	indexInSection: number; // bundle.gridBySection.get(sectionKey) 의 절대 인덱스
	blockLeaf: string;
	disclosureKey: string | null;
	scope: string | null;
	blockType: 'text' | 'table';
	label: string; // 편집 가능 시트명 (기본 = blockLeaf, 31자 트림)
	mode: ExportMode;
	periods: string[] | 'all'; // 셀 선택이면 그 period(들), 행 전체면 'all'
	order: number; // 드래그 정렬 = 시트 순서
}

const SHEET_NAME_MAX = 31;

/** 시트명 후보를 31자(유니코드)로 트림. 금지문자 정규화는 buildWorkbook.sheetName 가 최종 담당. */
export function trimLabel(raw: string): string {
	return [...(raw ?? '')].slice(0, SHEET_NAME_MAX).join('');
}

export function selectionId(sectionKey: string, indexInSection: number): string {
	return `${sectionKey}|${indexInSection}`;
}

// 섹션 라벨 · sectionKey = `${chapter}␟${sectionLeaf}`. 표시·기본 시트명 폴백용.
function sectionLeafOf(sectionKey: string): string {
	return sectionKey.split('␟').pop() ?? sectionKey;
}

/**
 * 선택 스토어 · ViewerStudio 가 1개 인스턴스를 만들어 ExportDrawer·PanelMatrix·PanelTocTree 와 공유한다.
 *
 * 회사 전환(code 변경) 시 ViewerStudio 가 `clear()` 를 호출한다(타 회사 선택 잔존 방지).
 */
export function createSelectionStore() {
	const items = $state<SheetSelection[]>([]);
	// 옵션 · 출처 시트 포함(provenance, 기본 ON). 회사 이식(N사)은 후속(브라우저 단일회사 단계에선 미배선).
	const opts = $state<{ includeSource: boolean }>({ includeSource: true });

	function indexById(id: string): number {
		return items.findIndex((s) => s.id === id);
	}
	function nextOrder(): number {
		return items.reduce((m, s) => Math.max(m, s.order), -1) + 1;
	}

	return {
		get items() {
			return items;
		},
		get count() {
			return items.length;
		},
		get includeSource() {
			return opts.includeSource;
		},
		set includeSource(v: boolean) {
			opts.includeSource = v;
		},

		has(id: string): boolean {
			return indexById(id) >= 0;
		},
		/** 현재 선택 id 집합 (PanelMatrix steady glow 매칭용). */
		idSet(): Set<string> {
			return new Set(items.map((s) => s.id));
		},

		/**
		 * 행(테이블/텍스트 블록) 추가. 이미 있으면 무시(중복 add=토글 off 는 remove 가 담당).
		 * periods 미지정(=undefined) 시 'all'(행 전체 기간). 특정 셀 선택이면 그 period 1개.
		 */
		add(args: {
			sectionKey: string;
			indexInSection: number;
			row: PanelRow;
			periods?: string[] | 'all';
		}): void {
			const id = selectionId(args.sectionKey, args.indexInSection);
			if (indexById(id) >= 0) return;
			const label = trimLabel(args.row.blockLeaf || sectionLeafOf(args.sectionKey));
			items.push({
				id,
				sectionKey: args.sectionKey,
				indexInSection: args.indexInSection,
				blockLeaf: args.row.blockLeaf,
				disclosureKey: args.row.disclosureKey,
				scope: args.row.scope,
				blockType: args.row.blockType,
				label,
				mode: 'horizontalized',
				periods: args.periods ?? 'all',
				order: nextOrder()
			});
		},

		/** 셀 클릭 토글 · 없으면 add, 있으면 remove. 클릭 1번 = on/off. */
		toggle(args: {
			sectionKey: string;
			indexInSection: number;
			row: PanelRow;
			periods?: string[] | 'all';
		}): void {
			const id = selectionId(args.sectionKey, args.indexInSection);
			if (indexById(id) >= 0) this.remove(id);
			else this.add(args);
		},

		remove(id: string): void {
			const i = indexById(id);
			if (i >= 0) items.splice(i, 1);
		},

		clear(): void {
			items.splice(0, items.length);
		},

		setLabel(id: string, label: string): void {
			const s = items[indexById(id)];
			if (s) s.label = trimLabel(label);
		},
		setMode(id: string, mode: ExportMode): void {
			const s = items[indexById(id)];
			if (s) s.mode = mode;
		},

		/** order=src 항목을 dst 위치로 이동(드래그 정렬). order 필드를 0..n-1 로 재배열. */
		reorder(srcId: string, dstId: string): void {
			const from = indexById(srcId);
			const to = indexById(dstId);
			if (from < 0 || to < 0 || from === to) return;
			const [moved] = items.splice(from, 1);
			items.splice(to, 0, moved);
			items.forEach((s, i) => (s.order = i));
		},

		/** order 순 정렬된 사본(렌더·파생용). */
		ordered(): SheetSelection[] {
			return [...items].sort((a, b) => a.order - b.order);
		}
	};
}

export type SelectionStore = ReturnType<typeof createSelectionStore>;

// ── buildWorkbook 입력 파생 (순수 · 스토어 무관, bundle 만 입력) ──

// 한 raw 셀 XML → 첫 <table> 의 격자(as-filed). 표가 없으면 텍스트만 1열 격자로(텍스트 블록 폴백).
function gridFromCellXml(rawXml: string): { grid: GridCell[][]; unit: string } {
	const normalized = normalizeDartXml(rawXml);
	const parts = splitHtmlAndText(normalized);
	let unit = '';
	let textBefore = '';
	for (const [kind, val] of parts) {
		if (kind === 'text') {
			// 표 직전 텍스트에서 단위 라벨 흡수(있으면). 표 캡션/단위는 시트 상단 라벨로.
			if (!unit) unit = detectUnit(val);
			textBefore = stripInlineTags(val);
		} else {
			const grid = tableGrid(val);
			if (grid.length) {
				if (!unit) unit = detectUnit(val);
				return { grid, unit };
			}
		}
	}
	// 표 없음 → 텍스트 1열 격자(문단별 1행). 빈셀은 null(coerceCell)로 honest-gap.
	const text = textBefore || stripInlineTags(normalized);
	const lines = text.split('\n').map((l) => l.trim()).filter(Boolean);
	const grid: GridCell[][] = lines.map((line) => [
		{ text: line, colspan: 1, rowspan: 1, align: '', isHeader: false }
	]);
	return { grid, unit };
}

// 행 라벨(첫 컬럼 식별 텍스트) · horizontalized 격자의 행 헤더. blockLeaf 또는 셀 첫 줄.
function periodsToUse(sel: SheetSelection, available: string[]): string[] {
	if (sel.periods === 'all') return available;
	return sel.periods.filter((p) => available.includes(p));
}

/**
 * 한 선택 → SheetInput (없으면 null = 데이터 없는 선택 skip).
 *
 * @param sel 선택 항목.
 * @param bundle 현재 회사 PanelBundle (raw XML 출처).
 * @returns buildWorkbook 입력 1개 또는 null.
 */
export function selectionToSheet(sel: SheetSelection, bundle: PanelBundle): SheetInput | null {
	const sectionRows = bundle.gridBySection.get(sel.sectionKey);
	const row = sectionRows?.[sel.indexInSection];
	if (!row) return null;

	const allPeriods = bundle.periods.filter((p) => row.cells[p] != null && row.cells[p] !== '');
	const use = periodsToUse(sel, allPeriods);
	if (use.length === 0) return null;

	// horizontalized · 표 행은 라벨 정렬 불확실 → as-filed 자동 폴백 + 시트 노트(honest-gap, PRD §4.1).
	// 텍스트(narrative) 행은 행=기간, 열=본문 텍스트의 수평화가 자연(라벨 정렬 문제 없음).
	if (sel.mode === 'horizontalized') {
		if (row.blockType === 'text') {
			// 행=각 기간, 2열(기간 | 본문). 최신 좌측(bundle.periods 순서).
			const grid: GridCell[][] = [
				[
					{ text: '기간', colspan: 1, rowspan: 1, align: '', isHeader: true },
					{ text: '내용', colspan: 1, rowspan: 1, align: '', isHeader: true }
				]
			];
			for (const p of use) {
				const text = stripInlineTags(normalizeDartXml(row.cells[p] ?? ''));
				grid.push([
					{ text: p, colspan: 1, rowspan: 1, align: '', isHeader: false },
					{ text, colspan: 1, rowspan: 1, align: '', isHeader: false }
				]);
			}
			return { label: sel.label, grid };
		}
		// 표 행 → as-filed 폴백(최신 기간) + 노트.
		const latest = use[0];
		const { grid, unit } = gridFromCellXml(row.cells[latest] ?? '');
		if (!grid.length) return null;
		return {
			label: sel.label,
			grid,
			unit: unit || undefined,
			note: `${latest} 원본 구조 · 수평화 미지원(표는 원본 그대로)`
		};
	}

	// as-filed · 선택 기간(들) 중 최신 1개의 표 구조 그대로 transcribe. 병합셀 보존.
	const period = use[0];
	const { grid, unit } = gridFromCellXml(row.cells[period] ?? '');
	if (!grid.length) return null;
	return {
		label: sel.label,
		grid,
		unit: unit || undefined,
		note: use.length === 1 ? undefined : `${period} 기준(원본은 시점별 구조 상이)`
	};
}

/** 출처 시트(provenance) · 어떤 회사·시점·섹션을 어떤 모드로 뽑았는지 기록. includeSource 옵션 ON 시 1장 추가. */
export function sourceSheet(
	selections: SheetSelection[],
	bundle: PanelBundle
): SheetInput {
	const head: GridCell[] = ['시트', '섹션', '항목', '범위', '시점'].map((t) => ({
		text: t,
		colspan: 1,
		rowspan: 1,
		align: '',
		isHeader: true
	}));
	const grid: GridCell[][] = [head];
	for (const s of selections) {
		const scopeLabel = s.mode === 'horizontalized' ? '수평화' : '원본';
		const periodLabel = s.periods === 'all' ? '전 기간' : s.periods.join(', ');
		grid.push(
			[s.label, sectionLeafOf(s.sectionKey), s.blockLeaf, scopeLabel, periodLabel].map((t) => ({
				text: t,
				colspan: 1,
				rowspan: 1,
				align: '',
				isHeader: false
			}))
		);
	}
	return {
		label: '출처',
		grid,
		note: `${bundle.corpName || bundle.stockCode} · DART 전자공시 · dartlab 가공 · ${selections.length}개 표`
	};
}

/**
 * 선택들 + 옵션 → buildWorkbook 입력 배열. 데이터 없는 선택은 자동 제외(honest, 빈 시트 0).
 *
 * @param selections order 순 선택 목록.
 * @param bundle 현재 회사 PanelBundle.
 * @param includeSource 출처 시트 포함 여부.
 * @returns SheetInput[] · buildWorkbook 에 그대로 전달.
 *
 * @example
 * const sheets = deriveWorkbookInput(store.ordered(), bundle, store.includeSource);
 * const bytes = buildWorkbook(sheets);
 */
export function deriveWorkbookInput(
	selections: SheetSelection[],
	bundle: PanelBundle,
	includeSource: boolean
): SheetInput[] {
	const sheets: SheetInput[] = [];
	for (const s of selections) {
		const sheet = selectionToSheet(s, bundle);
		if (sheet) sheets.push(sheet);
	}
	if (includeSource && sheets.length) sheets.push(sourceSheet(selections, bundle));
	return sheets;
}

// ── ExportPort 다리 · 직렬화 DTO(SheetSelectionDTO) → 내부 SheetSelection → buildWorkbook 바이트 ──
// public 어댑터(runtime)는 surfaces 를 import 못 하므로(역방향 금지), 셸이 이 함수로 ExportInput 을 .xlsx 바이트로
// 변환해 publicExportPort 의 exportShared.buildWorkbookBytes 로 주입한다. 직접 ViewerStudio 경로(deriveWorkbookInput
// →buildWorkbook)와 *동일* 격자/writer 라 산출 .xlsx 동형(패리티).

/** DTO 의 sectionKey 내 행 절대 인덱스 해석 · store id(`${sectionKey}|${index}`) 우선, 폴백은 (blockLeaf,disclosureKey,scope) 매칭. */
function resolveIndexInSection(sel: SheetSelectionDTO, rows: PanelRow[]): number {
	// store 생성 id 는 끝에 정수 인덱스(selectionId). id 가 `${sectionKey}|${n}` 이면 그 n 사용.
	const tail = sel.id.slice(sel.sectionKey.length + 1);
	const n = Number(tail);
	if (Number.isInteger(n) && n >= 0 && n < rows.length) return n;
	// 폴백 · 동일 식별자 첫 매칭(같은 blockLeaf 다중행은 disclosureKey/scope 로 좁힘).
	return rows.findIndex(
		(r) => r.blockLeaf === sel.blockLeaf && r.disclosureKey === sel.disclosureKey && r.scope === sel.scope
	);
}

/** SheetSelectionDTO → 내부 SheetSelection(bundle 행 해석). 행 미발견이면 null. */
function dtoToSelection(sel: SheetSelectionDTO, bundle: PanelBundle): SheetSelection | null {
	const rows = bundle.gridBySection.get(sel.sectionKey);
	if (!rows) return null;
	const idx = resolveIndexInSection(sel, rows);
	if (idx < 0) return null;
	const row = rows[idx];
	return {
		id: selectionId(sel.sectionKey, idx),
		sectionKey: sel.sectionKey,
		indexInSection: idx,
		blockLeaf: row.blockLeaf,
		disclosureKey: row.disclosureKey,
		scope: row.scope,
		blockType: row.blockType,
		label: trimLabel(sel.label || row.blockLeaf),
		mode: sel.mode,
		periods: sel.periods,
		order: sel.order
	};
}

/**
 * ExportInput(직렬화 DTO) + bundle → 진짜 .xlsx 바이트. publicExportPort 주입(03 §3 패리티 다리).
 *
 * @param input ExportInput(code·selections·includeProvenance).
 * @param bundle 현재 회사 PanelBundle(loadPanelBundle LRU 캐시 · 재다운로드 0).
 * @returns .xlsx Uint8Array 또는 null(내보낼 데이터 없음).
 *
 * @example
 * const bytes = exportInputToWorkbookBytes(input, bundle);
 */
export function exportInputToWorkbookBytes(input: ExportInput, bundle: PanelBundle): Uint8Array | null {
	const ordered = [...input.selections].sort((a, b) => a.order - b.order);
	const selections: SheetSelection[] = [];
	for (const dto of ordered) {
		const s = dtoToSelection(dto, bundle);
		if (s) selections.push(s);
	}
	if (!selections.length) return null;
	const includeSource = input.includeProvenance !== false;
	const sheets = deriveWorkbookInput(selections, bundle, includeSource);
	if (!sheets.length) return null;
	return buildWorkbook(sheets);
}
