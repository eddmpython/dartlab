// 리얼타임 기업분석보고서 조립기 · 데이터 작업대 포트(finance/search)만 사용.
// 정적 bake JSON 폐기. 모든 수치는 runtime.finance.bundle(HF parquet 직독) 결과를 조회 시점에 계산.
import type {
	DartLabRuntime,
	TerminalFinanceBundle,
	TerminalFinance,
	IndexRow,
	ValuationSnapshot,
	Num
} from '@dartlab/ui-contracts';
import { loadJson } from '@dartlab/ui-runtime/data/dartlabData';
import type { ReportBlock, ReportModel, ReportResult, ReportSection, OverviewModel, OverviewTake, Thesis, ThesisPillar } from './model';
import { lastNonNull, isSkipped } from './model';
import { findPerspective, PERSPECTIVES, type PerspectiveMeta } from './perspectives';
import type {
	ShareholderReturnYear,
	CapitalChangesBundle,
	Candle,
	ShareholdersView,
	OwnershipYear,
	WorkforceYear,
	ExecBoardYear,
	TopExecPay,
	AuditYear,
	AuditFeeYear,
	InvestmentsBundle
} from '@dartlab/ui-contracts';
import { KR_INDEX_PRESETS } from '@dartlab/ui-contracts';
import { pYear, fmtPct, fmtPctSigned, fmtMult, fmtAmt1, scaleAmt, fmtScaled, fmtRange, fmtShares, fmtWon, fmtPay, fmtNum } from './format';
import { calcBeta, yearEndCloses, priceSummary } from './market';
import { coverage, detectOneOff, finite, readTrend, cagr } from './series';
import { topPctLabel, valuationPos, buildValPeer, peerCompareTable, type IndDist, type PeerCtx, type ValPeer } from './peer';
import { quarterWindow, annualWindow, type QWindow } from './window';

// ── 공통 유틸 ──────────────────────────────────────────────
function annualView(fin: TerminalFinanceBundle): TerminalFinance | null {
	return fin.views.annual ?? fin.views[fin.defaultMode] ?? null;
}

function latestFiled(fin: TerminalFinanceBundle): string | null {
	const ds = Object.values(fin.filedDates ?? {})
		.filter((d): d is string => !!d && d.length >= 8)
		.sort();
	const d = ds[ds.length - 1];
	if (!d) return null;
	return `${d.slice(0, 4)}-${d.slice(4, 6)}-${d.slice(6, 8)}`;
}

const last = <T,>(arr: T[]): T => arr[arr.length - 1];



// 자기역사 위치 · 최신값이 자기 N년 범위의 하단/중단/상단 어디인지(밸류 self-history).
function selfBand(latest: number, series: number[]): { band: string; lo: number; hi: number } | null {
	const v = series.filter((x) => Number.isFinite(x));
	if (v.length < 3) return null;
	const lo = Math.min(...v);
	const hi = Math.max(...v);
	if (hi === lo) return null;
	const pos = (latest - lo) / (hi - lo);
	return { band: pos < 0.34 ? '하단' : pos > 0.66 ? '상단' : '중단', lo, hi };
}

// 라인차트용 다운샘플 · 균등 간격 + 끝점 보존.
function downsample(arr: number[], target = 80): number[] {
	if (arr.length <= target) return arr.slice();
	const step = arr.length / target;
	const out: number[] = [];
	for (let i = 0; i < target; i++) out.push(arr[Math.floor(i * step)]);
	out.push(arr[arr.length - 1]);
	return out;
}


// 흐름표 · 계정 × 기간 + YoY 열 (+ 선택 TTM 열). 금액(조) 자동 스케일. flow 계정 전용. 분기/연간 공용.
// ttm: 윈도 마지막 *정상* 분기에 정렬된 TTM(직전 4분기 합) 값 · 제외된 오염분기를 포함하지 않게 호출부에서 정렬.
function quarterFlowTable(
	rows: { label: string; values: Num[]; yoyOf?: Num[]; ttm?: Num }[],
	qw: QWindow,
	labelHeader: string,
	caption: string,
	yoyLabel = '최신 전년동기比'
): ReportBlock | null {
	const present = rows.filter((r) => coverage(qw.pick(r.values)) >= 2);
	if (!present.length) return null;
	const hasTtm = present.some((r) => r.ttm != null && Number.isFinite(r.ttm));
	const allVals = present.flatMap((r) => qw.pick(r.values)).concat(hasTtm ? present.map((r) => r.ttm ?? null) : []);
	const { unit, scale } = scaleAmt(allVals);
	const data = present.map((r) => {
		const rec: Record<string, string> = { [labelHeader]: r.label };
		const w = qw.pick(r.values);
		qw.periods.forEach((p, i) => {
			rec[p] = fmtScaled(w[i] ?? null, scale);
		});
		if (hasTtm) rec['TTM'] = r.ttm != null && Number.isFinite(r.ttm) ? fmtScaled(r.ttm, scale) : '-';
		// YoY = 최신 분기 전년동기 대비(열 하나로 압축 · 표 폭 관리)
		const yseries = qw.yoy(r.yoyOf ?? r.values);
		const lastY = lastNonNull(yseries);
		rec['YoY'] = lastY != null ? fmtPctSigned(lastY) : '-';
		return rec;
	});
	return { type: 'table', label: `${caption}${hasTtm ? ' · TTM=직전 4분기 합(최신 정상분기 정렬)' : ''} · YoY=${yoyLabel}`, data, unit };
}

function amtTable(
	rows: { label: string; values: Num[] }[],
	yearCols: string[],
	labelHeader: string,
	caption: string
): ReportBlock | null {
	// 저커버리지 행 제거 · 떨이 단일값(예: NAVER 매출원가 1개)이 표를 더럽히지 않게.
	const present = rows.filter((r) => coverage(r.values) >= 2);
	if (!present.length) return null;
	const allVals = present.flatMap((r) => r.values);
	const { unit, scale } = scaleAmt(allVals);
	const data = present.map((r) => {
		const rec: Record<string, string> = { [labelHeader]: r.label };
		yearCols.forEach((yc, i) => {
			rec[yc] = fmtScaled(r.values[i] ?? null, scale);
		});
		return rec;
	});
	return { type: 'table', label: caption, data, unit };
}

// 비율 표(% 또는 배). signed=true 면 +부호 표기(성장률).
function pctTable(
	rows: { label: string; values: Num[]; unit?: '%' | '배' }[],
	yearCols: string[],
	labelHeader: string,
	caption: string,
	signed = false
): ReportBlock | null {
	const present = rows.filter((r) => coverage(r.values) >= 2);
	if (!present.length) return null;
	// 단위 혼재(% + 배) 표는 셀에 단위 유지, 단일 % 표는 단위를 우상단으로 빼고 셀은 숫자만(칸 폭↓·줄바뀜 방지).
	const anyMult = present.some((r) => r.unit === '배');
	const tableUnit = anyMult ? undefined : '%';
	const data = present.map((r) => {
		const rec: Record<string, string> = { [labelHeader]: r.label };
		yearCols.forEach((yc, i) => {
			const v = r.values[i] ?? null;
			if (tableUnit) rec[yc] = v == null || !Number.isFinite(v) ? '-' : `${signed && (v as number) > 0 ? '+' : ''}${(v as number).toFixed(1)}`;
			else rec[yc] = r.unit === '배' ? fmtMult(v) : signed ? fmtPctSigned(v) : fmtPct(v);
		});
		return rec;
	});
	return { type: 'table', label: caption, data, unit: tableUnit };
}

