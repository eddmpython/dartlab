// 거시 forward 시뮬 · 브라우저 *런타임* BVAR 계산. 별도 데이터 빌드/배선·HF publish 0.
// 이미 로드된 observations(rt.macro.getSeries)로 BVAR 추정 → 해석적 분위 팬 + IRF.
// ⛔ Python 정본(src/dartlab/macro/simulate)과 *동일 수식* · golden parity 테스트로 drift 차단.
//    난수 0(해석적)이라 Python·TS byte 수준 일치. fan = 예측오차 분산 누적(Lütkepohl §2.2).
import type { MacroPoint, MacroSimFile, MacroSimFanVar, MacroSimScenario } from '@dartlab/ui-contracts';

// ── 시장 변수 사양 (Python _MARKET_SPECS mirror) ──
export interface SimVarSpec {
	id: string;
	label: string;
	transform: 'level' | 'logdiff100';
}
// 6변수 (Python _MARKET_SPECS mirror). 신용축 = BAA10Y(Baa−10Y 스프레드, 1986~). HY 는
// ICE BofA 라이선스로 FRED 가 2023-06~ 만 제공 → 백필 불가라 정통 신용스프레드로 편입.
const US_SPECS: SimVarSpec[] = [
	{ id: 'INDPRO', label: '산업생산', transform: 'logdiff100' },
	{ id: 'CPIAUCSL', label: '소비자물가', transform: 'logdiff100' },
	{ id: 'DCOILWTICO', label: '원유', transform: 'logdiff100' },
	{ id: 'FEDFUNDS', label: '정책금리', transform: 'level' },
	{ id: 'DGS10', label: '10년금리', transform: 'level' },
	{ id: 'BAA10Y', label: '신용스프레드', transform: 'level' }
];
const KR_SPECS: SimVarSpec[] = [
	{ id: 'IPI', label: '산업생산', transform: 'logdiff100' },
	{ id: 'CPI', label: '소비자물가', transform: 'logdiff100' },
	{ id: 'DCOILWTICO', label: '원유', transform: 'logdiff100' },
	{ id: 'BASE_RATE', label: '기준금리', transform: 'level' },
	{ id: 'USDKRW', label: '원/달러', transform: 'logdiff100' },
	{ id: 'BAA10Y', label: '신용스프레드', transform: 'level' }
];
const MARKET: Record<'KR' | 'US', { specs: SimVarSpec[]; policyIdx: number }> = {
	US: { specs: US_SPECS, policyIdx: 3 },
	KR: { specs: KR_SPECS, policyIdx: 3 }
};
const DELTA: Record<string, number> = { level: 0.8, logdiff100: 0.0 };
// 표준정규 분위 z (Python _Z 와 동일 상수).
const Z: Record<number, number> = { 5: -1.6448536, 10: -1.2815516, 25: -0.6744898, 50: 0, 75: 0.6744898, 90: 1.2815516, 95: 1.6448536 };

type Mat = number[][];

