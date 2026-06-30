// 브라우저 readWide 오케스트레이터 · panel long(flat 16-col) 하나에서 항목×기간 wide 를 온더플라이 계산.
//
// Python `panel.read.readWide` 1:1 포팅. 파이프라인 단계는 pipeline/* 모듈, TOC 는 toc/buildToc, 보고서유형
// 보정은 periodKind, 공유 키는 keys 로 분리(클린 모듈 트리). 본 파일은 단계 호출 + leafSeq·collapse·pivot·order
// 오케스트레이션만. 파생 artifact 0 (hyparquet 으로 HF panel 직접 read).

import { canonicalChapter, canonicalRank } from './canonical';
import { marketForCode, viewerUrl } from './dartUrl';
import { SEP, sectionKeyFor, spineOrderFor, scopeOf } from './keys';
import { computePeriodKind } from './periodKind';
import { absorbAttachedRow, sectionNum } from './pipeline/absorbAttached';
import { alignNotes } from './pipeline/alignNotes';
import { anchorLatest } from './pipeline/anchorLatest';
import { anchorNarrativeToSpineRow } from './pipeline/narrativeSpine';
import { dedupKeyed } from './pipeline/dedupKeyed';
import { buildToc } from './toc/buildToc';
import type { LeafRow, PanelBundle, PanelRow } from './types';

// period 최신순(내림차순) · "YYYYQn" 문자열 정렬.
function sortPeriodsDesc(periods: string[]): string[] {
	return [...periods].sort((a, b) => (a < b ? 1 : a > b ? -1 : 0));
}

