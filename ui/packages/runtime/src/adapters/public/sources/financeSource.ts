// 터미널 재무 데이터층 · dart/finance/{code}.parquet (HF, per-company) 을 hyparquet 로 직독.
// DuckDB-WASM 불필요 (per-company 파일 작음 → 전 row 읽고 JS 정규화). 28 표준계정 매핑은
// src/dartlab/viz/display/finance/accounts.py(_STANDARDS) 포팅. 분기 누적(YTD)→TTM 환산.
// 핵심 10 카드 spec 을 클라이언트에서 계산 (ui/web viz/catalog/finance.py 의 dashboard 핵심).
// 타입 정본 = contracts (옛 로컬 재정의는 contracts 로 승격 완료 · 중복 정의 금지).
import type { FinCard, FinMode, FinScope, FinSeries, Num, StmtKind, StmtRow, TerminalFinance, TerminalFinanceBundle } from '@dartlab/ui-contracts';
import { resolveMarket } from '@dartlab/ui-contracts';
import { moduleFallbackCore, type DataCore } from '../../../data/fetch/request';
// 28 표준계정·계정매칭·파싱 primitive 는 data/finance/accounts.ts 단일 SSOT (블로그 annual.ts 와 공유).
import { buildGrid, FINANCE_COLUMNS, isStock, num, Q_BY_CODE, type Parsed, type RawRow } from '../../../data/finance/accounts';

const browser = typeof window !== 'undefined';

// 재무제표 표(손익/재무상태/현금흐름) 행 정의 · STD key + 표시 라벨.
const STMT_DEF: Record<StmtKind, { key: string; kr: string; en: string }[]> = {
	IS: [
		{ key: 'revenue', kr: '매출액', en: 'Revenue' },
		{ key: 'costOfSales', kr: '매출원가', en: 'COGS' },
		{ key: 'grossProfit', kr: '매출총이익', en: 'Gross profit' },
		{ key: 'sga', kr: '판매관리비', en: 'SG&A' },
		{ key: 'operatingIncome', kr: '영업이익', en: 'Operating income' },
		{ key: 'financeIncome', kr: '금융수익', en: 'Finance income' },
		{ key: 'financeCosts', kr: '금융비용', en: 'Finance costs' },
		{ key: 'incomeTax', kr: '법인세비용', en: 'Income tax' },
		{ key: 'netIncome', kr: '당기순이익', en: 'Net income' }
	],
	BS: [
		{ key: 'assets', kr: '자산총계', en: 'Assets' },
		{ key: 'currentAssets', kr: '유동자산', en: 'Current assets' },
		{ key: 'cash', kr: '현금성자산', en: 'Cash' },
		{ key: 'inventories', kr: '재고자산', en: 'Inventories' },
		{ key: 'receivables', kr: '매출채권', en: 'Receivables' },
		{ key: 'liabilities', kr: '부채총계', en: 'Liabilities' },
		{ key: 'currentLiabilities', kr: '유동부채', en: 'Current liab' },
		{ key: 'equity', kr: '자본총계', en: 'Equity' },
		{ key: 'retainedEarnings', kr: '이익잉여금', en: 'Retained earnings' }
	],
	CF: [
		{ key: 'cfOperating', kr: '영업활동현금흐름', en: 'Operating CF' },
		{ key: 'cfInvesting', kr: '투자활동현금흐름', en: 'Investing CF' },
		{ key: 'cfFinancing', kr: '재무활동현금흐름', en: 'Financing CF' },
		{ key: 'capex', kr: '설비투자(CAPEX)', en: 'CapEx' },
		{ key: 'dividendsPaid', kr: '배당금지급', en: 'Dividends paid' }
	]
};

const TRILLION = 1e12; // 조 KRW 환산

// 표시 모드: 연간 / 분기(standalone 단일분기) / TTM(직전 4분기 합). 기본 = 분기 (계약 FinMode·번들 정의는 contracts).

// raw 행 캐시·번들 결과 캐시(옛 rowsCache·bundleCache Map)는 폐기 · fetch 코어가 parquet read 레벨에서
// 캐시(60분 TTL·LRU 256)·dedup 한다(데이터 워크벤치 SSOT 이관 P1). transform(번들 빌드)은 재실행되어도
// read 는 공유되며, 연결(CFS)·별도(OFS)·차트·표가 같은 cacheKey(finance.rows:{code}) read 1회를 나눠 쓴다.

// 재무 parquet 경로 · KR=dart/finance/{code}·US=edgar/financeStmt/{ticker}. 둘 다 FINANCE_COLUMNS
// 동형 스키마(US 는 파사드 Company.panel 표준화를 빌드타임 bake · edgar stage). 같은 reader·집계.
// resolveMarket SSOT 로 분기 (6자리=KR·영문=US ticker). US CIK 만 있는 경우는 ticker 부재 → dart 경로
// 폴백(미존재 → null, 정직 비표시).
function financeParquetPath(code: string): string {
	const m = resolveMarket(code);
	return m.market === 'US' && m.ticker ? `edgar/financeStmt/${m.ticker}.parquet` : `dart/finance/${code}.parquet`;
}

// 회사 parquet raw 행 · core 가 read 레벨 캐시·dedup. 미존재/실패 = null(정직 폴백).
function loadRows(core: DataCore, code: string): Promise<RawRow[] | null> {
	return core
		.requestParquetRows<RawRow>({
			origin: 'hfRange',
			path: financeParquetPath(code),
			columns: FINANCE_COLUMNS,
			cacheKey: `finance.rows:${code}`,
			cache: { scope: 'memory', ttlMs: 3_600_000, maxEntries: 256 }
		})
		.catch((e) => {
			console.warn('[terminal/finance] load failed', code, e);
			return null;
		});
}

// loadFinanceRows 는 landing(공시뷰어 provideFinanceRows)이 core 없이 (code)=>rows 콜백으로 주입한다 ·
// 시그니처 불변이 강행 제약. 따라서 이 경로 전용 core 를 모듈 내 lazy 생성(어댑터당 1 싱글턴 금지 원칙은
// 어댑터 컨텍스트 한정 · 여기는 어댑터 밖 셸 주입 콜백이라, read 레벨 bounded 캐시 확보가 목적).
const financeRowsCore = moduleFallbackCore();

// 정량재무제표 표(viewer FinanceDialog)용 raw 행 · bundle()(차트)과 같은 core read 캐시 공유라 회사당 1회만
// 다운로드. DuckDB-WASM 제거 후 표가 이 행으로 JS 집계(financeQuery). 미존재/실패 = null.
export function loadFinanceRows(stockCode: string): Promise<RawRow[] | null> {
	if (!browser) return Promise.resolve(null);
	return loadRows(financeRowsCore(), stockCode.trim());
}

