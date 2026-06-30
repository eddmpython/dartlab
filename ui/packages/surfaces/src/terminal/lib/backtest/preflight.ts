// 백테스트 대기 프리플라이트 · 전략 0개일 때 "이 종목·이 창의 진실"을 실행 전 정직하게 계산.
// 전부 candles + 비용프리셋만으로 (엔진 호출·look-ahead 0 = 전부 실현치). 중앙 하단 BacktestPreflight 가 렌더.
// 핵심: 이겨야 할 선(B&H) + 백테스트 가능성(거래가능 봉·분할/정지) + 비용 + 변동성 · 토론 만장일치 컴포지션.
import { mdd } from './engine';
import type { BtCostsBp, Candle } from './types';

export interface BtPreflight {
	bars: number; // 창 내 봉 수
	tradeableBars: number; // v>0 && o>0 (엔진 체결 조건과 동일) · 실제 거래 가능 봉
	fromT: string; // 창 시작일 YYYYMMDD
	toT: string; // 창 끝일
	bhRetPct: number; // 보유(B&H) 실현 수익 · 전략이 이겨야 할 선
	bhMddPct: number; // 보유 최대낙폭 (감수해야 할 고통)
	annVolPct: number | null; // 연환산 일수익 변동성 (낙폭 규모 기대)
	bhSharpe: number | null; // 보유(B&H) 실현 Sharpe (rf=0) · 위험조정 "이겨야 할 선" (표본<60 null)
	pos52wPct: number | null; // 52주 종가 범위 내 현재 위치 [0..100]
	haltBars: number; // 거래정지(v<=0 || o<=0) 봉 · 체결 이연 = 결과 왜곡 잠재
	splitSuspect: string | null; // 분할의심일 (무수정주가 → B&H 왜곡 경고)
	roundTripPct: number; // 1회 왕복 비용 % (수수료×2 + 거래세 + 슬리피지×2)
	windowShort: boolean; // < 60봉 · Sharpe/CAGR 거짓말 하한 미만(엔진과 동일 기준)
}

/**
 * 대기 상태 프리플라이트 계산 · candles 끝에서 windowBars 만큼 잘라 실현 B&H·데이터품질·비용·변동성 산출.
 * 엔진 호출 없음(B&H 는 단순 보유라 종가만으로 충분). 봉<2 또는 유효종가<2면 null.
 */
export function backtestPreflight(candles: Candle[], windowBars: number, costsBp: BtCostsBp): BtPreflight | null {
	const n = candles.length;
	if (n < 2) return null;
	const win = Math.max(2, Math.min(windowBars, n));
	const w = candles.slice(n - win);
	const closes = w.map((c) => c.c).filter((c) => c > 0);
	if (closes.length < 2) return null;

	const bhRetPct = (closes[closes.length - 1] / closes[0] - 1) * 100;
	const bhMddPct = mdd(closes); // 종가 시계열에 그대로 (peak-relative, base-independent)

	// 연환산 변동성 · 일수익률 표준편차 × √252 (엔진 riskRatios 와 동일 연환산)
	const rets: number[] = [];
	for (let i = 1; i < closes.length; i++) if (closes[i - 1] > 0) rets.push(closes[i] / closes[i - 1] - 1);
	let annVolPct: number | null = null;
	let bhSharpe: number | null = null;
	if (rets.length >= 20) {
		const mean = rets.reduce((a, r) => a + r, 0) / rets.length;
		const sd = Math.sqrt(rets.reduce((a, r) => a + (r - mean) * (r - mean), 0) / rets.length);
		annVolPct = sd * Math.sqrt(252) * 100;
		// 보유 실현 Sharpe · 표본<60 이면 null(엔진 riskRatios 하한과 동일, 소표본 거짓말 차단).
		if (rets.length >= 60 && sd > 0) bhSharpe = (mean / sd) * Math.sqrt(252);
	}

	// 52주 위치 · 최근 252봉(또는 창) 종가 범위 내 현재 위치
	const recent = w.slice(-252).map((c) => c.c).filter((c) => c > 0);
	let pos52wPct: number | null = null;
	if (recent.length >= 2) {
		const lo = Math.min(...recent);
		const hi = Math.max(...recent);
		const last = recent[recent.length - 1];
		pos52wPct = hi > lo ? ((last - lo) / (hi - lo)) * 100 : 50;
	}

	const tradeableBars = w.filter((c) => c.v > 0 && c.o > 0).length;
	const haltBars = win - tradeableBars;

	// 분할의심 · 전봉 종가 / 당봉 시가 비가 정수배(±2%) & ≥1.5배 (engine.findSplitSuspect 동일 로직)
	let splitSuspect: string | null = null;
	for (let i = 1; i < w.length; i++) {
		const prev = w[i - 1].c;
		const o = w[i].o;
		if (!(prev > 0) || !(o > 0)) continue;
		const r = prev / o;
		const rr = r >= 1 ? r : 1 / r;
		const near = Math.round(rr);
		if (rr >= 1.5 && near >= 2 && Math.abs(rr - near) / near < 0.02) {
			splitSuspect = w[i].t;
			break;
		}
	}

	// 왕복 비용 % · bp/100 = % (수수료 양측 + 매도세 + 슬리피지 양측). 기본 (1.5×2+15+10×2)/100 = 0.38%.
	const roundTripPct = (costsBp.commissionBp * 2 + costsBp.sellTaxBp + costsBp.slippageBp * 2) / 100;

	return {
		bars: win,
		tradeableBars,
		fromT: w[0].t,
		toT: w[w.length - 1].t,
		bhRetPct,
		bhMddPct,
		annVolPct,
		bhSharpe,
		pos52wPct,
		haltBars,
		splitSuspect,
		roundTripPct,
		windowShort: win < 60
	};
}
