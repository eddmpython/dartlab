// buildToc · 본문(gridBySection) 섹션 기반 chapter > sectionLeaf > blockLeaf 트리 (market-aware).
// DART: navigable 보고서 챕터(I~XII = REPORT_CHAPTER_LABELS)만 · 표지/확인서(cover/expert)·front-matter('')·
// stray 제외. VII.주주처럼 본문이 전부 ==chapter 아래인 챕터는 헤더를 절로 노출. EDGAR: form 챕터 전부 +
// edgarSectionStatus 로 오검출 Item(405/prose tail)·표지 제외, 재무제표 terse 키(BS/IS)는 사람 라벨 relabel
// (sectionKey 는 raw 보존 → grid lookup parity). companyApi.buildToc(서버)와 동형 · 단 빈셀(전 기간 무내용)
// 섹션은 JS 가 gridBySection 진입 전 skip(원 뷰어 엔진의 선재 차이).

import { isReportChapter } from '../canonical';
import { marketForCode } from '../dartUrl';
import { edgarSectionStatus, STMT_LABELS } from '../edgarSection';
import { SEP } from '../keys';
import type { PanelRow, PanelTocBlock, PanelTocChapter, PanelTocResponse, PanelTocSection } from '../types';

export function buildToc(
	code: string,
	corpName: string,
	gridBySection: Map<string, PanelRow[]>,
	periods: string[]
): PanelTocResponse {
	const isUs = marketForCode(code) === 'US';
	const order: string[] = []; // chapter first-appearance
	const chMap = new Map<string, { chapter: string; real: PanelTocSection[]; header: PanelTocSection | null }>();
	for (const [sk, rows] of gridBySection) {
		const i = sk.indexOf(SEP);
		const chapter = i < 0 ? sk : sk.slice(0, i);
		const rawLeaf = i < 0 ? '' : sk.slice(i + 1);
		if (!chapter) continue;
		let displayLeaf = rawLeaf;
		if (isUs) {
			const status = edgarSectionStatus(chapter, rawLeaf);
			if (status === 'junk') continue; // 오검출 Item·표지 제외 (panel 데이터엔 보존)
			if (status === 'stmt') displayLeaf = STMT_LABELS[rawLeaf] ?? rawLeaf; // BS → "Balance Sheet"
		}
		let ch = chMap.get(chapter);
		if (!ch) { ch = { chapter, real: [], header: null }; chMap.set(chapter, ch); order.push(chapter); }
		// blocks(chip) · blockLeaf 있는 행만, 첫등장 순서.
		const blocks: PanelTocBlock[] = [];
		const blockIdx = new Map<string, PanelTocBlock>();
		for (const r of rows) {
			if (!r.blockLeaf) continue;
			const ex = blockIdx.get(r.blockLeaf);
			if (ex) ex.rowCount++;
			else { const b: PanelTocBlock = { blockLeaf: r.blockLeaf, rowCount: 1 }; blockIdx.set(r.blockLeaf, b); blocks.push(b); }
		}
		const sec: PanelTocSection = { sectionLeaf: displayLeaf, sectionKey: sk, rowCount: rows.length, blocks };
		if (rawLeaf === chapter) ch.header = sec;
		else ch.real.push(sec);
	}
	// 챕터 거름 · DART: REPORT_CHAPTER_LABELS(I~XII, cover/expert·front-matter·stray 제외). EDGAR: form 챕터 전부.
	const chapters: PanelTocChapter[] = order
		.map((c) => chMap.get(c)!)
		.filter((ch) => (isUs ? !!ch.chapter : isReportChapter(ch.chapter)))
		.map((ch) => ({ chapter: ch.chapter, sections: ch.real.length ? ch.real : ch.header ? [ch.header] : [] }))
		.filter((ch) => ch.sections.length > 0);
	return { stockCode: code, corpName, chapters, periods };
}
