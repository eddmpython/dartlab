import { readFileSync } from 'node:fs';
import { describe, expect, it } from 'vitest';
import { MACRO_SERIES, type MacroLatest } from '@dartlab/ui-contracts';
import { CURRENT_MACRO_EDGE_SECTOR_KEYS, EDGE_SECTOR_TO_TAILWIND } from './macroMappings';
import {
	agreementOf,
	bucketOf,
	buildExposureMatrixRows,
	buildMacroEvidenceCards,
	buildMacroSimView,
	MACRO_EVIDENCE_SPECS,
	buildMacroGlanceView,
	buildMacroLensSnapshot,
	buildMacroPath,
	buildMarketMacroLensSnapshot,
	buildRegimeQuadrant,
	buildRegimeView,
	focusChannelAlignment,
	pickFocusCell,
	transitionFraction,
	type MacroChannel,
	type MacroDriverView,
	type MacroExposureMatrixRow,
	type MacroTransmissionEdgeView
} from './macroLens';
import type { Company, MacroFile, MacroRegimeModel, MacroRegimePayload, MacroSide } from './types';

const macro = JSON.parse(
	readFileSync(new URL('../../../../../../landing/static/dashboards/macro.json', import.meta.url), 'utf8')
) as MacroFile;

const CHANNELS: MacroChannel[] = ['revenue', 'margin', 'balanceSheet', 'cashFlow', 'valuation'];

const sectorTailwinds = () =>
	Object.entries(EDGE_SECTOR_TO_TAILWIND).flatMap(([sectorKey, map]) => {
		const tailwindKey = map.tailwindKey;
		if (!tailwindKey) return [];
		const tw = macro.sectorTailwind[tailwindKey];
		if (!tw) return [];
		return [{
			id: map.industryId ?? sectorKey,
			kr: map.kr,
			en: map.en,
			tailwindKey,
			blended: tw.blended
		}];
	});

const macroLatest = (): MacroLatest[] =>
	(macro.transmission?.drivers ?? []).flatMap((driver) => {
		const def = MACRO_SERIES.find((series) => series.id === driver.id);
		if (!def) return [];
		const date = driver.sourceLineage?.date?.replaceAll('-', '') || '20260618';
		const value = driver.sourceLineage?.value ?? 1;
		return [{
			def,
			v: value,
			d: date,
			chg: 1,
			spark: [value - 2, value - 1, value]
		}];
	});

const cloneMacro = (): MacroFile => JSON.parse(JSON.stringify(macro)) as MacroFile;

const companyFixture = (overrides: Partial<Company> = {}): Company => ({
	code: '005930',
	marketLabel: 'KOSPI',
	name: { kr: '삼성전자', en: 'Samsung Electronics' },
	sector: { kr: '반도체', en: 'Semiconductor' },
	industry: 'semiconductor',
	stage: '',
	role: '',
	eco: { id: '005930', label: '삼성전자', industry: 'semiconductor' },
	grades: [],
	radar: [],
	changes: [],
	price: {
		last: 70000,
		mktcap: '0',
		mktcapRaw: 0,
		ret1m: null,
		ret3m: null,
		ret1y: null,
		vol1y: null,
		hi52: null,
		lo52: null,
		vol: null,
		asOf: '2026-06-18'
	},
	fundamentals: { per: null, pbr: null, psr: null, npm: null, roe: null, opm: 12, dr: 40 },
	financials: {
		years: [],
		sales: [],
		op: [],
		net: [],
		opMargin: [],
		netMargin: [],
		roe: [],
		assetTurn: [],
		equityMult: [],
		deRatio: [],
		currRatio: [],
		dupont: { netMargin: null, assetTurn: null, equityMult: null, roe: null },
		assetMix: [],
		fundMix: [],
		cf: { op: null, inv: null, fin: null, fcf: null }
	},
	trendAnnual: { periods: ['2025'], sales: [], op: [], net: [], opMargin: [], freq: 'annual' },
	trendQuarter: null,
	income: { periods: [], rows: [] },
	balance: { periods: [], rows: [] },
	cashflow: { periods: [], rows: [] },
	ratios: [],
	credit: { grade: 'NA', healthScore: 0, pd: '·', tone: 'neutral', tracks: [], basis: { debtRatio: null, curr: null, opm: null } },
	analysis: { summary: { kr: '', en: '' }, tracks: [] },
	macroExposure: null,
	peers: [],
	story: null,
	percentile: null,
	valuation: null,
	risks: [],
	riskCatalog: [],
	tailwind: null,
	verdict: { composite: 0, band: { kr: '', en: '', tone: 'neutral' }, strengths: [], concerns: [], riskRed: 0, riskYellow: 0 },
	...overrides
} as unknown as Company);

// 합성 driver/edge stub · buildExposureMatrixRows/pickFocusCell가 읽는 필드만 채운다(나머지 cast).
const mkDriver = (id: string, relevance: MacroDriverView['relevance'] = 'secondary'): MacroDriverView =>
	({ id, label: id, relevance } as unknown as MacroDriverView);
const mkEdge = (
	driverId: string,
	channel: MacroChannel,
	evidenceLevel: MacroTransmissionEdgeView['evidenceLevel'],
	confidence: MacroTransmissionEdgeView['confidence'] = 'medium',
	extra: Partial<MacroTransmissionEdgeView> = {}
): MacroTransmissionEdgeView =>
	({ id: `${driverId}-${channel}`, driverId, channel, evidenceLevel, confidence, financialLine: `${channel} line`, valuationLever: 'growth', sign: 'positive', lagMonths: [1, 6], ...extra } as unknown as MacroTransmissionEdgeView);