// ── 관점 1: 수익성 (Earnings Power) · 분기 우선 ─────────────
function buildEarningsPower(
	tfx: TerminalFinance, // 본문 시간축 뷰(분기 우선)
	win: QWindow, // 본문 윈도(분기 8개 또는 연간 6개)
	tfA: TerminalFinance | null, // 연간 보충용
	tfT: TerminalFinance | null, // TTM(직전 4분기 합) · 계절성 평탄화 절대수준
	kind: '분기' | '연간',
	ctx: { corpName: string; peer: PeerCtx | null }
): { sections: ReportSection[]; findings: ReportModel['keyFindings']; closing: ReportModel['closing']; kpis: ReportModel['headlineKpis']; conclusion: string } {
	const { corpName, peer } = ctx;
	const isRow = (k: string): Num[] => tfx.statements.IS.find((r) => r.key === k)?.values ?? [];
	// TTM 값을 윈도 마지막 *정상* 분기에 정렬(제외된 오염분기 포함 방지).
	const ttmAt = (k: string): Num => { if (!tfT) return null; const idx = tfT.periods.indexOf(win.periods[win.periods.length - 1]); if (idx < 0) return null; const s = tfT.statements.IS.find((r) => r.key === k)?.values ?? []; return s[idx] ?? null; };
	const cfRow = (k: string): Num[] => tfx.statements.CF.find((r) => r.key === k)?.values ?? [];
	const bsRow = (k: string): Num[] => tfx.statements.BS.find((r) => r.key === k)?.values ?? [];
	const rRow = (k: string): Num[] => tfx.ratios.find((r) => r.key === k)?.values ?? [];
	const P = win.periods;
	const lastP = P[P.length - 1];
	const yoyTag = kind === '분기' ? '전년 동기' : '전년';
	const periodWord = kind === '분기' ? '분기' : '연도';

	const revLast = lastNonNull(win.pick(isRow('revenue')));
	const opmLast = lastNonNull(win.pick(rRow('opm')));
	const npmLast = lastNonNull(win.pick(rRow('npm')));
	const revYoyLast = lastNonNull(win.yoy(isRow('revenue')));
	const opYoyLast = lastNonNull(win.yoy(isRow('operatingIncome')));
	const eqL = lastNonNull(win.pick(rRow('earningsQuality')));
	const niLast = lastNonNull(win.pick(isRow('netIncome')));
	// ROE 는 분기 단독 연율화 금지 → 연간(tfA) 최신값 사용(라벨 명시).
	const roeAnnual = tfA ? lastNonNull(tfA.ratios.find((r) => r.key === 'roe')?.values ?? []) : null;

	const sections: ReportSection[] = [];
	const findings: ReportModel['keyFindings'] = [];

	// ── S1 분기 손익 추이 (간판) · 분기 + TTM(직전 4분기 합, 계절성 평탄화) ──
	const isTbl = quarterFlowTable(
		[
			{ label: '매출액', values: isRow('revenue'), ttm: ttmAt('revenue') },
			{ label: '매출원가', values: isRow('costOfSales'), ttm: ttmAt('costOfSales') },
			{ label: '매출총이익', values: isRow('grossProfit'), ttm: ttmAt('grossProfit') },
			{ label: '판매관리비', values: isRow('sga'), ttm: ttmAt('sga') },
			{ label: '영업이익', values: isRow('operatingIncome'), ttm: ttmAt('operatingIncome') },
			{ label: '당기순이익', values: isRow('netIncome'), ttm: ttmAt('netIncome') }
		],
		win,
		'손익 항목',
		`${kind} 손익 추이`,
		`최신 ${yoyTag}比`
	);
	const ttmRev = ttmAt('revenue');
	const ttmOp = ttmAt('operatingIncome');
	const opmRead = readTrend(win.pick(rRow('opm')), true);
	const opmW = finite(win.pick(rRow('opm')));
	const opmLo = opmW.length ? Math.min(...opmW) : null;
	const opmHi = opmW.length ? Math.max(...opmW) : null;
	const ttmClause = ttmRev != null ? ` 직전 4분기 합(TTM)으로는 매출 ${fmtAmt1(ttmRev)}·영업이익 ${fmtAmt1(ttmOp)}로, 계절성을 평탄화한 연환산 체력은 이 수준입니다.` : '';
	const s1lead = `${corpName}의 최근 ${kind}(${lastP}) 매출은 ${fmtAmt1(revLast)}로 ${yoyTag} 대비 ${fmtPctSigned(revYoyLast)}, 영업이익률 ${fmtPct(opmLast)}·순이익률 ${fmtPct(npmLast)}입니다.${ttmClause} 아래 표는 매출에서 영업이익·순이익으로 이어지는 손익 구조를 ${kind}별로 보여줍니다(TTM 열은 계절성 평탄화 절대수준, YoY는 ${yoyTag} 대비).`;
	const s1: ReportBlock[] = [{ type: 'text', text: s1lead }];
	if (isTbl) s1.push(isTbl);
	sections.push({ key: 'incomeStructure', title: `${kind} 손익 추이 -- 무엇으로 얼마를 버는가`, sourceEngine: 'analysis', blocks: s1, emph: true });
	findings.push({ key: '실적', finding: `${lastP} 매출 ${fmtAmt1(revLast)}(${fmtPctSigned(revYoyLast)} YoY) · 영업이익률 ${fmtPct(opmLast)}.`, sourceEngine: 'analysis' });

	// ── S2 마진 궤적 + 브리지(직전 기간 ΔOPM 귀속) ──
	const sgaPctSeries = isRow('sga').map((v, i) => { const rv = isRow('revenue')[i]; return v != null && rv != null && (rv as number) !== 0 ? ((v as number) / (rv as number)) * 100 : null; });
	const marginTbl = pctTable(
		[
			{ label: '매출총이익률', values: win.pick(rRow('gpm')) },
			{ label: '판관비율', values: win.pick(sgaPctSeries) },
			{ label: '영업이익률', values: win.pick(rRow('opm')) },
			{ label: '순이익률', values: win.pick(rRow('npm')) }
		],
		P,
		'수익성 지표',
		`수익성 비율 추이 (${kind})`
	);
	// 마진 브리지 · Δ영업이익률을 원가율 vs 판관비율로 귀속(OPM=매출총이익률−판관비율 항등).
	const gpmW = finite(win.pick(rRow('gpm')));
	let bridge = '';
	if (opmW.length >= 2 && gpmW.length >= 2) {
		const dOpm = opmW[opmW.length - 1] - opmW[opmW.length - 2];
		const dGpm = gpmW[gpmW.length - 1] - gpmW[gpmW.length - 2];
		const dSga = dGpm - dOpm;
		if (Math.abs(dOpm) >= 0.3) {
			bridge = ` 직전 ${periodWord} 대비 영업이익률 변화(${fmtPctSigned(dOpm)}p)는 주로 ${Math.abs(dGpm) >= Math.abs(dSga) ? '매출원가율' : '판관비율'} 쪽에서 비롯됐습니다.`;
			// 가격 vs 물량 단서 · 매출 방향과 원가율 방향의 동행/괴리(정밀 분해는 공시 한계로 제한).
			if (Math.abs(dGpm) >= 0.3 && revYoyLast != null) {
				const r = revYoyLast as number;
				const why = r > 2 ? (dGpm > 0 ? '매출이 늘며 원가율이 낮아져 가격·믹스 개선이나 규모의 경제' : '매출은 늘었으나 원가율이 올라 투입가 상승·믹스 악화') : r < -2 ? (dGpm > 0 ? '매출이 줄어도 원가율이 낮아져 비용 절감·믹스 개선' : '매출 감소와 원가율 상승이 겹쳐 부담 가중') : '원가·믹스';
				bridge += ` 매출이 ${yoyTag} 대비 ${fmtPctSigned(r)}인 가운데 매출총이익률이 ${fmtPctSigned(dGpm)}p 움직인 것은 ${why} 요인일 수 있습니다(가격·물량 정밀 분해는 공시 한계로 제한적).`;
			}
		}
	}
	const s2text = opmW.length >= 2 ? `영업이익률은 최근 ${opmW.length}개 ${periodWord} ${fmtPct(opmLo)}~${fmtPct(opmHi)} 범위에서 ${opmRead ?? '움직였습니다'}.${bridge} 매출총이익률·판관비율과 함께 보면 마진 변화가 원가에서 왔는지 판관비에서 왔는지 읽을 수 있습니다.` : `영업이익률은 ${fmtPct(opmLast)} 수준입니다.`;
	const s2: ReportBlock[] = [{ type: 'text', text: s2text }];
	if (marginTbl) s2.push(marginTbl);
	const npmOneOff = detectOneOff(win.pick(rRow('npm')), P);
	if (marginTbl && npmOneOff) s2.push({ type: 'text', text: `※ 순이익률 ${npmOneOff.year} ${fmtPct(npmOneOff.value)} 는 본업 마진 대비 이례적으로 높습니다 · 영업외 항목(평가손익·일회성 등)이 반영됐을 수 있어 본업 마진과 분리해 읽으십시오.` });
	if (marginTbl) {
		sections.push({ key: 'marginTrajectory', title: '마진 궤적 -- 남는 돈은 어디서 갈리나', sourceEngine: 'analysis', blocks: s2 });
		findings.push({ key: '마진', finding: `영업이익률 ${fmtPct(opmLast)} (최근 ${opmW.length}${periodWord} ${fmtPct(opmLo)}~${fmtPct(opmHi)})${bridge ? ' · 변화는 ' + (bridge.includes('원가') ? '원가' : '판관비') + ' 주도' : ''}.`, sourceEngine: 'analysis' });
	}

	// ── S2.5 동종업종 비교 (연간 · industryStats 분포 대비 백분위) ──
	if (peer && tfA) {
		const annOpm = lastNonNull(tfA.ratios.find((r) => r.key === 'opm')?.values ?? []);
		const annNpm = lastNonNull(tfA.ratios.find((r) => r.key === 'npm')?.values ?? []);
		const annRoe = lastNonNull(tfA.ratios.find((r) => r.key === 'roe')?.values ?? []);
		const pc = peerCompareTable(
			[
				{ label: '영업이익률', value: annOpm, key: 'opMargin', goodHigh: true, fmt: (v) => fmtPct(v) },
				{ label: '순이익률', value: annNpm, key: 'netMargin', goodHigh: true, fmt: (v) => fmtPct(v) },
				{ label: 'ROE', value: annRoe, key: 'roe', goodHigh: true, fmt: (v) => fmtPct(v) }
			],
			peer
		);
		if (pc) {
			const opmPh = pc.phrases.find((p) => p.label === '영업이익률');
			const roePh = pc.phrases.find((p) => p.label === 'ROE');
			// 관점 교차 · 마진 위치 vs ROE(자본효율) 위치의 갭(레버리지·자산효율 함의).
			const cross = opmPh && roePh && Math.abs(opmPh.top - roePh.top) >= 15 ? ` 영업이익률(${topPctLabel(opmPh)})과 ROE(${topPctLabel(roePh)})의 위치 차이는 자산효율·레버리지에서 갈린다는 뜻으로, 재무안정성·자본배분과 함께 보십시오.` : '';
			const lead = opmPh
				? `${corpName}의 영업이익률(연간 ${opmPh.valFmt})은 ${peer.name} 업종(유효표본 ${opmPh.n}사·결손 제외) 중 ${topPctLabel(opmPh)}로, 업종 중앙값(${opmPh.median}) 대비 ${opmPh.top <= 40 ? '뚜렷이 높은' : opmPh.top <= 60 ? '중간 수준의' : '낮은'} 수익성입니다. 자기 이력만으로는 알 수 없는 *업종 내 위치*를 더한 것으로, 동종업종 분포 대비 백분위일 뿐 목표주가·투자판단이 아닙니다.${cross}`
				: `아래는 ${peer.name} 분포 대비 위치입니다(연간 기준).`;
			sections.push({ key: 'peerCompare', title: '동종업종 비교 -- 업종에서 어디 서 있나', sourceEngine: 'industry', blocks: [{ type: 'text', text: lead }, pc.block] });
			if (opmPh) findings.push({ key: '업종비교', finding: `영업이익률 ${peer.name} 업종(${opmPh.n}사) 중 ${topPctLabel(opmPh)}${roePh ? ` · ROE ${topPctLabel(roePh)}` : ''} (중앙값 ${opmPh.median}).`, sourceEngine: 'industry' });
		}
	}

	// ── S3 성장·계절성 (YoY 우선 + 분기는 QoQ 보조) ──
	const growthRows = [
		{ label: `매출 (YoY, ${yoyTag}比)`, values: win.yoy(isRow('revenue')) },
		{ label: `영업이익 (YoY)`, values: win.yoy(isRow('operatingIncome')) }
	];
	if (kind === '분기') growthRows.push({ label: '매출 (QoQ, 직전분기比)', values: win.qoq(isRow('revenue')) });
	const growthTbl = pctTable(growthRows, P, '성장률', `성장률 (${kind})`, true);
	if (growthTbl) {
		const revYoyW = finite(win.yoy(isRow('revenue')));
		const yAvg = revYoyW.length ? revYoyW.reduce((s, x) => s + x, 0) / revYoyW.length : null;
		const accel = yAvg != null && revYoyLast != null ? ((revYoyLast as number) > yAvg + 2 ? '가속' : (revYoyLast as number) < yAvg - 2 ? '둔화' : '평균 수준') : null;
		const seasonNote = kind === '분기' ? ' 분기 비교는 계절성을 걷어내기 위해 전년 동기(YoY)를 1순위로 보며, QoQ는 사이클 신호로 보조합니다.' : '';
		const s3text = `매출은 최신 ${kind} 기준 ${yoyTag} 대비 ${fmtPctSigned(revYoyLast)}${accel ? `로, 최근 ${revYoyW.length}개 ${periodWord} 평균(${fmtPctSigned(yAvg)})${accel === '가속' ? '을 웃돌아 성장이 가속되는' : accel === '둔화' ? '을 밑돌아 성장이 둔화되는' : '과 비슷한'} 국면입니다` : '입니다'}. 성장은 마진과 함께 봐야 · 외형이 늘어도 마진이 꺾이면 이익 체력은 약해집니다.${seasonNote}`;
		sections.push({ key: 'growth', title: '성장·계절성 -- 외형은 커지고 있는가', sourceEngine: 'analysis', blocks: [{ type: 'text', text: s3text }, growthTbl] });
		findings.push({ key: '성장', finding: `매출 ${fmtPctSigned(revYoyLast)} YoY · 영업이익 ${fmtPctSigned(opYoyLast)} YoY${accel ? ` (${accel})` : ''}.`, sourceEngine: 'analysis' });
	}

	// ── S4 이익의 질 + 운전자본(CCC) ──
	const eqTbl = quarterFlowTable(
		[
			{ label: '당기순이익', values: isRow('netIncome') },
			{ label: '영업활동현금흐름', values: cfRow('cfOperating') }
		],
		win,
		'항목',
		`이익의 현금화 (${kind})`,
		`최신 ${yoyTag}比`
	);
	if (eqTbl) {
		const healthy = eqL != null && niLast != null && (niLast as number) > 0;
		const eqRead = readTrend(win.pick(rRow('earningsQuality')), true);
		const s4text = healthy
			? `최신 ${kind} 영업활동현금흐름은 당기순이익의 ${fmtMult(eqL)} 수준으로, 회계이익이 현금으로 ${(eqL as number) >= 1 ? '충분히' : '부분적으로'} 뒷받침됩니다${eqRead ? ` (배율은 최근 ${eqRead})` : ''}. 배율이 1배를 지속 밑돌면 운전자본 증가나 일회성 이익을 점검할 신호입니다.`
			: '최신 기간 순이익이 적자이거나 데이터가 부족해 현금화 배율은 산출하지 않았습니다(억지 채움 없음).';
		const s4: ReportBlock[] = [{ type: 'text', text: s4text }, eqTbl];

		// 운전자본·현금전환주기(CCC) · 재고·매출채권·매입채무 회전일. 분기=91일·연간=365일.
		const days = kind === '분기' ? 91 : 365;
		const rcv = win.pick(bsRow('receivables'));
		const inv = win.pick(bsRow('inventories'));
		const pay = win.pick(bsRow('payables'));
		const revW = win.pick(isRow('revenue'));
		const cogsW = win.pick(isRow('costOfSales'));
		// 평균잔액((기초+기말)/2) · BS 시점값을 flow 분모에 맞춰 평균(DuPont avgDen 규율과 일관, 기관 지적).
		const avgBal = (s: Num[], i: number): Num => { const c = s[i]; if (c == null || !Number.isFinite(c)) return null; const p = i > 0 ? s[i - 1] : null; return p != null && Number.isFinite(p) ? ((c as number) + (p as number)) / 2 : (c as number); };
		const dayR = (nv: Num, dv: Num): Num => (nv != null && dv != null && (dv as number) > 0 ? +(((nv as number) / (dv as number)) * days).toFixed(0) : null);
		const dso = revW.map((_, i) => dayR(avgBal(rcv, i), revW[i]));
		const dio = cogsW.map((_, i) => dayR(avgBal(inv, i), cogsW[i]));
		const dpo = cogsW.map((_, i) => dayR(avgBal(pay, i), cogsW[i]));
		const cccS = dso.map((_, i) => (dso[i] != null && dpo[i] != null ? +((dso[i] as number) + ((dio[i] as number) ?? 0) - (dpo[i] as number)).toFixed(0) : null));
		const cccTbl = reportTable(
			P,
			[
				{ label: 'CCC(현금전환주기)', cells: cccS.map((v) => fmtNum(v, '일')) },
				{ label: 'DSO(매출채권회전일)', cells: dso.map((v) => fmtNum(v, '일')) },
				{ label: 'DIO(재고회전일)', cells: dio.map((v) => fmtNum(v, '일')) },
				{ label: 'DPO(매입채무회전일)', cells: dpo.map((v) => fmtNum(v, '일')) }
			],
			'운전자본(일)',
			'현금전환주기 (일수)'
		);
		const cccLast = lastNonNull(cccS);
		if (cccTbl) {
			const cccRead = readTrend(cccS, false); // CCC↑ = 운전자본 부담↑ = 약화
			s4.push({ type: 'text', text: `현금전환주기(CCC = 매출채권회전일 + 재고회전일 − 매입채무회전일)는 영업에서 현금이 묶였다 풀리는 데 걸리는 일수입니다. 최신 ${kind} ${fmtNum(cccLast, '일')}로 최근 ${cccRead ?? '추이를 보입니다'}${kind === '분기' ? ' · 재고일수 급증은 수요 둔화의 선행 신호로 함께 봅니다(일수는 분기 매출·매출원가 기준 산출이라 계절성 영향).' : '.'}` });
			s4.push(cccTbl as ReportBlock);
		}
		sections.push({ key: 'earningsQuality', title: '이익의 질 · 운전자본 -- 번 돈이 현금으로 돌아오나', sourceEngine: 'analysis', blocks: s4 });
		findings.push({ key: '이익품질', finding: healthy ? `영업CF/순이익 ${fmtMult(eqL)}${cccLast != null ? ` · CCC ${fmtNum(cccLast, '일')}` : ''}.` : '현금화 배율 산출 불가(적자/결측).', sourceEngine: 'analysis' });
	}

	// ── S5 연간 추세 (보충) · 장기 그림은 별도 섹션으로(분기 본문과 분리) ──
	if (kind === '분기' && tfA) {
		const aw = annualWindow(tfA, 6);
		if (aw) {
			const aRev = aw.pick(tfA.statements.IS.find((r) => r.key === 'revenue')?.values ?? []);
			const aOpm = aw.pick(tfA.ratios.find((r) => r.key === 'opm')?.values ?? []);
			const aNpm = aw.pick(tfA.ratios.find((r) => r.key === 'npm')?.values ?? []);
			const aRoe = aw.pick(tfA.ratios.find((r) => r.key === 'roe')?.values ?? []);
			// ROIC · NOPAT(영업이익×(1−실효세율)) ÷ 투하자본(자기자본+비유동부채). ROE와 달리 레버리지 덜 오염.
			const aOi = aw.pick(tfA.statements.IS.find((r) => r.key === 'operatingIncome')?.values ?? []);
			const aNi = aw.pick(tfA.statements.IS.find((r) => r.key === 'netIncome')?.values ?? []);
			const aTax = aw.pick(tfA.statements.IS.find((r) => r.key === 'incomeTax')?.values ?? []);
			const aEq = aw.pick(tfA.statements.BS.find((r) => r.key === 'equity')?.values ?? []);
			const aLiab = aw.pick(tfA.statements.BS.find((r) => r.key === 'liabilities')?.values ?? []);
			const aCl = aw.pick(tfA.statements.BS.find((r) => r.key === 'currentLiabilities')?.values ?? []);
			// 투하자본 분모는 평균잔액((기초+기말)/2) · NOPAT(flow)÷IC(stock) 규율을 CCC 와 일치(애널 지적).
			const avgA = (s: Num[], i: number): number | null => { const c = s[i]; if (c == null || !Number.isFinite(c)) return null; const p = i > 0 ? s[i - 1] : null; return p != null && Number.isFinite(p) ? ((c as number) + (p as number)) / 2 : (c as number); };
			const aRoic = aw.periods.map((_, i) => {
				const oi = aOi[i];
				const eqAvg = avgA(aEq, i);
				if (oi == null || !Number.isFinite(oi) || eqAvg == null) return null;
				const ni = aNi[i];
				const tax = aTax[i];
				const pretax = ni != null && tax != null ? (ni as number) + (tax as number) : null;
				const effTax = pretax != null && pretax > 0 && tax != null ? Math.min(0.4, Math.max(0, (tax as number) / pretax)) : 0.22;
				const nopat = (oi as number) * (1 - effTax);
				const liabAvg = avgA(aLiab, i);
				const clAvg = avgA(aCl, i);
				const ic = eqAvg + (liabAvg != null && clAvg != null ? Math.max(0, liabAvg - clAvg) : 0);
				return ic > 0 ? +((nopat / ic) * 100).toFixed(1) : null;
			});
			const roicL = lastNonNull(aRoic);
			const { unit: annUnit, scale } = scaleAmt(aRev);
			const annTbl: ReportBlock = {
				type: 'table',
				label: '연간 추세 (사업보고서 기준)',
				data: [
					{ '연간 지표': `매출액(${annUnit.replace('원', '')})`, ...Object.fromEntries(aw.periods.map((p, i) => [p, fmtScaled(aRev[i], scale)])) },
					{ '연간 지표': '영업이익률(%)', ...Object.fromEntries(aw.periods.map((p, i) => [p, fmtPct(aOpm[i])])) },
					{ '연간 지표': '순이익률(%)', ...Object.fromEntries(aw.periods.map((p, i) => [p, fmtPct(aNpm[i])])) },
					{ '연간 지표': 'ROE(%)', ...Object.fromEntries(aw.periods.map((p, i) => [p, fmtPct(aRoe[i])])) },
					{ '연간 지표': 'ROIC(%)', ...Object.fromEntries(aw.periods.map((p, i) => [p, fmtPct(aRoic[i])])) }
				]
			};
			const aRevCagr = cagr(aw.pick(tfA.statements.IS.find((r) => r.key === 'revenue')?.values ?? []));
			sections.push({
				key: 'annualSupplement',
				title: '연간 추세 -- 장기 그림 (보충)',
				sourceEngine: 'analysis',
				blocks: [
					{ type: 'text', text: `분기는 최신 모멘텀을, 연간은 장기 추세를 봅니다. 최근 ${aw.periods.length}년 매출은 연평균 ${fmtPctSigned(aRevCagr)} 성장했고, ROE ${fmtPct(roeAnnual)}·ROIC ${fmtPct(roicL)} 수준입니다. ROIC(투하자본이익률 = 세후영업이익 ÷ 투하자본)는 레버리지에 덜 오염된 *순수 자본효율*로, 자본조달비용(WACC)을 지속 웃돌면 자본배분이 가치를 창출한다고 봅니다(연율화는 연간 기준, 분기 단독 연율화 안 함).` },
					annTbl,
					{ type: 'text', text: `※ ROIC = 영업이익×(1−실효세율) ÷ 투하자본(평균잔액 기준 자기자본+비유동부채). 투하자본은 BS 표준계정에서 근사한 값으로, 정밀 ROIC(영업투하자본·리스 조정 등)와는 차이가 있을 수 있습니다.` }
				]
			});
			if (roicL != null) findings.push({ key: '자본효율', finding: `ROIC ${fmtPct(roicL)} · ROE ${fmtPct(roeAnnual)} (ROIC는 레버리지 덜 오염된 자본효율).`, sourceEngine: 'analysis' });
		}
	}

	const kpis: ReportModel['headlineKpis'] = [
		{ label: `매출 (${lastP})`, value: fmtAmt1(revLast) },
		{ label: '영업이익률', value: fmtPct(opmLast) },
		{ label: '순이익률', value: fmtPct(npmLast) },
		{ label: `매출 ${yoyTag}比`, value: fmtPctSigned(revYoyLast) },
		{ label: 'ROE (연간)', value: fmtPct(roeAnnual) },
		{ label: '이익품질(CFO/NI)', value: fmtMult(eqL) }
	];
	const conclusion = `${corpName}의 최근 ${kind}(${lastP}) 매출은 ${fmtAmt1(revLast)}로 ${yoyTag} 대비 ${fmtPctSigned(revYoyLast)}, 영업이익률 ${fmtPct(opmLast)}·순이익률 ${fmtPct(npmLast)}입니다. 최근 ${opmW.length}개 ${periodWord} 영업이익률은 ${fmtPct(opmLo)}~${fmtPct(opmHi)} 범위에서 ${opmRead ?? '움직였으며'}${bridge ? `,${bridge.replace(/^ /, ' ')}` : ''}. 영업현금흐름은 순이익의 ${fmtMult(eqL)} 수준으로 회계이익이 현금으로 ${eqL != null && (eqL as number) >= 1 ? '충분히' : '부분적으로'} 뒷받침됩니다${roeAnnual != null ? ` (연간 ROE ${fmtPct(roeAnnual)})` : ''}.`;
	const closing: ReportModel['closing'] = [
		{ label: '재무', engine: 'analysis', line: `${lastP} 매출 ${fmtAmt1(revLast)}(${fmtPctSigned(revYoyLast)} YoY) · 영업이익률 ${fmtPct(opmLast)} · 이익품질 ${fmtMult(eqL)}. (분기 측정값, 투자판단 아님)` }
	];
	return { sections, findings, closing, kpis, conclusion };
}

