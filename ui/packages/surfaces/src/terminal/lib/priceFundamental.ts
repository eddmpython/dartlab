// 가격↔기초체력 지수 오버레이 · 주가·매출·자본을 같은 시작점(=100)으로 리베이스해 한 차트에 겹친다.
// 신규 데이터 0: 이미 로드된 finance 번들(기간 라벨·접수일) + price 캔들을 조인할 뿐이다.
// ★look-ahead 차단(honesty spine): 각 기간의 주가는 그 기간 *공시 접수일* 종가로 샘플 ·
// 사업연도 종료 시점이 아니라 그 숫자가 실제로 공표된 날 (미리보기 가격 금지).
import type { Candle, FinCard, Num, OwnershipYear, ShareholderReturnYear, TerminalFinance } from '@dartlab/ui-contracts';

const finite = (v: Num): v is number => typeof v === 'number' && Number.isFinite(v);

// 기간 라벨 → (연도, 분기). 'FY23'→{2023,4} · '23Q4'→{2023,4} · '23Q1'→{2023,1}
function parsePeriod(label: string): { year: number; q: number } | null {
	let m = label.match(/^FY(\d{2})$/);
	if (m) return { year: 2000 + +m[1]!, q: 4 };
	m = label.match(/^(\d{2})Q(\d)$/);
	if (m) return { year: 2000 + +m[1]!, q: +m[2]! };
	return null;
}
const Q_END = ['', '0331', '0630', '0930', '1231']; // 접수일 결측 시 분기말 폴백

// 오름차순 캔들에서 t ≤ dateYmd 인 마지막 종가 (공시 시점 가격 · 그 이후 가격은 미리보기라 금지)
function priceAtOrBefore(candles: Candle[], dateYmd: string): number | null {
	for (let i = candles.length - 1; i >= 0; i--) {
		const cd = candles[i];
		if (cd && cd.t <= dateYmd) return cd.c;
	}
	return null;
}

/**
 * 가격↔기초체력 오버레이 카드를 만든다. 주가·매출·자본 모두 첫 공통 유효 기간을 100 으로 정규화.
 *
 * @param view - 현재 모드(연간/분기/TTM)의 재무 뷰 · periods 라벨·statements 값 제공.
 * @param filedDates - `${year}-${q}` → 접수일(YYYYMMDD). 번들에서 직접.
 * @param candles - gov EOD 캔들(오름차순). null/단일점이면 카드 없음(honest-gap).
 * @returns 3선(=100) FinCard 또는 데이터 부족 시 null (→ 카드 비표시).
 *
 * @example
 *   const card = buildPriceFundamentalCard(finData, bundle.filedDates, candles);
 *   if (card) renderMini(card, finData.periods);
 */
export function buildPriceFundamentalCard(
	view: TerminalFinance,
	filedDates: Record<string, string>,
	candles: Candle[] | null
): FinCard | null {
	if (!candles || candles.length < 2) return null;
	const revRow = view.statements.IS.find((r) => r.key === 'revenue');
	const eqRow = view.statements.BS.find((r) => r.key === 'equity');
	if (!revRow || !eqRow) return null;

	// 각 기간의 공시 접수일(없으면 분기말) 종가
	const priceRaw: Num[] = view.periods.map((label) => {
		const pp = parsePeriod(label);
		if (!pp) return null;
		const filed = filedDates[`${pp.year}-${pp.q}`];
		const date = filed && filed.length === 8 ? filed : `${pp.year}${Q_END[pp.q]}`;
		return priceAtOrBefore(candles, date);
	});
	const rev = revRow.values;
	const eq = eqRow.values;

	// 기준(=100) = 주가·매출·자본 모두 유효한 첫 기간
	let base = -1;
	for (let i = 0; i < view.periods.length; i++) {
		if (finite(priceRaw[i]) && finite(rev[i]) && finite(eq[i])) { base = i; break; }
	}
	if (base < 0) return null;
	const idx = (arr: Num[]): Num[] => {
		const b = arr[base];
		if (!finite(b) || b === 0) return arr.map(() => null);
		return arr.map((v) => (finite(v) ? +((v / b) * 100).toFixed(1) : null));
	};
	const priceIdx = idx(priceRaw);
	if (priceIdx.filter(finite).length < 2) return null; // 단일 가격점 = 추세 무의미

	return {
		key: 'priceVsFundamentals',
		title: '가격 vs 기초체력 (=100)',
		unit: '=100',
		refLines: [100],
		// 세 선 모두 단일 좌축(이중축 금지 · 독립 오토스케일은 괴리 신호를 숨긴다). 로그 눈금으로
		// 자릿수 차(주가 급등 등)를 흡수: 같은 기울기 = 같은 성장률이라 한 선이 치솟아도 비교 가능.
		logLeft: true,
		series: [
			{ name: '주가', data: priceIdx, color: '#e879a6', type: 'line' },
			{ name: '매출', data: idx(rev), color: '#5b9bf0', type: 'line' },
			{ name: '자본', data: idx(eq), color: '#34d399', type: 'line' }
		]
	};
}

