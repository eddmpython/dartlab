// 캔들 표시용 순수 변환 · 수정주가 체이닝·주기 집계·하이킨아시. 로드·캐시는 runtime 어댑터
// (priceSource) 소관이라 여기엔 fetch 가 없다. 입력 불변·결정론 · 차트 크롬이 자유롭게 재적용.
import type { Candle } from '@dartlab/ui-contracts';

// 입력 배열 identity 기준 메모 · reapply·백테스트·이벤트 effect 가 같은 배열로 반복 호출 (백필 merge 시 새 배열 = 자동 무효화)
const adjCache = new WeakMap<Candle[], Candle[]>();

/** HTS 수정주가 · 등락률(기준가 대비) 체이닝으로 액면분할·병합·감자·권리락 단차 제거.
 *
 * KRX 기준가는 자본 액션 시 조정되므로 `종가/전일종가` 와 `1+등락률` 의 괴리 = 액션 배율.
 * 마지막 봉 기준으로 과거를 누적 보정 (가격 ×factor, 거래량 ÷factor). 괴리 ±3% 미만은
 * 반올림 노이즈로 간주해 무시. 등락률 누락 봉은 보정 불가 → 해당 일 괴리 통과(드묾). */
export function adjustCandles(daily: Candle[]): Candle[] {
	const n = daily.length;
	if (n < 2) return daily;
	const hit = adjCache.get(daily);
	if (hit) return hit;
	let factor = 1;
	let touched = false;
	const out: Candle[] = new Array(n);
	out[n - 1] = daily[n - 1];
	for (let i = n - 1; i > 0; i--) {
		const k = daily[i];
		const prev = daily[i - 1];
		const r = k.r;
		if (r != null && prev.c > 0) {
			const implied = k.c / (1 + r / 100); // 보정 반영된 전일 기준가
			const ratio = implied / prev.c;
			if (ratio > 0 && (ratio < 0.97 || ratio > 1.03)) {
				factor *= ratio;
				touched = true;
			}
		}
		out[i - 1] = factor === 1 ? prev : { ...prev, o: prev.o * factor, h: prev.h * factor, l: prev.l * factor, c: prev.c * factor, v: prev.v / factor };
	}
	const res = touched ? out : daily;
	adjCache.set(daily, res);
	return res;
}

// 월요일 시작 주 키 · YYYYMMDD → 해당 주 월요일 YYYYMMDD (UTC 산술, 시간대 무관)
function weekKey(t: string): string {
	const d = new Date(Date.UTC(+t.slice(0, 4), +t.slice(4, 6) - 1, +t.slice(6, 8)));
	d.setUTCDate(d.getUTCDate() - ((d.getUTCDay() + 6) % 7));
	return `${d.getUTCFullYear()}${String(d.getUTCMonth() + 1).padStart(2, '0')}${String(d.getUTCDate()).padStart(2, '0')}`;
}

/** 일봉 → 주봉('W')·월봉('M')·분기봉('Q')·년봉('Y') 집계. 라벨 t = 버킷 마지막 거래일(HTS 관행), 마지막 버킷 = 진행중 부분봉. */
export function aggregateCandles(daily: Candle[], tf: 'W' | 'M' | 'Q' | 'Y'): Candle[] {
	const out: Candle[] = [];
	let key = '';
	let cur: Candle | null = null;
	for (const k of daily) {
		const kk =
			tf === 'Y' ? k.t.slice(0, 4)
			: tf === 'Q' ? `${k.t.slice(0, 4)}Q${Math.floor((+k.t.slice(4, 6) - 1) / 3)}`
			: tf === 'M' ? k.t.slice(0, 6)
			: weekKey(k.t);
		if (kk !== key) {
			if (cur) out.push(cur);
			key = kk;
			cur = { ...k };
		} else if (cur) {
			cur.t = k.t;
			cur.h = Math.max(cur.h, k.h);
			cur.l = Math.min(cur.l, k.l);
			cur.c = k.c;
			cur.v += k.v;
			if (k.tv != null) cur.tv = (cur.tv ?? 0) + k.tv;
		}
	}
	if (cur) out.push(cur);
	return out;
}

/** 하이킨아시 변환 · haC=(o+h+l+c)/4, haO=(전봉haO+전봉haC)/2 (첫 봉 = (o+c)/2),
 * haH=max(h,haO,haC), haL=min(l,haO,haC). 순수함수: 입력 불변, prefix 안정(앞부분 슬라이스 결과 동일).
 * 표시 전용 변형값 · 시계열 버스(publishView)·백테스트는 원본 가격을 유지한다. */
export function heikinAshi(candles: Candle[]): Candle[] {
	if (!candles.length) return candles;
	const out: Candle[] = new Array(candles.length);
	let prevO = 0;
	let prevC = 0;
	for (let i = 0; i < candles.length; i++) {
		const k = candles[i];
		const haC = (k.o + k.h + k.l + k.c) / 4;
		const haO = i === 0 ? (k.o + k.c) / 2 : (prevO + prevC) / 2;
		out[i] = { ...k, o: haO, c: haC, h: Math.max(k.h, haO, haC), l: Math.min(k.l, haO, haC) };
		prevO = haO;
		prevC = haC;
	}
	return out;
}
