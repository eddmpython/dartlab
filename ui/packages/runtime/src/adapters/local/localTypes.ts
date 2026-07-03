// 로컬 Python 서버(/api) 응답 타입 · 계약 타입과 다른 원천 형태(정규화 대상).
// ui/web React 클라이언트(@/features/dashboard/api/client)와 같은 /api 표면이지만 그 패키지를 import 하지 않는다
// (ui/web 동결·React 결합). 어댑터가 같은 계약을 독립 선언한다.
// (ipo 리포트는 /api 응답이 계약(IpoReport)과 1:1 이라 별도 Client 타입 없이 계약 타입을 그대로 캐시 키에 쓴다.)
import type { IpoReport } from '@dartlab/ui-contracts';

export interface CompanyMeta {
	stockCode: string;
	corpName: string;
	market: string;
	sector: string;
	products: string[];
	blogPosts: { title: string; slug: string; url: string }[];
}

export interface DisclosureItem {
	title: string;
	rceptNo: string;
	url: string;
	discType: string;
}

export interface DayEvents {
	disclosures?: DisclosureItem[];
}

export interface PriceEventsPayload {
	stockCode: string;
	corpName: string | null;
	market: string;
	start: string;
	end: string;
	ohlc: number[][]; // [ts, open, high, low, close, volume]
	events: Record<string, DayEvents>;
}

// ── panel · 로컬 서버 응답 (계약과 발산) ──
// toc 블록은 rowCount 보유·leafType/disclosureKey 미보유 / grid chapter·sectionLeaf nullable·dartUrl nullable.
export interface ClientPanelTocBlock {
	blockLeaf: string;
	rowCount: number;
}
export interface ClientPanelTocSection {
	sectionLeaf: string;
	sectionKey: string; // `${chapter}␟${sectionLeaf}`
	rowCount: number;
	blocks: ClientPanelTocBlock[];
}
export interface ClientPanelTocChapter {
	chapter: string;
	sections: ClientPanelTocSection[];
}
export interface ClientPanelToc {
	stockCode: string;
	corpName: string;
	chapters: ClientPanelTocChapter[];
	periods: string[];
}
export interface ClientPanelRow {
	chapter: string;
	sectionLeaf: string;
	blockLeaf: string;
	disclosureKey: string | null;
	scope: string | null;
	blockType: 'text' | 'table';
	cells: Record<string, string>;
}
export interface ClientPanelGrid {
	stockCode: string;
	corpName: string;
	chapter: string | null;
	sectionLeaf: string | null;
	sectionKey: string;
	periods: string[];
	rows: ClientPanelRow[];
	dartUrlByPeriod?: Record<string, string | null>;
}
export interface ClientPanelInit {
	stockCode: string;
	corpName: string;
	toc: ClientPanelToc;
	firstChapter: string | null;
	firstSectionKey: string | null;
	grid: ClientPanelGrid | null;
}

// 회사 단위 fetch 1회 공유 캐시 (런타임 인스턴스 범위) · price·filing·company 포트가 같은 응답 재사용.
export interface LocalCaches {
	priceEvents: Map<string, Promise<PriceEventsPayload | null>>;
	panelInit: Map<string, Promise<ClientPanelInit | null>>;
	meta: Map<string, Promise<CompanyMeta | null>>;
	/** IPO 단건 리포트 · rcept 단위 불변 + 서버 런타임 파싱(수초)이라 재클릭 재파싱 방지. 키 = rcept:확정rcept. */
	ipoReport: Map<string, Promise<IpoReport | null>>;
}