describe('macroLens builders · current macro v19 artifact (redesign)', () => {
	it('builds a 2x2 regime model without leaking raw coordinate signals', () => {
		const view = buildRegimeQuadrant(macro);
		expect(view.cells.map((cell) => cell.key).sort()).toEqual(['deflation', 'goldilocks', 'reflation', 'stagflation']);

		const kr = view.markets.find((market) => market.market === 'KR')!;
		const us = view.markets.find((market) => market.market === 'US')!;
		expect(kr.cellKey).toBe('stagflation');
		expect('growthSignal' in kr).toBe(false);
		expect('inflationSignal' in kr).toBe(false);
		expect(us.cellKey).toBe('reflation');
	});

	it('builds the macro transmission rail from macro.transmission without all-sector fanout', () => {
		const path = buildMacroPath(macro.transmission, sectorTailwinds(), { mode: 'full', activeIndustryId: 'logistics' });
		expect(path.mode).toBe('full');
		expect(path.links.length + path.allSectorLinks.length).toBe(macro.transmission!.edges.length);
		expect([...path.coverageKeys].sort()).toEqual([...CURRENT_MACRO_EDGE_SECTOR_KEYS].sort());
	});

	it('builds a market-only glance before a company is selected', () => {
		const view = buildMacroGlanceView(macro, sectorTailwinds(), { mode: 'compact' });
		// asOf 는 빌드 시점(재빌드마다 변동) · 날짜 형태만 단언(하드코딩 결합 회피).
		expect(view.asOf).toMatch(/^\d{4}-\d{2}-\d{2}$/);
		expect(view.regime.markets).toHaveLength(2);
		expect(view.path.links.length).toBeGreaterThan(0);
		expect(view.sectorTailwinds.length).toBeGreaterThan(0);
	});
});

describe('macroLens snapshot · verdict layer removed, evidence gates kept', () => {
	it('produces no verdict layer and no single macro score', () => {
		const snapshot = buildMarketMacroLensSnapshot({
			macro,
			macroLatest: macroLatest(),
			sectorTailwinds: sectorTailwinds()
		});
		expect(snapshot.marketOnly).toBe(true);
		expect('verdict' in snapshot).toBe(false);
		// 단일 macro score / 방향점수 / /100 표면화 0 (verdict 부활 가드).
		const json = JSON.stringify(snapshot);
		expect(json).not.toContain('directionScore');
		expect(json).not.toContain('evidenceScore');
		expect(json).not.toContain('claimLevel');
	});

	it('blocks the macroData gate when a critical primary macro driver is stale', () => {
		const staleLatest = macroLatest().map((row) => row.def.id === 'USDKRW' ? { ...row, d: '20200101', chg: 35 } : row);
		const snapshot = buildMacroLensSnapshot({
			co: companyFixture(),
			macro,
			macroLatest: staleLatest,
			sectorTailwinds: sectorTailwinds(),
			coMovers: []
		});
		const gate = snapshot.evidenceGates.find((g) => g.id === 'macroData');
		expect(gate?.status).toBe('blocked');
		expect(gate?.blocks.join(' ')).toContain('USDKRW');
	});

	it('preserves transmission edge falsifiers (no verdict needed)', () => {
		const snapshot = buildMacroLensSnapshot({
			co: companyFixture(),
			macro,
			macroLatest: macroLatest(),
			sectorTailwinds: sectorTailwinds(),
			coMovers: []
		});
		const fxEdge = snapshot.transmissionEdges.find((edge) => edge.driverId === 'USDKRW');
		expect(fxEdge?.falsifiers[0]).toContain('달러 원가');
	});

	it('EN mode: comprehensive snapshot scan finds no Korean leak (payload edges + regime subtree + all Path/Sources prose)', () => {
		const HANGUL = /[가-힣]/;
		// macroWithRegime() carries BOTH the live Korean transmission payload AND a regime payload, so this single
		// snapshot exercises the payload edge path (R3 leak) AND the Regime Lens subtree (R5 coverage gap). Non-null
		// tailwind exercises sectorBinding.tailwind.label/labelEn (R5 walker blind spot).
		const snapshot = buildMacroLensSnapshot({
			co: companyFixture({
				tailwind: { key: 'semiconductor', kr: '반도체', en: 'Semiconductor', blended: 0.45, krScore: 0.5, usScore: 0.4, label: '순풍', labelEn: 'tailwind', tone: 'up' },
				// macroExposure carries Korean engine reasons + Korean indicator labels/impact (157 live companies) · exercise the analysis-data EN path.
				macroExposure: {
					exposureQuality: { status: 'blocked', reason: '회사 매출과 매크로 지표의 겹친 표본이 부족합니다.', blockedReason: 'selected macro regression absent', missingEvidence: [], sourceRef: 'analysis.macroExposure:005930', nObs: null, rSquared: null, window: null, frequency: null, lagMonths: null, coverage: 'missing', minObs: 5, method: 'ols', modelVersion: 'v1', targetMetric: 'salesGrowth' },
					// APT_PRICE is NOT in MACRO_SERIES (the 43-id contract), so this exercises the EXPOSURE_SERIES_EN map path (the R7 leak), not macroDefOf.
					selected: [{ seriesId: 'APT_PRICE', label: '아파트가격', impact: '상승', axis: 'macro', rSquared: 0.31, nObs: 8, window: '2018-2026', frequency: 'annual', lagMonths: 0, coverage: 'company', minObs: 5, method: 'ols', modelVersion: 'v1', targetMetric: 'salesGrowth', sourceRef: 'analysis.macroExposure:005930', sourceRefs: [], latestChange: 1.2 }]
				}
			} as unknown as Partial<Company>),
			macro: macroWithRegime(),
			macroLatest: macroLatest(),
			sectorTailwinds: sectorTailwinds(),
			coMovers: [],
			lang: 'en'
		});
		expect(snapshot.transmissionEdges.length).toBeGreaterThan(0);
		expect(snapshot.regime!.available).toBe(true);
		const fxEdge = snapshot.transmissionEdges.find((edge) => edge.driverId === 'USDKRW');
		expect(fxEdge?.falsifiers[0]).not.toMatch(HANGUL); // Korean in KR mode (see the test above)
		// Recursive Hangul scan of the WHOLE rendered snapshot (incl. regime). A bilingual pair only needs a clean
		// EN side: {kr,en}, X/XEn (e.g. label/labelEn), and XKr/XEn are all resolved to the EN member.
		// Skipped: marketPhase (phase label resolved at render via phaseHeadline), company (proper-noun name + {kr,en} sector),
		// glance (a separate market-overview surface this dialog does NOT render).
		const SKIP = new Set(['marketPhase', 'company', 'glance']);
		const leaks: string[] = [];
		const walk = (v: unknown, path: string): void => {
			if (typeof v === 'string') { if (HANGUL.test(v)) leaks.push(`${path} = ${v}`); return; }
			if (Array.isArray(v)) { v.forEach((x, i) => walk(x, `${path}[${i}]`)); return; }
			if (v && typeof v === 'object') {
				const o = v as Record<string, unknown>;
				for (const k of Object.keys(o)) {
					if (SKIP.has(k)) continue;
					if (k === 'kr' && 'en' in o) continue; // {kr,en} → scan EN side only
					if ((k + 'En') in o) continue; // X/XEn pair (e.g. label/labelEn) → scan EN side only
					if (k.endsWith('Kr') && (k.slice(0, -2) + 'En') in o) continue; // XKr/XEn pair → scan EN side only
					walk(o[k], `${path}.${k}`);
				}
			}
		};
		walk(snapshot, '$');
		expect(leaks, leaks.join('\n')).toEqual([]);
	});

	it('blocks the quant gate when quantCandidate lacks required evidence fields', () => {
		const snapshot = buildMacroLensSnapshot({
			co: companyFixture({
				macroExposure: {
					exposureQuality: {
						status: 'quantCandidate',
						reason: 'fixture invalid quant candidate',
						blockedReason: '',
						missingEvidence: [],
						sourceRef: 'test:macroExposure',
						nObs: null,
						rSquared: null,
						window: null,
						frequency: null,
						lagMonths: null,
						coverage: 'missing',
						minObs: 24,
						method: 'ols',
						modelVersion: 'test',
						targetMetric: 'sales'
					},
					selected: []
				}
			} as unknown as Partial<Company>),
			macro,
			macroLatest: macroLatest(),
			sectorTailwinds: sectorTailwinds(),
			coMovers: []
		});
		expect(snapshot.evidenceGates.find((g) => g.id === 'quant')?.status).toBe('blocked');
		expect(snapshot.evidenceGates.find((g) => g.id === 'quant')?.blocks.join(' ')).toContain('nObs missing');
	});

	it('hard-locks the path gate when macro.transmission is missing', () => {
		const noTransmission = cloneMacro();
		noTransmission.transmission = null;
		const snapshot = buildMacroLensSnapshot({
			co: companyFixture(),
			macro: noTransmission,
			macroLatest: macroLatest(),
			sectorTailwinds: sectorTailwinds(),
			coMovers: []
		});
		expect(snapshot.evidenceGates.find((g) => g.id === 'path')?.status).toBe('blocked');
	});

	it('drivers carry value/asOf/source for the Pulse strip (relevance != context)', () => {
		const snapshot = buildMacroLensSnapshot({
			co: companyFixture(),
			macro,
			macroLatest: macroLatest(),
			sectorTailwinds: sectorTailwinds(),
			coMovers: []
		});
		const pulse = snapshot.drivers.filter((d) => d.relevance !== 'context');
		expect(pulse.length).toBeGreaterThan(0);
		for (const d of pulse) {
			expect(typeof d.value).toBe('string');
			expect(d).toHaveProperty('asOf');
			expect(d).toHaveProperty('source');
		}
	});
});

