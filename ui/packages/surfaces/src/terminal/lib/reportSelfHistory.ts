// 정기보고서 자기이력(self-vs-self) 순수 계산 · 우측 레일 도시에 섹션의 환원불가능한 자기정규화 문장 1줄.
// 인력·주주환원 패널이 이미 1회 fetch 한 다년 배열(wf[]·srs[])에서 *시간축*을 뽑는다 · 새 fetch 0.
// 스냅샷 격자는 최신 1년만 보여줘 "지금"만 안다; 자기이력은 그 회사의 filing-period 궤적을 한 줄로(YYYY→YYYY).
//
// ⛔ 경계: 동종비교·백분위·"마지막 본 이후 변화"(watchlist)·점수/등급/매수-매도 톤 금지. 백분위 축은 Phase 2 baked
//   (cross-universe-percentile 머신), watchlist 델타는 terminal-improvement 소유. 여기는 오직 self-vs-self 사실.
// ⛔ 톤: 판정·형용사 0, 명시 기간 라벨 필수(control-shift 동형). prior non-null 일 때만 토큰(첫해 단독 = null).
import type { ShareholderReturnYear, WorkforceYear } from '@dartlab/ui-contracts';
import type { Num } from './types';

// ── 인력 자기이력 ── 총원 궤적 + 계약직 비중 이동. (백분위/1인당부가가치 = Phase 2 baked, 여기 미포함)
export interface WorkforceTrend {
	fromYear: string;
	toYear: string;
	headFrom: number;
	headTo: number;
	headPct: Num; // % · 총원 증감률 (earliest→latest, headFrom>0 일 때만)
	contractFromPct: Num; // % · 계약직 비중 (earliest)
	contractToPct: Num; // % · 계약직 비중 (latest)
}
export function workforceTrend(wf: WorkforceYear[] | null | undefined): WorkforceTrend | null {
	if (!wf || wf.length < 2) return null; // 단일 기간 = 궤적 미정의 (96.1% 종목 ≥2년, probe 실측)
	const withTotal = wf.filter((w) => w.total != null);
	if (withTotal.length < 2) return null;
	const first = withTotal[0];
	const last = withTotal[withTotal.length - 1];
	if (first.year === last.year) return null;
	const headFrom = first.total as number;
	const headTo = last.total as number;
	const contractRatio = (w: WorkforceYear): Num =>
		w.regular != null && w.contract != null && w.regular + w.contract > 0 ? (w.contract / (w.regular + w.contract)) * 100 : null;
	return {
		fromYear: first.year,
		toYear: last.year,
		headFrom,
		headTo,
		headPct: headFrom > 0 ? ((headTo - headFrom) / headFrom) * 100 : null,
		contractFromPct: contractRatio(first),
		contractToPct: contractRatio(last)
	};
}

// ── 주주환원 자기이력 ── 최근 연속 배당 연수 + 배당성향 이동 + 소각(appears-when-clean).
// "N년 연속 배당"은 가용 window 내 trailing run (window 넘는 연속 주장 금지 · F1 체이닝 전엔 ~3-5년 창).
export interface ReturnTrend {
	streak: number; // 최신부터 거꾸로 dps>0 인 연속 연수 (window 내)
	streakToYear: string; // 연속 배당이 이어진 최신 연도
	payoutFromYear: string;
	payoutToYear: string;
	payoutFromPct: Num; // % · 배당성향 (payoutPct non-null 첫·마지막, window 가 span 할 때만)
	payoutToPct: Num;
	cancelQty: Num; // 주 · 최신해 자사주 소각 (buybackCancel>0 일 때만, 한국 ~30종목 appears-when-clean)
	cancelYear: string | null;
}
export function returnTrend(srs: ShareholderReturnYear[] | null | undefined): ReturnTrend | null {
	if (!srs || !srs.length) return null;
	// trailing 연속 배당 · 최신부터 거꾸로 dps>0. 꼬리의 dps=null(당해 미발표 · 실측 005010 의 2025)은
	// 연속 중단이 아니라 건너뛴다(가장 최근 *배당 보고* 연도부터 계수). 단 중간 null/0 은 진짜 중단(undercount=정직).
	let i = srs.length - 1;
	while (i >= 0 && srs[i].dps == null) i--;
	let streak = 0;
	let streakToYear = '';
	for (; i >= 0; i--) {
		const d = srs[i].dps;
		if (d == null || d <= 0) break;
		if (streak === 0) streakToYear = srs[i].year;
		streak++;
	}
	// 배당성향 이동 · payoutPct non-null 첫·마지막 (서로 다른 연도일 때만)
	const withPayout = srs.filter((s) => s.payoutPct != null);
	const pFirst = withPayout.length >= 2 ? withPayout[0] : null;
	const pLast = withPayout.length >= 2 ? withPayout[withPayout.length - 1] : null;
	const payoutSpan = pFirst && pLast && pFirst.year !== pLast.year;
	// 소각 · 최신해 buybackCancel>0 (한국 시장 희소, 깨끗할 때만 등장)
	const latest = srs[srs.length - 1];
	const cancelQty = latest.buybackCancel != null && latest.buybackCancel > 0 ? latest.buybackCancel : null;
	if (streak < 2 && !payoutSpan && cancelQty == null) return null;
	return {
		streak,
		streakToYear,
		payoutFromYear: pFirst?.year ?? '',
		payoutToYear: pLast?.year ?? '',
		payoutFromPct: payoutSpan ? (pFirst as ShareholderReturnYear).payoutPct : null,
		payoutToPct: payoutSpan ? (pLast as ShareholderReturnYear).payoutPct : null,
		cancelQty,
		cancelYear: cancelQty != null ? latest.year : null
	};
}