// 재무건전성 점검(브라우저 · Python dCR 7축 아님). 측정값 *나란히*, 종합점수·등급 금지.
// 판정에 자기이력 편입(과거 미달 연수) + 전구간 결측 축은 honest-skip 행으로 명시.
function healthTable(
	axes: { name: string; series: Num[]; unit: '%' | '배' | '조'; good: 'high' | 'low'; threshold: number; thLabel: string }[]
): ReportBlock | null {
	const fmtOf = (u: '%' | '배' | '조') => (u === '%' ? fmtPct : u === '배' ? fmtMult : fmtAmt1);
	const rows = axes.map((a) => {
		const vals = a.series.filter((v): v is number => v != null && Number.isFinite(v));
		const fmt = fmtOf(a.unit);
		if (!vals.length) {
			// honest-skip · 축이 조용히 사라지지 않게 '산출 불가' 행 명시(예: 무차입사 이자보상배율).
			return { 지표: a.name, 최근값: '-', '최근 범위': '-', 기준: a.thLabel, 판정: '산출 불가' } as Record<string, string>;
		}
		const latest = vals[vals.length - 1];
		const lo = Math.min(...vals);
		const hi = Math.max(...vals);
		const isPass = (v: number) => (a.good === 'high' ? v >= a.threshold : v <= a.threshold);
		const breaches = vals.filter((v) => !isPass(v)).length;
		let verdict: string;
		if (!isPass(latest)) verdict = '주의';
		else if (breaches > 0) verdict = `양호 (과거 ${breaches}년 미달)`;
		else verdict = '양호';
		return {
			지표: a.name,
			최근값: fmt(latest),
			'최근 범위': fmtRange(lo, hi, a.unit),
			기준: a.thLabel,
			판정: verdict
		} as Record<string, string>;
	});
	if (!rows.length) return null;
	return { type: 'table', label: '재무건전성 점검 · 4축 측정값 (각 축 독립 · 종합점수 없음, Python 신용등급 아님)', data: rows };
}