describe('buildExposureMatrixRows · sparsity, cap 6, deterministic drop', () => {
	it('produces rows with cells.length === channels.length and filledCount', () => {
		const snapshot = buildMacroLensSnapshot({
			co: companyFixture(),
			macro,
			macroLatest: macroLatest(),
			sectorTailwinds: sectorTailwinds(),
			coMovers: []
		});
		const rows = buildExposureMatrixRows(snapshot.drivers, snapshot.topPressures, snapshot.transmissionEdges, CHANNELS);
		expect(rows.length).toBeLessThanOrEqual(6);
		for (const row of rows) {
			expect(row.cells).toHaveLength(CHANNELS.length);
			expect(row.filledCount).toBe(row.cells.filter(Boolean).length);
			for (const cell of row.cells) {
				if (cell) expect(['observed', 'sectorPrior', 'template']).toContain(cell.evidenceLevel);
			}
		}
	});

	it('caps at exactly 6 rows when 8 drivers are supplied', () => {
		const drivers = Array.from({ length: 8 }, (_, i) => mkDriver(`D${i}`));
		const edges = drivers.map((d, i) => mkEdge(d.id, CHANNELS[i % CHANNELS.length], 'template'));
		const rows = buildExposureMatrixRows(drivers, drivers, edges, CHANNELS);
		expect(rows).toHaveLength(6);
	});

	it('sorts by filledCount desc and, on equal filledCount, drops the last input row (stable)', () => {
		// 8 drivers, all filledCount === 1 (each 1 channel) → cap 6 drops input rows 7,8.
		const drivers = Array.from({ length: 8 }, (_, i) => mkDriver(`D${i}`));
		const edges = drivers.map((d) => mkEdge(d.id, 'revenue', 'template'));
		const rows = buildExposureMatrixRows(drivers, drivers, edges, CHANNELS);
		expect(rows.map((r) => r.driver.id)).toEqual(['D0', 'D1', 'D2', 'D3', 'D4', 'D5']);
		// 한 driver가 2채널(filledCount 2)이면 정렬 상단으로 올라온다.
		const edges2 = [...edges, mkEdge('D7', 'margin', 'template')];
		const rows2 = buildExposureMatrixRows(drivers, drivers, edges2, CHANNELS);
		expect(rows2[0].driver.id).toBe('D7');
		expect(rows2[0].filledCount).toBe(2);
	});

	it('keeps same-channel multiple drivers as separate rows (valuation stack)', () => {
		const drivers = [mkDriver('HY'), mkDriver('DGS10')];
		const edges = [mkEdge('HY', 'valuation', 'observed'), mkEdge('DGS10', 'valuation', 'template')];
		const rows = buildExposureMatrixRows(drivers, drivers, edges, CHANNELS);
		expect(rows).toHaveLength(2);
		expect(rows.every((r) => r.cells[CHANNELS.indexOf('valuation')] != null)).toBe(true);
	});

	it('does not throw and does not surface quantCandidate as a first-screen row (silent-drop guard)', () => {
		const snapshot = buildMacroLensSnapshot({
			co: companyFixture({
				macroExposure: {
					exposureQuality: {
						status: 'quantCandidate', reason: '', blockedReason: '', missingEvidence: [],
						sourceRef: 'test', nObs: 30, rSquared: 0.4, window: '2018-2026', frequency: 'monthly',
						lagMonths: 1, coverage: 'company', minObs: 24, method: 'ols', modelVersion: 't', targetMetric: 'sales'
					},
					selected: []
				}
			} as unknown as Partial<Company>),
			macro,
			macroLatest: macroLatest(),
			sectorTailwinds: sectorTailwinds(),
			coMovers: []
		});
		expect(() => buildExposureMatrixRows(snapshot.drivers, snapshot.topPressures, snapshot.transmissionEdges, CHANNELS)).not.toThrow();
		const rows = buildExposureMatrixRows(snapshot.drivers, snapshot.topPressures, snapshot.transmissionEdges, CHANNELS);
		// 행은 driver 키이며 어떤 셀도 exposureQuality status를 노출하지 않는다(근거 탭 전용).
		const json = JSON.stringify(rows);
		expect(json).not.toContain('quantCandidate');
	});
});

