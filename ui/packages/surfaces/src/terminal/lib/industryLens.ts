// 거시 산업 sweep 렌즈 SSOT · 좌측 LeftRail 산업층 · IndustryDialog 공유(정의 1곳).
// 각 렌즈 = 34산업을 가로지르는 한 차원. value/band/lower/unit + 정직 라벨.
// 측정 근거: tests/_attempts/macroIndustrySweep/ (산업을 *실제로 가르는* 신호만 채택, median 압축지표 배제).
import type { IndustryDist, IndustryMacro } from './engine';

export interface IndustryLens {
	key: string;
	kr: string;
	en: string;
	unit: string;
	lower: boolean; // true = 낮을수록 좋음(부채·밸류·부실) · 색 방향 반전
	valueOf: (m: IndustryMacro) => number | null; // 정렬·표시 값(median 등)
	bandOf: (m: IndustryMacro) => IndustryDist | null; // 분포 막대(없으면 null → 막대 생략)
	note: string; // 렌즈별 정직 라벨(04 §3)
}

export const INDUSTRY_LENSES: IndustryLens[] = [
	{
		key: 'prof', kr: '수익성', en: 'Margin', unit: '%', lower: false,
		valueOf: (m) => m.dist.opMargin?.median ?? null,
		bandOf: (m) => m.dist.opMargin,
		note: '영업이익률 중앙값 · 막대 = p10~p90 분포 (상장 동일가중)'
	},
	{
		key: 'growth', kr: '성장', en: 'Growth', unit: '%', lower: false,
		valueOf: (m) => m.dist.netIncomeCagr?.median ?? null,
		bandOf: (m) => m.dist.netIncomeCagr,
		note: '순이익 CAGR 중앙값 · 스냅샷(추세 아닌 방향)'
	},
	{
		key: 'debt', kr: '부채', en: 'Debt', unit: '%', lower: true,
		valueOf: (m) => m.dist.debtRatio?.median ?? null,
		bandOf: (m) => m.dist.debtRatio,
		note: '부채비율 중앙값 (낮을수록 안전)'
	},
	{
		key: 'value', kr: '밸류', en: 'Value', unit: '배', lower: true,
		valueOf: (m) => m.pbr?.median ?? null,
		bandOf: (m) => m.pbr,
		note: 'PBR 중앙값 = gov 시총 / 자본 (KRX 시총가중 업종지수 아님)'
	},
	{
		key: 'polar', kr: '마진분산', en: 'Spread', unit: '%p', lower: false,
		valueOf: (m) => m.marginIqr,
		bandOf: (m) => m.dist.opMargin,
		note: '영업이익률 IQR(p75−p25) = 산업 내 회사 간 격차. 넓다=격차 큼이지 좋고나쁨 아님(중립 관측)'
	},
	{
		key: 'risk', kr: '부실', en: 'Distress', unit: '%', lower: true,
		valueOf: (m) => m.bucket.profRisk,
		bandOf: () => null,
		note: '적자·저수익 비중 % (scan grade 버킷 · ordinal 평균 아님)'
	}
];

export const lensByKey = (key: string): IndustryLens => INDUSTRY_LENSES.find((l) => l.key === key) || INDUSTRY_LENSES[0];

// 렌즈 값 → 0~100 백분위(상대 위치, lower 반영) · DistCurve 톤·정렬 보조.
export function lensRank(lens: IndustryLens, value: number, all: number[]): number {
	if (!all.length) return 50;
	const below = all.filter((v) => v < value).length;
	const p = (below / all.length) * 100;
	return lens.lower ? 100 - p : p;
}
