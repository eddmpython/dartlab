// 가격 시계열 CSV 직렬화 (terminal-data-download PRD). 가격 차트가 *실제로 그리는 봉*
// (klinecharts v9 `chart.getDataList()`) 을 넘겨받아 데이터-only 행으로 정형한다.
// PriceChart 는 이 순수 헬퍼를 render 진실 봉으로 호출한다(candles prop 아님 = 백필 무성절단 방지).
//
// 함정 박제(01-architecture-traps-format):
//  - 봉 timestamp 는 ms-epoch (`toMs = Date.UTC(...)` 로 만들어짐). UTC 게터로 되돌려야 TZ off-by-one 0.
//  - turnover 는 봉이 이미 1e8 사전스케일(억 축)을 들고 있어 컬럼에서 생략(단위 거짓 방지, 함정 5).
//  - 결손 volume 은 빈셀(csvExport 가 null/undefined -> '')로 두고 0 을 쓰지 않는다. 진짜 0(거래정지)은 보존.
//  - 파일명 마지막 날짜는 봉(render 진실)에서 도출한다(prop 마지막 날짜 재사용 금지, 함정 2).

/** klinecharts v9 KLineData 부분집합 (직렬화에 필요한 필드만). */
export interface PriceBar {
	timestamp: number;
	open: number;
	high: number;
	low: number;
	close: number;
	volume?: number | null;
}

/** 데이터-only CSV 한 행. `t`=YYYYMMDD, OHLC, `v`=거래량(주, 결손 시 null=빈셀). */
export interface PriceCsvRow {
	t: string;
	o: number;
	h: number;
	l: number;
	c: number;
	v: number | null;
}

/** CSV 컬럼 순서 SSOT. turnover 는 함정 5 로 미포함. */
export const PRICE_CSV_COLUMNS: ReadonlyArray<keyof PriceCsvRow> = ['t', 'o', 'h', 'l', 'c', 'v'];

/** ms-epoch(Date.UTC 기반) -> YYYYMMDD. UTC 게터라 로컬 TZ 무관(하루 밀림 없음). */
export function barYmd(ms: number): string {
	const d = new Date(ms);
	const y = d.getUTCFullYear();
	const m = String(d.getUTCMonth() + 1).padStart(2, '0');
	const day = String(d.getUTCDate()).padStart(2, '0');
	return `${y}${m}${day}`;
}

/** getDataList() 봉 배열 -> CSV 행. 결손 volume 은 null(빈셀), 진짜 0 은 보존. */
export function priceBarsToRows(bars: PriceBar[]): PriceCsvRow[] {
	return bars.map((b) => ({
		t: barYmd(b.timestamp),
		o: b.open,
		h: b.high,
		l: b.low,
		c: b.close,
		v: b.volume ?? null
	}));
}

/** 파일명 = dartlab_{code}_{마지막봉 날짜}_{tf}[_adj].csv. 날짜는 봉(render 진실) 마지막에서 도출. */
export function priceCsvFilename(code: string, rows: PriceCsvRow[], tf: string, adj: boolean): string {
	const lastYmd = rows.length ? rows[rows.length - 1].t : '';
	return `dartlab_${code}_${lastYmd}_${tf}${adj ? '_adj' : ''}.csv`;
}