// ── 관점 2: 재무안정성 (Liquidity & Solvency) · 분기 우선 ─────
function buildLiquidity(
	tfx: TerminalFinance, // 본문 시간축(분기 우선)
	win: QWindow,
	kind: '분기' | '연간',
	tfA: TerminalFinance | null, // 자본배분(연간)·배당충당
	tfT: TerminalFinance | null, // TTM(직전 4분기 합)
	ctx: { corpName: string; peer: PeerCtx | null },
	debt: { ladder: { buckets: Num[]; shortTerm: Num; year: string } | null } | null,
	sr: ShareholderReturnYear[] | null
): { sections: ReportSection[]; findings: ReportModel['keyFindings']; closing: ReportModel['closing']; kpis: ReportModel['headlineKpis']; conclusion: string } {
	const { corpName, peer } = ctx;
	const isRow = (k: string): Num[] => tfx.statements.IS.find((r) => r.key === k)?.values ?? [];
	const cfRow = (k: string): Num[] => tfx.statements.CF.find((r) => r.key === k)?.values ?? [];
	// TTM 값 · 윈도 마지막 정상 분기 정렬(제외된 오염분기 미포함).
	const ttmCfAt = (k: string): Num => { if (!tfT) return null; const idx = tfT.periods.indexOf(win.periods[win.periods.length - 1]); if (idx < 0) return null; const s = tfT.statements.CF.find((r) => r.key === k)?.values ?? []; return s[idx] ?? null; };
	const ttmFcfV = ((): Num => { if (!tfT) return null; const idx = tfT.periods.indexOf(win.periods[win.periods.length - 1]); if (idx < 0) return null; const op = tfT.statements.CF.find((r) => r.key === 'cfOperating')?.values?.[idx]; const cx = tfT.statements.CF.find((r) => r.key === 'capex')?.values?.[idx]; return op != null ? (op as number) - (cx != null ? (cx as number) : 0) : null; })();
	const rRow = (k: string): Num[] => tfx.ratios.find((r) => r.key === k)?.values ?? [];
	const cardSeries = (k: string): Num[] => tfx.cards.find((c) => c.key === k)?.series?.[0]?.data ?? [];
	const P = win.periods;
	const lastP = P[P.length - 1];
	const periodWord = kind === '분기' ? '분기' : '연도';
	const snapWord = kind === '분기' ? '분기말' : '기말';

	// 파생 시계열 · 이자보상배율은 금융비용>0 일 때만(음수/음수가 양수로 뒤집혀 '양호' 오판 방지, R3).
	const oiAll = win.pick(isRow('operatingIncome'));
	const fcAll = win.pick(isRow('financeCosts'));
	const icr = oiAll.map((v, i) => (v != null && fcAll[i] != null && (fcAll[i] as number) > 0 ? (v as number) / (fcAll[i] as number) : null));
	const fcf = win.pick(cardSeries('fcfTrend'));

	const drL = lastNonNull(win.pick(rRow('debtRatio')));
	const crL = lastNonNull(win.pick(rRow('currentRatio')));
	const erL = lastNonNull(win.pick(rRow('equityRatio')));
	const icrL = lastNonNull(icr);
	const fcfL = lastNonNull(fcf);
	const cfoL = lastNonNull(win.pick(cfRow('cfOperating')));

	const sections: ReportSection[] = [];
	const findings: ReportModel['keyFindings'] = [];

	// ── S1 현금 창출·배분 (분기) + capex 강도 ──
	const cfTbl = quarterFlowTable(
		[
			{ label: '영업활동현금흐름', values: cfRow('cfOperating'), ttm: ttmCfAt('cfOperating') },
			{ label: '투자활동현금흐름', values: cfRow('cfInvesting'), ttm: ttmCfAt('cfInvesting') },
			{ label: '재무활동현금흐름', values: cfRow('cfFinancing'), ttm: ttmCfAt('cfFinancing') },
			{ label: '잉여현금흐름(FCF)', values: cardSeries('fcfTrend'), ttm: ttmFcfV }
		],
		win,
		'현금흐름',
		`${kind} 현금흐름`,
		'최신 전년동기比'
	);
	// capex 강도 · capex/매출(자본집약도). 분기 lumpy 라 추세로.
	const capexW = win.pick(cfRow('capex'));
	const revWl = win.pick(isRow('revenue'));
	const capexInt = capexW.map((v, i) => (v != null && revWl[i] != null && (revWl[i] as number) > 0 ? +(((v as number) / (revWl[i] as number)) * 100).toFixed(1) : null));
	const capexIntL = lastNonNull(capexInt);
	const fcfRead = readTrend(fcf, true);
	const s1: ReportBlock[] = [
		{
			type: 'text',
			text: `${corpName}의 현금은 영업에서 벌어 투자·재무로 흘러갑니다. 잉여현금흐름(FCF = 영업현금 − 설비투자)이 (+)이면 외부 차입 없이 자체 현금으로 굴러간다는 뜻입니다. 최신 ${kind} 영업현금흐름은 ${fmtAmt1(cfoL)}, FCF ${fmtAmt1(fcfL)}로 FCF는 최근 ${fcfRead ?? '추이를 보입니다'}${capexIntL != null ? `. 설비투자는 매출의 ${fmtPct(capexIntL)} 수준으로, ${(capexIntL as number) >= 10 ? '자본집약적' : '비교적 가벼운'} 투자 구조입니다` : ''}. (투자활동현금흐름의 (−)는 설비·지분 투자 집행으로 통상적인 모습이며, 붉은색은 음수 부호 표기일 뿐입니다.)`
		}
	];
	if (cfTbl) s1.push(cfTbl);
	if (cfTbl) {
		sections.push({ key: 'cashFlow', title: `${kind} 현금흐름 -- 현금은 어떻게 도는가`, sourceEngine: 'analysis', blocks: s1, emph: true });
		findings.push({ key: '현금흐름', finding: `${lastP} 영업CF ${fmtAmt1(cfoL)} · FCF ${fmtAmt1(fcfL)}${capexIntL != null ? ` · capex/매출 ${fmtPct(capexIntL)}` : ''}.`, sourceEngine: 'analysis' });
	}

	// ── S2 자본 배분 (연간) · 번 현금을 어디에 쓰나(영업CF→CAPEX→FCF→배당→잔여) ──
	// 자본배분은 *추세*로 본다(단년 스냅샷은 노이즈, 기관 지적) · 최근 N년 영업CF→CAPEX→FCF→배당→잔여.
	const aw5 = tfA ? annualWindow(tfA, 5) : null;
	if (tfA && aw5) {
		const aCfV = (k: string): Num[] => aw5.pick(tfA.statements.CF.find((r) => r.key === k)?.values ?? []);
		const opS = aCfV('cfOperating');
		const cxS = aCfV('capex');
		const dvS = aCfV('dividendsPaid');
		if (finite(opS).length >= 2) {
			const fcfS = opS.map((v, i) => (v != null ? (v as number) - (cxS[i] != null ? (cxS[i] as number) : 0) : null));
			const residS = fcfS.map((v, i) => (v != null ? (v as number) - (dvS[i] != null ? Math.abs(dvS[i] as number) : 0) : null));
			const allVals = [...opS, ...fcfS].filter((v): v is number => v != null && Number.isFinite(v));
			const { unit, scale } = scaleAmt(allVals);
			const cell = (v: Num, neg = false): string => (v == null || !Number.isFinite(v) ? '-' : fmtScaled(neg ? -Math.abs(v as number) : (v as number), scale));
			const yrs = aw5.periods;
			const mkRow = (label: string, vals: Num[], neg = false) => ({ '자본 배분': label, ...Object.fromEntries(yrs.map((y, i) => [y, cell(vals[i], neg)])) });
			const allocTbl: ReportBlock = {
				type: 'table',
				label: `자본 배분 추이 (단위: ${unit} · 음수=유출)`,
				data: [mkRow('영업활동현금흐름', opS), mkRow('− 설비투자(CAPEX)', cxS, true), mkRow('= 잉여현금흐름(FCF)', fcfS), mkRow('− 배당지급', dvS, true), mkRow('= 배당 후 잔여', residS)]
			};
			// 누적 함의 · Σ영업CF 중 CAPEX·배당 비중(투자형 vs 환원형 성향).
			const sum = (s: Num[]) => finite(s).reduce((a, b) => a + b, 0);
			const sOp = sum(opS);
			const sCx = sum(cxS.map((v) => (v != null ? Math.abs(v as number) : null)));
			const sDv = sum(dvS.map((v) => (v != null ? Math.abs(v as number) : null)));
			const capexPct = sOp > 0 ? (sCx / sOp) * 100 : null;
			const divPct = sOp > 0 ? (sDv / sOp) * 100 : null;
			const tilt = capexPct != null && divPct != null ? (capexPct > divPct * 1.5 ? '투자(CAPEX) 우선형' : divPct > capexPct ? '주주환원 우선형' : '투자·환원 병행형') : null;
			// 펀딩 갭 · 배당 후 잔여가 음수인 해(투자·배당이 영업CF 초과)는 어떻게 메웠나(지속가능성).
			const deficitYrs = yrs.filter((_, i) => residS[i] != null && (residS[i] as number) < 0);
			const gapNote = deficitYrs.length ? ` ${deficitYrs.join('·')}년은 투자·배당이 영업현금흐름을 초과해(배당 후 잔여 음수) 보유현금 소진이나 차입으로 메웠습니다 · 투자 우선형의 지속가능성은 곳간(현금·차입 여력)과 함께 봐야 합니다.` : '';
			// 재투자 질 좌표 · 투자(CAPEX) 우선형일 때 같은 기간 ROE 추세를 병치(늘린 자본이 수익으로 회수되는지의 *좌표*, 자본비용 비교·투자판정 아님). 환원형은 해당 질문이 약해 생략.
			const roeAw = aw5.pick(tfA.ratios.find((r) => r.key === 'roe')?.values ?? []);
			const roe0 = roeAw.find((v) => v != null && Number.isFinite(v)) ?? null;
			const roe1 = lastNonNull(roeAw);
			const investLean = capexPct != null && divPct != null && capexPct > divPct;
			const roeNote =
				investLean && roe0 != null && roe1 != null
					? ` 투자에 무게가 실린 배분이라 늘린 자본이 수익으로 회수되는지가 관건인데, 같은 기간 ROE는 ${fmtPct(roe0)} → ${fmtPct(roe1)}로 ${(roe1 as number) >= (roe0 as number) + 1 ? '개선됐습니다' : (roe1 as number) <= (roe0 as number) - 1 ? '낮아졌습니다' : '대체로 유지됐습니다'} · 재투자가 거둔 자본효율의 *좌표*이며 자본비용 비교·투자판단이 아닙니다.`
					: '';
			const allocText = `${corpName}가 최근 ${yrs.length}년 번 영업현금을 어디에 쓰는지 추세로 본 것입니다(단년 스냅샷은 노이즈라 흐름으로 봅니다). 누적 영업현금흐름 ${fmtAmt1(sOp)} 중 설비투자에 ${fmtAmt1(sCx)}(${fmtPct(capexPct)}), 배당에 ${fmtAmt1(sDv)}(${fmtPct(divPct)})를 배분해${tilt ? `, 자본배분은 ${tilt}에 가깝습니다` : ''}.${gapNote}${roeNote} (투자 → 주주환원 → 적립·상환 우선순위의 흐름)`;
			sections.push({ key: 'capitalAllocation', title: '자본 배분 -- 번 현금을 매년 어디에 쓰나 (연간 추세)', sourceEngine: 'analysis', blocks: [{ type: 'text', text: allocText }, allocTbl] });
			findings.push({ key: '자본배분', finding: `최근 ${yrs.length}년 누적 영업CF ${fmtAmt1(sOp)} 중 CAPEX ${fmtPct(capexPct)}·배당 ${fmtPct(divPct)}${tilt ? ` (${tilt})` : ''}.`, sourceEngine: 'analysis' });
		}
	}

	// ── S3 레버리지·유동성 (분기말 시점) ──
	const levTbl = pctTable(
		[
			{ label: '부채비율', values: win.pick(rRow('debtRatio')) },
			{ label: '자기자본비율', values: win.pick(rRow('equityRatio')) },
			{ label: '유동비율', values: win.pick(rRow('currentRatio')) }
		],
		P,
		'안정성 지표',
		`레버리지·유동성 비율 (${snapWord} 시점)`
	);
	if (levTbl) {
		const drRead = readTrend(win.pick(rRow('debtRatio')), false); // 부채비율↑ = 약화
		const s2text = `부채비율 ${fmtPct(drL)} · 유동비율 ${fmtPct(crL)} 입니다(${snapWord} 시점값). 부채비율은 자본 대비 부채(낮을수록 안정), 유동비율은 1년 내 갚을 부채 대비 1년 내 현금화 자산(100% 이상이면 단기 상환 여력)입니다.${drRead ? ` 부채비율은 최근 ${finite(win.pick(rRow('debtRatio'))).length}개 ${periodWord} ${drRead}.` : ''}`;
		sections.push({ key: 'leverage', title: '레버리지·유동성 -- 빚은 감당 가능한가', sourceEngine: 'analysis', blocks: [{ type: 'text', text: s2text }, levTbl] });
		const drTag = drL != null ? (drL <= 100 ? ' (낮음)' : drL >= 200 ? ' (높음)' : '') : '';
		findings.push({ key: '안정성', finding: `부채비율 ${fmtPct(drL)}${drTag} · 유동비율 ${fmtPct(crL)} · 자기자본비율 ${fmtPct(erL)}.`, sourceEngine: 'analysis' });
	}

	// ── S3.5 동종업종 비교 (연간 · 안정성·운전자본 백분위) ──
	if (peer && tfA) {
		const annDr = lastNonNull(tfA.ratios.find((r) => r.key === 'debtRatio')?.values ?? []);
		const annCr = lastNonNull(tfA.ratios.find((r) => r.key === 'currentRatio')?.values ?? []);
		// CCC 는 peer 비교에서 제외 · 회사값은 평균잔액, industryStats CCC 빌드 정의 미확인이라
		// 사과-오렌지 비교 위험(기관 무결성 지적). 부채비율·유동비율(정의 명확)만 업종 좌표화.
		const pc = peerCompareTable(
			[
				{ label: '부채비율', value: annDr, key: 'debtRatio', goodHigh: false, fmt: (v) => fmtPct(v) },
				{ label: '유동비율', value: annCr, key: 'currentRatio', goodHigh: true, fmt: (v) => fmtPct(v) }
			],
			peer
		);
		if (pc) {
			const drPh = pc.phrases.find((p) => p.label === '부채비율');
			const lead = drPh
				? `${corpName}의 부채비율(연간 ${drPh.valFmt})은 ${peer.name} 업종(유효표본 ${drPh.n}사·결손 제외) 중 안정성 ${topPctLabel(drPh)}로, 업종 중앙값(${drPh.median}) 대비 ${drPh.top <= 40 ? '재무가 견고한' : drPh.top <= 60 ? '중간 수준의' : '레버리지가 높은'} 편입니다. 절대 임계치(부채비율 200%)는 업종 무관 일반 기준이라, 자본집약 업종에서는 이 업종 분포 위치가 더 적절한 좌표입니다(목표주가·투자판단 아님).`
				: `아래는 ${peer.name} 분포 대비 안정성 위치입니다(연간 기준).`;
			sections.push({ key: 'peerSolvency', title: '동종업종 비교 -- 안정성은 업종에서 어디쯤', sourceEngine: 'industry', blocks: [{ type: 'text', text: lead }, pc.block] });
			if (drPh) findings.push({ key: '업종안정성', finding: `부채비율 ${peer.name} 업종(${drPh.n}사) 중 안정성 ${topPctLabel(drPh)} (중앙값 ${drPh.median}).`, sourceEngine: 'industry' });
		}
	}

	// ── S4 재무건전성 점검 (분기말 시점) ──
	const hTbl = healthTable([
		{ name: '부채비율', series: win.pick(rRow('debtRatio')), unit: '%', good: 'low', threshold: 200, thLabel: '200% 이하 (업종 무관 일반 기준)' },
		{ name: '유동비율', series: win.pick(rRow('currentRatio')), unit: '%', good: 'high', threshold: 100, thLabel: '100% 이상' },
		{ name: '이자보상배율', series: icr, unit: '배', good: 'high', threshold: 1, thLabel: '1배 이상' },
		{ name: '잉여현금흐름(FCF)', series: fcf, unit: '조', good: 'high', threshold: 0, thLabel: '0 이상' }
	]);
	if (hTbl) {
		const pass = { dr: drL != null && drL <= 200, cr: crL != null && crL >= 100, icr: icrL != null && icrL >= 1, fcf: fcfL != null && fcfL >= 0 };
		const nm: Record<string, string> = { dr: '레버리지(부채비율)', cr: '유동성(유동비율)', icr: '이자감당(이자보상배율)', fcf: '현금창출(FCF)' };
		const weak = (Object.keys(pass) as (keyof typeof pass)[]).filter((k) => !pass[k]);
		const strong = (Object.keys(pass) as (keyof typeof pass)[]).filter((k) => pass[k]);
		let synth =
			weak.length === 0
				? `네 축(레버리지·유동성·이자감당·현금창출)이 모두 기준을 충족해, 단일 축의 두드러진 취약점은 보이지 않습니다.`
				: `${weak.map((k) => nm[k]).join('·')}이(가) 기준에 미달해 이 회사 재무 안정성에서 먼저 살펴봐야 할 지점입니다${strong.length ? `, 반면 ${strong.map((k) => nm[k]).join('·')}은(는) 기준을 충족합니다` : ''}.`;
		// FCF 배당 충당 · 연간 기준(분기 FCF·배당은 lumpy).
		const divAnn = tfA ? lastNonNull((tfA.statements.CF.find((r) => r.key === 'dividendsPaid')?.values ?? []).map((v) => (v != null ? Math.abs(v as number) : null))) : null;
		const fcfAnnArr = tfA ? (tfA.statements.CF.find((r) => r.key === 'cfOperating')?.values ?? []).map((v, i) => { const cx = tfA.statements.CF.find((r) => r.key === 'capex')?.values?.[i]; return v != null ? (v as number) - (cx != null ? (cx as number) : 0) : null; }) : [];
		const fcfAnn = lastNonNull(fcfAnnArr);
		if (divAnn != null && (divAnn as number) > 0 && fcfAnn != null && (fcfAnn as number) > 0) {
			const cover = (fcfAnn as number) / (divAnn as number);
			synth += ` 연간 기준 잉여현금흐름(${fmtAmt1(fcfAnn)})은 배당지급(${fmtAmt1(divAnn as number)})의 ${cover >= 1 ? `${cover.toFixed(1)}배로 배당을 자체 잉여현금으로 충당할 수 있는 수준` : `${Math.round(cover * 100)}% 수준`}입니다.`;
		}
		const s3: ReportBlock[] = [
			{ type: 'text', text: `아래는 재무 안정성을 레버리지·유동성·이자감당·현금창출 4개 축으로 *나란히* 본 것입니다(${snapWord} 시점·이자감당은 ${kind}). 각 축은 독립이며 하나의 종합점수로 합치지 않습니다 · dartlab 정밀 신용등급(Python 7축 dCR)이 아니라 브라우저 재무비율 점검표입니다. 판정은 최신값 기준, 과거 미달 이력은 함께 표기합니다.` },
			hTbl,
			{ type: 'text', text: synth },
			{ type: 'text', text: `※ 이자보상배율은 영업이익÷금융비용으로 계산했습니다. 금융비용에는 이자비용 외 외화환산손실·평가손실 등이 섞일 수 있어 순수 이자비용 기준과 다를 수 있습니다(금융비용이 큰 자본집약 업종).` }
		];
		sections.push({ key: 'financialHealth', title: '재무건전성 점검 -- 어느 축이 견고하고 어느 축이 약한가', sourceEngine: 'analysis', blocks: s3 });
		const weakTag = weak.length ? ` · 약한 고리 ${weak.map((k) => nm[k].replace(/\(.*\)/, '')).join('·')}` : ' · 4축 모두 충족';
		findings.push({ key: '재무건전성', finding: `이자보상배율 ${fmtMult(icrL)} · 부채비율 ${fmtPct(drL)} · FCF ${fmtAmt1(fcfL)}${weakTag}.`, sourceEngine: 'analysis' });
	}

	// S5 채무 만기 사다리 (report.debtProfile · 데이터 있을 때만)
	const ladder = debt?.ladder ?? null;
	if (ladder && ladder.buckets.some((v) => v != null && (v as number) > 0)) {
		const W = 1e12; // 원 → 조
		const names = ['1년 이하', '1~2년', '2~3년', '3~4년', '4~5년', '5~10년', '10년 초과'];
		// 꼬리 빈 구간 절단 · 마지막 유효 만기 이후 연속 빈 행 제거(삼성처럼 단기 2칸만인 경우 휑한 표 방지).
		let lastFilled = 0;
		ladder.buckets.forEach((v, i) => { if (v != null && (v as number) > 0) lastFilled = i; });
		const barRows = ladder.buckets.slice(0, lastFilled + 1).map((v, i) => {
			const amt = v != null ? (v as number) / W : 0;
			return { label: names[i] ?? `구간${i + 1}`, value: amt, display: v != null && (v as number) > 0 ? fmtAmt1(amt) : '-' };
		});
		const stb = ladder.shortTerm != null ? fmtAmt1((ladder.shortTerm as number) / W) : '-';
		// 1년 이하 만기 집중도 · 차환 부담 한 줄.
		const total = barRows.reduce((s, r) => s + r.value, 0);
		const nearPct = total > 0 ? (barRows[0].value / total) * 100 : null;
		const concText = nearPct != null ? ` 1년 이하 만기가 사채의 ${fmtPct(nearPct)}로, ${nearPct >= 50 ? '단기 차환 부담이 큰' : nearPct >= 25 ? '단기 비중이 일부 있는' : '만기가 비교적 분산된'} 구조입니다.` : '';
		sections.push({
			key: 'debtLadder',
			title: '채무 만기 사다리 -- 언제 얼마를 갚아야 하나',
			sourceEngine: 'analysis',
			blocks: [
				{ type: 'text', text: `사채 만기를 잔존기간별로 나눈 것입니다(${ladder.year} 기준). 단기(1년 이하)에 몰려 있으면 차환 부담이 큽니다. 전자단기사채·CP 등 단기성 채무 합계는 ${stb} 입니다.${concText}` },
				{ type: 'bars', label: '사채 잔존만기 분포 (단위: 조원)', rows: barRows }
			]
		});
		findings.push({ key: '채무만기', finding: `단기성 채무 ${stb} · 1년 이하 만기 ${fmtAmt1((ladder.buckets[0] as number) / W)}.`, sourceEngine: 'analysis' });
	}

	const kpis: ReportModel['headlineKpis'] = [
		{ label: '부채비율', value: fmtPct(drL) },
		{ label: '자기자본비율', value: fmtPct(erL) },
		{ label: '유동비율', value: fmtPct(crL) },
		{ label: '이자보상배율', value: fmtMult(icrL) },
		{ label: '잉여현금흐름', value: fmtAmt1(fcfL) },
		{ label: '영업현금흐름', value: fmtAmt1(cfoL) }
	];
	const conclusion = `${corpName}의 최신 ${kind}(${lastP}) 영업현금흐름은 ${fmtAmt1(cfoL)}, 잉여현금흐름 ${fmtAmt1(fcfL)}입니다. ${snapWord} 부채비율 ${fmtPct(drL)}·유동비율 ${fmtPct(crL)}·이자보상배율 ${fmtMult(icrL)}로, 레버리지·유동성·이자감당·현금창출 네 축을 나란히 점검하면 재무 안정성의 강한 축과 약한 고리가 드러납니다(종합점수로 합치지 않습니다).`;
	const closing: ReportModel['closing'] = [
		{ label: '재무', engine: 'analysis', line: `${lastP} 부채비율 ${fmtPct(drL)} · 유동비율 ${fmtPct(crL)} · 이자보상배율 ${fmtMult(icrL)} · FCF ${fmtAmt1(fcfL)}. (분기 측정값, 투자판단 아님)` }
	];
	return { sections, findings, closing, kpis, conclusion };
}

// 연도 키 보고 데이터용 범용 표 · 행마다 이미 포맷된 문자열 셀.
function reportTable(years: string[], rows: { label: string; cells: string[] }[], labelHeader: string, caption: string): ReportBlock | null {
	const present = rows.filter((r) => r.cells.some((c) => c && c !== '-'));
	if (!present.length) return null;
	const data = present.map((r) => {
		const rec: Record<string, string> = { [labelHeader]: r.label };
		years.forEach((y, i) => {
			rec[y] = r.cells[i] ?? '-';
		});
		return rec;
	});
	return { type: 'table', label: caption, data };
}

