// 정기보고서 주석 구성 · XBRL 셀(xbrlCells)에서 비용 성격별·부문별 매출을 뽑아 기간 시계열로.
// 비용 = acode(정부 IFRS 택소노미가 곧 카테고리). 부문 = axisPath 세그먼트 멤버. 표 레이아웃 파싱 0(태그 직독).
// 순수 함수(렌더·IO 0) · reportSource 가 panel 기간별로 호출. 최근 분기(ACONTEXT 2025-03+)만 자연 포착.

import type { CompositionPoint, CompositionSeries } from '@dartlab/ui-contracts';
import type { XbrlCell } from './xbrlCells';

// 비용: 총계(ExpenseByNature)·재고변동(ChangesInInventories) acode 제외.
const COST_DROP = /ExpenseByNature|ChangesInInventories/;
// 부문: 화이트(영업/보고부문 축)·블랙(지역·고객·제품)·집계멤버·2자리 국가코드.
const SEG_AXIS = /OperatingSegments|ReportableSegments|BusinessSegments/;
const SEG_NONSEG = /Geograph|Countr|Domestic|Foreign|Overseas|MajorCustomer|ProductsAndServices|Americas|Europe|Asia|Africa|China|Japan|Korea|NorthAmerica|SouthAmerica|MiddleEast|Oceania/;
const SEG_AGG = /^(Operating|Consolidated|Total|Reportable|Business|Intersegment)?Segments?$|^(Operating|Consolidated|Total|Reportable)$/;
const SEG_CC = /^(Cn|Us|Jp|Kr|Uk|De|Fr|Eu|In|Vn|Sg|Hk|Tw|Au|Ca|Br|Ru|Mx|Id|Th|My|Ph|It|Es|Nl|Pl|Tr|Ae|Sa)$/i;

// 당기 셀만 · 해당 기간 연도 & 흐름 모드(A=누적YTD / Y=연간). 전기/전전기(ctxYear<year) 배제.
const isCurrent = (c: XbrlCell, year: number): boolean => c.ctxYear === year && (c.ctxMode === 'A' || c.ctxMode === 'Y');

/** axisPath leaf → 읽을 세그먼트명. entity 접두·택소노미 꼬리·집계어 제거. */
export function segName(axis: string): string {
	let last = axis.split('|').pop() ?? '';
	last = last.replace(/^entity\d+_/, '');
	last = last.replace(/(Member)?Of(Entity|Reportable|Disclosure|Consolidat|Segment|Operating|Total|Group|Geograph|Countr)[\s\S]*$/, '');
	last = last.replace(/MemberOf[\s\S]*$/, '');
	last = last.replace(/(Member|Segments?|Business|Sector|Division|Operations?)$/, '');
	return last.trim();
}

/** 한 기간 비용 성격별 구성 · acode별 당기 값(라벨=한글명). key=acode(언어무관 정체성). */
export function costCells(cells: XbrlCell[], year: number): Map<string, { name: string; value: number }> {
	const out = new Map<string, { name: string; value: number }>();
	for (const c of cells) {
		if (!isCurrent(c, year) || c.value <= 0) continue;
		if (!c.acode || COST_DROP.test(c.acode)) continue;
		const prev = out.get(c.acode);
		out.set(c.acode, { name: (c.label || '').trim() || c.acode, value: (prev?.value ?? 0) + c.value });
	}
	return out;
}

/** 한 기간 부문별 매출 · Revenue 셀 × 영업/보고부문 축(지역·고객·제품·집계 배제). key=세그먼트명. */
export function segmentCells(cells: XbrlCell[], year: number): Map<string, { name: string; value: number }> {
	const out = new Map<string, { name: string; value: number }>();
	for (const c of cells) {
		if (!isCurrent(c, year) || c.value <= 0) continue;
		if (c.acode.indexOf('Revenue') < 0) continue;
		const ax = c.axisPath;
		if (!SEG_AXIS.test(ax) || SEG_NONSEG.test(ax)) continue;
		const nm = segName(ax);
		if (!nm || SEG_AGG.test(nm) || SEG_CC.test(nm)) continue;
		const prev = out.get(nm);
		out.set(nm, { name: nm, value: (prev?.value ?? 0) + c.value });
	}
	return out;
}

export interface PeriodComposition {
	period: string;
	year: string;
	quarter: string;
	items: Map<string, { name: string; value: number }>; // key→(표시명,값)
}

/** 기간별 구성 → 시계열(CompositionSeries). 전 기간 합계 상위 K 카테고리(+비용은 '기타' 롤업) 안정 정렬. */
export function buildSeries(perPeriod: PeriodComposition[], { topK, rollupOther }: { topK: number; rollupOther: boolean }): CompositionSeries | null {
	// 표시명을 정체성으로 재키잉(병합) · 서로 다른 acode 가 같은 한글 라벨(예 '급여')을 가지면 categories 에
	// 중복명이 생겨 다이얼로그·패널의 keyed {#each (name)} 가 each_key_duplicate 로 렌더 throw → 마운트 실패.
	// 같은 표시명은 같은 경제 카테고리이므로 값 합산이 정합. (부문은 이미 name-key 라 무변.)
	const merged: PeriodComposition[] = perPeriod.map((p) => {
		const m = new Map<string, { name: string; value: number }>();
		for (const v of p.items.values()) {
			const prev = m.get(v.name);
			m.set(v.name, { name: v.name, value: (prev?.value ?? 0) + v.value });
		}
		return { ...p, items: m };
	});
	const valid = merged.filter((p) => p.items.size > 0);
	if (valid.length < 1) return null;
	valid.sort((a, b) => a.period.localeCompare(b.period));
	// 전 기간 카테고리 합계 → 상위 K. 표시명 = 최신 기간 표기.
	const gtot = new Map<string, number>();
	const gdisp = new Map<string, string>();
	for (const p of valid) for (const [k, v] of p.items) gtot.set(k, (gtot.get(k) ?? 0) + v.value);
	for (let i = valid.length - 1; i >= 0; i--) for (const [k, v] of valid[i]!.items) gdisp.set(k, v.name);
	const topKeys = [...gtot.entries()].sort((a, b) => b[1] - a[1]).map((e) => e[0]).slice(0, topK);
	const topSet = new Set(topKeys);
	const categories = topKeys.map((k) => gdisp.get(k) ?? k).concat(rollupOther ? ['기타'] : []);
	const points: CompositionPoint[] = valid.map((p) => {
		let total = 0;
		for (const v of p.items.values()) total += v.value;
		const shares = topKeys.map((k) => (total > 0 ? ((p.items.get(k)?.value ?? 0) / total) * 100 : 0));
		if (rollupOther) {
			const sumTop = shares.reduce((a, b) => a + b, 0);
			shares.push(Math.max(0, 100 - sumTop));
		}
		return { period: p.period, year: p.year, quarter: p.quarter, total, shares };
	});
	return { categories, points };
}