/**
 * PER·PBR 추이(밸류에이션 배수 시계열) 카드를 만든다. 연도별 사업보고서 접수일 종가 ÷ 그 해 EPS·BPS.
 * 오버레이가 못 답하는 *밸류에이션 수준*("자기 이력 대비 싸냐/비싸냐")을 본다. 신규 데이터 0 ·
 * 주가 캔들 + EPS(shareholderReturn) + 발행주식수(ownership) + 자본(연간 statements) 조인.
 *
 * @param annualView - 연간 재무 뷰 · 자본(BS.equity, 조) 시계열 제공. null 이면 PBR 생략(PER 만).
 * @param filedDates - `${year}-${q}` → 접수일(YYYYMMDD). FY 는 `${year}-4`.
 * @param candles - gov/krx EOD 캔들(오름차순). 결측 연도 = 가격 null(공백).
 * @param sr - 연간 주주환원(EPS) · 없으면 카드 없음(honest-gap).
 * @param own - 연간 소유구조(stockTotal=총발행주식수) · 없으면 PBR 공백.
 * @returns { card, periods } 또는 데이터 부족 시 null. PER 좌축·PBR 우축, 둘 다 '배'.
 *
 * @example
 *   const vc = buildPerPbrCard(bundle.views.annual, bundle.filedDates, candles, sr, own);
 *   if (vc) renderMini(vc.card, vc.periods);
 */
export function buildPerPbrCard(
	annualView: TerminalFinance | null,
	filedDates: Record<string, string>,
	candles: Candle[] | null,
	sr: ShareholderReturnYear[] | null,
	own: OwnershipYear[] | null
): { card: FinCard; periods: string[] } | null {
	if (!candles || candles.length < 2 || !sr || !sr.length) return null;

	// 자본(연간) 연도 → 조 값. annual statements 의 FY 라벨을 4자리 연도로 환원.
	const eqByYear = new Map<string, number>();
	const eqRow = annualView?.statements.BS.find((r) => r.key === 'equity');
	if (eqRow && annualView) {
		annualView.periods.forEach((p, i) => {
			const m = p.match(/^FY(\d{2})$/);
			const v = eqRow.values[i];
			if (m && finite(v)) eqByYear.set('20' + m[1]!, v); // 조
		});
	}
	const sharesByYear = new Map<string, number>();
	for (const o of own ?? []) if (finite(o.stockTotal)) sharesByYear.set(o.year, o.stockTotal);

	// 각 연도 사업보고서 접수일(없으면 연말) 종가 · look-ahead 차단(EPS 공표 시점 가격)
	const priceOf = (year: string): number | null => {
		const filed = filedDates[`${year}-4`];
		const date = filed && filed.length === 8 ? filed : `${year}1231`;
		return priceAtOrBefore(candles, date);
	};

	const years = sr.map((s) => s.year).filter((y) => /^\d{4}$/.test(y)).sort();
	const srByYear = new Map(sr.map((s) => [s.year, s]));
	const per: Num[] = [];
	const pbr: Num[] = [];
	for (const y of years) {
		const px = priceOf(y);
		const eps = srByYear.get(y)?.eps ?? null;
		per.push(finite(px) && finite(eps) && eps > 0 ? +(px / eps).toFixed(1) : null); // 적자(EPS≤0)=공백
		const eq = eqByYear.get(y) ?? null; // 조
		const sh = sharesByYear.get(y) ?? null; // 주
		const bps = finite(eq) && eq > 0 && finite(sh) && sh > 0 ? (eq * 1e12) / sh : null;
		pbr.push(finite(px) && bps != null ? +(px / bps).toFixed(2) : null); // 자본잠식·주식수 결측=공백
	}
	if (per.filter(finite).length < 2 && pbr.filter(finite).length < 2) return null;

	return {
		card: {
			key: 'perPbrTrend',
			title: 'PER·PBR 추이',
			unit: '배',
			series: [
				{ name: 'PER', data: per, color: '#e879a6', type: 'line' },
				{ name: 'PBR', data: pbr, color: '#22d3ee', type: 'line', axis: 'r' } // 우축 · 배수 자릿수 달라 비교 무의미, 각 추세만
			]
		},
		periods: years.map((y) => 'FY' + y.slice(2))
	};
}