// ── 핵심: leaf 행들 → PanelBundle (순수, 로컬 parity 테스트 가능) ──
export function buildPanelBundle(
	leafRows: LeafRow[],
	opts: { code: string; corpName?: string; noteTaxonomy?: Record<string, string> }
): PanelBundle {
	const rows = leafRows.slice(); // 빈 content 도 leafSeq 랭킹·뼈대에 포함 (Python readWide 와 동일, 빈셀은 출력서 제외)
	const market = marketForCode(opts.code);
	const empty: PanelBundle = {
		stockCode: opts.code,
		corpName: opts.corpName ?? '',
		toc: { stockCode: opts.code, corpName: opts.corpName ?? '', chapters: [], periods: [] },
		periods: [],
		gridBySection: new Map(),
		dartUrlByPeriod: {},
		periodKind: {}
	};
	if (rows.length === 0) return empty;

	// corpName · panel 에 회사명 컬럼 없음(corp=코드). opt 로만 주입, 없으면 빈값(라우트가 코드로 표기).
	const corpName = opts.corpName ?? '';

	alignNotes(rows, opts.noteTaxonomy ?? {});
	anchorLatest(rows);
	const deduped = dedupKeyed(rows);

	// canonicalChapter (sectionPath 깊은 canonical 원소 우선 + 구조신호 0 NT_ 주석 → III 복원) + (첨부) 흡수
	// + narrative era 변종 SPINE 통일.
	for (const r of deduped) {
		r.chapter = canonicalChapter(r.chapter, r.sectionPath, r.disclosureKey);
		absorbAttachedRow(r);
		anchorNarrativeToSpineRow(r); // chapter 확정·(첨부) 흡수 후 = SPINE 룩업 키 정합 (read.py 1:1)
	}

	// leafSeq · narrative(disclosureKey null) 는 (chapter,sectionLeaf,leafType,period) 내 blockOrder ordinal rank, keyed=0.
	const seqGroups = new Map<string, LeafRow[]>();
	for (const r of deduped) {
		if (r.disclosureKey != null) {
			(r as LeafRow & { leafSeq: number }).leafSeq = 0;
			continue;
		}
		const gk = [r.chapter ?? '', r.sectionLeaf ?? '', r.leafType ?? '', r.period ?? ''].join(SEP);
		let arr = seqGroups.get(gk);
		if (!arr) seqGroups.set(gk, (arr = []));
		arr.push(r);
	}
	for (const arr of seqGroups.values()) {
		arr.sort((a, b) => (a.blockOrder ?? 0) - (b.blockOrder ?? 0));
		arr.forEach((r, i) => ((r as LeafRow & { leafSeq: number }).leafSeq = i + 1));
	}

	// collapse · indexKey(=[chapter,sectionLeaf,blockLeaf,leafType,disclosureKey,scope,leafSeq]) × period.
	interface Agg {
		chapter: string; sectionLeaf: string; blockLeaf: string; leafType: string;
		disclosureKey: string | null; scope: string | null; leafSeq: number;
		cellParts: Map<string, { bo: number; text: string }[]>; // period → leaves
	}
	const aggs = new Map<string, Agg>();
	const periodSet = new Set<string>();
	for (const r of deduped) {
		const scope = scopeOf(r.xbrlClass);
		const leafSeq = (r as LeafRow & { leafSeq: number }).leafSeq;
		const chapter = r.chapter ?? '';
		const sectionLeaf = r.sectionLeaf ?? '';
		const blockLeaf = r.blockLeaf ?? '';
		const leafType = r.leafType ?? '';
		const period = r.period ?? '';
		periodSet.add(period);
		const ik = [chapter, sectionLeaf, blockLeaf, leafType, r.disclosureKey ?? ' ', scope ?? '', leafSeq].join(SEP);
		let a = aggs.get(ik);
		if (!a) aggs.set(ik, (a = { chapter, sectionLeaf, blockLeaf, leafType, disclosureKey: r.disclosureKey, scope, leafSeq, cellParts: new Map() }));
		let parts = a.cellParts.get(period);
		if (!parts) a.cellParts.set(period, (parts = []));
		parts.push({ bo: r.blockOrder ?? 0, text: r.contentRaw ?? '' });
	}

	const periods = sortPeriodsDesc([...periodSet]);
	const q4 = periods.filter((p) => p.endsWith('Q4'));
	const latestP = (q4.length ? q4 : periods).reduce((m, p) => (p > m ? p : m), '');

	// 각 agg → cells(join by blockOrder) + skeleton(_skel=latestP _bo, _skelOld=마지막 period _bo).
	interface Built extends Agg { cells: Record<string, string>; skel: number | null; skelOld: number | null; canonRank: number | null; spOrder: number | null; secNum: number | null; secSub: number; }
	const built: Built[] = [];
	for (const a of aggs.values()) {
		const cells: Record<string, string> = {};
		let skel: number | null = null;
		let skelOld: number | null = null;
		let lastPeriodSeen = '';
		const periodKeys = [...a.cellParts.keys()].sort();
		for (const p of periodKeys) {
			const parts = a.cellParts.get(p)!.slice().sort((x, y) => x.bo - y.bo);
			const joined = parts.map((x) => x.text).join('');
			if (joined) cells[p] = joined; // 빈셀 제외(serializePanelRows 동일)
			const minBo = parts.reduce((m, x) => Math.min(m, x.bo), Infinity);
			if (p === latestP) skel = minBo;
			if (p >= lastPeriodSeen) { lastPeriodSeen = p; skelOld = minBo; } // 마지막(최대) period 의 _bo
		}
		const [secNum, secSub] = sectionNum(a.sectionLeaf);
		built.push({
			...a,
			cells,
			skel,
			skelOld,
			canonRank: canonicalRank(a.chapter),
			spOrder: spineOrderFor(a.disclosureKey, a.chapter, a.sectionLeaf),
			secNum,
			secSub
		});
	}

	// order · [_canonRank, _secNum(절 번호), _secSub, _spOrder(XBRL 척추), _skel, _skelOld, leafSeq] nulls_last (orderBySpine 1:1).
	const nl = (v: number | null) => (v == null ? Infinity : v);
	built.sort((x, y) =>
		nl(x.canonRank) - nl(y.canonRank) ||
		nl(x.secNum) - nl(y.secNum) ||
		x.secSub - y.secSub ||
		nl(x.spOrder) - nl(y.spOrder) ||
		nl(x.skel) - nl(y.skel) ||
		nl(x.skelOld) - nl(y.skelOld) ||
		x.leafSeq - y.leafSeq
	);

	// PanelRow + gridBySection (빈셀 행 제외 = serializePanelRows 동일).
	const gridBySection = new Map<string, PanelRow[]>();
	for (const b of built) {
		if (Object.keys(b.cells).length === 0) continue; // 본문 0 행 skip
		const row: PanelRow = {
			chapter: b.chapter,
			sectionLeaf: b.sectionLeaf,
			blockLeaf: b.blockLeaf,
			leafType: b.leafType,
			disclosureKey: b.disclosureKey,
			scope: b.scope,
			blockType: Object.values(b.cells).some((v) => v.includes('<TABLE')) ? 'table' : 'text',
			cells: b.cells
		};
		const sk = sectionKeyFor(b.chapter, b.sectionLeaf);
		let arr = gridBySection.get(sk);
		if (!arr) gridBySection.set(sk, (arr = []));
		arr.push(row);
	}

	const toc = buildToc(opts.code, corpName, gridBySection, periods);

	// dartUrlByPeriod · period 별 첫 rceptNo (leafRows 원본).
	const rceptByPeriod = new Map<string, string>();
	for (const r of leafRows) {
		if (r.period && r.rceptNo && !rceptByPeriod.has(r.period)) rceptByPeriod.set(r.period, r.rceptNo);
	}
	const dartUrlByPeriod: Record<string, string | null> = {};
	for (const p of periods) dartUrlByPeriod[p] = viewerUrl(market, rceptByPeriod.get(p) ?? null);

	// 보고서 유형 보정 · period 별 비빈 셀수(본문량) 누적 → computePeriodKind (사업보고서 분기 검출).
	const cellCount: Record<string, number> = {};
	for (const arr of gridBySection.values()) {
		for (const row of arr) for (const p in row.cells) cellCount[p] = (cellCount[p] ?? 0) + 1;
	}
	const periodKind = computePeriodKind(periods, cellCount);

	return { stockCode: opts.code, corpName, toc, periods, gridBySection, dartUrlByPeriod, periodKind };
}