describe('pickFocusCell · observed priority, channel tie-break, determinism', () => {
	const rowsOf = (edges: MacroTransmissionEdgeView[]): MacroExposureMatrixRow[] => {
		const byDriver = new Map<string, MacroTransmissionEdgeView[]>();
		for (const e of edges) {
			if (!byDriver.has(e.driverId)) byDriver.set(e.driverId, []);
			byDriver.get(e.driverId)!.push(e);
		}
		return [...byDriver.entries()].map(([driverId, es]) => ({
			driver: mkDriver(driverId),
			cells: CHANNELS.map((ch) => es.find((e) => e.channel === ch) ?? null),
			filledCount: es.length
		}));
	};

	it('prefers observed over template', () => {
		const focus = pickFocusCell(rowsOf([mkEdge('A', 'margin', 'template'), mkEdge('B', 'valuation', 'observed')]));
		expect(focus?.edge.driverId).toBe('B');
	});

	it('breaks ties by channel priority (revenue > margin > valuation), not by change/lag', () => {
		// 3 observed edges all medium confidence · 채널 우선순위로 revenue(EXPORT)가 초점.
		const focus = pickFocusCell(rowsOf([
			mkEdge('PPI_SEMI', 'margin', 'observed', 'medium'),
			mkEdge('EXPORT', 'revenue', 'observed', 'medium'),
			mkEdge('BAMLH0A0HYM2', 'valuation', 'observed', 'medium')
		]));
		expect(focus?.edge.driverId).toBe('EXPORT');
		expect(focus?.channel).toBe('revenue');
	});

	it('is deterministic across repeated calls on identical input', () => {
		const edges = [mkEdge('PPI_SEMI', 'margin', 'observed'), mkEdge('EXPORT', 'revenue', 'observed'), mkEdge('BAMLH0A0HYM2', 'valuation', 'observed')];
		const a = pickFocusCell(rowsOf(edges));
		const b = pickFocusCell(rowsOf(edges));
		expect(a?.edge.driverId).toBe(b?.edge.driverId);
	});

	it('returns null when no cell is filled', () => {
		expect(pickFocusCell([{ driver: mkDriver('X'), cells: CHANNELS.map(() => null), filledCount: 0 }])).toBeNull();
	});

	it('handles a lagMonths===null focus edge without throwing (chain renders direct)', () => {
		const focus = pickFocusCell(rowsOf([mkEdge('X', 'revenue', 'observed', 'medium', { lagMonths: null })]));
		expect(focus?.edge.lagMonths).toBeNull();
		expect(focus?.edge.financialLine).toBeTruthy();
		expect(focus?.edge.valuationLever).toBeTruthy();
	});

	it('on real semiconductor data returns a stable non-null focus with chain inputs', () => {
		const snapshot = buildMacroLensSnapshot({
			co: companyFixture(),
			macro,
			macroLatest: macroLatest(),
			sectorTailwinds: sectorTailwinds(),
			coMovers: []
		});
		const rows = buildExposureMatrixRows(snapshot.drivers, snapshot.topPressures, snapshot.transmissionEdges, CHANNELS);
		const focus = pickFocusCell(rows);
		expect(focus).not.toBeNull();
		expect(focus!.edge.financialLine).toBeTruthy();
		expect(focus!.edge.valuationLever).toBeTruthy();
		const again = pickFocusCell(rows);
		expect(focus!.edge.driverId).toBe(again!.edge.driverId);
	});
});

// ───────────────────────── 국면 렌즈 (Regime Lens · 초강화) view-model ─────────────────────────
// 라이브 macro.json 은 regime 키 미보유(prebuild deploy 시 주입). 합성 fixture(실 payload shape)로 검증.

const usModels = (): Record<string, MacroRegimeModel> => ({
	probit: { probability: 0.18, probabilityRounded: 0.2, zone: 'low', zoneLabel: '낮음', spread: 0.4, horizon: '12M', timeKind: 'leading', precisionNote: 'Estrella-Mishkin 고정계수·표준오차 미산출', asOf: '2026-06-15', seriesId: 'T10Y3M', staleAfterDays: 7 },
	sahm: { value: 0.1, triggered: false, zone: 'normal', zoneLabel: '정상', horizon: 'realtime', timeKind: 'trigger(동행)', asOf: '2026-05-01', seriesId: 'UNRATE', staleAfterDays: 45 },
	lei: { signal: 'caution', signalLabel: '경계', mom6m: -1.2, availableComponents: 9, totalComponents: 10, overlapNote: 'term-spread·initial-claims 내포(probit/Sahm 부분 상관)', horizon: '6-9M', timeKind: 'leading', asOf: '2026-05', staleAfterDays: 75 },
	hamilton: { contractionProb: null, converged: false, separation: 0.31, iterations: 50, status: 'EM 미수렴', timeKind: 'retrospective', horizon: '동행', staleAfterDays: 120, revisionLabel: '분기 GDP·수정 대상', asOf: '2026-Q1', seriesId: 'A191RL1Q225SBEA', seriesSource: 'FRED' }
});

