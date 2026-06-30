// 유니버스 백테스터 계약 · 전종목 크로스섹셔널 랭킹(17년 가격보존). terminal-strategy-lab 05 §2.
// 단일종목 엔진(terminal/lib/backtest)과 별도 객체 · candles-aligned 회계를 버리고 holdings 회계.
// 공유 = 순수 equity 헬퍼 6종(mdd·riskRatios·benchmarkStats·endRet·cagr·mddWindowOf)뿐.

export type RankSignalKey = 'mom12_1' | 'lowVol' | 'high52w' | 'liquidity';
export type DelistReason = 'none' | 'merger' | 'unknown' | 'codeChange';

/** gov/prices/universe-monthly.parquet 한 행(월말 1행/종목/월). 실측 스키마(buildUniversePanel.py). */
export interface UniverseRow {
	ym: string; // YYYYMM
	stockCode: string;
	close: number;
	mktcap: number;
	turnover: number; // 월평균 거래대금
	momMonthly: number | null; // 12-1 모멘텀(월간)
	volMonthly6m: number | null; // 월수익 변동성 연환산
	high52wProx: number | null; // close / 최근12개월 최고 월말종가
	retFwd1m: number | null; // 다음달 수익(완전월그리드 reindex · 정지월=null)
	retFwd3m: number | null;
	delistReason: DelistReason; // 합병=last-close 제외, unknown=양극단 밴드(U-G1)
}

export interface UniverseSpec {
	rebalance: 'M' | 'Q'; // 월/분기 리밸런싱
	rankSignal: RankSignalKey;
	buckets: number; // 분위 수(5=5분위)
	liquidityPctile: number; // ★유동성 컷 · 그 리밸 시점 turnover 상위 (1−p) 만(PIT). 0.7=상위30%. 필수(실측: 없으면 penny 인공물). U-G3
	windowFrom: string; // YYYYMM
	windowTo: string;
	// P1 고정(데이터 보기 전 결정된 규칙): 동일가중·long-only·OOS 강제. selection 자유도 봉인.
}

/** 한 리밸 시점 스냅샷 · decisionYm(랭킹) < fillYm(체결) 불변(look-ahead 차단·U-G2 PIT). */
export interface RebalanceSnapshot {
	ym: string;
	decisionYm: string;
	fillYm: string;
	byBucket: { bucket: number; codes: string[] }[];
	turnover: number; // 직전 대비 보유 교체율(분위 평균)
	nEligible: number;
	mergerExits: number;
	unknownExits: number;
}

export interface UniverseMetrics {
	topRetPct: number;
	topMddPct: number;
	topSharpe: number | null;
	spreadEndPct: number; // Q상위−Q하위 종착 차(%p)
	avgTurnover: number;
}

/** 한 청산가정의 1회 실행(unknown 폐지만 분기 · 합병/정상 공유). */
export interface UniverseRun {
	navByBucket: Record<number, number[]>; // 분위별 NAV(시작 100), ymAxis 길이
	ewBench: number[]; // 동일가중 전체 유니버스 NAV
	spread: number[]; // 상위분위 NAV − 하위분위 NAV
	metrics: UniverseMetrics;
}

export interface UniverseBtResult {
	ymAxis: string[]; // 리밸 ym 축(NAV 길이)
	optimistic: UniverseRun; // unknown 폐지 = 0손실(마지막 종가)
	conservative: UniverseRun; // unknown 폐지 = −100%(완전손실) · 헤드라인 기준
	unknownDependence: number; // 두 실행 상위분위 종착 차(%p) = 밴드 폭 = 진짜 unknown 의존도(U-G1)
	headlineSuppressed: boolean; // 밴드 폭>30%p → hero 숫자 차단(U-G1 ④)
	rebalances: RebalanceSnapshot[];
	status: 'ok' | 'invalid';
	nUnknownExits: number; // 밴드에 든 unknown 폐지 종목 수
	nMergerExits: number; // last-close 처리(밴드 제외)
}

export const RANK_SIGNAL_LABEL: Record<RankSignalKey, { kr: string; en: string; lowerBetter: boolean }> = {
	mom12_1: { kr: '모멘텀 12-1', en: 'Momentum 12-1', lowerBetter: false },
	lowVol: { kr: '저변동성', en: 'Low volatility', lowerBetter: true },
	high52w: { kr: '52주 신고가 근접', en: '52w high proximity', lowerBetter: false },
	liquidity: { kr: '유동성(거래대금)', en: 'Liquidity', lowerBetter: false }
	// reversal1m 제거 · high52wProx 의 역을 '1개월 반전'으로 오라벨(진짜 trailing-1m 수익 시계열 부재). 데이터 생기면 재도입.
};