// ── 관점 3: 주주와의 약속 (Capital Return & Dilution) ──────
function buildCapitalReturn(
	sr: ShareholderReturnYear[] | null,
	cc: CapitalChangesBundle | null,
	ctx: { corpName: string; niSeries: Num[]; yearCols: string[] }
): { sections: ReportSection[]; findings: ReportModel['keyFindings']; closing: ReportModel['closing']; kpis: ReportModel['headlineKpis']; conclusion: string } | null {
	const { corpName } = ctx;
	if (!sr || !sr.length) return null;
	const ys = sr.slice(-6);
	const yc = ys.map((y) => y.year);
	const latest = ys[ys.length - 1];
	// 배당은 주총 확정이 늦어 최신 연도가 비는 경우가 많다 → 배당 데이터가 있는 최근 연도 기준.
	const divYear = [...ys].reverse().find((y) => y.dps != null && Number.isFinite(y.dps as number)) ?? null;
	const divAsOf = divYear && divYear.year !== latest.year ? ` (${divYear.year} 기준)` : '';
	// 연도→순이익(조) 맵(누적 배당성향 계산용 · sr 연도와 tf 윈도 연도 매칭).
	const niByYear = new Map<string, number>();
	ctx.yearCols.forEach((y, i) => {
		const v = ctx.niSeries[i];
		if (v != null && Number.isFinite(v)) niByYear.set(y, v as number);
	});

	const sections: ReportSection[] = [];
	const findings: ReportModel['keyFindings'] = [];

	// S1 배당 정책
	const divTbl = reportTable(
		yc,
		[
			{ label: '주당배당금(DPS)', cells: ys.map((y) => fmtWon(y.dps)) },
			{ label: '배당성향', cells: ys.map((y) => fmtPct(y.payoutPct)) },
			{ label: '배당수익률', cells: ys.map((y) => fmtPct(y.yieldPct)) },
			{ label: '총배당금', cells: ys.map((y) => fmtWon(y.totalDividend)) }
		],
		'배당 지표',
		'배당 정책'
	);
	if (divTbl) {
		// 배당정책 성격 · 편차로 안정/변동 분류(한 해 값이 아니라 정책의 일관성을 읽음).
		const payoutSeries = finite(ys.map((y) => y.payoutPct));
		let policyText = '';
		if (payoutSeries.length >= 3) {
			const plo = Math.min(...payoutSeries);
			const phi = Math.max(...payoutSeries);
			const spread = phi - plo;
			policyText = spread > 30 ? ` 배당성향이 ${fmtPct(plo)}~${fmtPct(phi)}로 편차가 커, 이익에 연동해 움직이는(일관된 수준이라 보기 어려운) 정책입니다.` : spread > 12 ? ` 배당성향은 최근 ${fmtPct(plo)}~${fmtPct(phi)} 사이에서 움직였습니다.` : ` 배당성향은 ${fmtPct(plo)}~${fmtPct(phi)}로 비교적 안정적으로 유지됐습니다.`;
		}
		// 누적 배당성향 · Σ배당 / Σ순이익(분모 급변 해의 왜곡을 평탄화).
		let sumDiv = 0;
		let sumNi = 0;
		for (const y of ys) {
			const ni = niByYear.get(y.year);
			if (y.totalDividend != null && Number.isFinite(y.totalDividend as number) && ni != null && ni > 0) {
				sumDiv += y.totalDividend as number;
				sumNi += ni * 1e12;
			}
		}
		const cumPayout = sumNi > 0 ? (sumDiv / sumNi) * 100 : null;
		const cumText = cumPayout != null ? ` 최근 ${ys.length}년 누적으로는 순이익의 ${fmtPct(cumPayout)}를 배당으로 돌려줬습니다(연도별 분모 변동을 평탄화한 값).` : '';
		sections.push({
			key: 'dividend',
			title: '배당 정책 -- 주주에게 얼마를 돌려주나',
			sourceEngine: 'analysis',
			blocks: [
				{ type: 'text', text: `${corpName}의 배당입니다. 배당성향은 순이익 중 배당으로 나간 비율, 배당수익률은 주가 대비 배당입니다.${divYear ? ` 가장 최근 확정 배당은 주당 ${fmtWon(divYear.dps)}, 배당성향 ${fmtPct(divYear.payoutPct)}${divAsOf} 입니다.` : ''}${policyText}${cumText}${divAsOf ? ' 최신 회계연도 배당은 주주총회 확정 전이라 표에서 비어 있습니다.' : ''}` },
				divTbl
			],
			emph: true
		});
		if (divYear) findings.push({ key: '배당', finding: `DPS ${fmtWon(divYear.dps)} · 배당성향 ${fmtPct(divYear.payoutPct)}${cumPayout != null ? ` (누적 ${fmtPct(cumPayout)})` : ''} · 배당수익률 ${fmtPct(divYear.yieldPct)}${divAsOf}.`, sourceEngine: 'analysis' });
	}

	// S2 자사주 행동 · ★소각(영구) vs 기말 보유(금고주) 구분.
	// 자사주 수치는 공시상 양수 카운트(finTabs 계약) · 정정공시 합산으로 음수가 나오면 신뢰불가 → 보류.
	let suppressed = false;
	const cnt = (v: Num): string => {
		if (v != null && Number.isFinite(v) && (v as number) < 0) {
			suppressed = true;
			return '-';
		}
		return fmtShares(v);
	};
	const buyTbl = reportTable(
		yc,
		[
			{ label: '자사주 매입', cells: ys.map((y) => cnt(y.buybackQty)) },
			{ label: '자사주 처분', cells: ys.map((y) => cnt(y.disposalQty)) },
			{ label: '자사주 소각', cells: ys.map((y) => cnt(y.buybackCancel)) },
			{ label: '기말 보유(금고주)', cells: ys.map((y) => cnt(y.treasuryEnd)) }
		],
		'자사주(보통주)',
		'자사주 매입·소각·보유'
	);
	if (buyTbl) {
		// 자사주 패턴 읽기 · 섹션 제목('사서 태우나, 쌓아 두나')에 답한다(누적 소각 + 금고주 방향).
		const cancels = ys.map((y) => y.buybackCancel).filter((v): v is number => v != null && Number.isFinite(v) && v >= 0);
		const sumCancel = cancels.reduce((s, x) => s + x, 0);
		const treFirst = ys.find((y) => y.treasuryEnd != null && Number.isFinite(y.treasuryEnd as number) && (y.treasuryEnd as number) >= 0)?.treasuryEnd as number | undefined;
		const treLast = [...ys].reverse().find((y) => y.treasuryEnd != null && Number.isFinite(y.treasuryEnd as number) && (y.treasuryEnd as number) >= 0)?.treasuryEnd as number | undefined;
		const treWord = treFirst != null && treLast != null ? (treLast > treFirst * 1.05 ? '늘었습니다' : treLast < treFirst * 0.95 ? '줄었습니다' : '큰 변화가 없습니다') : null;
		const hasBuy = ys.some((y) => y.buybackQty != null && Number.isFinite(y.buybackQty as number) && (y.buybackQty as number) > 0);
		let pattern: string;
		if (sumCancel > 0 && (treWord === '줄었습니다' || treWord === '큰 변화가 없습니다' || treWord == null)) pattern = '매입한 자사주를 주로 *소각*해 영구 환원하는';
		else if (sumCancel > 0 && treWord === '늘었습니다') pattern = '소각과 금고주 적립을 *병행*하는';
		else if (treWord === '늘었습니다') pattern = '자사주를 소각보다 *금고주로 쌓아 두는*(향후 재매각 시 희석 가능)';
		else if (hasBuy || sumCancel > 0) pattern = '자사주 활동이 제한적인';
		else pattern = '최근 자사주 매입·소각이 거의 없는';
		const buyRead = ` 이 회사는 최근 ${ys.length}년 누적 소각 ${fmtShares(sumCancel)}, 기말 보유(금고주)는 ${treWord ?? '집계가 제한적'} · ${pattern} 모습입니다.`;
		// 금고주 잠재희석% · 기말 금고주 ÷ 발행주식수(순이익÷EPS 근사). 재매각 시 희석 폭(기관 지적).
		const shYear = [...ys].reverse().find((y) => { const ni = niByYear.get(y.year); return ni != null && y.eps != null && Number.isFinite(y.eps as number) && (y.eps as number) > 0; });
		const sharesEst = shYear ? (niByYear.get(shYear.year)! * 1e12) / (shYear.eps as number) : null;
		const dilPct = sharesEst != null && sharesEst > 0 && treLast != null && treLast >= 0 ? (treLast / sharesEst) * 100 : null;
		// 실현 희석(이미 처분된 자사주) vs 잠재 희석(기말 금고주) 구분 · 과거·미래 희석을 한 줄에 닫음.
		const sumDisp = finite(ys.map((y) => y.disposalQty)).filter((v) => v >= 0).reduce((a, b) => a + b, 0);
		const dilLine = dilPct != null && dilPct >= 0.05 ? ` 기말 금고주는 발행주식의 약 ${fmtPct(dilPct)}로, 전량 재매각 시 최대 ${fmtPct(dilPct)}만큼 희석될 수 있습니다(발행주식수는 순이익÷EPS로 근사).${sumDisp > 0 ? ` 한편 최근 ${ys.length}년 처분된 자사주 ${fmtShares(sumDisp)}는 이미 시장에 풀린 *실현* 희석이고, 기말 금고주는 향후 처분 시의 *잠재* 희석으로 구분해 봅니다.` : ''}` : '';
		const buyBlocks: ReportBlock[] = [
			{ type: 'text', text: `자사주 매입이 곧 주주환원은 아닙니다. 매입 후 *소각*하면 주식수가 영구히 줄어 주당 가치가 오르지만, *기말 보유(금고주)*로 쌓아 두면 나중에 다시 팔려 희석될 수 있습니다 · 둘을 구분해 봐야 합니다.${buyRead}${dilLine}` },
			buyTbl
		];
		if (suppressed)
			buyBlocks.push({ type: 'text', text: `※ 자사주 수치는 공시상 양수(주식 수)여야 하나, 정정공시 합산 등으로 순변동이 음수가 된 칸은 신뢰할 수 없어 표면화를 보류(−)했습니다.` });
		sections.push({ key: 'buyback', title: '자사주 행동 -- 사서 태우나, 쌓아 두나', sourceEngine: 'analysis', blocks: buyBlocks });
		const patternTag = sumCancel > 0 && treWord !== '늘었습니다' ? '소각 중심' : treWord === '늘었습니다' ? '금고주 적립' : '제한적';
		findings.push({ key: '자사주', finding: `누적 소각 ${fmtShares(sumCancel)} · 금고주 ${treWord ?? '제한적'} → ${patternTag}.`, sourceEngine: 'analysis' });
	}

	// S3 자본 변동·희석
	if (cc && cc.years.length) {
		const cy = cc.years.slice(-6);
		const cyc = cy.map((y) => String(y.year));
		const dilTbl = reportTable(
			cyc,
			[
				{ label: '유상증자', cells: cy.map((y) => fmtShares(y.paidIn)) },
				{ label: '전환권 행사', cells: cy.map((y) => fmtShares(y.conversion)) },
				{ label: '감자·소각', cells: cy.map((y) => fmtShares(y.reduction)) }
			],
			'자본 변동(주)',
			'발행주식 변동 (희석 ↔ 환원)'
		);
		if (dilTbl)
			sections.push({
				key: 'dilution',
				title: '자본 변동·희석 -- 주식 수는 늘었나 줄었나',
				sourceEngine: 'analysis',
				blocks: [
					{ type: 'text', text: `유상증자·전환권 행사는 주식 수를 늘려(희석), 감자·소각은 줄입니다(환원). 아래는 연도별 발행주식 변동입니다(주식 수 기준).` },
					dilTbl
				]
			});
		if (dilTbl) {
			// 순희석 방향 · 증자·전환(+) 대 감자·소각(−) 합산.
			let netShares = 0;
			for (const y of cy) netShares += (Number(y.paidIn) || 0) + (Number(y.conversion) || 0) + (Number(y.reduction) || 0);
			const dilDir = netShares > 0 ? '발행주식 순증(희석 우위)' : netShares < 0 ? '발행주식 순감(소각·감자 우위)' : '발행주식수 큰 변동 없음';
			findings.push({ key: '희석', finding: `최근 ${cy.length}년 ${dilDir}.`, sourceEngine: 'analysis' });
		}
	}

	const kpis: ReportModel['headlineKpis'] = [
		{ label: divYear ? `주당배당금${divAsOf}` : '주당배당금', value: fmtWon(divYear?.dps ?? null) },
		{ label: '배당성향', value: fmtPct(divYear?.payoutPct ?? null) },
		{ label: '배당수익률', value: fmtPct(divYear?.yieldPct ?? null) },
		{ label: '총배당금', value: fmtWon(divYear?.totalDividend ?? null) },
		{ label: `최근 소각 (${latest.year})`, value: cnt(latest.buybackCancel) },
		{ label: `기말 자사주 (${latest.year})`, value: cnt(latest.treasuryEnd) }
	];
	const conclusion = divYear
		? `${corpName} · 주당배당금 ${fmtWon(divYear.dps)}, 배당성향 ${fmtPct(divYear.payoutPct)}, 배당수익률 ${fmtPct(divYear.yieldPct)}${divAsOf}.`
		: `${corpName} · 최근 확정 배당 이력이 없습니다(무배당 또는 미확정). 자사주 정책 중심으로 정리했습니다.`;
	// ⚠ 종합 의견도 cnt() 경유 · 표·KPI 에서 보류(−)한 음수 소각값이 결론에서 새지 않게(C1).
	const closing: ReportModel['closing'] = [
		{ label: '재무', engine: 'analysis', line: divYear ? `배당성향 ${fmtPct(divYear.payoutPct)} · DPS ${fmtWon(divYear.dps)}${divAsOf} · 최근 자사주 소각 ${cnt(latest.buybackCancel)}.` : `배당 없음 · 최근 자사주 소각 ${cnt(latest.buybackCancel)}.` }
	];
	return { sections, findings, closing, kpis, conclusion };
}