// ── 행렬 헬퍼 (numpy 대응, 작은 행렬 전용) ──
const zeros = (r: number, c: number): Mat => Array.from({ length: r }, () => new Array(c).fill(0));
const eye = (n: number): Mat => Array.from({ length: n }, (_, i) => Array.from({ length: n }, (_, j) => (i === j ? 1 : 0)));
function transpose(a: Mat): Mat {
	const r = a.length, c = a[0].length, t = zeros(c, r);
	for (let i = 0; i < r; i++) for (let j = 0; j < c; j++) t[j][i] = a[i][j];
	return t;
}
function matMul(a: Mat, b: Mat): Mat {
	const r = a.length, k = b.length, c = b[0].length, out = zeros(r, c);
	for (let i = 0; i < r; i++) for (let m = 0; m < k; m++) { const aim = a[i][m]; if (aim === 0) continue; for (let j = 0; j < c; j++) out[i][j] += aim * b[m][j]; }
	return out;
}
// Gauss-Jordan 역행렬(부분 피벗). 특이/실패 시 null.
function matInv(src: Mat): Mat | null {
	const n = src.length;
	const a = src.map((row, i) => [...row, ...eye(n)[i]]);
	for (let col = 0; col < n; col++) {
		let piv = col;
		for (let r = col + 1; r < n; r++) if (Math.abs(a[r][col]) > Math.abs(a[piv][col])) piv = r;
		if (Math.abs(a[piv][col]) < 1e-12) return null;
		[a[col], a[piv]] = [a[piv], a[col]];
		const d = a[col][col];
		for (let j = 0; j < 2 * n; j++) a[col][j] /= d;
		for (let r = 0; r < n; r++) { if (r === col) continue; const f = a[r][col]; if (f === 0) continue; for (let j = 0; j < 2 * n; j++) a[r][j] -= f * a[col][j]; }
	}
	return a.map((row) => row.slice(n));
}
// 하삼각 Cholesky (A = L Lᵀ). 비양정치 시 null.
function cholesky(a: Mat): Mat | null {
	const n = a.length, l = zeros(n, n);
	for (let i = 0; i < n; i++) for (let j = 0; j <= i; j++) {
		let s = a[i][j];
		for (let k = 0; k < j; k++) s -= l[i][k] * l[j][k];
		if (i === j) { if (s <= 0) return null; l[i][j] = Math.sqrt(s); }
		else l[i][j] = s / l[j][j];
	}
	return l;
}
// OLS 계수 (XᵀX)⁻¹ Xᵀy · 잔차 std(ddof) 용.
function olsResidStd(x: Mat, y: number[], ddof: number): number {
	const xt = transpose(x), xtxInv = matInv(matMul(xt, x));
	if (!xtxInv) return 1;
	const xty = matMul(xt, y.map((v) => [v]));
	const beta = matMul(xtxInv, xty).map((r) => r[0]);
	let ss = 0;
	for (let i = 0; i < x.length; i++) { let pred = 0; for (let j = 0; j < beta.length; j++) pred += x[i][j] * beta[j]; ss += (y[i] - pred) ** 2; }
	const dof = x.length - ddof;
	return dof > 0 ? Math.sqrt(ss / dof) : Math.sqrt(ss / x.length);
}

export interface BvarFit { b: Mat; sigma: Mat; n: number; p: number; specs: SimVarSpec[]; lastLevels: number[]; }

// ── BVAR 추정 (Python bvar.py mirror) ──
function arResidStd(panel: Mat, p: number): number[] {
	const t = panel.length, n = panel[0].length, sig: number[] = [];
	for (let i = 0; i < n; i++) {
		const y: number[] = [], x: Mat = [];
		for (let ti = p; ti < t; ti++) { y.push(panel[ti][i]); const row: number[] = []; for (let lag = 1; lag <= p; lag++) row.push(panel[ti - lag][i]); row.push(1); x.push(row); }
		let s = olsResidStd(x, y, p + 1);
		if (!isFinite(s) || s <= 0) { const col = panel.map((r) => r[i]); const mu = col.reduce((a, b) => a + b, 0) / col.length; s = Math.sqrt(col.reduce((a, b) => a + (b - mu) ** 2, 0) / col.length) || 1; }
		sig.push(s);
	}
	return sig;
}
export function estimateBvar(panel: Mat, specs: SimVarSpec[], p: number, lam: number, lastLevels: number[]): BvarFit | null {
	const t = panel.length, n = panel[0].length, k = n * p + 1, eps = 1e-4;
	const sigma = arResidStd(panel, p);
	// Y, X
	const y: Mat = [], x: Mat = [];
	for (let ti = p; ti < t; ti++) { y.push([...panel[ti]]); const row: number[] = []; for (let lag = 1; lag <= p; lag++) row.push(...panel[ti - lag]); row.push(1); x.push(row); }
	// Minnesota dummies
	const yd: Mat = [], xd: Mat = [];
	for (let lag = 1; lag <= p; lag++) for (let r = 0; r < n; r++) {
		const yr = new Array(n).fill(0), xr = new Array(k).fill(0);
		xr[(lag - 1) * n + r] = (lag * sigma[r]) / lam;
		if (lag === 1) yr[r] = (DELTA[specs[r].transform] * sigma[r]) / lam;
		yd.push(yr); xd.push(xr);
	}
	for (let r = 0; r < n; r++) { const yr = new Array(n).fill(0); yr[r] = sigma[r]; yd.push(yr); xd.push(new Array(k).fill(0)); }
	{ const yr = new Array(n).fill(0), xr = new Array(k).fill(0); xr[k - 1] = 1 / eps; yd.push(yr); xd.push(xr); }
	const xs = [...x, ...xd], ys = [...y, ...yd];
	const xst = transpose(xs), xtxInv = matInv(matMul(xst, xs));
	if (!xtxInv) return null;
	const b = matMul(xtxInv, matMul(xst, ys)); // (k, n)
	// resid, sPost, sigmaHat
	const xsB = matMul(xs, b), resid = xs.map((_, i) => ys[i].map((v, j) => v - xsB[i][j]));
	const sPost = matMul(transpose(resid), resid);
	const nu = xs.length - k, denom = Math.max(nu - n - 1, 1);
	const sigmaHat = sPost.map((row) => row.map((v) => v / denom));
	return { b, sigma: sigmaHat, n, p, specs, lastLevels };
}
// companion 행렬
function companion(fit: BvarFit): Mat {
	const { n, p, b } = fit, c = zeros(n * p, n * p);
	for (let lag = 1; lag <= p; lag++) for (let i = 0; i < n; i++) for (let j = 0; j < n; j++) c[i][(lag - 1) * n + j] = b[(lag - 1) * n + j][i];
	for (let i = 0; i < n * (p - 1); i++) c[n + i][i] = 1;
	return c;
}
export function maxCompanionModulus(fit: BvarFit): number {
	// 스펙트럴 반경 ρ(C) ≈ Gelfand 공식 ‖C^k‖_F^(1/k) (k 큼) · 임의(복소고유값) 행렬에 수렴.
	// power iteration 은 복소 dominant 고유값에서 모듈러스를 못 잡아 부적합. 안정성 게이트(ρ<1)용.
	const c = companion(fit), m = c.length, K = 100;
	let ck = c.map((r) => [...r]);
	for (let k = 1; k < K; k++) ck = matMul(ck, c);
	let fro = 0;
	for (let i = 0; i < m; i++) for (let j = 0; j < m; j++) fro += ck[i][j] * ck[i][j];
	fro = Math.sqrt(fro);
	return fro === 0 ? 0 : Math.pow(fro, 1 / K);
}

