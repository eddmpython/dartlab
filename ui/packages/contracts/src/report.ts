// 사업보고서 파생 시리즈 계약 — landing reportSeries.ts 10종 승격 (census A-3, 단계-0 결정: ReportPort 분리).
// 빈값 규약: null = 해당 데이터셋 미존재/미공시. 필드 단위 null 의미는 각 주석 (예: AuditFeeYear.nonAuditFee 0=계약 없음 / null=미공시).
import type { Num } from './runtime';

export interface WorkforceYear {
	year: string;
	total: Num;
	male: Num;
	female: Num;
	regular: Num;
	contract: Num;
	avgSalary: Num; // 원/인 (급여총액/총원)
	totalSalary: Num; // 원
	tenure: Num; // 평균 근속연수
}

export interface InvestmentRow {
	name: string;
	purpose: string;
	stakePct: Num;
	bookValue: Num; // 원
	acquiredAmt: Num; // 원 (최초취득)
	targetNet: Num; // 피출자사 당기순이익 (원)
}

export interface InvestmentsView {
	year: string;
	rows: InvestmentRow[]; // 전체 출자사 (장부가 desc) — 인라인 스크롤·출자 다이얼로그 단일 소스
	moreCount: number; // 현재 0 (rows 가 전체) — 계약 호환 유지
	moreBook: number; // 현재 0 (원) — 계약 호환 유지
}

export interface InvestmentTrendYear {
	year: string;
	bookTotal: Num; // 합계행 장부가 (원)
	count: number; // 유효 개별 출자사 수
}

// 기간별 피출자사 스냅샷 — 시간축(연도/분기) 그래프·재생용. latest 와 동일 소스(보고된 (year,quarter)).
export interface InvestmentPeriod {
	year: string;
	quarter: string; // '1분기'|'2분기'|'3분기'|'4분기' (보고서종류; 4분기=사업보고서). 소비처가 year+quarter 로 라벨 포맷
	rows: InvestmentRow[]; // 그 기간 전체 피출자사 (장부가 desc)
}

export interface InvestmentsBundle {
	latest: InvestmentsView;
	trend: InvestmentTrendYear[]; // 연도 오름차순
	periods: InvestmentPeriod[]; // 보고된 (year,quarter) 오름차순 — 시간축. latest/trend 와 동일 소스
}

export interface OwnershipYear {
	year: string;
	majorPct: Num; // 최대주주측 합산 지분율 %
	minorPct: Num; // 소액주주 지분율 %
	minorCount: Num; // 소액주주 수 (명)
	stockTotal: Num; // 총발행주식수 (주)
}

// 최대주주 개별 행 — 역방향 소유("누가 이 회사를 소유하나"). 개인은 개인정보·동명이인 가드로 익명 집계(실명 미노출).
export type ShareholderKind = 'institution' | 'corp' | 'gov' | 'treasury' | 'person';
export interface ShareholderRow {
	name: string; // 기관·법인·정부·자기주식 실명 (개인은 named 에 넣지 않음 — person 집계로)
	relate: string; // canonical 관계 라벨 (원문 자유문자열 정규화). 미상 = ''
	ratio: Num; // 지분율 %
	shares: Num; // 보유 주식수
	kind: ShareholderKind;
	code: string | null; // 법인주주 상장 해소 시 종목코드 (클릭 이동) — 소비처가 lookupListed 로 채움
}
export interface PersonAggregate {
	count: number; // 특수관계인 개인 수
	ratio: Num; // 개인 지분율 합 %
	shares: Num; // 개인 보유주식 합
}
export interface ShareholdersView {
	year: string;
	quarter: string; // '1분기'|'2분기'|'3분기'|'4분기' — year 와 함께 기간키(시간축 매칭). 기존 단일 뷰는 최신기
	named: ShareholderRow[]; // 기관·법인·정부·자기주식 (실명, 지분 desc)
	person: PersonAggregate | null; // 개인 익명 집계 (1줄). 개인 없으면 null
	totalPct: Num; // 최대주주측 합산 지분율 (계행) — 정합 검증용
}

export interface ExecBoardYear {
	year: string;
	execAvgPay: Num; // 이사·감사 1인평균 보수 (원)
	execTotalPay: Num; // 보수총액 (원)
	execCount: Num;
	directors: Num;
	outsideDirectors: Num;
}