// 범위에 파싱 가능한 데이터(분기·금액)가 있는지 · 가용 범위 판정용.
function scopeHasData(rows: RawRow[], fs: FinScope): boolean {
	for (const r of rows) {
		if ((r.fs_div || '') !== fs) continue;
		if (!Q_BY_CODE[String(r.reprt_code || '')] || !Number.isFinite(Number(r.bsns_year)) || num(r.thstrm_amount) == null) continue;
		return true;
	}
	return false;
}

// 터미널 재무 번들 · core 를 어댑터당 1 인스턴스로 주입(전역 싱글턴 금지). read 는 core 가 캐시·dedup 하고,
// 번들 빌드(transform)는 재실행돼도 무거운 read 를 공유하므로 결과 레벨 bundleCache Map 은 폐기.
export function loadTerminalFinance(core: DataCore, stockCode: string, scope?: FinScope): Promise<TerminalFinanceBundle | null> {
	if (!browser) return Promise.resolve(null);
	const code = stockCode.trim();
	return (async () => {
		const rows = await loadRows(core, code);
		if (!rows) return null;
		const avail: FinScope[] = (['CFS', 'OFS'] as FinScope[]).filter((s) => scopeHasData(rows, s));
		if (avail.length === 0) return null;
		// 기본 = 연결 우선(최신성보다 우선) · 연결이 있으면 옛 분기여도 연결, 연결이 아예 없을 때만 별도. 지정 + 가용 시 그대로.
		const fallback: FinScope = avail.includes('CFS') ? 'CFS' : 'OFS';
		const useScope: FinScope = scope && avail.includes(scope) ? scope : fallback;
		const bundle = buildBundle(rows, useScope, avail);
		if (bundle) bundle.currency = resolveMarket(code).market === 'US' ? 'USD' : 'KRW';
		return bundle;
	})();
}

// ── SCE(자본변동표) 브리지 · 최신 연간(11011)·최신 rcept_no 의 합계 차원에서
// 기초자본 → +순이익 → +기타포괄 → −배당 → ±자기주식 → ±기타(잔차 plug) → 기말자본 워터폴.
// 합계 차원 = account_detail 에 '|' 없는 '연결재무제표 [member]'/'재무제표 [member]' root
// (삼성·카카오·POSCO·NAVER·덕양산업·신흥 6사 실측 공통). 미식별·기초/기말/순이익 결측 회사는
// null · 카드 비표시가 정직. 기타 = 기말 anchor 대조 잔차(소유주거래·연결범위변동·주식보상 등).
function buildSceBridge(rows: RawRow[], fs: string, ociFromCis: (year: number) => Num): FinCard | null {
	const nrm = (v: unknown) => String(v ?? '').replace(/\s+/g, ' ').trim();
	const sce = rows.filter((r) => (r.fs_div || '') === fs && r.sj_div === 'SCE' && String(r.reprt_code || '') === '11011');
	let year = -1;
	for (const r of sce) { const y = Number(r.bsns_year); if (Number.isFinite(y) && y > year) year = y; }
	if (year < 0) return null;
	const ofYear = sce.filter((r) => Number(r.bsns_year) === year);
	let rcept = ''; // 정정공시 · 최신 접수만
	for (const r of ofYear) { const rc = String(r.rcept_no || ''); if (rc > rcept) rcept = rc; }
	const byNm = new Map<string, number>(); // 합계 차원 계정명 → 금액 (중복 nm 은 첫 행)
	for (const r of ofYear) {
		if (String(r.rcept_no || '') !== rcept) continue;
		const d = nrm(r.account_detail);
		if (d.includes('|') || !d.includes('재무제표')) continue;
		const nm = nrm(r.account_nm);
		const amt = num(r.thstrm_amount);
		if (nm && amt != null && !byNm.has(nm)) byNm.set(nm, amt);
	}
	if (byNm.size === 0) return null;
	const items = [...byNm.entries()].map(([nm, amt]) => ({ nm, amt }));
	const pick = (...preds: ((nm: string) => boolean)[]): number | null => {
		for (const p of preds) { const hit = items.find((x) => p(x.nm)); if (hit) return hit.amt; }
		return null;
	};
	const begin = pick((n) => n.includes('수정후') && n.includes('기초'), (n) => n.includes('기초'));
	const end = pick((n) => n.includes('기말'), (n) => n.includes('자본총계'));
	const ni = pick((n) => n.includes('당기순이익'), (n) => n.includes('순이익') && !n.includes('총포괄'));
	if (begin == null || end == null || ni == null) return null;
	// 기타포괄: SCE 총포괄 행(TCI−NI) → SCE 단독 '기타포괄손익' 행 → CIS(총포괄−순이익) 폴백 순
	const tci = pick((n) => n.includes('총포괄'));
	const ociRow = items.find((x) => x.nm === '기타포괄손익' || x.nm === '연결기타포괄손익');
	const oci = tci != null ? tci - ni : ociRow ? ociRow.amt : ociFromCis(year);
	// 배당 · 변형 5종 실측('배당'·'연차/중간배당금'·'현금배당'·'배당금지급'·'소유주에 대한 배분…').
	// 항상 자본 유출이라 −|합| (공시 부호 혼재 방어). 주식배당은 자본 내 재분류라 제외.
	let divSum = 0;
	for (const x of items) if (x.nm.includes('배당') && !x.nm.includes('주식배당')) divSum += Math.abs(x.amt);
	// 자기주식 · 취득 = 항상 유출(−|v|), 처분 = 항상 유입(+|v|), 그 외(소각·거래 증감)는 공시 부호 그대로
	let treas = 0;
	for (const x of items) {
		if (!x.nm.includes('자기주식')) continue;
		treas += x.nm.includes('취득') ? -Math.abs(x.amt) : x.nm.includes('처분') ? Math.abs(x.amt) : x.amt;
	}
	const t = (v: number) => +(v / TRILLION).toFixed(3);
	const steps: NonNullable<FinCard['steps']> = [{ name: '기초자본', value: t(begin), total: true }, { name: '순이익', value: t(ni) }];
	if (oci != null) steps.push({ name: '기타포괄', value: t(oci) });
	if (divSum >= TRILLION * 0.0005) steps.push({ name: '배당', value: t(-divSum) });
	if (Math.abs(treas) >= TRILLION * 0.0005) steps.push({ name: '자기주식', value: t(treas) });
	// 잔차 plug · 기말 anchor 정직. |값| 미미(10억 미만 또는 기말의 0.2% 미만)하면 생략.
	const shown = steps.slice(1).reduce((a, s) => a + (s.value ?? 0), 0);
	const plug = +(t(end) - t(begin) - shown).toFixed(3);
	if (Math.abs(plug) >= Math.max(0.001, Math.abs(t(end)) * 0.002)) steps.push({ name: '기타', value: plug });
	steps.push({ name: '기말자본', value: t(end), total: true });
	return { key: 'sceBridge', title: `자본변동 브리지 · FY${String(year).slice(2)}`, unit: '조', kind: 'waterfall', steps, series: [] };
}