// ── 평균 경로 + 예측오차 SE (Python fan.py mirror) ──
function meanPath(fit: BvarFit, history: Mat, horizon: number): Mat {
	const { n, p, b } = fit, hist = history.slice(-p), buf = hist.map((r) => [...r]), out: Mat = [];
	for (let h = 0; h < horizon; h++) {
		const x: number[] = [];
		for (let lag = 1; lag <= p; lag++) x.push(...buf[buf.length - lag]);
		const yhat = new Array(n).fill(0);
		for (let j = 0; j < n; j++) { for (let m = 0; m < n * p; m++) yhat[j] += x[m] * b[m][j]; yhat[j] += b[n * p][j]; }
		out.push(yhat); buf.push(yhat);
	}
	return out;
}
// VAR(p) MA 계수 Φ_0..Φ_{horizon-1} (각 n×n). Φ_h = J C^h J^T. fan·scenarioPath 공유 닻(drift 차단).
function companionMA(fit: BvarFit, horizon: number): Mat[] {
	const { n, p } = fit, c = companion(fit), npn = n * p;
	const sel = zeros(n, npn); for (let i = 0; i < n; i++) sel[i][i] = 1;
	const selT = transpose(sel);
	const coefs: Mat[] = [];
	let cj = eye(npn);
	for (let h = 0; h < horizon; h++) { coefs.push(matMul(matMul(sel, cj), selT)); cj = matMul(cj, c); }
	return coefs;
}
function forecastSE(fit: BvarFit, horizon: number): Mat {
	const { n } = fit, coefs = companionMA(fit, horizon), sigma = fit.sigma;
	const accum = zeros(n, n), se: Mat = [];
	for (let h = 0; h < horizon; h++) {
		const phi = coefs[h]; // Φ_h (n,n)
		const contrib = matMul(matMul(phi, sigma), transpose(phi));
		for (let i = 0; i < n; i++) for (let j = 0; j < n; j++) accum[i][j] += contrib[i][j];
		se.push(Array.from({ length: n }, (_, i) => Math.sqrt(Math.max(accum[i][i], 0))));
	}
	return se;
}