const usRegimePayload = (overrides: Partial<MacroRegimePayload> = {}): MacroRegimePayload => ({
	market: 'US',
	computedAt: '2026-06-18T00:00:00Z',
	forecast: { models: usModels(), missing: [] },
	rates: { spread10y3m: 0.4, sign: '+', curveShape: 'flat', curveShapeLabel: '평탄', curveSource: 'NelsonSiegel.interpretation', asOf: '2026-06-15', seriesId: 'T10Y3M', staleAfterDays: 7, missing: [] },
	gar: { gar5: -1.5, gar25: 0.4, median: 2.1, gar75: 3.2, gar95: 4.4, skewness: -0.8, tailRisk: 'elevated', tailRiskLabel: '주의', currentFCI: 0.32, observations: 42, horizon: 4, timeKind: 'forward', seriesNote: 'FCI 조건부 GDP 성장률 분위(점추정 아닌 조건부 분포)', asOf: '2026-Q1', staleAfterDays: 120, revisionLabel: '분기 GDP·수정 대상' },
	regimeBand: { band: [0.05, 0.04, 0.06, 0.09, 0.14, 0.22, 0.31, 0.28, 0.19, 0.12, 0.08], converged: true, separation: 0.74, timeKind: 'retrospective', horizon: '동행', asOf: '2026-Q1', staleAfterDays: 120 },
	...overrides
});

const krRegimePayload = (): MacroRegimePayload => ({
	market: 'KR',
	computedAt: '2026-06-18T00:00:00Z',
	forecast: {
		models: { lei: { cliMomentum: 1.1, cliLevel: 99.8, growthApprox: 1.4, growthLabel: '확장', asOf: '2026-04', staleAfterDays: 75 } },
		missing: [
			{ id: 'probit', status: 'notApplicable', reason: 'US 전용' },
			{ id: 'sahm', status: 'notApplicable', reason: 'US 전용' },
			{ id: 'hamilton', status: '단위 parity 미확정·표시 보류', reason: 'GROWTH↔A191RL1Q225SBEA 단위 동일성 미확정' },
			{ id: 'gar', status: 'notApplicable', reason: 'US 중심(FCI 입력)' }
		]
	},
	rates: { missing: [{ id: 'yieldCurve', status: 'notApplicable', reason: 'US 전용' }] }
});

const macroWithRegime = (us = usRegimePayload(), kr = krRegimePayload()): MacroFile => {
	const m = cloneMacro();
	m.regime = { kr, us };
	return m;
};

describe('macro regime view-model · transitionFraction', () => {
	it('emits an integer fraction triggered/(triggered+pending), never a percent', () => {
		const side = { transition: { from: 'slowdown', to: 'contraction', progress: 33, triggered: ['gold_surging'], pending: ['vix_spiking', 'term_spread_inverted'] } } as unknown as MacroSide;
		const frac = transitionFraction(side);
		expect(frac).not.toBeNull();
		// fraction 은 언어중립 '1/3' 만 · '충족'/'met' 접미는 템플릿이 T() 로 붙인다(i18n).
		expect(frac!.fraction).toBe('1/3');
		expect(frac!.from).toBe('slowdown');
		expect(frac!.to).toBe('contraction');
		// 백분율·progress 노출 0 (L1757 % 경로 미재현).
		expect(frac!.fraction).not.toContain('%');
		expect(JSON.stringify(frac)).not.toContain('33');
	});
	it('returns null when transition is null (KR) → no fraction rendered', () => {
		expect(transitionFraction({ transition: null } as unknown as MacroSide)).toBeNull();
		expect(transitionFraction(undefined)).toBeNull();
		expect(transitionFraction(null)).toBeNull();
	});
});

describe('macro regime view-model · bucketOf (§3.3 3-step table)', () => {
	it('maps probit moderate → 0 (absorbed) and the full §3.3 table', () => {
		expect(bucketOf({ zone: 'low' })).toBe(0);
		expect(bucketOf({ zone: 'moderate' })).toBe(0); // 흡수
		expect(bucketOf({ zone: 'elevated' })).toBe(1);
		expect(bucketOf({ zone: 'high' })).toBe(2);
		expect(bucketOf({ zone: 'normal' })).toBe(0); // sahm
		expect(bucketOf({ zone: 'warning' })).toBe(1);
		expect(bucketOf({ zone: 'recession' })).toBe(2);
		expect(bucketOf({ signal: 'expansion' })).toBe(0); // lei
		expect(bucketOf({ signal: 'caution' })).toBe(1);
		expect(bucketOf({ signal: 'recession_warning' })).toBe(2);
		expect(bucketOf({ contractionProb: 0.1 })).toBe(0); // hamilton <0.25
		expect(bucketOf({ contractionProb: 0.4 })).toBe(1); // <0.5
		expect(bucketOf({ contractionProb: 0.6 })).toBe(2); // >=0.5
	});
	it('returns null for status-only / null models (excluded from agreement)', () => {
		expect(bucketOf({ status: 'EM 미수렴', contractionProb: null })).toBeNull();
		expect(bucketOf({ status: '데이터부족·표시 보류' })).toBeNull();
		expect(bucketOf(undefined)).toBeNull();
		expect(bucketOf(null)).toBeNull();
	});
});

describe('macro regime view-model · agreementOf (adjacent=agree, names disagreeing, no score)', () => {
	it('returns 교차 불가 with valid count when <2 valid (bilingual {kr,en})', () => {
		expect(agreementOf([{ model: 'CLI', bucket: null }]).kr).toBe('교차 불가 (유효 0개)');
		expect(agreementOf([{ model: 'CLI', bucket: null }]).en).toBe('cross-check N/A (0 valid)');
		expect(agreementOf([{ model: 'probit', bucket: 0 }, { model: 'Sahm', bucket: null }]).kr).toBe('교차 불가 (유효 1개)');
	});
	it('treats adjacent buckets (0-1, 1-2) as agreement', () => {
		const txt = agreementOf([{ model: 'probit', bucket: 0 }, { model: 'LEI', bucket: 1 }]);
		expect(txt.kr).toContain('동의');
		expect(txt.en).toContain('agree');
		expect(txt.kr).not.toContain('vs');
	});
	it('names the disagreeing models when ≥2 buckets apart', () => {
		const txt = agreementOf([
			{ model: 'probit', bucket: 0 },
			{ model: 'Sahm', bucket: 0 },
			{ model: 'LEI', bucket: 2 }
		]);
		expect(txt.kr).toContain('LEI');
		expect(txt.kr).toContain('침체');
		expect(txt.kr).toContain('vs');
		expect(txt.en).toContain('Recession');
	});
	it('renders no ordinal/score/badge token (verdict backdoor guard)', () => {
		const txt = agreementOf([{ model: 'probit', bucket: 0 }, { model: 'LEI', bucket: 2 }]);
		expect(txt.kr).not.toMatch(/\/100|score|badge|점수/i);
		expect(txt.en).not.toMatch(/\/100|score|badge|점수/i);
		expect(txt.kr).not.toMatch(/\b[0-2]\b/); // 서수 bucket 숫자 비노출
		expect(txt.en).not.toMatch(/\b[0-2]\b/);
	});
});

