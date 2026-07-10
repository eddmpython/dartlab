/**
 * EDGAR(US) 노드 런타임 로더 · 신규 베이크 0.
 *
 * `edgar/scan/finance.parquet` 은 이미 공개 HF 에 발행되어 있다(무인증 200 실측). 브라우저가
 * DuckDB-WASM 으로 그것을 직독해 US ScanNode 를 만든다. 새 parquet 을 굽지 않고, 새 배관도
 * 만들지 않는다(registerHfParquet 재사용).
 *
 * 만드는 필드는 `US_FIELDS`(marketScope.ts)와 반드시 일치한다. 여기 없는 컬럼은 US 행에서
 * "결측" 이 아니라 "이 시장엔 없는 개념" 으로 렌더된다.
 *
 * 산업 분류는 KR 34 KSIC 와 이름이 다르다(SIC sector). 그래서 `industry` 를 `SIC:{sector}` 로
 * 네임스페이스 격리한다. KR 산업칩과 섞이지 않고, KR 분포에도 끼지 않는다.
 */

import type { DartDb } from './duckSql';
import type { ScanNode } from './types';

const EDGAR_FINANCE_PATH = 'edgar/scan/finance.parquet';

interface EdgarRow {
	stockCode: string;
	corpName: string | null;
	sector: string | null;
	sic: number | null;
	cik: string | null;
	fy: number;
	sales: number | null;
	operating_profit: number | null;
	net_profit: number | null;
	total_assets: number | null;
	total_stockholders_equity: number | null;
	total_liabilities: number | null;
}

/** edgarScan 의 등급 분기와 동일 (scan/builders/edgar/scan.py). 같은 뜻이어야 같은 칩이다. */
function profGrade(opMargin: number | null, roe: number | null): string | null {
	const best = Math.max(opMargin ?? -Infinity, roe ?? -Infinity);
	if (!Number.isFinite(best)) return null;
	if (best >= 20) return '우수';
	if (best >= 10) return '양호';
	if (best >= 5) return '보통';
	if (best >= 0) return '저수익';
	return '적자';
}

/**
 * 분모가 양수일 때만 비율이 정의된다.
 *
 * 자본잠식(equity <= 0) 기업의 ROE 는 "큰 값" 이 아니라 **뜻이 없는 값**이다. 적자 x 음의
 * 자본이 양의 ROE 로 뒤집혀 나온다. 실측: EDGAR 8,035 사 중 2,316 사(28.8%)가 equity <= 0 이고,
 * 그대로 두면 ROE 정렬 상단이 전부 이 부호뒤집힘으로 채워진다. 그것은 랭킹이 아니라 거짓말이다.
 * 그래서 null(UNKNOWN)로 둔다. missing > wrong.
 */
const pct = (numer: number | null, denom: number | null): number | null =>
	numer !== null && denom !== null && denom > 0 ? (numer / denom) * 100 : null;

/**
 * 최신 회계연도(fy) 1 행/티커로 US 노드를 만든다.
 *
 * 절대금액은 USD 원값 그대로 둔다. 억원으로 환산하지 않는다(환율 가정을 심으면
 * 조용한 오답이 된다). 표기와 정렬은 marketScope 의 규칙이 막는다.
 */
export async function loadEdgarNodes(db: DartDb): Promise<ScanNode[]> {
	await db.registerHfParquet('edgarScanFin', EDGAR_FINANCE_PATH);
	// 티커가 있는 회사만. 빌더는 티커를 못 찾으면 stockCode 에 CIK 를 넣는데(builder.py:194),
	// 실측 8,035 행 중 2,868 행(35.7%)이 그 케이스다. 대부분 펀드·신탁·비상장 filer 라
	// 종목 스크리너의 대상이 아니고, id 가 CIK 면 종목 드릴다운도 성립하지 않는다.
	// US 검색 인덱스(buildSearchIndexUs)가 "openable 티커만" 담는 것과 같은 기준이다.
	const rows = await db.query<EdgarRow>(`
		SELECT stockCode, corpName, sector, sic, cik, fy,
		       sales, operating_profit, net_profit,
		       total_assets, total_stockholders_equity, total_liabilities
		FROM (
			SELECT *, ROW_NUMBER() OVER (PARTITION BY stockCode ORDER BY fy DESC) AS rn
			FROM edgarScanFin
			WHERE stockCode IS NOT NULL AND regexp_matches(stockCode, '^[A-Za-z]')
		)
		WHERE rn = 1
	`);

	return rows.map((r) => {
		const opMargin = pct(r.operating_profit, r.sales);
		const netMargin = pct(r.net_profit, r.sales);
		const roe = pct(r.net_profit, r.total_stockholders_equity);
		const roa = pct(r.net_profit, r.total_assets);
		const debtRatio = pct(r.total_liabilities, r.total_stockholders_equity);
		const sector = r.sector ?? 'unclassified';
		return {
			// id = ticker(영문). KR 6 자리 숫자와 충돌하지 않는다. CIK 는 6 자리라 id 로 쓰지 않는다.
			id: String(r.stockCode).toUpperCase(),
			label: r.corpName ?? String(r.stockCode).toUpperCase(),
			market: 'US',
			submarket: 'US',
			currency: 'USD',
			// KSIC 와 섞이지 않도록 네임스페이스 격리.
			industry: `SIC:${sector}`,
			industryName: sector,
			industryScheme: 'SIC',
			sic: r.sic,
			cik: r.cik,
			fy: r.fy,
			roe,
			roa,
			opMargin,
			netMargin,
			debtRatio,
			profGrade: profGrade(opMargin, roe),
			revenue: r.sales,
			operatingProfit: r.operating_profit,
			netProfit: r.net_profit,
			totalAssets: r.total_assets,
			totalEquity: r.total_stockholders_equity
		} as unknown as ScanNode;
	});
}