// ── 관점 4: 시장평가 (Market & Valuation Context) ──────
// NEVER-CLAIM 위험 최대 · 목표주가·매수/매도·적정주가 환산 절대 금지. 측정값·맥락만.
function buildMarket(
	candles: Candle[] | null,
	marketCandles: Candle[] | null,
	sr: ShareholderReturnYear[] | null,
	ctx: { corpName: string; benchName: string; valPeer: ValPeer | null }
): { sections: ReportSection[]; findings: ReportModel['keyFindings']; closing: ReportModel['closing']; kpis: ReportModel['headlineKpis']; conclusion: string } | null {
	const { corpName, benchName, valPeer } = ctx;
	if (!candles || !candles.length) return null;
	const ps = priceSummary(candles);
	if (!ps) return null;
	const beta = marketCandles ? calcBeta(candles, marketCandles) : null;

	const sections: ReportSection[] = [];
	const findings: ReportModel['keyFindings'] = [];

	// S1 주가 궤적 · 이미 로드한 캔들로 가격 라인 직접 렌더(시장 관점에 차트 0은 결격).
	const won = (v: number) => `${Math.round(v).toLocaleString('en-US')}원`;
	const sortedC = [...candles].filter((c) => Number.isFinite(c.c) && c.c > 0).sort((a, b) => a.t.localeCompare(b.t));
	const winC = sortedC.slice(-250);
	const closes = winC.map((c) => c.c);
	const tvWin = winC.map((c) => c.tv).filter((v): v is number => v != null && Number.isFinite(v) && v > 0);
	const avgTv = tvWin.length ? tvWin.reduce((s, x) => s + x, 0) / tvWin.length : null;
	const s1blocks: ReportBlock[] = [
		{ type: 'text', text: `${corpName}의 최근 주가 흐름입니다. 아래는 가격 *사실*이며 매수·매도 의견이 아닙니다.` }
	];
	if (closes.length >= 8) {
		s1blocks.push({
			type: 'line',
			label: `최근 1년(약 ${winC.length}거래일) 종가`,
			series: downsample(closes, 80),
			xLabels: [winC[0].t.slice(0, 7).replace('-', '.'), winC[winC.length - 1].t.slice(0, 7).replace('-', '.')],
			markers: [
				{ label: '52주 최고', v: ps.hi },
				{ label: '52주 최저', v: ps.lo }
			],
			valueFmt: 'won'
		});
	}
	s1blocks.push({
		type: 'metrics',
		metrics: [
			{ label: '현재가', value: won(ps.last) },
			{ label: '52주 최고', value: won(ps.hi) },
			{ label: '52주 최저', value: won(ps.lo) },
			{ label: '1년 수익률', value: ps.ret1y != null ? fmtPctSigned(ps.ret1y * 100) : '-' },
			{ label: '일평균 거래대금', value: avgTv != null ? fmtAmt1(avgTv / 1e12) : '-' }
		]
	});
	// 이례적 수익률 선제 방어 · 분할·기준일 오정렬 의심 가드(데이터 신뢰 트리거).
	if (ps.ret1y != null && (ps.ret1y > 1.5 || ps.ret1y < -0.6))
		s1blocks.push({ type: 'text', text: `※ 1년 수익률 ${fmtPctSigned((ps.ret1y as number) * 100)}는 이례적으로 큽니다 · 액면분할·기준일 정렬·데이터 점검이 필요할 수 있습니다(분할 조정은 원천 데이터 책임). 절대 수익률보다 추세·변동성으로 읽으십시오.` });
	sections.push({ key: 'priceTrack', title: '주가 궤적 -- 시장은 어떻게 움직였나', sourceEngine: 'quant', blocks: s1blocks, emph: true });
	findings.push({ key: '주가', finding: `현재가 ${won(ps.last)} · 1년 ${ps.ret1y != null ? fmtPctSigned(ps.ret1y * 100) : '-'} · 52주 ${won(ps.lo)}~${won(ps.hi)}.`, sourceEngine: 'quant' });

	// S2 시장 동행성 (베타) · 코스피 대비 명시
	if (beta) {
		const lowR2 = beta.r2 < 0.2;
		const mag = beta.beta > 1.05 ? `${benchName}보다 약 ${Math.round((beta.beta - 1) * 100)}% 더 크게` : beta.beta < 0.95 ? `${benchName}보다 약 ${Math.round((1 - beta.beta) * 100)}% 덜` : `${benchName}과 거의 같은 폭으로`;
		const betaText = `베타는 시장(${benchName})이 1% 움직일 때 이 종목이 평균 몇 % 움직였는지를 회귀로 추정한 값입니다 · 즉 최근 ${beta.days}거래일 동안 ${mag} 움직였다는 *과거 사실*이며, 등락 방향을 예측하지 않습니다. (회귀 윈도 약 2년 · 위 1년 수익률과 측정 기간이 다릅니다. R² ${beta.r2.toFixed(2)}${lowR2 ? ' · 설명력이 낮아 참고용' : ''})`;
		sections.push({
			key: 'beta',
			title: '시장 동행성 -- 시장과 얼마나 함께 움직이나',
			sourceEngine: 'quant',
			blocks: [
				{ type: 'text', text: betaText },
				{
					type: 'metrics',
					metrics: [
						{ label: `베타 (${benchName} 대비)`, value: beta.beta.toFixed(2) },
						{ label: '설명력 (R²)', value: beta.r2.toFixed(2) },
						{ label: '관측 거래일', value: `${beta.days}일` }
					]
				}
			]
		});
		findings.push({ key: '위험', finding: `베타 ${beta.beta.toFixed(2)}(${benchName} 대비) · 설명력 R² ${beta.r2.toFixed(2)} · 관측 ${beta.days}일.`, sourceEngine: 'quant' });
	}

	// S3 밸류 맥락 · PER 자기역사(연말가/EPS). 적정주가 환산 금지.
	if (sr && sr.length) {
		const yec = yearEndCloses(candles);
		const ys = sr.slice(-6);
		const perCells = ys.map((y) => {
			const px = yec.get(y.year);
			if (px == null || y.eps == null || !Number.isFinite(y.eps as number) || (y.eps as number) <= 0) return '-';
			return fmtMult(px / (y.eps as number));
		});
		const yieldCells = ys.map((y) => fmtPct(y.yieldPct));
		const perTbl = reportTable(
			ys.map((y) => y.year),
			[
				{ label: 'PER (연말가÷EPS)', cells: perCells },
				{ label: '배당수익률', cells: yieldCells }
			],
			'밸류 지표',
			'밸류에이션 맥락 (자기역사)'
		);
		if (perTbl) {
			const perVals = perCells.map((c) => parseFloat(c)).filter((v) => Number.isFinite(v));
			// 현재 PER 의 자기역사 위치(하단/중단/상단) · 허용된 유일한 밸류 판단(타사·목표가 아님).
			const lastEpsV = [...ys].reverse().find((y) => y.eps != null && Number.isFinite(y.eps as number) && (y.eps as number) > 0);
			const curPerNum = lastEpsV ? ps.last / (lastEpsV.eps as number) : null;
			const band = curPerNum != null ? selfBand(curPerNum, perVals) : null;
			const bandText = band
				? ` 현재가 기준 PER ${fmtMult(curPerNum)}는 자기 ${perVals.length}년 범위(${band.lo.toFixed(1)}~${band.hi.toFixed(1)}배)의 ${band.band}에 있습니다 · 이 회사 기준으로는 ${band.band === '하단' ? '낮게' : band.band === '상단' ? '높게' : '중간 정도로'} 평가받는 구간입니다(타사 비교·목표주가 아님).`
				: perVals.length >= 2
					? ` 최근 PER는 자기 ${perVals.length}년 범위 ${Math.min(...perVals).toFixed(1)}~${Math.max(...perVals).toFixed(1)}배 안에서 움직였습니다.`
					: '';
			const valBlocks: ReportBlock[] = [
				{ type: 'text', text: `PER는 주가를 주당순이익(EPS)으로 나눈 배수로, 시장이 1원의 이익에 얼마를 매겼는지 보여줍니다. 여기서는 *적정주가를 환산하지 않고*, 이 회사 자신의 과거 PER 범위와만 비교합니다.${bandText}` },
				perTbl
			];
			// 주가 변동을 EPS(이익) × 멀티플(PER)로 분해 · 항등식, 인과·전망 아님.
			const yec2 = yec;
			const annual = ys
				.map((y) => ({ year: y.year, eps: y.eps, px: yec2.get(y.year) }))
				.filter((a) => a.eps != null && Number.isFinite(a.eps as number) && (a.eps as number) > 0 && a.px != null && Number.isFinite(a.px as number));
			if (annual.length >= 2) {
				const a0 = annual[annual.length - 2];
				const a1 = annual[annual.length - 1];
				const epsG = ((a1.eps as number) / (a0.eps as number) - 1) * 100;
				const multG = ((a1.px as number) / (a1.eps as number) / ((a0.px as number) / (a0.eps as number)) - 1) * 100;
				const priceG = ((a1.px as number) / (a0.px as number) - 1) * 100;
				const driver = Math.abs(epsG) >= Math.abs(multG) ? '이익(EPS) 변화' : '시장이 매긴 멀티플(PER) 변화';
				valBlocks.push({
					type: 'text',
					text: `${a0.year}→${a1.year} 연말 주가는 ${fmtPctSigned(priceG)} 변했는데, 이는 EPS ${fmtPctSigned(epsG)}와 멀티플(PER) ${fmtPctSigned(multG)}의 곱으로 분해됩니다 · ${driver}가 더 크게 작용했습니다(항등 분해이며 전망이 아닙니다).`
				});
			}
			valBlocks.push({ type: 'text', text: `※ 상단 KPI의 'PER(현재)'는 현재가 기준, 위 표는 각 연도의 *연말가* 기준이라 같은 해라도 값이 다를 수 있습니다. 주식 분할이 있던 회사는 연도 간 PER이 불연속으로 보일 수 있습니다(분할 조정은 원천 데이터 책임).` });
			sections.push({ key: 'valuation', title: '밸류에이션 맥락 -- 시장은 이익에 얼마를 매겼나', sourceEngine: 'quant', blocks: valBlocks });
			findings.push({ key: '밸류', finding: `PER ${band ? fmtMult(curPerNum) + ` (자기역사 ${band.band})` : perCells[perCells.length - 1]} · 배당수익률 ${yieldCells[yieldCells.length - 1]}.`, sourceEngine: 'quant' });
		}
	}

	// S3.5 동종업종 밸류에이션 위치 · valuation.parquet(네이버 per/pbr) 동종 분포 백분위(런타임 산출). 좌표일 뿐.
	if (valPeer && (valPeer.per.dist || valPeer.pbr.dist)) {
		const vrows: { label: string; v: Num; d: IndDist | null }[] = [
			{ label: 'PER', v: valPeer.per.v, d: valPeer.per.dist },
			{ label: 'PBR', v: valPeer.pbr.v, d: valPeer.pbr.dist }
		];
		const vdata: Record<string, string>[] = [];
		const vphrases: string[] = [];
		for (const r of vrows) {
			if (r.v == null || !Number.isFinite(r.v) || !r.d) continue;
			const pos = valuationPos(r.v, r.d);
			vdata.push({ 지표: r.label, 회사값: fmtMult(r.v), '업종 중앙값': fmtMult(r.d.median), '업종 내 위치': pos ? pos.label : '-' });
			if (pos) vphrases.push(`${r.label} ${fmtMult(r.v)} → 동종 ${pos.label}`);
		}
		if (vdata.length) {
			// 지표별 유효표본 분리 표기 · per 는 적자 제외로 pbr 보다 작을 수 있어 한 수(maxN)로 합치지 않는다(애널리스트 정직성).
			const perN = valPeer.per.dist?.n ?? 0;
			const pbrN = valPeer.pbr.dist?.n ?? 0;
			const nLabel = perN && pbrN ? `PER ${perN}·PBR ${pbrN}사` : `${Math.max(perN, pbrN)}사`;
			sections.push({
				key: 'valuationPeer',
				title: '동종업종 밸류에이션 -- 같은 업종 대비 비싼가 싼가',
				sourceEngine: 'industry',
				blocks: [
					{ type: 'text', text: `${corpName}의 PER·PBR을 같은 업종(${valPeer.industryName}) 분포와 비교한 *좌표*입니다. 높으면 시장이 이익·자산 1원에 더 많이(더 비싸게) 매긴 것이고, 낮으면 더 싸게 매긴 것입니다 · 성장 기대·이익 변동성·사업 위험이 반영된 결과이며 고평가/저평가 단정이나 매수·매도 의견이 아닙니다.` },
					{ type: 'table', label: `동종업종 밸류에이션 비교 · ${valPeer.industryName} (유효표본 ${nLabel}, 주체 제외·적자·결손·자본잠식 제외)`, snapshot: true, data: vdata },
					{ type: 'text', text: `※ 이 표의 PER/PBR은 일 1회 시장 스냅샷(네이버 기준, 최근 4분기 TTM)으로, 위 '밸류에이션 맥락(자기역사)'의 연말가÷연간EPS PER과는 시점·정의가 다릅니다. 적자 기업은 PER이 정의되지 않아 분포·표본에서 제외됩니다(PBR은 자본 기준이라 더 넓게 포함).` }
				]
			});
			findings.push({ key: '밸류비교', finding: vphrases.length ? vphrases.join(' · ') + '.' : 'PER·PBR 동종 좌표.', sourceEngine: 'industry' });
		}
	}

	const lastEps = sr ? [...sr].reverse().find((y) => y.eps != null && Number.isFinite(y.eps as number) && (y.eps as number) > 0) : null;
	const curPer = lastEps ? fmtMult(ps.last / (lastEps.eps as number)) : '-';
	const kpis: ReportModel['headlineKpis'] = [
		{ label: '현재가', value: won(ps.last) },
		{ label: '1년 수익률', value: ps.ret1y != null ? fmtPctSigned(ps.ret1y * 100) : '-' },
		{ label: `베타(${benchName})`, value: beta ? beta.beta.toFixed(2) : '-' },
		{ label: '설명력(R²)', value: beta ? beta.r2.toFixed(2) : '-' },
		{ label: 'PER(현재)', value: curPer },
		{ label: '배당수익률', value: fmtPct(lastEps?.yieldPct ?? (sr ? [...sr].reverse().find((y) => y.yieldPct != null)?.yieldPct ?? null : null)) }
	];
	const conclusion = `${corpName} · 현재가 ${won(ps.last)}, 1년 수익률 ${ps.ret1y != null ? fmtPctSigned(ps.ret1y * 100) : '-'}${beta ? `, 베타 ${beta.beta.toFixed(2)}(${benchName} 대비)` : ''}. (가격 사실 · 매수·매도 의견 아님)`;
	const closing: ReportModel['closing'] = [
		{ label: '시장', engine: 'quant', line: `${beta ? `베타 ${beta.beta.toFixed(2)} · ` : ''}1년 수익률 ${ps.ret1y != null ? fmtPctSigned(ps.ret1y * 100) : '-'} · PER ${curPer}. 가격·밸류 맥락이며 투자판단 아님.` }
	];
	return { sections, findings, closing, kpis, conclusion };
}

// ── 관점 5: 지배구조 (Ownership, People & Governance) ──
interface OwnershipData {
	shareholders: ShareholdersView | null;
	ownership: OwnershipYear[] | null;
	workforce: WorkforceYear[] | null;
	execBoard: ExecBoardYear[] | null;
	topExecPay: TopExecPay | null;
	auditTrail: AuditYear[] | null;
	auditFees: AuditFeeYear[] | null;
	investments: InvestmentsBundle | null;
}