describe('macro regime view-model · focusChannelAlignment (narrative only, no 수혜/sensitivity)', () => {
	const focusOf = (channel: MacroChannel, sign: MacroTransmissionEdgeView['sign']) =>
		({ channel, edge: { sign } });
	it('describes alignment when edge sign positive (bilingual, no 수혜/sensitivity)', () => {
		const txt = focusChannelAlignment({ growth: 'rising', inflation: 'rising' }, focusOf('revenue', 'positive'))!;
		expect(txt.kr).toContain('정합');
		expect(txt.kr).toContain('성장↑');
		expect(txt.en).toContain('aligned');
		expect(txt.kr).not.toMatch(/수혜|유리|매수/);
		expect(txt.en).not.toMatch(/favored|favou?rs|buy/i);
		expect(txt.kr).not.toMatch(/\d/); // 민감도 숫자 0
		expect(txt.en).not.toMatch(/\d/);
	});
	it('describes 역방향 when edge sign negative', () => {
		const txt = focusChannelAlignment({ growth: 'rising', inflation: 'rising' }, focusOf('balanceSheet', 'negative'))!;
		expect(txt.kr).toContain('역방향');
		expect(txt.en).toContain('opposite');
		expect(txt.kr).not.toMatch(/수혜|유리/);
	});
	it('returns null when no quadrant or no focusCell', () => {
		expect(focusChannelAlignment(null, focusOf('revenue', 'positive'))).toBeNull();
		expect(focusChannelAlignment({ growth: 'rising' }, null)).toBeNull();
		expect(focusChannelAlignment({ growth: 'stable' }, focusOf('revenue', 'positive'))).toBeNull();
	});
});