// 해석적 분위 팬 (Python forwardFan mirror). 결정론·byte 일치 대상.
export function forwardFan(fit: BvarFit, history: Mat, horizon: number, histMonths = 18): Record<string, MacroSimFanVar> {
	const mean = meanPath(fit, history, horizon), se = forecastSE(fit, horizon);
	const QS = [5, 25, 50, 75, 95] as const;
	const out: Record<string, MacroSimFanVar> = {};
	fit.specs.forEach((s, i) => {
		const rec: MacroSimFanVar = {
			transform: s.transform, label: s.label, seriesId: s.id,
			history: history.slice(-histMonths).map((r) => r[i]),
			mean: mean.map((r) => r[i]),
			q5: [], q25: [], q50: [], q75: [], q95: []
		};
		const dyn = rec as unknown as Record<string, number[]>;
		for (const q of QS) dyn[`q${q}`] = mean.map((r, h) => r[i] + Z[q] * se[h][i]);
		if (s.transform === 'logdiff100') {
			const lvl0 = fit.lastLevels[i];
			for (const q of QS) { let acc = 0; dyn[`level_q${q}`] = dyn[`q${q}`].map((g) => { acc += g / 100; return lvl0 * Math.exp(acc); }); }
		}
		out[s.label] = rec;
	});
	return out;
}

// ── 월말 리샘플 + 정상성 변환 (Python _panel.py mirror) ──
function monthly(pts: MacroPoint[]): Map<string, number> {
	const m = new Map<string, number>();
	for (const p of pts) m.set(p.d.slice(0, 6), p.v); // d 오름차순 → 같은 달 마지막 값
	return m;
}
function buildPanel(seriesById: Record<string, MacroPoint[]>, specs: SimVarSpec[], minObs: number): { panel: Mat; lastLevels: number[]; yms: string[] } | null {
	const maps = specs.map((s) => monthly(seriesById[s.id] ?? []));
	if (maps.some((m) => m.size === 0)) return null;
	let common: string[] | null = null;
	for (const m of maps) { const keys = [...m.keys()]; common = common === null ? keys : common.filter((k) => m.has(k)); }
	common = (common ?? []).sort();
	if (common.length < minObs + 1) return null;
	const levels: Mat = common.map((ym) => maps.map((m) => m.get(ym) as number));
	const t = levels.length, n = specs.length, x: Mat = [];
	for (let ti = 1; ti < t; ti++) {
		const row: number[] = [];
		for (let i = 0; i < n; i++) {
			if (specs[i].transform === 'logdiff100') { const a = levels[ti - 1][i], b = levels[ti][i]; if (a <= 0 || b <= 0) return null; row.push(100 * (Math.log(b) - Math.log(a))); }
			else row.push(levels[ti][i]);
		}
		x.push(row);
	}
	if (x.some((r) => r.some((v) => !isFinite(v)))) return null;
	return { panel: x, lastLevels: levels[t - 1], yms: common.slice(1) };
}

// ── IRF (Python irf.py mirror) ──
function impulseResponse(fit: BvarFit, horizon: number, shockVar: number): Record<string, number[]> {
	const { n, p, b } = fit, l = cholesky(fit.sigma);
	const out: Record<string, number[]> = {};
	if (!l) return out;
	const impact = new Array(n).fill(0); for (let i = 0; i < n; i++) impact[i] = l[i][shockVar];
	const scale = impact[shockVar] !== 0 ? 1 / l[shockVar][shockVar] : 0; // shockSize=1
	const imp = impact.map((v) => v * scale);
	const resp: number[][] = [imp];
	const buf: number[][] = Array.from({ length: p }, () => new Array(n).fill(0)); buf.push(imp);
	for (let h = 1; h <= horizon; h++) {
		const x: number[] = []; for (let lag = 1; lag <= p; lag++) x.push(...buf[buf.length - lag]);
		const yhat = new Array(n).fill(0);
		for (let j = 0; j < n; j++) for (let m = 0; m < n * p; m++) yhat[j] += x[m] * b[m][j];
		resp.push(yhat); buf.push(yhat);
	}
	fit.specs.forEach((s, i) => { out[s.label] = resp.map((r) => r[i]); });
	return out;
}