function buildOwnership(
	d: OwnershipData,
	ctx: { corpName: string; fin: { revSeries: Num[]; oiSeries: Num[]; yearCols: string[] } }
): { sections: ReportSection[]; findings: ReportModel['keyFindings']; closing: ReportModel['closing']; kpis: ReportModel['headlineKpis']; conclusion: string } | null {
	const { corpName, fin } = ctx;
	const sections: ReportSection[] = [];
	const findings: ReportModel['keyFindings'] = [];
	// 연도→매출·영업이익(조) 맵 · 1인당 생산성 계산용(인력 연도와 재무 윈도 매칭).
	const revByYear = new Map<string, number>();
	const oiByYear = new Map<string, number>();
	fin.yearCols.forEach((y, i) => {
		const rv = fin.revSeries[i];
		const ov = fin.oiSeries[i];
		if (rv != null && Number.isFinite(rv)) revByYear.set(y, rv as number);
		if (ov != null && Number.isFinite(ov)) oiByYear.set(y, ov as number);
	});

	// S1 소유 구조
	const ow = d.ownership?.slice(-6) ?? [];
	let majorL: number | null = null;
	let minorL: number | null = null;
	if (ow.length) {
		const owTbl = reportTable(
			ow.map((y) => y.year),
			[
				{ label: '최대주주측 지분', cells: ow.map((y) => fmtPct(y.majorPct)) },
				{ label: '소액주주 지분', cells: ow.map((y) => fmtPct(y.minorPct)) },
				{ label: '소액주주 수', cells: ow.map((y) => fmtNum(y.minorCount, '명')) }
			],
			'소유 지표',
			'지분 분포 추이'
		);
		majorL = lastNonNull(ow.map((y) => y.majorPct)) as number | null;
		minorL = lastNonNull(ow.map((y) => y.minorPct)) as number | null;
		// 소유 집중도 방향(중립 서술 · 좋고 나쁨 아님).
		const majSeries = finite(ow.map((y) => y.majorPct));
		let concText = '';
		if (majSeries.length >= 3) {
			const f = majSeries[0];
			const l = majSeries[majSeries.length - 1];
			concText = l > f * 1.02 ? ` 최대주주측 지분이 ${fmtPct(f)}→${fmtPct(l)}로 높아져 소유가 더 집중되는 방향입니다.` : l < f * 0.98 ? ` 최대주주측 지분이 ${fmtPct(f)}→${fmtPct(l)}로 낮아져 소유가 다소 분산되는 방향입니다.` : ` 최대주주측 지분은 ${fmtPct(l)} 안팎에서 안정적입니다.`;
		}
		const s1: ReportBlock[] = [
			{ type: 'text', text: `${corpName}의 소유 구조입니다. 최대주주측 지분이 높으면 경영권은 안정적이나 소액주주 영향력은 작고, 소액주주 지분·주주 수가 많으면 그 반대입니다.${concText}` }
		];
		// 100% 누적 점유 막대 · 연도별 집중도를 한눈에(최대주주측·소액·기타).
		const shareRows = ow
			.filter((y) => y.majorPct != null && Number.isFinite(y.majorPct as number))
			.map((y) => {
				const mj = y.majorPct as number;
				const mn = y.minorPct != null && Number.isFinite(y.minorPct as number) ? (y.minorPct as number) : 0;
				const other = Math.max(0, 100 - mj - mn);
				return { year: y.year, segs: [{ label: '최대주주측', pct: mj, key: 'major' }, { label: '소액주주', pct: mn, key: 'minor' }, { label: '기타', pct: other, key: 'other' }] };
			});
		if (shareRows.length >= 2) {
			s1.push({ type: 'share', label: '지분 점유 추이 (연도별, %)', rows: shareRows, legend: [{ label: '최대주주측', key: 'major' }, { label: '소액주주', key: 'minor' }, { label: '기타', key: 'other' }] });
			// 최대주주측+소액주주 합이 100% 초과(원천 분류 중복 가능)면 정직 각주.
			if (ow.some((y) => y.majorPct != null && y.minorPct != null && (y.majorPct as number) + (y.minorPct as number) > 100.5))
				s1.push({ type: 'text', text: `※ 일부 연도는 최대주주측·소액주주 지분 합이 100%를 넘습니다(공시 원천의 분류 중복 가능) · 점유 막대는 비율 표시이며 각 수치는 공시 원값을 따릅니다.` });
		}
		if (owTbl) s1.push(owTbl);
		// control-shift 정직 플래그 · ≥5%p 변동은 본문 각주 + keyFindings 양쪽에.
		const first = ow.find((y) => y.majorPct != null)?.majorPct as number | undefined;
		const lastM = majorL;
		const shifted = first != null && lastM != null && Math.abs(lastM - first) >= 5;
		if (shifted)
			s1.push({ type: 'text', text: `※ 최대주주측 지분이 ${fmtPct(first)} → ${fmtPct(lastM)}로 ${Math.abs((lastM as number) - (first as number)).toFixed(1)}%p 변동했습니다 · 지배구조 변화 신호로 함께 보십시오.` });
		// 최대주주 개별(현재) · 방어 가드: person 분류 행은 실명 미노출(익명집계로만). 개인정보 레드라인.
		if (d.shareholders?.named?.length) {
			const top = d.shareholders.named.filter((r) => r.kind !== 'person').slice(0, 6);
			if (top.length)
				s1.push({
					type: 'table',
					label: `주요 주주 (${d.shareholders.year} 기준)`,
					snapshot: true,
					data: top.map((r) => ({ 주주: r.name, 관계: r.relate || '-', 지분율: fmtPct(r.ratio) }))
				});
			if (d.shareholders.person) s1.push({ type: 'text', text: `특수관계 개인 ${d.shareholders.person.count}인은 개인정보 보호로 익명 집계(합산 지분 ${fmtPct(d.shareholders.person.ratio)})했습니다.` });
		}
		sections.push({ key: 'ownershipStruct', title: '소유 구조 -- 누가 이 회사를 가졌나', sourceEngine: 'analysis', blocks: s1, emph: true });
		findings.push({ key: '소유', finding: `최대주주측 ${fmtPct(majorL)} · 소액주주 ${fmtPct(minorL)}${shifted ? ` · 지분 ${Math.abs((lastM as number) - (first as number)).toFixed(1)}%p 변동(지배구조 변화)` : ''}.`, sourceEngine: 'analysis' });
	}

	// S2 인력
	const wf = d.workforce?.slice(-6) ?? [];
	let perRevL: number | null = null;
	if (wf.length) {
		// 1인당 생산성 · 인력 분석의 핵심(린한 고마진사 vs 비대한 회사 구분). 재무 윈도와 연도 매칭.
		const perRevCells = wf.map((y) => {
			const rev = revByYear.get(y.year);
			return rev != null && y.total != null && (y.total as number) > 0 ? fmtPay((rev * 1e12) / (y.total as number)) : '-';
		});
		const perOiCells = wf.map((y) => {
			const oi = oiByYear.get(y.year);
			return oi != null && y.total != null && (y.total as number) > 0 ? fmtPay((oi * 1e12) / (y.total as number)) : '-';
		});
		const hasPer = perRevCells.some((c) => c !== '-');
		const lastWf = wf[wf.length - 1];
		const revLast = revByYear.get(lastWf.year);
		perRevL = revLast != null && lastWf.total != null && (lastWf.total as number) > 0 ? (revLast * 1e12) / (lastWf.total as number) : null;
		const rows = [
			{ label: '총원', cells: wf.map((y) => fmtNum(y.total, '명')) },
			{ label: '정규직', cells: wf.map((y) => fmtNum(y.regular, '명')) },
			{ label: '평균 급여', cells: wf.map((y) => fmtPay(y.avgSalary)) },
			{ label: '평균 근속', cells: wf.map((y) => (y.tenure != null ? `${(y.tenure as number).toFixed(1)}년` : '-')) }
		];
		if (hasPer) {
			rows.push({ label: '1인당 매출', cells: perRevCells });
			rows.push({ label: '1인당 영업이익', cells: perOiCells });
		}
		const wfTbl = reportTable(wf.map((y) => y.year), rows, '인력 지표', '인력·보상·생산성 추이');
		const perText = perRevL != null ? ` 직원 1인당 매출은 ${fmtPay(perRevL)} 수준으로, 인력 규모 대비 외형의 효율을 가늠하는 지표입니다(직군 구성에 따라 회사 간 단순 비교는 주의).` : '';
		if (wfTbl)
			sections.push({
				key: 'workforce',
				title: '인력 -- 누가 일하고 얼마를 받나',
				sourceEngine: 'analysis',
				blocks: [{ type: 'text', text: `직원 규모와 보상, 그리고 1인당 생산성입니다. 평균 급여는 급여총액을 인원으로 나눈 값입니다.${perText}` }, wfTbl]
			});
		if (wfTbl) findings.push({ key: '인력', finding: `총원 ${fmtNum(lastWf.total, '명')} · 평균급여 ${fmtPay(lastWf.avgSalary)}${perRevL != null ? ` · 1인당 매출 ${fmtPay(perRevL)}` : ''}.`, sourceEngine: 'analysis' });
	}

	// S3 이사회·보수
	const eb = d.execBoard?.slice(-6) ?? [];
	if (eb.length) {
		const ebTbl = reportTable(
			eb.map((y) => y.year),
			[
				{ label: '이사회 인원', cells: eb.map((y) => fmtNum(y.directors, '명')) },
				{ label: '사외이사', cells: eb.map((y) => fmtNum(y.outsideDirectors, '명')) },
				{ label: '사외이사 비율', cells: eb.map((y) => (y.directors != null && (y.directors as number) > 0 && y.outsideDirectors != null ? fmtPct(((y.outsideDirectors as number) / (y.directors as number)) * 100) : '-')) },
				{ label: '이사·감사 1인 평균보수', cells: eb.map((y) => fmtPay(y.execAvgPay)) }
			],
			'이사회 지표',
			'이사회 구성·보수 추이'
		);
		const lastEb0 = eb[eb.length - 1];
		const odRatio = lastEb0.directors != null && (lastEb0.directors as number) > 0 && lastEb0.outsideDirectors != null ? ((lastEb0.outsideDirectors as number) / (lastEb0.directors as number)) * 100 : null;
		const odText = odRatio != null ? ` 최근 사외이사 비율은 ${fmtPct(odRatio)}로 과반 권고 기준을 ${odRatio >= 50 ? '충족합니다' : '밑돕니다'}.` : '';
		const s3: ReportBlock[] = [{ type: 'text', text: `이사회 구성과 보수입니다. 사외이사 비율이 높을수록 경영진 견제 장치가 두텁다고 봅니다(과반이 권고 기준).${odText}` }];
		if (ebTbl) s3.push(ebTbl);
		// 상위 임원 보수(현재) · 스냅샷 표(시계열 아님)는 인셋 처리.
		if (d.topExecPay?.rows?.length) {
			const rows = d.topExecPay.rows.slice(0, 6);
			s3.push({ type: 'table', label: `상위 임원 보수 (${d.topExecPay.year} 기준)`, snapshot: true, data: rows.map((r) => ({ 임원: r.name, 직위: r.title || '-', 보수: fmtPay(r.pay) })) });
			// 임원-직원 보수 배수(거버넌스 표준 datapoint) · 직원 평균급여 대비.
			const empAvgL = lastNonNull(wf.map((y) => y.avgSalary)) as number | null;
			const payMult = d.topExecPay.avgPay != null && empAvgL != null && empAvgL > 0 ? (d.topExecPay.avgPay as number) / empAvgL : null;
			if (d.topExecPay.avgPay != null) s3.push({ type: 'text', text: `같은 해 이사·감사 1인 평균보수는 ${fmtPay(d.topExecPay.avgPay)}로, 직원 평균급여의 ${payMult != null ? `약 ${payMult.toFixed(1)}배` : '여러 배'}입니다 · 보수 격차를 함께 보십시오.` });
		}
		if (ebTbl) {
			sections.push({ key: 'board', title: '이사회·보수 -- 누가 견제하고 얼마를 받나', sourceEngine: 'analysis', blocks: s3 });
			const lastEb = eb[eb.length - 1];
			findings.push({ key: '이사회', finding: `이사회 ${fmtNum(lastEb.directors, '명')} · 사외이사 ${fmtNum(lastEb.outsideDirectors, '명')}${odRatio != null ? ` (${fmtPct(odRatio)}, 과반 ${odRatio >= 50 ? '충족' : '미달'})` : ''}.`, sourceEngine: 'analysis' });
		}
	}

	// S4 감사·외부출자
	const at = d.auditTrail?.slice(-6) ?? [];
	const af = d.auditFees?.slice(-1)?.[0] ?? null;
	if (at.length || af) {
		const s4: ReportBlock[] = [];
		if (at.length) {
			s4.push({ type: 'text', text: `감사 이력입니다. 감사의견이 '적정'이 아니거나 자주 바뀌면 회계 신뢰성을 따져봐야 합니다.` });
			s4.push({ type: 'table', label: '감사 의견 이력', snapshot: true, data: at.map((y) => ({ 사업연도: String(y.year), 감사인: y.auditor || '-', 감사의견: y.opinion || '-' })) });
			const nonClean = at.filter((y) => y.opinion && y.opinion !== '적정');
			if (nonClean.length) {
				s4.push({ type: 'text', text: `※ 적정이 아닌 감사의견(${nonClean.map((y) => `${y.year} ${y.opinion}`).join(', ')})이 있습니다 · 회계 신뢰성을 별도로 확인하십시오.` });
				findings.push({ key: '감사경보', finding: `적정 외 감사의견 ${nonClean.length}건(${nonClean.map((y) => `${y.year} ${y.opinion}`).join(', ')}) · 회계 신뢰성 점검 필요.`, sourceEngine: 'analysis' });
			}
			// 감사인 변경은 중립 사실로만 마킹(한국 주기적 지정감사=의무 로테이션이라 경보 아님).
			const auditors = [...new Set(at.map((y) => y.auditor).filter(Boolean))];
			if (auditors.length > 1) s4.push({ type: 'text', text: `감사인 변경: ${auditors.join(' → ')}. 한국은 주기적 지정감사 제도로 감사인 교체가 의무인 경우가 많아, 변경 자체가 부정 신호는 아닙니다.` });
		}
		const metrics: { label: string; value: string }[] = [];
		if (af) {
			metrics.push({ label: `감사보수 (${af.year})`, value: fmtPay(af.auditFee) });
			if (af.nonAuditFee != null) metrics.push({ label: '비감사보수', value: fmtPay(af.nonAuditFee) });
		}
		if (d.investments?.latest) {
			metrics.push({ label: `타법인 출자사 (${d.investments.latest.year})`, value: fmtNum(d.investments.latest.rows.length, '개사') });
			const book = d.investments.latest.rows.reduce((s, r) => s + ((r.bookValue as number) || 0), 0);
			if (book > 0) metrics.push({ label: '출자 장부가 합계', value: fmtPay(book) });
		}
		if (metrics.length) s4.push({ type: 'metrics', metrics });
		if (s4.length) {
			sections.push({ key: 'audit', title: '감사·외부출자 -- 회계는 믿을 만한가', sourceEngine: 'analysis', blocks: s4 });
			const lastAt = at[at.length - 1];
			if (lastAt) findings.push({ key: '감사', finding: `${lastAt.year} 감사의견 ${lastAt.opinion || '-'} (${lastAt.auditor || '-'}).`, sourceEngine: 'analysis' });
		}
	}

	if (!sections.length) return null;

	const lastAt = at[at.length - 1];
	const wfTotalL = lastNonNull(wf.map((y) => y.total));
	const wfSalaryL = lastNonNull(wf.map((y) => y.avgSalary));
	const odL = lastNonNull(eb.map((y) => y.outsideDirectors));
	const totalStr = wf.length ? fmtNum(wfTotalL, '명') : '-';
	const odStr = eb.length ? fmtNum(odL, '명') : '-';
	const kpis: ReportModel['headlineKpis'] = [
		{ label: '최대주주측 지분', value: fmtPct(majorL) },
		{ label: '소액주주 지분', value: fmtPct(minorL) },
		{ label: '총원', value: totalStr },
		{ label: '평균 급여', value: wf.length ? fmtPay(wfSalaryL) : '-' },
		{ label: '사외이사', value: odStr },
		{ label: '감사의견', value: lastAt?.opinion || '-' }
	];
	const conclusion = `${corpName} · 최대주주측 지분 ${fmtPct(majorL)}, 총원 ${totalStr}${lastAt ? `, ${lastAt.year} 감사의견 ${lastAt.opinion || '-'}` : ''}.`;
	const closing: ReportModel['closing'] = [
		{ label: '재무', engine: 'analysis', line: `최대주주측 ${fmtPct(majorL)} · 총원 ${totalStr} · 사외이사 ${odStr}${lastAt ? ` · 감사의견 ${lastAt.opinion || '-'}` : ''}.` }
	];
	return { sections, findings, closing, kpis, conclusion };
}

// ── 미구현 관점 · 정직 '준비 중' ───────────────────────────
function pendingModel(
	code: string,
	corpName: string,
	industry: string | undefined,
	persp: PerspectiveMeta,
	asOf: string,
	dataBasis: string
): ReportModel {
	return {
		stockCode: code,
		corpName,
		asOf,
		dataBasis,
		industry,
		perspectiveKey: persp.key,
		perspectiveLabel: persp.label,
		conclusion: `「${persp.label}」 관점은 다음 사이클에서 구현됩니다.`,
		headlineKpis: [],
		narrativeOverview: '',
		keyFindings: [],
		sections: [],
		closing: [],
		provenance: { engines: {}, note: '' },
		assumptionsNote: '',
		qualityLabel: 'conditional',
		focusQuestions: persp.focusQuestions,
		pending: true
	};
}

