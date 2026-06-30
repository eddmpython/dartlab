// 공시뷰어 데이터 계약 · ui/web `features/dashboard/api/client.ts` 와 동일 shape.
// 브라우저 readWide(panelWide.ts)가 산출하고 Svelte 컴포넌트가 소비.

// panel parquet 한 leaf 행 (brower read 필요 컬럼). 컬럼 목록은 panelLoad.READ_COLUMNS. pipeline 입력 단위.
export interface LeafRow {
	chapter: string | null;
	sectionLeaf: string | null;
	sectionPath: string | null;
	blockLeaf: string | null;
	leafType: string | null;
	disclosureKey: string | null;
	xbrlClass: string | null;
	blockOrder: number | null;
	contentRaw: string | null;
	period: string | null;
	rceptNo: string | null;
}

export interface PanelRow {
	chapter: string;
	sectionLeaf: string;
	blockLeaf: string;
	leafType: string;
	disclosureKey: string | null; // null = narrative 행
	scope: string | null;
	blockType: 'text' | 'table';
	cells: Record<string, string>; // period → 셀 본문 (raw DART XML, 무손실)
}

export interface PanelTocBlock {
	blockLeaf: string;
	rowCount: number;
}

export interface PanelTocSection {
	sectionLeaf: string;
	sectionKey: string; // `${chapter}␟${sectionLeaf}`
	rowCount: number;
	blocks: PanelTocBlock[];
}

export interface PanelTocChapter {
	chapter: string;
	sections: PanelTocSection[];
}

export interface PanelTocResponse {
	stockCode: string;
	corpName: string;
	chapters: PanelTocChapter[];
	periods: string[]; // 최신좌측 정렬 (timeline SSOT)
}

// 한 회사 전체 · 브라우저가 panel 하나에서 온더플라이로 산출.
export interface PanelBundle {
	stockCode: string;
	corpName: string;
	toc: PanelTocResponse;
	periods: string[];
	gridBySection: Map<string, PanelRow[]>; // sectionKey → rows
	dartUrlByPeriod: Record<string, string | null>;
	periodKind: Record<string, 'annual' | 'quarter'>; // period → 보고서 유형(회사별 결산 보정). "연간만" 필터용
}