// ── 시나리오 조건부 forward (Python scenarioPath.py mirror) ──
// 정책 변수 경로를 고정한 Gaussian 조건부 예측(Doan-Litterman-Sims 1984). 해석적·결정론 → parity.
//   μ̃ = μ + Ω R'(R Ω R')⁻¹ δ,   Ω̃ = Ω − Ω R'(R Ω R')⁻¹ R Ω
interface ScenarioPreset { key: string; labelKr: string; labelEn: string; condLabelKr: string; condLabelEn: string; deltaPath: number[]; }
const SCENARIO_PRESETS: ScenarioPreset[] = [
	{ key: 'tighten', labelKr: '긴축 +100bp', labelEn: 'Tightening +100bp', condLabelKr: '정책금리 +100bp · 6M', condLabelEn: 'policy +100bp · 6M', deltaPath: [1, 1, 1, 1, 1, 1] },
	{ key: 'ease', labelKr: '완화 −150bp', labelEn: 'Easing −150bp', condLabelKr: '정책금리 −25bp/월 · 6M', condLabelEn: 'policy −25bp/mo · 6M', deltaPath: [-0.25, -0.5, -0.75, -1, -1.25, -1.5] }
];

// (H·n, H·n) 누적 예측오차 공분산 Ω. 블록(a,b) = Σ_{j=0}^{min(a,b)} Φ_j Σ Φ_{j+|b−a|}'.
function stackedCov(fit: BvarFit, horizon: number): Mat {
	const coefs = companionMA(fit, horizon), sigma = fit.sigma, n = fit.n, hn = horizon * n;
	const omega = zeros(hn, hn);
	for (let a = 0; a < horizon; a++) for (let b = a; b < horizon; b++) {
		const d = b - a, block = zeros(n, n);
		for (let j = 0; j <= a; j++) {
			const cc = matMul(matMul(coefs[j], sigma), transpose(coefs[j + d]));
			for (let i = 0; i < n; i++) for (let q = 0; q < n; q++) block[i][q] += cc[i][q];
		}
		for (let i = 0; i < n; i++) for (let q = 0; q < n; q++) { omega[a * n + i][b * n + q] = block[i][q]; if (a !== b) omega[b * n + q][a * n + i] = block[i][q]; }
	}
	return omega;
}

// 정책 변수(condIdx)를 baseline+condDeltas 로 고정한 조건부 forward 분위 경로(forwardFan 동형).
export function conditionalPath(fit: BvarFit, history: Mat, condIdx: number, condDeltas: number[], horizon: number): Record<string, MacroSimFanVar> {
	const n = fit.n, mean = meanPath(fit, history, horizon), omega = stackedCov(fit, horizon);
	const hn = horizon * n, m = Math.min(condDeltas.length, horizon);
	const muStack: number[] = [];
	for (let h = 0; h < horizon; h++) for (let i = 0; i < n; i++) muStack.push(mean[h][i]);
	const omRt = zeros(hn, m); // Ω R' · column a = Ω[:, a·n+condIdx]
	for (let r = 0; r < hn; r++) for (let a = 0; a < m; a++) omRt[r][a] = omega[r][a * n + condIdx];
	const rOmRt = zeros(m, m); // R Ω R' = omRt 의 조건 행
	for (let a = 0; a < m; a++) for (let bb = 0; bb < m; bb++) rOmRt[a][bb] = omRt[a * n + condIdx][bb];
	const inv = matInv(rOmRt);
	if (!inv) return {}; // fail-closed
	const gain = matMul(omRt, inv); // (hn × m)
	const muCond = muStack.map((v, r) => { let s = v; for (let a = 0; a < m; a++) s += gain[r][a] * condDeltas[a]; return s; });
	const condSE: number[] = []; // sqrt(diag(Ω) − diag(gain · R Ω))
	for (let r = 0; r < hn; r++) { let red = 0; for (let a = 0; a < m; a++) red += gain[r][a] * omega[a * n + condIdx][r]; condSE.push(Math.sqrt(Math.max(omega[r][r] - red, 0))); }
	const QS = [5, 25, 50, 75, 95] as const;
	const out: Record<string, MacroSimFanVar> = {};
	fit.specs.forEach((s, i) => {
		const cm = (h: number) => muCond[h * n + i], cse = (h: number) => condSE[h * n + i];
		const rec: MacroSimFanVar = { transform: s.transform, label: s.label, seriesId: s.id, mean: Array.from({ length: horizon }, (_, h) => cm(h)), q5: [], q25: [], q50: [], q75: [], q95: [] };
		const dyn = rec as unknown as Record<string, number[]>;
		for (const q of QS) dyn[`q${q}`] = Array.from({ length: horizon }, (_, h) => cm(h) + Z[q] * cse(h));
		if (s.transform === 'logdiff100') {
			const lvl0 = fit.lastLevels[i];
			for (const q of QS) { let acc = 0; dyn[`level_q${q}`] = dyn[`q${q}`].map((g) => { acc += g / 100; return lvl0 * Math.exp(acc); }); }
		}
		out[s.label] = rec;
	});
	return out;
}