describe('macro regime view-model · buildRegimeView (US confluence, KR asymmetry)', () => {
	it('is undefined-safe when macro.regime is absent (renders nothing)', () => {
		// regime 키를 명시적으로 제거(라이브 artifact 의 regime 배포 여부와 무결합) · undefined-safety 만 검증.
		const view = buildRegimeView({ ...macro, regime: undefined }, null);
		expect(view.available).toBe(false);
		expect(view.us).toBeNull();
		expect(view.kr).toBeNull();
		// 전향 분수는 macro.us.transition 라이브라 regime 없어도 시도(라이브 macro 는 transition 부재 → null 가능).
	});
	it('builds 4 US confluence tiles with own horizon/timing, no single 12M frame', () => {
		const view = buildRegimeView(macroWithRegime(), null);
		expect(view.available).toBe(true);
		expect(view.us!.tiles).toHaveLength(4);
		expect(view.us!.totalCount).toBe(4);
		// hamilton status-only → suppressed, validCount=3 (probit/sahm/lei).
		expect(view.us!.validCount).toBe(3);
		const ham = view.us!.tiles.find((t) => t.model === 'hamilton')!;
		expect(ham.suppressed).toBe(true);
		expect(ham.zoneLabel.kr).toBe('표시 보류');
		expect(ham.zoneLabel.en).toBe('suppressed');
		// 각 타일이 자기 호라이즌 (단일 '12M·확률' 프레임 아님).
		const probit = view.us!.tiles.find((t) => t.model === 'probit')!;
		const sahm = view.us!.tiles.find((t) => t.model === 'sahm')!;
		const lei = view.us!.tiles.find((t) => t.model === 'lei')!;
		expect(probit.horizonLabel.kr).toContain('12M');
		expect(probit.horizonLabel.kr).toContain('leading');
		expect(sahm.horizonLabel.kr).toContain('realtime');
		expect(lei.horizonLabel.kr).toContain('6-9M');
		expect(ham.horizonLabel.kr).toContain('retrospective');
	});
	it('probit zone is primary, probability 5%p rounded is secondary, precisionNote in title', () => {
		const view = buildRegimeView(macroWithRegime(), null);
		const probit = view.us!.tiles.find((t) => t.model === 'probit')!;
		expect(probit.zoneLabel.kr).toBe('낮음'); // zone 주역(KR)
		expect(probit.zoneLabel.en).toBe('Low'); // enum 매핑(EN)
		expect(probit.secondary).toBe('~20%'); // probabilityRounded
		expect(probit.note.kr).toContain('표준오차 미산출'); // precisionNote
		// 소수 2자리(0.18) 단독 노출 0.
		expect(probit.secondary).not.toContain('18');
		expect(probit.secondary).not.toContain('0.1');
	});
	it('gaugeValue carries raw 0~1 probability for probit/hamilton, null for sahm/lei (arc geometry input)', () => {
		const view = buildRegimeView(macroWithRegime(), null);
		const probit = view.us!.tiles.find((t) => t.model === 'probit')!;
		const sahm = view.us!.tiles.find((t) => t.model === 'sahm')!;
		const lei = view.us!.tiles.find((t) => t.model === 'lei')!;
		const ham = view.us!.tiles.find((t) => t.model === 'hamilton')!;
		expect(probit.gaugeValue).toBe(0.18); // 원확률(probability), probabilityRounded(0.2) 아님
		expect(sahm.gaugeValue).toBeNull(); // %p 트리거 · 0~1 확률 아님
		expect(lei.gaugeValue).toBeNull(); // 방향 신호 · 0~1 확률 아님
		expect(ham.gaugeValue).toBeNull(); // EM 미수렴(contractionProb null) → suppressed
	});
	it('LEI tile carries overlapNote (partial correlation, not fully independent)', () => {
		const view = buildRegimeView(macroWithRegime(), null);
		const lei = view.us!.tiles.find((t) => t.model === 'lei')!;
		expect(lei.note.kr).toContain('내포');
		expect(lei.note.kr).toMatch(/term-spread|initial-claims/);
	});
	it('yield curve note carries the double-count guard, agreement counts probit once', () => {
		const view = buildRegimeView(macroWithRegime(), null);
		expect(view.us!.yieldCurve).not.toBeNull();
		expect(view.us!.yieldCurve!.spread).toBe(0.4); // 온도계 기하 입력 = rates.spread10y3m 원수치
		expect(view.us!.yieldCurve!.note.kr).toContain('동일곡선');
		expect(view.us!.yieldCurve!.note.kr).toContain('독립 신호 아님');
		// agreement 는 텍스트만(점수·badge 0).
		expect(view.us!.agreement.kr).not.toMatch(/\/100|score|badge/i);
		expect(view.us!.agreement.en).not.toMatch(/\/100|score|badge/i);
	});
	it('GaR renders all 5 quantiles + skewness + tailRisk + 4Q forward (no single-number collapse, fan allowed)', () => {
		const view = buildRegimeView(macroWithRegime(), null);
		const gar = view.us!.gar!;
		expect(gar.available).toBe(true);
		expect(gar.bars.map((b) => b.key)).toEqual(['gar5', 'gar25', 'median', 'gar75', 'gar95']);
		expect(gar.bars.find((b) => b.key === 'median')!.value).toBe(2.1); // median 동반
		expect(gar.skewness).toBe(-0.8);
		expect(gar.tailRiskLabel.kr).toBe('주의');
		expect(gar.horizonLabel.kr).toContain('4Q 전향');
		expect(gar.horizonLabel.en).toContain('forward');
	});
	it('GaR hides when status-only (표본 부족)', () => {
		const view = buildRegimeView(macroWithRegime(usRegimePayload({ gar: { status: '표본 부족·표시 보류' } })), null);
		expect(view.us!.gar).toBeNull();
	});
	it('regime band is a ≤24-point sparkline with 회고적·smoothed caption (not bars/point-est)', () => {
		const view = buildRegimeView(macroWithRegime(), null);
		const band = view.us!.band!;
		expect(band.available).toBe(true);
		expect(band.points.length).toBeLessThanOrEqual(24);
		expect(band.points.length).toBe(11);
		// 절대 침체확률(0~1) 보존 · per-window 재정규화 금지(진폭 정직).
		expect(Math.max(...band.points)).toBeLessThanOrEqual(1);
		expect(Math.min(...band.points)).toBeGreaterThanOrEqual(0);
		expect(band.points[0]).toBeCloseTo(0.05, 5); // 원 확률 그대로(정규화 시 0 이 됨)
		expect(band.caption.kr).toContain('회고적');
		expect(band.caption.kr).toContain('smoothed');
		expect(band.caption.en).toContain('retrospective');
	});
	it('quadrant direction shows growth/inflation labels + assets, raw signals never exposed', () => {
		// 합성 us.quadrant 부착(라이브 macro.us.quadrant 존재 여부 무관 · fixture 명시).
		const m = macroWithRegime();
		m.us = { ...m.us, quadrant: { quadrant: 'reflation', quadrantLabel: '리플레이션', growth: 'rising', inflation: 'rising', growthSignal: 662678, inflationSignal: 26.71, assetImplication: { commodity: 'overweight', bond: 'underweight' }, description: '' } } as unknown as MacroSide;
		const view = buildRegimeView(m, { channel: 'revenue', edge: { sign: 'positive' } });
		const q = view.us!.quadrant!;
		expect(q.growthLabel.kr).toBe('성장↑');
		expect(q.growthLabel.en).toBe('growth↑');
		expect(q.inflationLabel.kr).toBe('물가↑');
		expect(q.alignment!.kr).toContain('정합');
		expect(q.alignment!.en).toContain('aligned');
		// raw growthSignal/inflationSignal 비노출.
		const json = JSON.stringify(q);
		expect(json).not.toContain('662678');
		expect(json).not.toContain('26.71');
	});
	it('KR confluence is CLI momentum 1 tile; hamilton in missing as 단위 parity 미확정', () => {
		const view = buildRegimeView(macroWithRegime(), null);
		expect(view.kr!.tiles).toHaveLength(1);
		expect(view.kr!.tiles[0].modelName).toBe('CLI momentum');
		// KR 은 yieldCurve/GaR/band 없음(US 중심).
		expect(view.kr!.yieldCurve).toBeNull();
		expect(view.kr!.gar).toBeNull();
		expect(view.kr!.band).toBeNull();
		// hamilton/probit/sahm/gar 은 빈 셀 아닌 명시 라벨.
		const ham = view.kr!.notApplicable.find((n) => n.id === 'hamilton')!;
		expect(ham.reason.kr).toContain('단위');
		const probit = view.kr!.notApplicable.find((n) => n.id === 'probit')!;
		expect(probit.reason.kr).toContain('US 전용');
		expect(probit.reason.en).toContain('US-only');
		// CLI 1타일뿐이라 교차 불가(단일 모델 문구·'유효 0개' 모순 제거).
		expect(view.kr!.agreement.kr).toContain('교차 불가');
		expect(view.kr!.agreement.kr).toContain('단일 모델');
		expect(view.kr!.agreement.en).toContain('single model');
	});
	it('snapshot.regime is wired · present when deployed, undefined-safe when absent', () => {
		// regime 제거 → available:false (artifact 배포 여부와 무결합).
		const noRegime = buildMarketMacroLensSnapshot({ macro: { ...macro, regime: undefined }, macroLatest: macroLatest(), sectorTailwinds: sectorTailwinds() });
		expect(noRegime.regime).toBeDefined();
		expect(noRegime.regime!.available).toBe(false);
		// regime 주입 → available:true + US 4타일.
		const withRegime = buildMarketMacroLensSnapshot({ macro: macroWithRegime(), macroLatest: macroLatest(), sectorTailwinds: sectorTailwinds() });
		expect(withRegime.regime!.available).toBe(true);
		expect(withRegime.regime!.us!.tiles).toHaveLength(4);
	});
});