function buildBundle(rows: RawRow[], fs: FinScope, availScopes: FinScope[]): TerminalFinanceBundle | null {
	// 손익 출처: IS(별도 손익계산서) 있으면 IS, 없으면 CIS(단일 포괄손익계산서·카카오류) 를 IS 로 채택.
	const incomeSrc = rows.some((r) => (r.fs_div || '') === fs && r.sj_div === 'IS') ? 'IS' : 'CIS';
	const parsed: Parsed[] = [];
	const filedDates: Record<string, string> = {}; // (year,q) → 최초 접수일 · 실적 발표 마커용
	for (const r of rows) {
		{
			const q0 = Q_BY_CODE[String(r.reprt_code || '')];
			const y0 = Number(r.bsns_year);
			const rc = String(r.rcept_no || '').replace(/\D/g, '').slice(0, 8);
			if (q0 && Number.isFinite(y0) && rc.length === 8) {
				const k = `${y0}-${q0}`;
				if (!filedDates[k] || rc < filedDates[k]) filedDates[k] = rc;
			}
		}
		if ((r.fs_div || '') !== fs) continue;
		const q = Q_BY_CODE[String(r.reprt_code || '')];
		const year = Number(r.bsns_year);
		const amt = num(r.thstrm_amount);
		if (!q || !Number.isFinite(year) || amt == null) continue;
		const sjRaw = String(r.sj_div || '');
		const mk = (sj: string): Parsed => ({
			sj,
			year,
			q,
			id: String(r.account_id || ''),
			nm: String(r.account_nm || ''),
			detail: String(r.account_detail || ''),
			ord: num(r.ord) ?? Number.MAX_SAFE_INTEGER,
			amt
		});
		// CIS 원본 레인 · 포괄손익 격차 카드·SCE 브리지 OCI 폴백 전용 (IS 정규화와 독립)
		if (sjRaw === 'CIS') parsed.push(mk('CIS'));
		if (sjRaw === 'IS' || sjRaw === 'CIS') {
			if (sjRaw !== incomeSrc) continue; // 채택 안 한 손익표는 IS 정규화 스킵 (CIS 레인은 위에서 보존)
			parsed.push(mk('IS'));
		} else parsed.push(mk(sjRaw)); // BS · CF · SCE
	}
	if (parsed.length === 0) return null;

	// 표준계정 × (year,q) 매핑 · STD 별 독립 매칭 (row 소비/순서 의존 없음).
	// id 매칭 우선, 없으면 nm 키워드. 같은 셀 다중 후보 시 account_detail='-' 우선·ord 최소.
	const grid = buildGrid(parsed);

	// 사용 가능한 (year,q) 모음 (자산총계 또는 매출 존재 기준) · 분기 우선
	const pkSet = new Set<string>();
	for (const key of ['revenue', 'assets', 'cfOperating', 'netIncome']) {
		for (const pk of grid[key]?.keys() ?? []) pkSet.add(pk);
	}
	const allPk = Array.from(pkSet)
		.map((pk) => {
			const parts = pk.split('-').map(Number); // pk = `${year}-${q}` 구성이라 두 토큰 항상 존재
			return { pk, y: parts[0] ?? 0, q: parts[1] ?? 0 };
		})
		.sort((a, b) => a.y - b.y || a.q - b.q);
	if (allPk.length === 0) return null;

	// 분기(Q1~Q3) 존재 여부 → 분기·TTM 모드 가능. annual 은 Q4(연간) 존재 시.
	const hasInterim = allPk.some((p) => p.q !== 4);
	const hasAnnual = allPk.some((p) => p.q === 4);

	const rawV = (key: string, y: number, q: number): Num => grid[key]?.get(`${y}-${q}`)?.amt ?? null;

	// IS/CF flow standalone(단일분기) · DART 분기 규약 혼합 자동판정.
	// 연도 Σ(Q1..Q3) > annual 이면 YTD 누적(차분), 아니면 standalone(Q4 = annual − Σ).
	const stdCache = new Map<string, Num>();
	const standalone = (key: string, y: number, q: number): Num => {
		const ck = `${key}|${y}|${q}`;
		const hit = stdCache.get(ck);
		if (hit !== undefined) return hit;
		const q1 = rawV(key, y, 1), q2 = rawV(key, y, 2), q3 = rawV(key, y, 3), a = rawV(key, y, 4);
		const allInterim = q1 != null && q2 != null && q3 != null;
		const ytd = allInterim && a != null && q1! + q2! + q3! > a! * 1.05;
		let res: Num;
		if (q === 1) res = q1; // Q1 누적 = Q1 standalone
		else if (q === 4) {
			if (a == null) res = null;
			else if (ytd) res = q3 != null ? a - q3 : null;
			else if (allInterim) res = a - (q1! + q2! + q3!);
			else res = a; // annual-only 연도
		} else {
			const cur = rawV(key, y, q);
			if (cur == null) res = null;
			else if (ytd) { const prev = rawV(key, y, q - 1); res = prev != null ? cur - prev : cur; }
			else res = cur;
		}
		stdCache.set(ck, res);
		return res;
	};

	// SCE 브리지 (모드 무관 · 최신 연간 1개 스냅샷). OCI 폴백 = 같은 연도 CIS 연간(총포괄−순이익).
	const ociFromCis = (y: number): Num => {
		const tci = rawV('cisComprehensive', y, 4);
		const niC = rawV('cisNetIncome', y, 4);
		return tci != null && niC != null ? tci - niC : null;
	};
	const sceBridge = buildSceBridge(rows, fs, ociFromCis);

	// 분기 시즌성 히트맵 · 연도(최신 위)×분기 standalone 매출 격자, 색 = 전년동기比 (모드 무관 스냅샷).
	// YoY 첫 비교 연도를 살리기 위해 값은 최근 8년 표시·비교는 9년째까지 본다.
	const seasonality = ((): FinCard | null => {
		if (!hasInterim) return null;
		const years = [...new Set(allPk.map((p) => p.y))].sort((a, b) => a - b);
		const vq = (y: number, q: number): Num => {
			const v = standalone('revenue', y, q);
			return v == null ? null : +(v / TRILLION).toFixed(3);
		};
		const heatRows: string[] = [];
		const vals: Num[][] = [];
		const yoyG: Num[][] = [];
		for (const y of years.slice(-8).reverse()) {
			const rv = [1, 2, 3, 4].map((q) => vq(y, q));
			if (!rv.some((v) => v != null)) continue;
			heatRows.push(`FY${String(y).slice(2)}`);
			vals.push(rv);
			yoyG.push(rv.map((cur, i) => {
				const prev = vq(y - 1, i + 1);
				return cur != null && prev != null && Math.abs(prev) > 1e-9 ? +(((cur - prev) / Math.abs(prev)) * 100).toFixed(1) : null;
			}));
		}
		if (heatRows.length < 2) return null;
		return { key: 'seasonality', title: '분기 매출 히트맵 (색=YoY)', unit: '조', kind: 'heatmap', series: [], heat: { rows: heatRows, cols: ['Q1', 'Q2', 'Q3', 'Q4'], vals, yoy: yoyG } };
	})();

	// ── 모드별(연간/분기/TTM) 뷰 빌드 ──
	const buildMode = (mode: FinMode): TerminalFinance | null => {
		const isAnnual = mode === 'annual';
		const KEEP = isAnnual ? 24 : 48; // 최대한 많은 기간 (막대 얇아도 무방)
		let used: { y: number; q: number; gi: number }[];
		if (isAnnual) {
			used = allPk.filter((p) => p.q === 4).slice(-KEEP).map((p) => ({ y: p.y, q: 4, gi: -1 }));
		} else if (mode === 'ttm') {
			// TTM 은 직전 4분기 필요 → 앞 3분기(gi<3) 제외해 선두 빈칸 방지
			used = allPk.map((p, gi) => ({ y: p.y, q: p.q, gi })).filter((e) => e.gi >= 3).slice(-KEEP);
		} else {
			used = allPk.map((p, gi) => ({ y: p.y, q: p.q, gi })).slice(-KEEP);
		}
		// 접지 원칙: DART 제출 분기는 그대로 노출. 과거의 "최신 이상치 pop" 휴리스틱은
		// 실제 정식 공시(예: 메모리 슈퍼사이클 분기 급증)를 조용히 삭제해 최신 분기가 누락되는
		// 회귀를 일으켰다 · 값 기준 파괴적 삭제는 폐지하고, 원본 공시값을 표시한다.
		if (used.length === 0) return null;
		const periods = used.map((p) => (isAnnual ? `FY${String(p.y).slice(2)}` : `${String(p.y).slice(2)}Q${p.q}`));

		// 값: BS = 시점. flow(IS·CF) = annual 연간 / quarter 단일분기 / ttm 직전 4분기 합.
		const flowAt = (key: string, i: number): Num => {
			const p = used[i];
			if (!p) return null;
			if (isAnnual) return rawV(key, p.y, 4); // 사업보고서 flow = 연간 누계 원본 (standalone 은 Q4 석달치라 FY 라벨과 불일치)
			if (mode === 'quarter') return standalone(key, p.y, p.q);
			let s = 0;
			for (let k = 0; k < 4; k++) {
				const gi = p.gi - k;
				if (gi < 0) return null;
				const a = allPk[gi];
				if (!a) return null;
				const v = standalone(key, a.y, a.q);
				if (v == null) return null;
				s += v;
			}
			return s;
		};
		const valAtIdx = (key: string, i: number): Num => {
			if (isStock(key)) {
				const p = used[i];
				return p ? rawV(key, p.y, p.q) : null;
			}
			return flowAt(key, i);
		};
		const lag = isAnnual ? 1 : 4; // YoY: 연간 1년 전, 분기/TTM 4분기 전

		// 계정 시리즈 · 조 KRW 환산 (BS 시점, flow 모드별).
		// 정밀도 6자리(=백만원) · toFixed(3)은 0.001조=10억 양자화라 소형주(매출 수백억)는 전 값이 10억 배수로
		// 반올림돼 실제값(1,147억)이 1,150억으로 틀리게 보였다. 대형주는 6자리여도 표시 단계에서 동일 반올림.
		const ser = (key: string): Num[] => used.map((_, i) => { const v = valAtIdx(key, i); return v == null ? null : +(v / TRILLION).toFixed(6); });
		const raw = (key: string): Num[] => used.map((_, i) => valAtIdx(key, i));
		const ratio = (numK: string, denK: string, scale = 100, avgDen = false): Num[] => {
			const n = raw(numK);
			const d = raw(denK);
			return used.map((_, i) => {
				const nn = n[i];
				let dd = d[i];
				if (avgDen && i > 0 && d[i - 1] != null && dd != null) dd = (dd + d[i - 1]!) / 2;
				return nn != null && dd != null && dd !== 0 ? +((nn / dd) * scale).toFixed(1) : null;
			});
		};
		const yoy = (key: string): Num[] => {
			const v = raw(key);
			return used.map((_, i) => {
				const cur = v[i];
				const prev = i >= lag ? v[i - lag] : null;
				return cur != null && prev != null && prev !== 0 ? +(((cur - prev) / Math.abs(prev)) * 100).toFixed(1) : null;
			});
		};
		const compose = (...parts: [string, number][]): Num[] =>
			used.map((_, i) => {
				let s = 0;
				let any = false;
				for (const [k, sign] of parts) { const v = valAtIdx(k, i); if (v != null) { s += sign * v; any = true; } }
				return any ? +(s / TRILLION).toFixed(6) : null; // 6자리=백만원 (ser 와 동일 · 소형주 FCF 10억 양자화 방지)
			});

		// 보조: grossProfit 없으면 revenue - costOfSales
		const grossProfitSer = (): Num[] => {
			const gp = raw('grossProfit');
			const rev = raw('revenue');
			const cogs = raw('costOfSales');
			return used.map((_, i) => {
				const direct = gp[i];
				if (direct != null) return direct;
				return rev[i] != null && cogs[i] != null ? rev[i]! - cogs[i]! : null;
			});
		};
		const gpRatio = (): Num[] => {
			const g = grossProfitSer();
			const rev = raw('revenue');
			return used.map((_, i) => (g[i] != null && rev[i] ? +((g[i]! / rev[i]!) * 100).toFixed(1) : null));
		};

		const C = { rev: '#5b9bf0', op: '#fb923c', net: '#34d399', good: '#34d399', warn: '#fbbf24', purple: '#a78bfa', red: '#f0616f', blue: '#60a5fa', cyan: '#22d3ee', dim: '#64748b' };

		// FCF (원 단위) + raw 시리즈 분모 비율 (CF 마진용)
		const fcfRaw = used.map((_, i) => { const op = valAtIdx('cfOperating', i); const cx = valAtIdx('capex', i); return op != null ? op - (cx ?? 0) : null; });
		const ratioOfSeries = (numRaw: Num[], denKey: string, scale = 100): Num[] => { const d = raw(denKey); return used.map((_, i) => (numRaw[i] != null && d[i] ? +((numRaw[i]! / d[i]!) * scale).toFixed(1) : null)); };

		// 현금전환주기 · DSO·DPO 필수, DIO 결측(재고 미계상)은 0 처리. 분기=91일, 연간/TTM=365일.
		// (메인 16카드의 CCC 카드와 현금·투자 탭이 공유 · cards 배열보다 먼저 계산)
		const days = mode === 'quarter' ? 91 : 365;
		const rcv = raw('receivables');
		const inv = raw('inventories');
		const pay = raw('payables');
		const revRaw = raw('revenue');
		const cogsRaw = raw('costOfSales');
		const dayRatio = (n: Num, d: Num): Num => (n != null && d != null && d > 0 ? +((n / d) * days).toFixed(1) : null);
		const dso = used.map((_, i) => dayRatio(rcv[i] ?? null, revRaw[i] ?? null));
		const dio = used.map((_, i) => dayRatio(inv[i] ?? null, cogsRaw[i] ?? null));
		const dpo = used.map((_, i) => dayRatio(pay[i] ?? null, cogsRaw[i] ?? null));
		const ccc = used.map((_, i) => (dso[i] != null && dpo[i] != null ? +(dso[i]! + (dio[i] ?? 0) - dpo[i]!).toFixed(1) : null));

		// 메인·탭 공유 카드 4종 · 16카드 승격분 (수익성·현금 탭에도 동일 객체 재사용, 정의 1곳)
		const costStructureCard: FinCard = { key: 'costStructure', title: '비용구조', unit: '조', stacked: true, series: [
			{ name: '매출원가', data: ser('costOfSales'), color: C.red, type: 'bar' },
			{ name: '판관비', data: ser('sga'), color: C.warn, type: 'bar' },
			{ name: '매출', data: ser('revenue'), color: C.rev, type: 'line' }
		] };
		// 이익의 현금화 · 옛 이익품질(CFO/NI 단일 바) 상위호환 대체: 절대액 병치 + 배율 우축
		const cfoRaw = raw('cfOperating');
		const niRaw = raw('netIncome');
		const cashConversionCard: FinCard = { key: 'cashConversion', title: '이익의 현금화', unit: '조', series: [
			{ name: '순이익', data: ser('netIncome'), color: C.net, type: 'bar' },
			{ name: '영업CF', data: ser('cfOperating'), color: C.good, type: 'bar' },
			{ name: 'CFO/NI(배)', data: used.map((_, i) => (cfoRaw[i] != null && niRaw[i] != null && niRaw[i]! > 0 ? +(cfoRaw[i]! / niRaw[i]!).toFixed(2) : null)), color: C.cyan, type: 'line', axis: 'r' }
		] };
		const dupontCard: FinCard = { key: 'dupont', title: 'ROE 분해 (DuPont)', unit: '%', series: [
			{ name: 'ROE', data: ratio('netIncome', 'equity', 100, true), color: C.net, type: 'bar' },
			{ name: '순이익률', data: ratio('netIncome', 'revenue'), color: C.cyan, type: 'line' },
			{ name: '자산회전(회)', data: ratio('revenue', 'assets', 1, true), color: C.blue, type: 'line', axis: 'r' },
			{ name: '레버리지(배)', data: ratio('assets', 'equity', 1), color: C.red, type: 'line', axis: 'r' }
		] };
		const cccCard: FinCard = { key: 'ccc', title: '현금전환주기', unit: '일', series: [
			{ name: 'CCC', data: ccc, color: C.purple, type: 'bar' },
			{ name: 'DSO', data: dso, color: C.blue, type: 'line' },
			{ name: 'DIO', data: dio, color: C.warn, type: 'line' },
			{ name: 'DPO', data: dpo, color: C.good, type: 'line' }
		] };

		// ── 조달구조 · 유동/비유동 대신 조달 *원천* 분해: 이자 내는 차입(빨강) vs 거래에서 생긴
		// 영업·기타부채(파랑 · 충당·리스·법인세 포함이라 '기타' 동반 정직 라벨) vs 주주가 준
		// 납입자본(주황) vs 스스로 번 이익잉여금(초록) vs 잔차 기타자본(회색).
		// 잔차 2종(영업·기타부채, 기타자본)이 합=자산총계 항등식을 구조적으로 보장하고, signed 가
		// 결손금·병리 잔차를 0 아래로 숨김없이 노출. liabilities=null 게이트 = "BS 미파싱" 증거 ·
		// 게이트 통과 시 차입 계정 null 은 0(무차입)으로 읽는다 (결측을 잔차로 흘려 공짜 레버리지를
		// 과대평가하는 편향이 더 위험). ──
		const t3 = (v: Num): Num => (v == null ? null : +(v / TRILLION).toFixed(3));
		const borrowAt = (i: number): Num => {
			if (valAtIdx('liabilities', i) == null) return null;
			return (valAtIdx('shortDebt', i) ?? 0) + (valAtIdx('currentLtDebt', i) ?? 0) + (valAtIdx('longDebt', i) ?? 0);
		};
		const borrowSer: Num[] = used.map((_, i) => t3(borrowAt(i)));
		const opLiabSer: Num[] = used.map((_, i) => {
			const liab = valAtIdx('liabilities', i);
			const b = borrowAt(i);
			return liab == null || b == null ? null : t3(liab - b);
		});
		const paidInSer: Num[] = used.map((_, i) => {
			const cs = valAtIdx('capitalStock', i);
			const sp = valAtIdx('capitalSurplus', i);
			return cs == null && sp == null ? null : t3((cs ?? 0) + (sp ?? 0));
		});
		const otherEqSer: Num[] = used.map((_, i) => {
			const eq = valAtIdx('equity', i);
			if (eq == null) return null;
			return t3(eq - (valAtIdx('capitalStock', i) ?? 0) - (valAtIdx('capitalSurplus', i) ?? 0) - (valAtIdx('retainedEarnings', i) ?? 0));
		});
		// 자본측 매핑 전멸(자본금·이익잉여금 전 기간 null) 회사는 단일 '자본' 으로 강등 · 잔차가 자본 전체를 삼키는 왜곡 방지
		const hasEquitySplit = used.some((_, i) => valAtIdx('capitalStock', i) != null || valAtIdx('retainedEarnings', i) != null);
		const fundingEquity: FinSeries[] = hasEquitySplit
			? [
					{ name: '납입자본', data: paidInSer, color: C.op, type: 'bar' },
					{ name: '이익잉여금', data: ser('retainedEarnings'), color: C.good, type: 'bar' },
					{ name: '기타자본', data: otherEqSer, color: C.dim, type: 'bar' }
				]
			: [{ name: '자본', data: ser('equity'), color: C.good, type: 'bar' }];
		// 순상거래신용(매입채무−매출채권, 좌축 공유 라인) · 양수 = 거래상대 돈으로 영업하는 힘의 직접 측정
		const netTradeSer: Num[] = used.map((_, i) => (pay[i] != null && rcv[i] != null ? t3(pay[i]! - rcv[i]!) : null));

		// ── 재무제표 분석 핵심 16카드 · 4행×4 분석 내러티브 (행=질문, 좌→우=절대액→분해→비율→변화율).
		// 1행 손익 "얼마나 버나" · 2행 현금 "이익이 진짜인가" · 3행 효율 "자본을 잘 굴리나" · 4행 체력 "버틸 수 있나".
		// ⚠ 카드 수 = 4의 배수 불변 (.finGrid 행당 4장 강제 · 운영자 룰: 2장·1장 행 금지). ──
		const cards: FinCard[] = [
			// 1행 · 손익
			{ key: 'incomeBreakdown', title: '손익구조', unit: '조', series: [
				{ name: '매출', data: ser('revenue'), color: C.rev, type: 'bar' },
				{ name: '영업익', data: ser('operatingIncome'), color: C.op, type: 'line', axis: 'r' },
				{ name: '순익', data: ser('netIncome'), color: C.net, type: 'line', axis: 'r' }
			] },
			costStructureCard,
			{ key: 'marginTrend', title: '이익률', unit: '%', series: [
				{ name: 'GPM', data: gpRatio(), color: C.warn, type: 'line' },
				{ name: 'OPM', data: ratio('operatingIncome', 'revenue'), color: C.op, type: 'line' },
				{ name: 'NPM', data: ratio('netIncome', 'revenue'), color: C.net, type: 'line' }
			] },
			{ key: 'growthYoy', title: '성장 YoY', unit: '%', series: [
				{ name: '매출', data: yoy('revenue'), color: C.rev, type: 'bar' },
				{ name: '영업익', data: yoy('operatingIncome'), color: C.op, type: 'line' },
				{ name: '순익', data: yoy('netIncome'), color: C.net, type: 'line' }
			] },
			// 2행 · 현금. signed-stack: 영업(유입)은 0선 위, 투자·재무(유출)는 0선 아래로 쌓아
			// "한 해 들어온 현금 vs 나간 현금"을 0선이 가르고, 순현금 선이 바닥선(증감)을 보여 준다.
			// → grouped 막대(부호·합 안 보임) 대비 현금 내러티브가 직독된다. cardGuide cashflowSigned 와 짝.
			{ key: 'cashflowSigned', title: '현금흐름', unit: '조', stacked: true, signed: true, series: [
				{ name: '영업', data: ser('cfOperating'), color: C.good, type: 'bar' },
				{ name: '투자', data: ser('cfInvesting'), color: C.blue, type: 'bar' },
				{ name: '재무', data: ser('cfFinancing'), color: C.op, type: 'bar' },
				{ name: '순현금', data: compose(['cfOperating', 1], ['cfInvesting', 1], ['cfFinancing', 1]), color: C.purple, type: 'line' }
			] },
			cashConversionCard,
			{ key: 'cfMargin', title: '현금마진', unit: '%', series: [
				{ name: 'CFO/매출', data: ratio('cfOperating', 'revenue'), color: C.good, type: 'line' },
				{ name: 'FCF/매출', data: ratioOfSeries(fcfRaw, 'revenue'), color: C.warn, type: 'line' }
			] },
			{ key: 'fcfTrend', title: 'FCF', unit: '조', series: [
				{ name: 'FCF', data: compose(['cfOperating', 1], ['capex', -1]), color: C.warn, type: 'line' },
				{ name: '영업CF', data: ser('cfOperating'), color: C.good, type: 'line' },
				{ name: 'CAPEX', data: compose(['capex', -1]), color: C.dim, type: 'line' }
			] },
			// 3행 · 효율
			{ key: 'returnTrend', title: 'ROE·ROA', unit: '%', series: [
				{ name: 'ROE', data: ratio('netIncome', 'equity', 100, true), color: C.net, type: 'line' },
				{ name: 'ROA', data: ratio('netIncome', 'assets', 100, true), color: C.blue, type: 'line' }
			] },
			dupontCard,
			cccCard,
			{ key: 'assetGrowth', title: '자산·자본성장', unit: '%', series: [
				{ name: '자산', data: yoy('assets'), color: C.blue, type: 'bar' },
				{ name: '자본', data: yoy('equity'), color: C.good, type: 'line' }
			] },
			// 4행 · 체력
			{ key: 'assetComposition', title: '자산구조', unit: '조', stacked: true, series: [
				{ name: '현금', data: ser('cash'), color: C.good, type: 'bar' },
				{ name: '매출채권', data: ser('receivables'), color: C.blue, type: 'bar' },
				{ name: '재고', data: ser('inventories'), color: C.warn, type: 'bar' },
				{ name: '기타', data: compose(['assets', 1], ['cash', -1], ['receivables', -1], ['inventories', -1]), color: C.dim, type: 'bar' }
			] },
			{ key: 'fundingStructure', title: '조달구조', unit: '조', stacked: true, signed: true, series: [
				{ name: '차입부채', data: borrowSer, color: C.red, type: 'bar' },
				{ name: '영업·기타부채', data: opLiabSer, color: C.blue, type: 'bar' },
				...fundingEquity,
				{ name: '순상거래신용', data: netTradeSer, color: C.cyan, type: 'line' }
			] },
			{ key: 'leverageTrend', title: '레버리지·유동', unit: '%', refLines: [100], series: [
				{ name: '부채비율', data: ratio('liabilities', 'equity'), color: C.red, type: 'bar' },
				{ name: '유동비율', data: ratio('currentAssets', 'currentLiabilities'), color: C.blue, type: 'line', axis: 'r' }
			] },
			{ key: 'netDebt', title: '순차입금', unit: '조', series: [
				{ name: '순차입', data: compose(['shortDebt', 1], ['currentLtDebt', 1], ['longDebt', 1], ['cash', -1]), color: C.red, type: 'bar' }
			] }
		];

		// ── 전체화면 탭 심화 카드 (FinFullscreen 전용) · 동일 헬퍼·동일 기간 축, 모드 토글 동작 ──
		const fc = raw('financeCosts');
		const taxRaw = raw('incomeTax');
		const oiRaw = raw('operatingIncome');
		// 실효세율 · 세전이익 = 순이익 + 법인세 (계정 누락에 강건). 세전 ≤ 0 → null.
		const effTax: Num[] = used.map((_, i) => {
			const t = taxRaw[i];
			const ni = niRaw[i];
			if (t == null || ni == null) return null;
			const pretax = ni + t;
			return pretax > 0 ? +((t / pretax) * 100).toFixed(1) : null;
		});
		// ── 워터폴 브리지 2종 (전체화면 탭 선두) · 현재 모드의 최신 유효 기간 1개 스냅샷 ──
		const lastIdx = (...keys: string[]): number => {
			for (let i = used.length - 1; i >= 0; i--) if (keys.every((k) => valAtIdx(k, i) != null)) return i;
			return -1;
		};
		const tn = (key: string, i: number): Num => {
			const v = valAtIdx(key, i);
			return v == null ? null : +(v / TRILLION).toFixed(3);
		};
		// 손익 브리지: 매출 → −원가 → −판관비 → ±기타영업(plug) → 영업이익 → +순금융 → −법인세 → 순이익
		const plBridge = ((): FinCard | null => {
			const i = lastIdx('revenue', 'operatingIncome', 'netIncome');
			if (i < 0) return null;
			const rev = tn('revenue', i)!;
			const cogs = tn('costOfSales', i);
			const sgaV = tn('sga', i);
			const oi = tn('operatingIncome', i)!;
			const ni = tn('netIncome', i)!;
			const fi = tn('financeIncome', i);
			const fcV = tn('financeCosts', i);
			const finNetV = fi != null || fcV != null ? +((fi ?? 0) - (fcV ?? 0)).toFixed(3) : null;
			const tax = tn('incomeTax', i);
			// 기타영업 plug = 보고 영업이익 − (매출 − 원가 − 판관비) · 유의미(매출 0.2% 또는 10억↑)할 때만 노출
			const plug = +(oi - (rev - (cogs ?? 0) - (sgaV ?? 0))).toFixed(3);
			const steps: NonNullable<FinCard['steps']> = [{ name: '매출', value: rev }];
			if (cogs != null) steps.push({ name: '매출원가', value: -cogs });
			if (sgaV != null) steps.push({ name: '판관비', value: -sgaV });
			if (Math.abs(plug) >= Math.max(0.001, Math.abs(rev) * 0.002)) steps.push({ name: '기타영업', value: plug });
			steps.push({ name: '영업이익', value: oi, total: true });
			if (finNetV != null) steps.push({ name: '순금융', value: finNetV });
			if (tax != null) steps.push({ name: '법인세', value: -tax });
			steps.push({ name: '순이익', value: ni, total: true });
			return { key: 'plBridge', title: `손익 브리지 · ${periods[i]}`, unit: '조', kind: 'waterfall', steps, series: [] };
		})();
		// 현금 브리지: 영업CF → −CAPEX → FCF → −배당금지급 → 잔여
		const cashBridge = ((): FinCard | null => {
			const i = lastIdx('cfOperating');
			if (i < 0) return null;
			const cfo = tn('cfOperating', i)!;
			const cx = tn('capex', i);
			const divRaw = tn('dividendsPaid', i);
			if (cx == null && divRaw == null) return null; // 구성 단계 전무 · 브리지 무의미
			const divOut = divRaw != null ? Math.abs(divRaw) : null; // 일부 공시 음수 표기 방어 (배당지급 = 항상 유출)
			const fcf = +(cfo - (cx ?? 0)).toFixed(3);
			const steps: NonNullable<FinCard['steps']> = [{ name: '영업CF', value: cfo }];
			if (cx != null) steps.push({ name: 'CAPEX', value: -cx });
			steps.push({ name: 'FCF', value: fcf, total: true });
			if (divOut != null) steps.push({ name: '배당지급', value: -divOut });
			steps.push({ name: '잔여', value: +(fcf - (divOut ?? 0)).toFixed(3), total: true });
			return { key: 'cashBridge', title: `현금 브리지 · ${periods[i]}`, unit: '조', kind: 'waterfall', steps, series: [] };
		})();
		// 포괄손익 격차 · CIS 원본 레인 (순이익 vs 총포괄, 우축 OCI). CIS 미보유·매칭 실패 회사는
		// 전 시리즈 null → FinFullscreen 카드 필터가 자동 비표시.
		const ociSer: Num[] = used.map((_, i) => {
			const tci = valAtIdx('cisComprehensive', i);
			const niC = valAtIdx('cisNetIncome', i);
			return tci != null && niC != null ? +((tci - niC) / TRILLION).toFixed(3) : null;
		});
		const ociCard: FinCard = { key: 'oci', title: '포괄손익 격차', unit: '조', series: [
			{ name: '순이익', data: ser('cisNetIncome'), color: C.net, type: 'bar' },
			{ name: '총포괄이익', data: ser('cisComprehensive'), color: C.purple, type: 'line' },
			{ name: 'OCI', data: ociSer, color: C.warn, type: 'line', axis: 'r' }
		] };
		// 자본 구성 추이 · BS 자본 내부 분해 (자본금·이익잉여금·기타). fundingStructure(부채·자본
		// 조달 전체)와 분해 축이 달라 중복 아님. 두 구성 계정 다 없으면 비표시 (기타 왜곡 방지).
		const equityComposition = ((): FinCard | null => {
			const cs = ser('capitalStock');
			const re = ser('retainedEarnings');
			if (!cs.some((v) => v != null) || !re.some((v) => v != null)) return null;
			return { key: 'equityComposition', title: '자본 구성 추이', unit: '조', stacked: true, signed: true, series: [
				{ name: '자본금', data: cs, color: C.dim, type: 'bar' },
				{ name: '이익잉여금', data: re, color: C.good, type: 'bar' },
				{ name: '기타·비지배', data: compose(['equity', 1], ['capitalStock', -1], ['retainedEarnings', -1]), color: C.blue, type: 'bar' },
				{ name: '자본총계', data: ser('equity'), color: C.purple, type: 'line' }
			] };
		})();
		const tabCards = {
			profitability: [
				...(plBridge ? [plBridge] : []),
				...(seasonality ? [seasonality] : []),
				costStructureCard,
				{ key: 'finNet', title: '금융손익', unit: '조', series: [
					{ name: '금융수익', data: ser('financeIncome'), color: C.good, type: 'bar' },
					{ name: '금융비용(−)', data: compose(['financeCosts', -1]), color: C.red, type: 'bar' },
					{ name: '순금융', data: compose(['financeIncome', 1], ['financeCosts', -1]), color: C.purple, type: 'line' }
				] },
				{ key: 'taxEffective', title: '법인세·실효세율', unit: '조', series: [
					{ name: '법인세', data: ser('incomeTax'), color: C.dim, type: 'bar' },
					{ name: '실효세율%', data: effTax, color: C.warn, type: 'line', axis: 'r' }
				] },
				dupontCard,
				ociCard
			] as FinCard[],
			cashflow: [
				...(cashBridge ? [cashBridge] : []),
				cashConversionCard,
				{ key: 'workingCapital', title: '운전자본', unit: '조', series: [
					{ name: '순운전자본', data: compose(['receivables', 1], ['inventories', 1], ['payables', -1]), color: C.blue, type: 'bar' },
					{ name: 'NWC/매출%', data: used.map((_, i) => { const n = (rcv[i] ?? 0) + (inv[i] ?? 0) - (pay[i] ?? 0); return rcv[i] != null && pay[i] != null && revRaw[i] != null && revRaw[i]! > 0 ? +((n / revRaw[i]!) * 100).toFixed(1) : null; }), color: C.warn, type: 'line', axis: 'r' }
				] },
				cccCard,
				{ key: 'capexCycle', title: '투자 사이클', unit: '조', series: [
					{ name: 'CAPEX', data: ser('capex'), color: C.blue, type: 'bar' },
					{ name: 'CAPEX/매출%', data: ratio('capex', 'revenue'), color: C.warn, type: 'line', axis: 'r' },
					{ name: 'CAPEX/영업CF%', data: used.map((_, i) => { const cx = raw('capex')[i]; return cx != null && cfoRaw[i] != null && cfoRaw[i]! > 0 ? +((cx / cfoRaw[i]!) * 100).toFixed(1) : null; }), color: C.red, type: 'line', axis: 'r' }
				] }
			] as FinCard[],
			debt: [
				{ key: 'debtMix', title: '차입 구성 vs 현금', unit: '조', stacked: true, series: [
					{ name: '단기성차입(1년내)', data: compose(['shortDebt', 1], ['currentLtDebt', 1]), color: C.red, type: 'bar' },
					{ name: '장기차입금·사채', data: ser('longDebt'), color: C.op, type: 'bar' },
					{ name: '현금성자산', data: ser('cash'), color: C.good, type: 'line' }
				] },
				{ key: 'interestCover', title: '이자보상 (영업익/금융비용)', unit: '배', refLines: [1], series: [
					{ name: '이자보상배율', data: used.map((_, i) => (oiRaw[i] != null && fc[i] != null && fc[i]! > 0 ? +(oiRaw[i]! / fc[i]!).toFixed(2) : null)), color: C.cyan, type: 'bar' }
				] }
			] as FinCard[],
			// 주주환원·소유 탭 선두 · SCE 브리지(모드 무관 스냅샷) + 자본 구성 추이(모드 동작)
			shareholder: [...(sceBridge ? [sceBridge] : []), ...(equityComposition ? [equityComposition] : [])] as FinCard[]
		};

		// 회사에 데이터 전무(빈 파케이)면 null. 개별 카드 sparse 는 셀 유지 (빈칸 방지).
		if (!cards.some((c) => c.series.some((s) => s.data.some((v) => v != null)))) return null;
		// 파생 인사이트 · 실적 모멘텀(YoY) + 현금흐름 품질(영업CF/순익).
		const revYoy = yoy('revenue');
		const opYoy = yoy('operatingIncome');
		const cashQuality: Num[] = used.map((_, i) => {
			const cf = valAtIdx('cfOperating', i);
			const ni = valAtIdx('netIncome', i);
			return cf != null && ni != null && ni > 0 ? +(cf / ni).toFixed(2) : null;
		});
		// 재무제표 표 · 전 기간 계정×기간 (조 KRW). 손익·재무상태·현금흐름·비용.
		const mkStmt = (defs: { key: string; kr: string; en: string }[]): StmtRow[] => defs.map((d) => ({ key: d.key, kr: d.kr, en: d.en, values: ser(d.key) }));
		const statements: Record<StmtKind, StmtRow[]> = { IS: mkStmt(STMT_DEF.IS), BS: mkStmt(STMT_DEF.BS), CF: mkStmt(STMT_DEF.CF) };
		// 핵심 비율 시계열 · 재무제표와 동일 기간 축. 수익성·안정성·현금. (% · 이익품질만 배)
		const ratios: StmtRow[] = [
			{ key: 'roe', kr: 'ROE', en: 'ROE', unit: '%', values: ratio('netIncome', 'equity', 100, true) },
			{ key: 'roa', kr: 'ROA', en: 'ROA', unit: '%', values: ratio('netIncome', 'assets', 100, true) },
			{ key: 'gpm', kr: '매출총이익률', en: 'Gross margin', unit: '%', values: gpRatio() },
			{ key: 'opm', kr: '영업이익률', en: 'Operating margin', unit: '%', values: ratio('operatingIncome', 'revenue') },
			{ key: 'npm', kr: '순이익률', en: 'Net margin', unit: '%', values: ratio('netIncome', 'revenue') },
			{ key: 'debtRatio', kr: '부채비율', en: 'Debt/Equity', unit: '%', values: ratio('liabilities', 'equity') },
			{ key: 'currentRatio', kr: '유동비율', en: 'Current', unit: '%', values: ratio('currentAssets', 'currentLiabilities') },
			{ key: 'equityRatio', kr: '자기자본비율', en: 'Equity ratio', unit: '%', values: ratio('equity', 'assets') },
			{ key: 'cfoMargin', kr: '영업CF마진', en: 'CFO margin', unit: '%', values: ratio('cfOperating', 'revenue') },
			{ key: 'earningsQuality', kr: '이익품질(CFO/NI)', en: 'Earnings quality', unit: '배', values: ratio('cfOperating', 'netIncome', 1) }
		];
		return { periods, freq: mode, cards, tabCards, revYoy, opYoy, cashQuality, statements, ratios };
	};

	const views: Record<FinMode, TerminalFinance | null> = {
		annual: hasAnnual ? buildMode('annual') : null,
		quarter: hasInterim ? buildMode('quarter') : null,
		ttm: hasInterim ? buildMode('ttm') : null
	};
	// 기본 = 분기 (실적 추적의 기본 시간축 · 운영자 결정 2026-06-11). TTM·연간은 버튼 전환.
	const modes: FinMode[] = [];
	if (views.quarter) modes.push('quarter');
	if (views.ttm) modes.push('ttm');
	if (views.annual) modes.push('annual');
	if (modes.length === 0) return null;
	const defaultMode: FinMode = views.quarter ? 'quarter' : views.annual ? 'annual' : modes[0]!; // 윗줄 length 가드로 항상 존재

	return { currency: 'KRW', scope: fs, availScopes, modes, views, defaultMode, filedDates };
}