// ── 진입점 ─────────────────────────────────────────────────
export async function buildReport(
	rt: DartLabRuntime,
	code: string,
	perspectiveKey: string
): Promise<ReportResult> {
	const persp = findPerspective(perspectiveKey);
	// 회사명·업종 = map/search-index.json (데이터 작업대 loadJson 직독). public search.universe 미배선.
	const [fin, universe, indStats] = await Promise.all([
		rt.finance.bundle(code),
		loadJson<IndexRow[]>('map/search-index.json', { fetchFn: fetch, preferLocal: true }).catch(() => null),
		loadJson<Record<string, { name: string; count: number; distribution: Record<string, IndDist | null> }>>('map/industryStats.json', { fetchFn: fetch, preferLocal: true }).catch(() => null)
	]);
	const meta = (universe ?? []).find((r) => r.stockCode === code);
	const corpName = meta?.corpName ?? code;
	const industry = meta?.industry || undefined;
	// 동종업종 백분위 · search-index industry 키 === industryStats 키. 분포 있으면 peer 좌표 제공.
	const peer: PeerCtx | null = industry && indStats?.[industry] ? { name: indStats[industry].name, count: indStats[industry].count, dist: indStats[industry].distribution } : null;

	if (!fin) return { skipped: true, stockCode: code, reason: '재무 데이터셋이 없습니다(미상장·미공시).' };
	const tf = annualView(fin); // 연간 · 연 1회 확정 항목(배당·소유·인력·감사) + 장기추세 보충 섹션
	const tfQ = fin.views.quarter ?? null; // 분기 · 손익·현금·효율 본문의 주(主) 시간축
	const tfT = fin.views.ttm ?? null; // TTM · 직전 4분기 합(계절성 평탄화 절대수준)
	if ((!tf || !tf.periods.length) && (!tfQ || !tfQ.periods.length))
		return { skipped: true, stockCode: code, reason: '재무 데이터가 없습니다.' };

	// scope 명시(기관 요구) · 번들 기본은 연결(CFS). 별도만 보고한 회사는 별도.
	const scope = fin.scope === 'OFS' ? '별도' : '연결';
	const scopeNote = fin.availScopes.length > 1 ? `${scope}재무제표 기준(별도재무제표 별도 보고)` : `${scope}재무제표 기준`;
	// 분기 표는 6분기(+TTM·YoY 열)까지만 · 8분기는 라벨+8+TTM+YoY 가 본문폭을 넘어 가로 스크롤이 생긴다.
	// 최신 분기 YoY 는 4분기 전(윈도 내)과 비교하므로 6분기로도 충분.
	const qw = tfQ ? quarterWindow(tfQ, 6) : null;

	const asOf = latestFiled(fin) ?? (tf ? pYear(last(tf.periods)) : '');
	const dataBasis = qw ? `${qw.periods[qw.periods.length - 1]} (분기 · ${scope})` : tf ? `FY${pYear(last(tf.periods)).slice(2)} (연간 · ${scope})` : `(${scope})`;

	if (!persp.built) return pendingModel(code, corpName, industry, persp, asOf, dataBasis);

	// 연간 슬라이스(연 1회 확정 항목 + 장기추세 보충용)
	const n = tf ? Math.min(6, tf.periods.length) : 0;
	const idx = tf ? Array.from({ length: n }, (_, k) => tf.periods.length - n + k) : [];
	const yearCols = idx.map((i) => pYear(tf!.periods[i]));
	const pick = (values: Num[]): Num[] => idx.map((i) => values[i] ?? null);

	// 본문 시간축 · 분기 우선, 없으면 연간. 재무 챕터(수익성·재무안정성)가 공유.
	const win = qw ?? (tf ? annualWindow(tf) : null);
	const tfWin = qw ? tfQ : tf;
	const winKind: '분기' | '연간' = qw ? '분기' : '연간';
	let built;
	if (persp.key === 'liquidity') {
		if (!tfWin || !win) return { skipped: true, stockCode: code, reason: '재무 시계열이 부족합니다.' };
		const [debt, sr] = await Promise.all([
			rt.report.debtProfile(code).catch(() => null),
			rt.report.shareholderReturn(code).catch(() => null)
		]);
		built = buildLiquidity(tfWin, win, winKind, tf, winKind === '분기' ? tfT : null, { corpName, peer }, debt, sr);
	} else if (persp.key === 'capitalReturn') {
		const [sr, cc] = await Promise.all([
			rt.report.shareholderReturn(code).catch(() => null),
			rt.report.capitalChanges(code).catch(() => null)
		]);
		built = buildCapitalReturn(sr, cc, { corpName, niSeries: pick(tf?.statements.IS.find((r) => r.key === 'netIncome')?.values ?? []), yearCols });
	} else if (persp.key === 'market') {
		// 벤치마크 = 상장시장(markets.json)별 · 코스닥 종목에 코스피를 들이대지 않게(R1).
		const markets = await loadJson<Record<string, string>>('map/markets.json', { fetchFn: fetch, preferLocal: true }).catch(() => null);
		const mkt = markets?.[code] ?? '';
		const isKosdaq = mkt.startsWith('KOSDAQ');
		const benchRef = isKosdaq ? KR_INDEX_PRESETS[2] : KR_INDEX_PRESETS[0]; // 코스닥 : 코스피
		const benchName = isKosdaq ? '코스닥' : '코스피';
		const [candles, marketCandles, sr, valSnap] = await Promise.all([
			rt.price.govCandles(code).catch(() => null),
			rt.index.series(benchRef).catch(() => null),
			rt.report.shareholderReturn(code).catch(() => null),
			rt.report.valuationSnapshot().catch(() => null)
		]);
		const valPeer = buildValPeer(valSnap, universe, code, industry, peer?.name);
		built = buildMarket(candles, marketCandles, sr, { corpName, benchName, valPeer });
	} else if (persp.key === 'ownership') {
		const [shareholders, ownership, workforce, execBoard, topExecPay, auditTrail, auditFees, investments] = await Promise.all([
			rt.report.shareholders(code).catch(() => null),
			rt.report.ownership(code).catch(() => null),
			rt.report.workforce(code).catch(() => null),
			rt.report.execBoard(code).catch(() => null),
			rt.report.topExecPay(code).catch(() => null),
			rt.report.auditTrail(code).catch(() => null),
			rt.report.auditFees(code).catch(() => null),
			rt.report.investments(code).catch(() => null)
		]);
		built = buildOwnership(
			{ shareholders, ownership, workforce, execBoard, topExecPay, auditTrail, auditFees, investments },
			{
				corpName,
				fin: {
					revSeries: pick(tf?.statements.IS.find((r) => r.key === 'revenue')?.values ?? []),
					oiSeries: pick(tf?.statements.IS.find((r) => r.key === 'operatingIncome')?.values ?? []),
					yearCols
				}
			}
		);
	} else {
		// 수익성 · 분기 우선 본문 + 연간 보충
		if (!tfWin || !win) return { skipped: true, stockCode: code, reason: '재무 시계열이 부족합니다.' };
		built = buildEarningsPower(tfWin, win, tf, winKind === '분기' ? tfT : null, winKind, { corpName, peer });
	}
	if (!built || !built.sections.length)
		return { skipped: true, stockCode: code, reason: '이 관점에 채울 데이터가 부족합니다(예: 무배당 기업).' };

	// 출처 = 섹션 sourceEngine 별 정직 집계(재무/시장 혼재 시 각각).
	const ENG_LABEL: Record<string, string> = {
		analysis: '재무분석',
		quant: '시장·기술',
		credit: '신용평가',
		industry: '산업비교',
		macro: '거시',
		story: '종합서사'
	};
	const engAgg: Record<string, { label: string; sections: number; blocks: number }> = {};
	for (const s of built.sections) {
		const e = s.sourceEngine;
		if (!engAgg[e]) engAgg[e] = { label: ENG_LABEL[e] ?? e, sections: 0, blocks: 0 };
		engAgg[e].sections++;
		engAgg[e].blocks += s.blocks.length;
	}

	return {
		stockCode: code,
		corpName,
		asOf,
		dataBasis,
		industry,
		perspectiveKey: persp.key,
		perspectiveLabel: persp.label,
		conclusion: built.conclusion,
		headlineKpis: built.kpis,
		narrativeOverview: `이 보고서는 ${corpName}의 ${persp.label} · ${persp.question} · 를 ${scopeNote}으로 정리했습니다. 손익·현금·효율은 ${qw ? '분기(전년동기 YoY)를 주(主)로, 장기 그림은 연간 보충 섹션' : '연간'}으로 보며, 배당·소유·인력·감사 등 연 1회 확정 항목은 사업보고서(연간) 기준입니다.`,
		keyFindings: built.findings,
		sections: built.sections,
		closing: built.closing,
		provenance: {
			engines: engAgg,
			note: `재무·주가·정기보고 공시를 ${scope}재무제표 기준으로 계산했습니다.`
		},
		assumptionsNote:
			`${scopeNote} · 손익·현금흐름은 ${qw ? '단일분기(누계 YTD는 차분 정규화)·전년동기(YoY) 비교·TTM(직전 4분기 합) 병기' : '연간'} · 재무상태표는 기말 시점값 · 수익성 비율의 연율화는 연간 기준(분기 단독 연율화 안 함) · 운전자본 회전일은 평균잔액·${qw ? '분기(91일)' : '연간(365일)'} 기준이라 계절성 영향 · 동종업종 백분위는 industryStats 분포(연간) 대비 좌표(목표주가 아님) · 사업부문(세그먼트) 분해는 공시 주석 인코딩 의존으로 이 버전에서는 제공하지 않습니다(추정 대신 비표기) · 표 단위는 자릿수에 따라 조/억 자동 스케일 · 공시 항목이 빈약한 행은 자동 생략 · 일회성 손익이 큰 기간은 각주 표시 · 재무건전성 점검은 브라우저 재무비율(Python 신용등급 dCR 아님)${qw && qw.excluded.length ? ` · ⚠ 최신 ${qw.excluded.map((e) => e.period).join('·')}는 영업이익률이 본업 범위를 크게 벗어나(데이터 정합성 의심) 분석 윈도에서 제외` : ''}.`,
		qualityLabel: built.sections.length >= 3 ? 'verified' : 'conditional',
		focusQuestions: persp.focusQuestions
	};
}

// ── 5관점 통합 리드 (Executive Overview) · 보고서를 한 몸으로 묶는 thesis + 관점별 한 줄 ──
// 5관점을 모두 빌드(fetch 는 런타임 캐시 공유)해 관점을 *교차*한 긴장 서술을 만든다.
// 종합점수·매수의견 아님 · 사실의 교차(마진 위치 vs 환원 강도 vs 밸류 위치)일 뿐.
// 구조화 thesis · 정규식 산문(thesis: string) 폐기 후계. 관점 ReportModel 들에서 중심논거·
// 지지기둥·약세론·트리거·콜을 결박해 계약 Thesis 로. Python story.thesis.buildThesis 와 동일
// 계약(#5 drift-pinned) · TS 측은 관점 결론을, Python 측은 ROIC−WACC 메커니즘을 central 로.
function buildThesisStruct(built: ReportModel[]): Thesis {
	const m = (k: string) => built.find((r) => r.perspectiveKey === k);
	const findOf = (r: ReportModel | undefined, k: string): string => r?.keyFindings.find((f) => f.key === k)?.finding ?? '';
	const ep = m('earningsPower');
	const mk = m('market');
	const first = built[0];

	const central = (ep?.conclusion || first.conclusion || '').trim();

	const pillarOrder = ['earningsPower', 'liquidity', 'capitalReturn', 'market'];
	const pillars: ThesisPillar[] = [];
	for (const key of pillarOrder) {
		const r = m(key);
		if (r?.conclusion && pillars.length < 3) pillars.push({ claim: r.conclusion.trim(), sectionKey: key, refs: [] });
	}

	const valBand = /자기역사\s*(하단|중단|상단)/.exec(findOf(mk, '밸류'))?.[1] ?? null;
	const bearCase = valBand
		? `시장은 이를 자기 PER ${valBand}에 반영 중 · 밸류 ${valBand} 재평가가 논지 시험대`
		: (mk?.conclusion?.trim() ?? '');

	const triggers = built.flatMap((r) => r.focusQuestions ?? []).slice(0, 4);
	const call = mk?.conclusion?.trim() || null;

	return { central, pillars, bearCase, triggers, call };
}

export async function buildOverview(rt: DartLabRuntime, code: string): Promise<OverviewModel | null> {
	const results = await Promise.all(
		PERSPECTIVES.map((p) =>
			buildReport(rt, code, p.key)
				.then((r) => (isSkipped(r) ? null : r))
				.catch(() => null)
		)
	);
	const built = results.filter((r): r is ReportModel => r != null);
	if (!built.length) return null;
	const first = built[0];
	const takes: OverviewTake[] = built.map((r) => ({ key: r.perspectiveKey, label: r.perspectiveLabel, line: r.conclusion, engine: r.sections[0]?.sourceEngine ?? 'analysis' }));

	// 관점 교차 thesis · 내가 만드는 finding 포맷에서 앵커 추출(안전 폴백).
	const m = (k: string) => built.find((r) => r.perspectiveKey === k);
	const findOf = (r: ReportModel | undefined, k: string): string => r?.keyFindings.find((f) => f.key === k)?.finding ?? '';
	const ep = m('earningsPower');
	const li = m('liquidity');
	const cr = m('capitalReturn');
	const mk = m('market');
	const marginTop = /영업이익률[^상하]*((?:상|하)위[^·.]+)/.exec(findOf(ep, '업종비교'))?.[1]?.trim() ?? null;
	const drTop = /안정성\s*((?:상|하)위[^(]+)/.exec(findOf(li, '업종안정성'))?.[1]?.trim() ?? null;
	const payout = /배당성향\s*([\d.]+%)/.exec(findOf(cr, '배당'))?.[1] ?? null;
	const payoutNum = payout ? parseFloat(payout) : null;
	const valBand = /자기역사\s*(하단|중단|상단)/.exec(findOf(mk, '밸류'))?.[1] ?? null;

	const parts: string[] = [`${first.corpName}를 ${PERSPECTIVES.map((p) => p.label).join('·')} 다섯 관점으로 봤습니다.`];
	const clauses: string[] = [];
	if (marginTop) clauses.push(`수익력은 동종업종 ${marginTop}로 업종 상위권`);
	if (drTop) clauses.push(`재무 안정성은 ${drTop}`);
	if (clauses.length) parts.push(clauses.join('이고, ') + '입니다.');
	const tail: string[] = [];
	if (payoutNum != null) tail.push(`다만 주주환원은 배당성향 ${payout}로 ${payoutNum < 30 ? '이익체력 대비 보수적' : payoutNum > 60 ? '적극적' : '중간 수준'}`);
	if (valBand) tail.push(`시장은 이를 자기 PER ${valBand}에 반영`);
	if (tail.length) parts.push(tail.join('이고, ') + '하고 있습니다.');
	const thesis = parts.join(' ');

	return { corpName: first.corpName, stockCode: code, asOf: first.asOf, dataBasis: first.dataBasis, industry: first.industry, thesis, thesisStruct: buildThesisStruct(built), takes };
}
