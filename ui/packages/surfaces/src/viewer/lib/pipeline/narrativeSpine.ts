// anchorNarrativeToSpine · 섹션 라벨을 SPINE(최신 필링 골격=핵) 등재 라벨로 통일. Python read 1:1.
// 3중 수렴(전부 bounded·항목 동일성 구조 보장, 자유 fuzzy 0 · keyed/narrative 균일, sectionLeaf 는 그룹핑 라벨):
//   ① 챕터-자기행(로마/【 헤더) 변형 → canonical 챕터 라벨 ("IV. 감사인의~"→"V. 회계감사인의 감사의견 등")
//   ② SPINE 코어 일치 = 표면 표기 정규화("6.배당 등"→"6.배당", 옛 번호→현행 번호)
//   ③ era-alias(서식개정 실질 명칭변경, 운영자 수동) · 옛 INS_* keyed 감사절 포함 현행 절로 수렴

import { canonLabel, NARRATIVE_ERA_ALIASES } from '../canonical';
import { NOTE_TITLE_NORM, SEP, SPINE_ORDER } from '../keys';
import type { LeafRow } from '../types';

const NARR_NUM_RE = /^\s*\d+(-\d+)?\.?\s*/; // 선행 절 번호
const NARR_ETC_RE = /\s*등\s*$/; // 후행 '등'(era 변종)
const SELF_HDR_RE = /^\s*(?:[IVXLCDM]+\s*\.|【)/; // 챕터-자기행 헤더형 · 번호절 비대상

export function narrativeCore(leaf: string): string {
	return (leaf ?? '').replace(NARR_NUM_RE, '').trim().replace(NARR_ETC_RE, '').replace(NOTE_TITLE_NORM, '');
}

// SPINE_ORDER 키(NARR::{chapter}␟{sectionLeaf})에서 {chapter␟코어 → 정식 sectionLeaf} 룩업 (첫 등장 우선).
const SPINE_NARR_MAP: Record<string, string> = (() => {
	const m: Record<string, string> = {};
	for (const ident of Object.keys(SPINE_ORDER)) {
		if (!ident.startsWith('NARR::')) continue;
		const body = ident.slice('NARR::'.length);
		const i = body.indexOf(SEP);
		if (i < 0) continue;
		const chap = body.slice(0, i);
		const leaf = body.slice(i + 1);
		const key = `${chap}${SEP}${narrativeCore(leaf)}`;
		if (!(key in m)) m[key] = leaf;
	}
	return m;
})();

// 서식개정 era-alias · {chapter␟옛코어 → 현행 SPINE 라벨}. 현행코어가 SPINE 미등재면 미등재(데이터가 가부 결정).
const ERA_ALIAS_MAP: Record<string, string> = (() => {
	const m: Record<string, string> = {};
	for (const [chap, aliases] of Object.entries(NARRATIVE_ERA_ALIASES)) {
		for (const [oldCore, newCore] of Object.entries(aliases)) {
			const label = SPINE_NARR_MAP[`${chap}${SEP}${newCore}`];
			if (label != null) m[`${chap}${SEP}${oldCore}`] = label;
		}
	}
	return m;
})();

export function anchorNarrativeToSpineRow(r: LeafRow): void {
	// ① 챕터-자기행 변형 수렴 · 헤더형이면서 canonical 라벨이 자기 chapter 와 일치할 때만.
	const leaf = r.sectionLeaf ?? '';
	if (r.chapter != null && SELF_HDR_RE.test(leaf) && canonLabel(leaf) === r.chapter) {
		r.sectionLeaf = r.chapter;
	}
	// ② SPINE 코어 일치(표면 정규화) → ③ era-alias(서식개정) · keyed 포함 균일.
	const key = `${r.chapter ?? ''}${SEP}${narrativeCore(r.sectionLeaf ?? '')}`;
	const canon = SPINE_NARR_MAP[key] ?? ERA_ALIAS_MAP[key];
	if (canon != null) r.sectionLeaf = canon;
}
