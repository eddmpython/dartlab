// 라이브 데이터 API 노출 화이트리스트 — SSOT = src/dartlab/core/dataConfig.py::downloadCatalog().
//
// 보안 경계: public:True · flat(nested 아님) · 표형 dir 만. private 6종(allFilings·edgar/scan·
// stemIndex·edinet·ai/knowledge·original·news/private)은 공개 dartlab-data 와 same-repo 라 토큰
// 차단이 안 먹는다 → 이 코드 allowlist 가 유일 방어(03-tier2-live-worker). 미포함 dir = 자동 404.
//
// 본 목록은 downloadCatalog.ts(브라우저 미러)와 글자 동일. dir↔shardKind drift 는
// tests/core/test_download_catalog.py::test_worker_allowlist_in_sync 가 강제(CI fail) — 새 public
// 카테고리는 Python 이 자동 도출, 이 미러는 여기 한 줄 추가해야 가드 통과.
export const RELEASES = [
	{ dir: 'dart/finance', label: 'DART 재무 숫자', shardKind: 'company' },
	{ dir: 'dart/ipo', label: '신규상장 IPO 공모분석 리포트 (증권신고서 6카테고리 파싱본)', shardKind: 'bulk' },
	{ dir: 'dart/panel', label: 'DART 공시 수평화 (회사당, 17-col)', shardKind: 'company' },
	{ dir: 'dart/report', label: 'DART 정기보고서', shardKind: 'company' },
	{ dir: 'dart/scan', label: 'DART 전종목 횡단분석 프리빌드', shardKind: 'bulk' },
	{ dir: 'edgar/finance', label: 'SEC EDGAR 재무 (companyfacts 파생)', shardKind: 'bulk' },
	{ dir: 'edgar/financeStmt', label: 'SEC EDGAR 재무 (표준화, 회사당)', shardKind: 'company' },
	{ dir: 'edgar/meta', label: 'SEC EDGAR 분기 벌크 메타 (sub/pre/tag)', shardKind: 'bulk' },
	{ dir: 'edgar/panel', label: 'SEC EDGAR 공시 수평화 (회사당, 16-col)', shardKind: 'company' },
	{ dir: 'edgar/prices/company', label: 'SEC 회사별 일별 OHLCV', shardKind: 'company' },
	{ dir: 'edgar/tickers', label: 'SEC ticker↔CIK 맵', shardKind: 'bulk' },
	{ dir: 'expectations', label: '기대치 격자 원장 (발행 봉인 + 사후 채점, append-only, 시뮬레이터 검증척추)', shardKind: 'series' },
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
	{ dir: 'research/brokerage', label: '증권사 리서치 메타 인덱스 (월별)', shardKind: 'series' }
];

// dir → 엔트리 O(1) 조회 (allowlist 게이트).
export const ALLOW = new Map(RELEASES.map((e) => [e.dir, e]));

// Tier2(라이브 변환) 적격 — 회사당/series flat 만. dateShard·bulk(날짜샤드·전종목 대형)는 413 → Tier1.
export function isTier2(shardKind) {
	return shardKind === 'company' || shardKind === 'series';
}
