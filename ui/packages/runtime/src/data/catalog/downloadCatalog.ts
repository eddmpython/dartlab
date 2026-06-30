// 다운로드 센터 노출 카탈로그 · SSOT = Python `src/dartlab/core/dataConfig.py::downloadCatalog()`.
// TS 는 Python import 불가라 손수 미러(brand.ts·hf.ts 동일 패턴). dir↔shardKind drift 는
// `tests/core/test_download_catalog.py` 가 강제(불일치 시 CI fail) · 새 public 카테고리 추가 시
// Python 은 자동 도출, 본 미러는 여기 한 줄 추가해야 가드 통과.
//
// 보안: 본 목록은 DATA_RELEASES `public:True` · flat(nested 아님) · 표형 dir 만. private(allFilings·
// edgar/scan·stemIndex·edinet·ai/knowledge·original·news/private)는 애초에 도출에서 빠진다.

export type ShardKind = 'company' | 'series' | 'dateShard' | 'bulk';

export interface CatalogEntry {
	/** HF parquet dir · URL `/v1/{dir}/{id}.{ext}` 의 {dir}. */
	dir: string;
	/** 다운로드 센터 표시 라벨. */
	label: string;
	/** {id} 의미 · 'company'(종목코드/ticker)·'series'(시리즈/지수/월)·'dateShard'(날짜, 대형)·'bulk'(단일/대형). */
	shardKind: ShardKind;
}

/** Tier2(라이브 워커) 적격 · 회사당/series flat 만. dateShard·bulk 는 대형이라 Tier1 다운로드 전용. */
export function isTier2Eligible(entry: CatalogEntry): boolean {
	return entry.shardKind === 'company' || entry.shardKind === 'series';
}

export const DOWNLOAD_CATALOG: CatalogEntry[] = [
	{ dir: 'dart/finance', label: 'DART 재무 숫자', shardKind: 'company' },
	{ dir: 'dart/panel', label: 'DART 공시 수평화 (회사당, 17-col)', shardKind: 'company' },
	{ dir: 'dart/report', label: 'DART 정기보고서', shardKind: 'company' },
	{ dir: 'dart/scan', label: 'DART 전종목 횡단분석 프리빌드', shardKind: 'bulk' },
	{ dir: 'edgar/finance', label: 'SEC EDGAR 재무 (companyfacts 파생)', shardKind: 'bulk' },
	{ dir: 'edgar/financeStmt', label: 'SEC EDGAR 재무 (표준화, 회사당)', shardKind: 'company' },
	{ dir: 'edgar/meta', label: 'SEC EDGAR 분기 벌크 메타 (sub/pre/tag)', shardKind: 'bulk' },
	{ dir: 'edgar/panel', label: 'SEC EDGAR 공시 수평화 (회사당, 16-col)', shardKind: 'company' },
	{ dir: 'edgar/prices/company', label: 'SEC 회사별 일별 OHLCV', shardKind: 'company' },
	{ dir: 'edgar/tickers', label: 'SEC ticker↔CIK 맵', shardKind: 'bulk' },
	{ dir: 'gov/indices/date', label: '공공데이터 시장지수 일별 (날짜 샤딩, 대형)', shardKind: 'dateShard' },
	{ dir: 'gov/indices/index', label: '공공데이터 지수별 일별 시계열', shardKind: 'series' },
	{ dir: 'gov/prices/company', label: '공공데이터 회사별 일별 OHLCV+시총', shardKind: 'company' },
	{ dir: 'gov/prices/date', label: '공공데이터 일별 전종목 OHLCV (날짜 샤딩, 대형)', shardKind: 'dateShard' },
	{ dir: 'krx/indices', label: 'KRX 시장지수 일별 (long)', shardKind: 'bulk' },
	{ dir: 'krx/prices', label: 'KRX 일별 전종목 OHLCV (long, 대형)', shardKind: 'bulk' },
	{ dir: 'krx/prices/company', label: 'KRX 회사별 일별 OHLCV+시총', shardKind: 'company' },
	{ dir: 'macro/customs', label: '관세청 무역통계 월별 수출입', shardKind: 'series' },
	{ dir: 'macro/ecos', label: 'ECOS 한국은행 거시경제 시계열', shardKind: 'series' },
	{ dir: 'macro/fred', label: 'FRED 거시경제 시계열', shardKind: 'series' },
	{ dir: 'research/brokerage', label: '증권사 리서치 메타 인덱스 (월별)', shardKind: 'series' },
];