describe('buildMacroEvidenceCards', () => {
	// 합성 시리즈 · 빌더는 순수(now 미사용)라 endYm 을 데이터 최신월에서 유도. d 오름차순.
	const monthly = (startYm: string, count: number): { d: string; v: number }[] =>
		Array.from({ length: count }, (_, i) => {
			let y = Number(startYm.slice(0, 4));
			let m = Number(startYm.slice(4, 6)) + i;
			y += Math.floor((m - 1) / 12);
			m = ((m - 1) % 12) + 1;
			return { d: `${y}${String(m).padStart(2, '0')}15`, v: i };
		});

	it('정렬 · 다중 cadence 입력이 동일 길이·오름차순 periods 산출', () => {
		const out = buildMacroEvidenceCards('US', {
			INDPRO: monthly('202001', 60),
			PAYEMS: [{ d: '20230101', v: 1 }, { d: '20240601', v: 2 }] // 희소
		}, 'kr');
		expect(out.periods).toHaveLength(48);
		for (const card of out.cards) for (const s of card.series) expect(s.data).toHaveLength(48);
		expect(out.periods[0]).toMatch(/^\d{2}\.\d{2}$/);
		expect(out.periods[47] > out.periods[0]).toBe(true);
	});

	it('결측 시리즈 제외 · 데이터 있는 시리즈만 카드에 포함', () => {
		const out = buildMacroEvidenceCards('US', { INDPRO: monthly('202201', 30) }, 'kr');
		const growth = out.cards.find((c) => c.key === 'usGrowth');
		expect(growth).toBeDefined();
		expect(growth!.series.map((s) => s.name)).toEqual(['산업생산 YoY']); // PAYEMS 미주입 → 제외
		expect(out.cards.find((c) => c.key === 'usInflation')).toBeUndefined(); // 데이터 0 카드 미생성
	});

	it('빈 seriesMap → cards=[] · periods=[]', () => {
		const out = buildMacroEvidenceCards('US', {}, 'kr');
		expect(out.cards).toEqual([]);
		expect(out.periods).toEqual([]);
	});

	it('dual-axis spec 보존 · 우축 series 의 axis=r 유지·좌축 미지정', () => {
		const out = buildMacroEvidenceCards('US', {
			T10Y2Y: monthly('202201', 30),
			BAMLH0A0HYM2: monthly('202201', 30),
			VIXCLS: monthly('202201', 30)
		}, 'kr');
		const fin = out.cards.find((c) => c.key === 'usFinancial');
		expect(fin).toBeDefined();
		expect(fin!.series.find((s) => s.name.startsWith('VIX'))!.axis).toBe('r');
		expect(fin!.series.find((s) => s.name.includes('장단기'))!.axis).toBeUndefined();
	});

	it('스펙 seriesId 는 전부 MACRO_SERIES 화이트리스트 실재', () => {
		const known = new Set(MACRO_SERIES.map((s) => s.id));
		for (const market of ['KR', 'US'] as const)
			for (const spec of MACRO_EVIDENCE_SPECS[market])
				for (const s of spec.series) expect(known.has(s.id)).toBe(true);
	});
});

describe('buildMacroSimView', () => {
	const fanVar = (seriesId: string, transform: string) => ({
		transform, label: seriesId, seriesId,
		history: Array.from({ length: 18 }, (_, i) => i * 0.1),
		q5: Array.from({ length: 12 }, () => 0), q25: Array.from({ length: 12 }, () => 1),
		q50: Array.from({ length: 12 }, () => 2), q75: Array.from({ length: 12 }, () => 3),
		q95: Array.from({ length: 12 }, () => 4), mean: Array.from({ length: 12 }, () => 2)
	});
	const okSim = (regimePath: Record<string, unknown>) => ({
		market: 'US', status: 'ok', asOf: '2026-05', seed: 20260624, horizon: 12,
		model: { kind: 'BVAR', nObs: 483, status: 'ok' },
		fan: {
			산업생산: fanVar('INDPRO', 'logdiff100'), 소비자물가: fanVar('CPIAUCSL', 'logdiff100'),
			원유: fanVar('DCOILWTICO', 'logdiff100'), 정책금리: fanVar('FEDFUNDS', 'level'), '10년금리': fanVar('DGS10', 'level')
		},
		irf: { 산업생산: [0, -0.1, -0.2], 정책금리: [1, 0.9, 0.8], shockLabel: '정책금리 +100bp', caveat: 'recursive-identification·illustrative' },
		regimePath, missing: []
	});

	it('status ok → 팬 4장(원유 제외)·periods 30(과거18+미래12)·IRF·honesty', () => {
		const v = buildMacroSimView(okSim({ status: '레짐 분리 약함·표시 보류' }) as never, 'kr');
		expect(v.status).toBe('ok');
		expect(v.fanCards.length).toBe(4); // 원유(DCOILWTICO) 제외
		expect(v.fanCards.some((c) => c.key === 'DCOILWTICO')).toBe(false);
		expect(v.periods.length).toBe(30);
		expect(v.irf?.shockLabel).toContain('정책금리');
		expect(v.honesty.sampleN).toBe(483);
		expect(v.regimePath).toBeNull(); // status 있으면 보류
	});

	it('팬 카드 = 실적 1 + 밴드 3(p50/p90/p10), 미래는 anchor 에서 emanate', () => {
		const v = buildMacroSimView(okSim({ status: 'x' }) as never, 'kr');
		const card = v.fanCards[0];
		expect(card.series.length).toBe(4);
		const mid = card.series.find((s) => s.name === '중앙')!;
		// 과거 17 null + anchor + 미래 12 = 30
		expect(mid.data.length).toBe(30);
		expect(mid.data.slice(0, 17).every((x) => x == null)).toBe(true);
		expect(mid.data[17]).not.toBeNull(); // anchor
		expect(mid.data[18]).toBe(2); // q50 첫값
	});

	it('regimePath status 없음 → forward 경로 채움', () => {
		const v = buildMacroSimView(okSim({ forward: [{ h: 1, pContraction: 0.3 }, { h: 2, pContraction: 0.32 }], history: [0.2, 0.25], current: 0.25, ergodic: 0.33 }) as never, 'kr');
		expect(v.regimePath).not.toBeNull();
		expect(v.regimePath!.forward.length).toBe(2);
		expect(v.regimePath!.forward[0].p).toBe(0.3);
		expect(v.regimePath!.current).toBe(0.25);
	});

	it('status ≠ ok 또는 null → holdback(빈 카드)', () => {
		expect(buildMacroSimView(null, 'kr').status).toBe('holdback');
		expect(buildMacroSimView({ status: '표본 부족·표시 보류', fan: {} } as never, 'kr').status).toBe('holdback');
		expect(buildMacroSimView(null, 'kr').fanCards.length).toBe(0);
	});
});
