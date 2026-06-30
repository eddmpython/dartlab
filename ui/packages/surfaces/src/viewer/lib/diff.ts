// 셀 diff / 행 식별 순수 헬퍼 · ui/web `analysis.$code.viewer.tsx` 1:1 포팅.
// diff/timeline 은 프론트 인접셀 비교 (백엔드 계산 0).

import type { PanelRow } from './types';
import type { FinanceStatement } from './finance/types';
import { plainText, maxAmountKrw, parseConstraint, amtOk, type AmtConstraint } from './searchIndex';

// 레일 라벨 = 사용자가 탐색하는 항목 축 = blockLeaf (TOC chip 과 동일).
export function rowLabel(r: PanelRow): string {
	return r.blockLeaf || '';
}

// row 가 visible window 안에 본문이 하나라도 있을 때만 렌더 (옛 기간 ghost row 차단).
export function hasVisibleContent(row: PanelRow, windowPeriods: string[]): boolean {
	for (const p of windowPeriods) {
		const v = row.cells?.[p];
		if (typeof v === 'string' && v.trim().length > 0) return true;
	}
	return false;
}

// ──────────────────────────────────────────────────────────────────────────
// 화면 내 분석 (viewport analysis) · 학습·임베딩·LLM 0 의 결정론 휴리스틱.
//
// ★5회사 실측 판정(memory project_viewer_ai_analysis): 메인 격자 셀은 raw DART XML
// (텍스트/표 덩어리, 항목 라벨 열 없음)이라 "셀 추세"는 라벨없는 max숫자가 기간마다 딴 항목을
// 가리켜(노이즈 점프 ×35만) gimmick → 본 모듈은 추세를 내지 않는다(carve).
// 진짜 가치 = facet(금액·비율·연도) 추출: BM25 가 구조적으로 못 보는(부등식·단위환산) 정량 사실을
// 산술로 전수 포착(constraintFacet.py 실측: BM25 재현율 4~28%). 진짜 추세는 정렬된 finance 숫자
// (financeSignals)에서만 · 거기엔 계정 라벨이 있어 신뢰 가능.
//
// 입력은 viewport 그대로: rows(activeSection×activeBlock) × periods(windowPeriods, 최신좌측).
// 재사용: searchIndex maxAmountKrw(조 다의어 2중차단)·parseConstraint·amtOk·plainText.
// ──────────────────────────────────────────────────────────────────────────

const PERCENT = /(?<![\d.])(\d{1,3}(?:\.\d+)?)\s*%/g;
const YEAR = /\b(20\d{2})\s*년/g;

export interface CellFacet {
	rowIndex: number; // rows[] 인덱스 = PanelMatrix glow 좌표
	label: string;
	period: string;
	amount: number; // 셀 maxAmountKrw (원), 없으면 0
	percents: number[];
	years: number[];
}

export interface ViewportAnalysis {
	sectionKey: string | null;
	periods: string[];
	rowsVisible: number; // window 내 본문 있는 행 수
	amountCells: number; // 금액 facet 있는 셀 수
	percentCells: number;
	yearCells: number;
	biggestAmount: number; // 화면 내 최대 금액(원)
	facets: CellFacet[]; // facet 1개 이상인 셀
	constraint: AmtConstraint | null; // query 에서 파싱한 제약("100억 이상")
	constraintHits: CellFacet[]; // 제약 만족 셀 (constraint 있을 때만, glow 타깃)
}

function extractAll(re: RegExp, text: string): number[] {
	const out: number[] = [];
	re.lastIndex = 0;
	let m: RegExpExecArray | null;
	while ((m = re.exec(text)) !== null) {
		const v = parseFloat(m[1]);
		if (Number.isFinite(v)) out.push(v);
	}
	return out;
}

export function analyzeViewport(
	rows: PanelRow[],
	periods: string[],
	opts: { sectionKey?: string | null; query?: string } = {}
): ViewportAnalysis {
	const facets: CellFacet[] = [];
	const constraintHits: CellFacet[] = [];
	const { c } = opts.query ? parseConstraint(opts.query) : { c: null };
	let amountCells = 0;
	let percentCells = 0;
	let yearCells = 0;
	let rowsVisible = 0;
	let biggestAmount = 0;

	for (let i = 0; i < rows.length; i++) {
		const r = rows[i];
		if (!hasVisibleContent(r, periods)) continue;
		rowsVisible++;
		const label = rowLabel(r);
		for (const p of periods) {
			const raw = r.cells?.[p];
			if (!raw) continue;
			const text = plainText(raw);
			const amount = maxAmountKrw(text);
			const percents = extractAll(PERCENT, text);
			const years = extractAll(YEAR, text);
			if (amount <= 0 && percents.length === 0 && years.length === 0) continue;
			if (amount > 0) {
				amountCells++;
				if (amount > biggestAmount) biggestAmount = amount;
			}
			if (percents.length) percentCells++;
			if (years.length) yearCells++;
			const facet: CellFacet = { rowIndex: i, label, period: p, amount, percents, years };
			facets.push(facet);
			if (c && amtOk(amount, c)) constraintHits.push(facet);
		}
	}

	return {
		sectionKey: opts.sectionKey ?? null,
		periods,
		rowsVisible,
		amountCells,
		percentCells,
		yearCells,
		biggestAmount,
		facets,
		constraint: c,
		constraintHits
	};
}

