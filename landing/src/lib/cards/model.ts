// 라이브 카드 캐러셀 모델 — /report 의 ReportModel 을 슬라이드 덱으로 투영한 결과 타입.
// 굽지 않음(라이브). 카드 본문 차트는 report 인라인 SVG 헬퍼($lib/report/render)로 그려 백테스트·
// klinecharts 0 의존(백본). 손글 narration·hero 이미지는 큐레이션 오버레이(P5)·hfMedia(P0)에서 합류.
import type { ReportSourceEngine } from '$lib/report/model';

/** hfMedia(companies/index.json)의 회사별 항목 — 서빙용(name=콘텐츠해시 삽입된 served 파일명). */
export interface MediaAsset {
	/** 콘텐츠해시 삽입 served 파일명 (`dram-chip.ab12cd34.webp`). */
	name: string;
	hash: string;
}
export interface MediaCompany {
	displayName: string;
	market: 'kr' | 'us';
	similarTo: string[];
	assets: MediaAsset[];
}
export interface MediaIndex {
	version: number;
	companies: Record<string, MediaCompany>;
}

/** 슬라이드 공통 머리 — splitTitle 로 쪼갠 섹션 제목 + 큐레이션 손글 caption(note) + 배경 hero 사진. */
interface CardHead {
	heading?: string;
	sub?: string;
	engine?: ReportSourceEngine;
	/** 큐레이션 오버레이(CarouselSpec.notes)에서 주입한 손글 한 줄 — no-new-number(본문 숫자⊆). 자동 투영엔 없음. */
	note?: string;
	/** 배경 hero 사진 URL — 전 슬라이드가 회사 사진을 배경으로(인스타 에디토리얼). hero 전부를 슬라이드에 순환 배정. */
	bg?: string;
	/** 챕터 라벨(표지/핵심지표/재무/사업·운영) — 캡션 패널 섹션 점프 네비(chapterAnchors)용. 20장+ 익명 닷 보완. */
	chapter?: string;
}

// 카드(슬라이드) 판별 유니온. chart 계열(line/bars/share/table)은 ReportBlock 과 1:1.
export type CarouselCard =
	| (CardHead & {
			kind: 'cover';
			corpName: string;
			stockCode: string;
			perspectiveLabel: string;
			conclusion: string;
			dataBasis: string;
	  })
	| (CardHead & { kind: 'kpis'; metrics: { label: string; value: string }[] })
	| (CardHead & { kind: 'narrative'; text: string })
	| (CardHead & { kind: 'flags'; tone: 'warning' | 'opportunity'; items: string[] })
	| (CardHead & {
			kind: 'line';
			series: number[];
			xLabels?: [string, string];
			markers?: { label: string; v: number }[];
			valueFmt?: 'won';
	  })
	| (CardHead & { kind: 'bars'; rows: { label: string; value: number; display: string; tone?: 'neg' }[] })
	| (CardHead & {
			kind: 'share';
			rows: { year: string; segs: { label: string; pct: number; key: string }[] }[];
			legend: { label: string; key: string }[];
	  })
	// 주석 구성(부문별매출·비용성격별) — 시간축 100% 세로 스택 컬럼 + 구성 테이블(터미널 NotesDashboardDialog 동형).
	| (CardHead & {
			kind: 'composition';
			categories: string[]; // 정제 표시명 — 색(index)·범례·적층·표행 순서 SSOT (최신 비중 desc)
			periods: string[]; // 짧은 기간 라벨(세로 스택 x축 + 표 헤더) — 최근 N
			shares: number[][]; // [기간][카테고리] 비중%(0~100) — 적층 높이 + 표 셀
			amounts: (number | null)[]; // [카테고리] 최신 기간 금액(원) — 표 '당기' 열
			latestTotal: number; // 최신 기간 합계(원)
			latestPeriod: string; // 최신 기간 라벨(헤더 우측)
	  })
	| (CardHead & { kind: 'table'; cols: string[]; data: Record<string, string>[]; unit?: string })
	| (CardHead & { kind: 'finChart'; stockCode: string; cardKey?: string }) // MiniFinChart 백본(finance.bundle) — cardKey=관점 카드 선택(없으면 cards[0])
	| (CardHead & { kind: 'closing'; thesis: string })
	| (CardHead & { kind: 'empty'; reason: string }) // pending/skip 정직 카드(broken img 아님)
	// ── 편집 카드(기존 SNS 캐러셀 계약 carousels/{code}.json 손글 카피) — `[[강조]]`=accentImpact ──
	| (CardHead & { kind: 'editorial'; date?: string; line: string; sub?: string }) // 커버
	| (CardHead & { kind: 'editorialBeat'; kicker?: string; line: string; sub?: string }) // 헤드라인 비트
	| (CardHead & { kind: 'editorialStat'; kicker?: string; bigNumber: string; unit?: string; context?: string }); // 큰 숫자