export interface DebtProfileYear {
	year: string;
	bond1y: Num; // 사채 잔존만기 1년이하 (원)
	bond1to5: Num;
	bond5to10: Num;
	bond10plus: Num;
	bondTotal: Num;
	stb: Num; // 단기사채 미상환 (원)
	cp: Num; // CP 미상환 (원)
}

export interface DebtLadder {
	year: string; // 2% 검산 통과한 최신 연도
	buckets: Num[]; // 7버킷 (원): ≤1y · 1~2y · 2~3y · 3~4y · 4~5y · 5~10y · 10y+
	shortTerm: Num; // 전단채+CP 합계 (원)
}

export interface DebtProfileBundle {
	years: DebtProfileYear[]; // 연도 오름차순
	ladder: DebtLadder | null; // 검산 통과 연도 없으면 null
}

export interface ShareholderReturnYear {
	year: string;
	dps: Num; // 주당 현금배당금 (원, 보통주)
	eps: Num; // 주당순이익 (원) — (연결) 우선
	totalDividend: Num; // 원
	payoutPct: Num;
	yieldPct: Num;
	buybackQty: Num; // 자사주 취득 (주, 보통주 총계)
	disposalQty: Num;
	buybackCancel: Num; // 소각 (주)
	treasuryEnd: Num; // 기말 보유 (주)
}

export interface CapitalChangeEvent {
	date: string; // 발행(감소)일자 공시 원문 (예: '2025.08.21')
	year: number;
	kind: 'paidIn' | 'conversion' | 'reduction';
	type: string; // 발행(감소)형태 원문
	qty: number; // 주 — 감자·소각은 음수
}

export interface DilutionYear {
	year: number;
	paidIn: Num;
	conversion: Num;
	reduction: Num; // 음수, 주
}

export interface CapitalChangesBundle {
	events: CapitalChangeEvent[]; // 일자 오름차순 — 주가차트 마커 연결용
	years: DilutionYear[]; // 연도 합산 — 희석 이력 카드용
}

export interface AuditYear {
	year: number; // 사업연도 (= 사업보고서 접수연도 − 1)
	auditor: string;
	opinion: string | null; // 적정/한정/부적정/의견거절 표준화 — 미기재 null
	special: string | null;
}

export interface TopExecPayRow {
	name: string;
	title: string;
	pay: number; // 보수총액 (원)
}

export interface TopExecPay {
	year: string;
	avgPay: Num; // 같은 연도 이사·감사 1인평균 보수 (원)
	rows: TopExecPayRow[]; // 보수 내림차순 top 8
}

export interface AuditFeeYear {
	year: number;
	auditFee: Num; // 감사용역 계약보수 (원)
	nonAuditFee: Num; // 비감사용역 보수 합 (원) — 계약 없으면 0, 미공시 null
}

// 밸류에이션 스냅샷 행 — dart/scan/valuation.parquet (네이버 per/pbr, 전 종목 1행/종목, snapshotAt 일 1회).
// 동종업종 밸류에이션 *좌표*용(자기역사 PER 과 정의·시점 분리). null = 적자·미산출(네이버가 결손사 null 처리).
export interface ValuationRow {
	per: Num; // 주가수익비율 (TTM 연결 EPS 기준, 네이버 표준)
	pbr: Num; // 주가순자산비율
	marketCap: Num; // 시가총액(원)
}
// stockCode → ValuationRow. 전 종목 1파일(소형) — 동종 분포·주체 위치를 조회 시점 계산.
export type ValuationSnapshot = Record<string, ValuationRow>;