// SCENARIO_PRESETS 전체를 조건부 경로로 산출 → 다이얼로그 overlay 소비.
function buildScenarios(fit: BvarFit, history: Mat, market: 'KR' | 'US', horizon: number): MacroSimScenario[] {
	const condIdx = MARKET[market].policyIdx;
	return SCENARIO_PRESETS.map((p) => ({
		key: p.key, label: p.labelKr, labelEn: p.labelEn, condLabel: p.condLabelKr, condLabelEn: p.condLabelEn,
		condVar: fit.specs[condIdx].label, fan: conditionalPath(fit, history, condIdx, p.deltaPath, horizon)
	}));
}

/**
 * 거시 forward 시뮬을 *런타임* 계산. getSeries(이미 로드된 observations)로 BVAR → 해석적 팬.
 * 반환 = MacroSimFile(Python toPayload 와 동형). 데이터 부족·불안정은 fail-closed(status).
 */
export async function computeMacroSim(
	market: 'KR' | 'US',
	getSeries: (id: string) => Promise<MacroPoint[] | null>,
	opts: { horizon?: number; lag?: number; lam?: number; minObs?: number } = {}
): Promise<MacroSimFile> {
	const horizon = opts.horizon ?? 12, lag = opts.lag ?? 6, lam = opts.lam ?? 0.2, minObs = opts.minObs ?? 120;
	const cfg = MARKET[market];
	const ids = [...new Set(cfg.specs.map((s) => s.id))];
	const loaded = await Promise.all(ids.map(async (id) => [id, await getSeries(id)] as const));
	const seriesById: Record<string, MacroPoint[]> = {};
	for (const [id, pts] of loaded) if (pts) seriesById[id] = pts;

	const hold = (status: string, missing: { id: string; status: string; reason: string }[] = []): MacroSimFile => ({
		market, status, asOf: '', horizon, model: { kind: 'BVAR', status: '표시 보류' }, fan: {}, irf: {}, regimePath: { status }, missing
	});

	const built = buildPanel(seriesById, cfg.specs, minObs);
	if (!built) return hold('표본 부족·표시 보류', cfg.specs.filter((s) => !seriesById[s.id]).map((s) => ({ id: s.id, status: '표시 보류', reason: '시리즈 부재' })));

	const fit = estimateBvar(built.panel, cfg.specs, lag, lam, built.lastLevels);
	if (!fit) return hold('추정 실패·표시 보류');
	const eig = maxCompanionModulus(fit);
	// 게이트 1.05 · Gelfand(Frobenius) 추정이 near-unit-root(정책금리 ρ≈0.997)·고차원에서 ~수% 과대평가해도
	// 통과, 진짜 폭발(비정상)만 fail-close. fan 유한성(아래)이 2차 가드.
	if (!isFinite(eig) || eig >= 1.05) return hold('불안정(비정상)·표시 보류', [{ id: 'stability', status: '표시 보류', reason: `eig ${eig.toFixed(3)}` }]);

	const fan = forwardFan(fit, built.panel, horizon);
	const fanFinite = Object.values(fan).every((v) => v.q5.every(isFinite) && v.q95.every(isFinite));
	if (!fanFinite) return hold('불안정·표시 보류', [{ id: 'fan', status: '표시 보류', reason: '밴드 비유한' }]);
	const irf: MacroSimFile['irf'] = { ...impulseResponse(fit, 24, cfg.policyIdx), shockLabel: '정책금리 +100bp', caveat: 'recursive-identification·illustrative' };
	const scenarios = buildScenarios(fit, built.panel, market, horizon);
	const nObs = built.panel.length;
	// regimePath = Hamilton EM(중) → TS 런타임 미포팅. 현재 Python 도 분리도 약해 보류 → 일관 보류.
	return {
		market, status: 'ok', asOf: built.yms[built.yms.length - 1], horizon,
		model: { kind: 'BVAR', lag, prior: 'minnesota', nObs, companionEig: +eig.toFixed(4), status: 'ok' },
		fan, irf, scenarios, regimePath: { status: '국면경로 · 런타임 미산출' }, missing: []
	};
}