// ──────────────────────────────────────────────────────────────────────────
// finance 정렬숫자 위 신호 · FinanceStatement(loadFinanceStatement 결과, 계정라벨·동류기간·진짜 숫자)
// 의 단조추세·흑적전환·큰변동을 결정론으로 뽑는다. panel 셀과 달리 계정 라벨이 있어 "이 숫자가 무엇인지"가
// 명확 = 신뢰 가능한 추세. 사람이 9기간 격자에서 못 잡는 것(연속추세·부호전환 시점·배수점프)을 산술로.
// 입력 stmt.periods 는 최신좌측, freq 단위로 동류(YoY/QoQ 혼동 없음).
// ──────────────────────────────────────────────────────────────────────────

export type FinanceSignalKind = 'flip' | 'streak' | 'mover';

export interface FinanceSignal {
	accountId: string;
	label: string;
	depth: number;
	points: { period: string; value: number }[]; // 최신좌측, null 제외
	latest: number;
	prev: number | null;
	deltaPct: number | null; // (latest-prev)/|prev|
	direction: 'up' | 'down' | 'flat' | 'mixed';
	monotoneRun: number; // 과거→현재 최장 동일방향 연속 포인트 수
	signFlip: boolean; // 흑↔적자 (인접 부호 전환)
	flipAt: string | null; // 부호 전환이 일어난 기간(최신쪽)
	kind: FinanceSignalKind;
	severity: number; // 랭킹용 (클수록 주목)
}

function classifyFinance(pointsNewestFirst: { period: string; value: number }[]): {
	direction: FinanceSignal['direction'];
	monotoneRun: number;
	signFlip: boolean;
	flipAt: string | null;
} {
	const chron = [...pointsNewestFirst].reverse(); // 과거 먼저
	let ups = 0;
	let downs = 0;
	let runDir = 0;
	let run = 1;
	let bestRun = 1;
	let signFlip = false;
	let flipAt: string | null = null;
	for (let i = 1; i < chron.length; i++) {
		const a = chron[i - 1].value;
		const b = chron[i].value;
		if ((a < 0) !== (b < 0) && (a !== 0 || b !== 0)) {
			signFlip = true;
			flipAt = chron[i].period; // 전환 후 기간
		}
		const dir = b > a ? 1 : b < a ? -1 : 0;
		if (dir > 0) ups++;
		else if (dir < 0) downs++;
		if (dir !== 0 && dir === runDir) {
			run++;
			bestRun = Math.max(bestRun, run);
		} else if (dir !== 0) {
			runDir = dir;
			run = 2;
			bestRun = Math.max(bestRun, run);
		}
	}
	const direction = ups > 0 && downs === 0 ? 'up' : downs > 0 && ups === 0 ? 'down' : ups === 0 && downs === 0 ? 'flat' : 'mixed';
	return { direction, monotoneRun: bestRun, signFlip, flipAt };
}

export function financeSignals(
	stmt: FinanceStatement,
	opts: { minRun?: number; minDeltaPct?: number; topK?: number } = {}
): FinanceSignal[] {
	const minRun = opts.minRun ?? 4;
	const minDeltaPct = opts.minDeltaPct ?? 0.3;
	const out: FinanceSignal[] = [];
	for (const row of stmt.rows) {
		const points: { period: string; value: number }[] = [];
		for (const p of stmt.periods) {
			const v = row.values[p];
			if (typeof v === 'number' && Number.isFinite(v)) points.push({ period: p, value: v });
		}
		if (points.length < 2) continue;
		const latest = points[0].value;
		const prev = points[1]?.value ?? null;
		const deltaPct = prev !== null && prev !== 0 ? (latest - prev) / Math.abs(prev) : null;
		const cls = classifyFinance(points);

		const isFlip = cls.signFlip;
		const isStreak = (cls.direction === 'up' || cls.direction === 'down') && cls.monotoneRun >= minRun;
		const isMover = deltaPct !== null && Math.abs(deltaPct) >= minDeltaPct;
		if (!isFlip && !isStreak && !isMover) continue;

		const kind: FinanceSignalKind = isFlip ? 'flip' : isStreak ? 'streak' : 'mover';
		const severity =
			(isFlip ? 1e6 : 0) + (isStreak ? cls.monotoneRun * 1e3 : 0) + (deltaPct !== null ? Math.abs(deltaPct) * 100 : 0);

		out.push({
			accountId: row.accountId,
			label: row.label,
			depth: row.depth,
			points,
			latest,
			prev,
			deltaPct,
			direction: cls.direction,
			monotoneRun: cls.monotoneRun,
			signFlip: cls.signFlip,
			flipAt: cls.flipAt,
			kind,
			severity
		});
	}
	out.sort((a, b) => b.severity - a.severity);
	return opts.topK ? out.slice(0, opts.topK) : out;
}