// ── 주석 구성 시계열 — 정기보고서가 분기마다 보고한 당기 구성(비용 성격별·부문별 매출)의 변화.
// 데이터 원천 = panel contentRaw 의 정부 XBRL <TE ACODE ACONTEXT> 태그 *런타임 직독*(별도 bake 0).
// 비용 = acode(IFRS 택소노미가 곧 카테고리), 부문 = axisPath 세그먼트 멤버. 최근 분기(ACONTEXT 2025-03+)만.
// 분기는 YTD 누적이라 절대액(total)은 분기리셋 사다리꼴; 비중(shares)은 전 기간 비교가능 → 헤드라인은 100% 적층 믹스. ──
export interface CompositionPoint {
	period: string; // 'YYYYQn'
	year: string; // 'YYYY'
	quarter: string; // '1분기'..'4분기' (4분기=사업보고서=연간 누적)
	total: number; // 원 — 당기 합계
	shares: number[]; // categories[] 정렬 비중% (합 ~100, 없는 카테고리=0)
}
export interface CompositionSeries {
	categories: string[]; // 안정 카테고리(표시명) — 전 기간 합계 desc 상위 K (비용은 마지막 '기타' 롤업). 색·범례·적층 순서 SSOT
	points: CompositionPoint[]; // period 오름차순
}
// 비용 체질 + 부문별 매출. 둘 다 없으면(미공시/단일부문) 각각 null.
export interface NoteSeriesBundle {
	cost: CompositionSeries | null; // 비용 성격별(acode 카테고리)
	segment: CompositionSeries | null; // 부문별 매출(axisPath 세그먼트). 단일부문/미태깅이면 null
}

// ── 사업 서술 표 — II.사업의내용의 HTML 표(생산능력·가동률·원재료·주요제품·매출수주)를 격자전개
// (tableGrid)로 직사각 정규화한 일반 표. panel contentRaw 런타임 직독(별도 bake 0). XBRL 셀이 아닌
// 표 레이아웃이라 typed 시계열 대신 헤더+행 그대로 노출(CleanTable). 최신 사업보고서(Q4) 기준. ──
export interface BusinessTable {
	topic: string; // 'salesOrder' | 'rawMaterial' | 'productService'
	title: string; // sectionLeaf (사람이 읽는 섹션명)
	period: string; // 'YYYYQn'
	headers: string[]; // 표 헤더 행
	rows: string[][]; // 데이터 행 (헤더 제외, 격자 정렬)
}
export interface BusinessTablesBundle {
	tables: BusinessTable[]; // 토픽별 본문 표 (없으면 빈 배열로 오지 않고 bundle 자체 null)
}

export interface ReportPort {
	workforce(code: string): Promise<WorkforceYear[] | null>;
	/** 밸류에이션 스냅샷(전 종목 per/pbr/marketCap, dart/scan/valuation.parquet 통파일 직독). 동종 밸류에이션 좌표용. 미존재는 null. */
	valuationSnapshot(): Promise<ValuationSnapshot | null>;
	investments(code: string): Promise<InvestmentsBundle | null>;
	shareholderReturn(code: string): Promise<ShareholderReturnYear[] | null>;
	ownership(code: string): Promise<OwnershipYear[] | null>;
	/** 최대주주 개별 — 역방향 소유("누가 이 회사를 소유하나"). 개인 익명 집계. 미지원/미존재는 null. */
	shareholders(code: string): Promise<ShareholdersView | null>;
	/** 최대주주 기간 시계열 — shareholders() 의 전(全) (year,quarter) 버전(오름차순). shareholders() 는 이 결과의 최신. 미지원은 null. */
	shareholderPeriods(code: string): Promise<ShareholdersView[] | null>;
	execBoard(code: string): Promise<ExecBoardYear[] | null>;
	debtProfile(code: string): Promise<DebtProfileBundle | null>;
	capitalChanges(code: string): Promise<CapitalChangesBundle | null>;
	auditTrail(code: string): Promise<AuditYear[] | null>;
	topExecPay(code: string): Promise<TopExecPay | null>;
	auditFees(code: string): Promise<AuditFeeYear[] | null>;
	/** 주석 구성 시계열 — 비용 성격별(acode) + 부문별 매출(axisPath). panel contentRaw 의 정부 XBRL 태그 런타임 직독
	 * (별도 bake 0). 최근 분기(ACONTEXT 2025-03+)만. 우측 글랜스·상세 다이얼로그 공용. 둘 다 없으면 null. */
	noteSeries(code: string): Promise<NoteSeriesBundle | null>;
	/** 사업 서술 표. II.사업의내용 HTML 표(생산능력·가동률·원재료·주요제품·매출수주)를 격자전개로 정규화.
	 * panel contentRaw 런타임 직독(별도 bake 0). 최신 사업보고서(Q4) 기준. 표 없으면 null. */
	businessTables(code: string): Promise<BusinessTablesBundle | null>;
}