export interface CarouselDeck {
	stockCode: string;
	corpName: string;
	market?: 'kr' | 'us';
	perspectiveKey: string;
	perspectiveLabel: string;
	asOf: string;
	heroUrls: string[]; // 회사 hero 전부(슬라이드 배경 순환). 첫 장 = 표지 사진.
	cards: CarouselCard[];
}

// ── 편집 카드 캐러셀 계약(carousels/{code}.json) — 기존 SNS 캐러셀 손글 카피 SSOT. ──
export interface ContractSlide {
	layout: 'editorial' | 'editorialBeat' | 'editorialStat';
	date?: string;
	kicker?: string;
	line?: string;
	sub?: string;
	bigNumber?: string;
	unit?: string;
	context?: string;
	image?: string; // semantic 파일명(해시 없음) — 렌더가 hfMedia 매니페스트로 해석
}

export interface ContractExplainer {
	term: string;
	body: string;
}

export interface ContractRelatedNews {
	title: string;
	url: string;
	source?: string;
	date?: string;
	description?: string;
	track?: 'naver' | 'gdelt' | 'official' | 'web' | string;
}

export interface ContractMetric {
	label: string;
	value: string;
}

export interface CarouselContract {
	/** 종목코드 — 회사 캐러셀만. 이슈(standalone)는 빈 문자열(렌더가 회사 report 조회 안 함). */
	code: string;
	/** 글 슬러그(`003230-samyang-foods`) 또는 이슈 슬러그(`2026-06-korea-macro`) — serve 키. 회사당 N편(1:N). */
	slug: string;
	name: string;
	/** standalone 이슈 캐러셀(블로그 글 없음) — true 면 PostModal '블로그 이어 읽기' CTA 숨김·회사 차트 미첨부. */
	standalone?: boolean;
	sector?: string;
	/** 인스타 포스트 제목(blog title / meta.json title) — 우측 캡션 패널 헤드라인. */
	title?: string;
	/** 인스타 캡션(caption) — 포스트 우측 설명 산문(문단=빈 줄 구분). 슬라이드와 별개의 본문. */
	caption?: string;
	/** 편집자가 검증한 핵심 지표 — 자동 재무 번들 결측 시 빈 KPI 대신 이 값을 렌더한다. */
	keyMetrics?: ContractMetric[];
	/** 짧은 설명 — 록빌/CDMO 같은 낯선 용어를 캡션 옆에서 바로 풀어준다. */
	explainers?: ContractExplainer[];
	/** 관련 뉴스/근거 링크 — 네이버 보관 뉴스나 공식 발표 원문. */
	relatedNews?: ContractRelatedNews[];
	/** 고정 댓글(pinnedComment) — 근거·면책. 캡션 하단 작게. */
	pinnedComment?: string;
	/** 발간일(blog date, YYYY-MM-DD) — 피드 최신순 정렬·표시용. */
	date?: string;
	slides: ContractSlide[];
	/** 자동 덱 오버레이(blog frontmatter `carousel:` hero/order/notes) — 계약에 실어 /cards 가 라이브(blog 번들 비의존). */
	spec?: CarouselSpec;
}
/** 단일 파일 carousels/index.json — 전 캐러셀 계약(슬라이드까지) 배열. date 내림차순 발간 순서.
 *  피드·상세 모두 이 한 번 fetch 로(별도 인덱스 파일·카드별 round-trip 0). 회사당 N편=같은 code 다른 slug. */
export interface ContractIndex {
	posts: CarouselContract[];
}

// ── 큐레이션 오버레이(P5) — blog frontmatter `carousel:` 선택 블록. 없으면 자동 투영만. ──
export interface CarouselSpec {
	/** 슬라이드별 손글 narration — key=섹션 key 또는 슬라이드 인덱스, 숫자는 모델값 부분집합(no-new-number). */
	notes?: Record<string, string>;
	/** 표지에 띄울 hero 파일명(미지정 시 hfMedia 첫 hero). */
	hero?: string;
	/** 슬라이드 노출 순서/필터(섹션 key 목록). 미지정 시 자동 순서. */
	order?: string[];
}
