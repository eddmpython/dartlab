// 비정기(수시)공시 — dart/allFilings/recent.parquet (HF, 전 이력 통합 1파일) 을 stock_code
// 필터로 단건 읽기. 일자 date-scan(휴일 404 콘솔오염) 폐기 — 통합파일은 stock_code 정렬이라
// filter pushdown 이 회사 row-group 만 읽음. content_raw 없음(빌드시 메타만). per-code 캐시.
// 통합파일 생성: .github/scripts/sync/buildAllFilingsRecent.py (정기보고서는 이미 제외됨).
// 타입 정본 = contracts (NonRegularFiling 승격 완료 — 중복 정의 금지).
import type { MarketFiling, NonRegularFiling } from '@dartlab/ui-contracts';
import { resolveMarket } from '@dartlab/ui-contracts';
import type { DataCore } from '../../../data/fetch/request';
import { originConfigured } from '../../../data/origins/registry';

interface RecentRow extends Record<string, unknown> {
	stock_code?: unknown;
	rcept_dt?: unknown;
	report_nm?: unknown;
	rcept_no?: unknown;
	flr_nm?: unknown;
}

const COLS = ['stock_code', 'rcept_dt', 'report_nm', 'rcept_no', 'flr_nm'];
const REGULAR = ['사업보고서', '반기보고서', '분기보고서'];

function fmtDate(s: string): string {
	const c = String(s).replace(/\D/g, '').slice(0, 8);
	return c.length === 8 ? `${c.slice(0, 4)}-${c.slice(4, 6)}-${c.slice(6, 8)}` : String(s);
}

// ── EDGAR(US) 공시 — edgar/allFilings/{recent,market_recent}.parquet 직독 (KR dart/allFilings 대칭).
// buildEdgarAllFilingsRecent 가 굽는 camelCase 컬럼. 정기보고서(10-K/10-Q)는 빌드서 이미 제외 — 수시만.
interface EdgarFilingRow extends Record<string, unknown> {
	stockCode?: unknown;
	entityName?: unknown;
	filingDate?: unknown;
	form?: unknown;
	accessionNo?: unknown;
	docDescription?: unknown;
	url?: unknown;
}
const EDGAR_FILING_COLS = ['stockCode', 'entityName', 'filingDate', 'form', 'accessionNo', 'docDescription', 'url'];

// EDGAR 행 → NonRegularFiling. reportNm = form(+설명). accessionNo 가 rceptNo, entityName 이 filer(회사 자신).
function toEdgarNonRegular(r: EdgarFilingRow): NonRegularFiling | null {
	const rceptNo = String(r.accessionNo ?? '').trim();
	if (!rceptNo) return null;
	const form = String(r.form ?? '').trim();
	const desc = String(r.docDescription ?? '').trim();
	return {
		rceptNo,
		reportNm: desc && desc !== form ? `${form} · ${desc}` : form,
		rceptDate: fmtDate(String(r.filingDate ?? '')),
		filer: String(r.entityName ?? '').trim(),
		url: String(r.url ?? '').trim()
	};
}

async function loadEdgarCompanyFilings(core: DataCore, ticker: string): Promise<NonRegularFiling[]> {
	try {
		const rows = await core.requestParquetRows<EdgarFilingRow>({
			origin: 'hfRange',
			path: 'edgar/allFilings/recent.parquet',
			columns: EDGAR_FILING_COLS,
			filter: { stockCode: { $in: [ticker] } },
			cacheKey: `edgarFilings.recent:one:${ticker}`,
			cache: { scope: 'memory', ttlMs: 10 * 60_000, maxEntries: 256 }
		});
		const seen = new Set<string>();
		const out: NonRegularFiling[] = [];
		for (const r of rows) {
			const f = toEdgarNonRegular(r);
			if (!f || seen.has(f.rceptNo)) continue;
			seen.add(f.rceptNo);
			out.push(f);
		}
		out.sort((a, b) => b.rceptDate.localeCompare(a.rceptDate) || b.rceptNo.localeCompare(a.rceptNo));
		return out;
	} catch {
		return [];
	}
}

async function loadEdgarMarketFeed(core: DataCore): Promise<MarketFiling[]> {
	try {
		const rows = await core.requestParquetWholeFile<EdgarFilingRow>({
			origin: 'hf',
			path: 'edgar/allFilings/market_recent.parquet',
			columns: EDGAR_FILING_COLS,
			cacheKey: 'edgarFilings.marketFeed',
			cache: { scope: 'memory', ttlMs: 10 * 60_000, maxEntries: 2 }
		});
		const seen = new Set<string>();
		const out: MarketFiling[] = [];
		for (const r of rows ?? []) {
			const f = toEdgarNonRegular(r);
			const stockCode = String(r.stockCode ?? '').trim();
			if (!f || !stockCode || seen.has(f.rceptNo)) continue;
			seen.add(f.rceptNo);
			out.push({ ...f, stockCode, corpName: String(r.entityName ?? '').trim() });
		}
		return out;
	} catch {
		return [];
	}
}

// 워커 marketFilingsWorker — DART list 당일 전체 공시(라이브). 시장 피드·종목 비정기 공용(코어 캐시 공유).
// 미배선/실패는 []. 워커 응답 {asOf, items:[{rceptNo,rceptDate,stockCode,corpName,reportNm,filer}]}.
interface LiveFilingRow {
	rceptNo?: string;
	rceptDate?: string;
	stockCode?: string;
	corpName?: string;
	reportNm?: string;
	filer?: string;
}
function loadLiveMarketFilings(core: DataCore): Promise<LiveFilingRow[]> {
	if (!originConfigured('marketFilingsWorker')) return Promise.resolve([]); // 워커 미배선 → HF base 만
	return core
		.request<{ items?: LiveFilingRow[] }>({
			origin: 'marketFilingsWorker',
			path: '', // 쿼리 없는 고정 라우트
			cacheKey: 'allFilings.live.today',
			cache: { scope: 'memory', ttlMs: 5 * 60_000, maxEntries: 1 },
			parse: (r) => (r.ok ? (r.json() as Promise<{ items?: LiveFilingRow[] }>) : Promise.resolve({}))
		})
		.then((j) => (Array.isArray(j.items) ? j.items : []))
		.catch(() => []);
}

export async function loadCompanyNonRegularFilings(core: DataCore, stockCode: string): Promise<NonRegularFiling[]> {
	const code = stockCode.trim();
	const m = resolveMarket(code);
	if (m.market === 'US' && m.ticker) return loadEdgarCompanyFilings(core, m.ticker); // US = edgar/allFilings 직독
	if (!/^\d{6}$/.test(code)) return [];
	try {
		// HF 누적(전 이력) + 라이브 당일 공시(이 종목분 필터) 동시 — 라이브가 배치 사이 갭(당일) 메움.
		const [rows, live] = await Promise.all([
			core.requestParquetRows<RecentRow>({
				origin: 'hfRange',
				path: 'dart/allFilings/recent.parquet',
				columns: COLS,
				filter: { stock_code: { $in: [code] } },
				cacheKey: `allFilings.recent:one:${code}`,
				cache: { scope: 'memory', ttlMs: 10 * 60_000, maxEntries: 256 } // 신선도 — 짧은 TTL, 자체 Map 폐기
			}),
			loadLiveMarketFilings(core)
		]);
		const seen = new Set<string>();
		const result: NonRegularFiling[] = [];
		// 라이브(오늘) 먼저 — 이 종목분만, 최신 우선 dedup(rceptNo)
		for (const r of live) {
			if (String(r.stockCode ?? '').trim() !== code) continue;
			const rceptNo = String(r.rceptNo ?? '').trim();
			const reportNm = String(r.reportNm ?? '').trim();
			if (!rceptNo || seen.has(rceptNo) || REGULAR.some((n) => reportNm.includes(n))) continue;
			seen.add(rceptNo);
			result.push({ rceptNo, reportNm, rceptDate: fmtDate(String(r.rceptDate ?? '')), filer: String(r.filer ?? '').trim(), url: `https://dart.fss.or.kr/dsaf001/main.do?rcpNo=${rceptNo}` });
		}
		for (const r of rows) {
			const rceptNo = String(r.rcept_no ?? '').trim();
			const reportNm = String(r.report_nm ?? '').trim();
			if (!rceptNo || seen.has(rceptNo) || REGULAR.some((n) => reportNm.includes(n))) continue;
			seen.add(rceptNo);
			result.push({
				rceptNo,
				reportNm,
				rceptDate: fmtDate(String(r.rcept_dt ?? '')),
				filer: String(r.flr_nm ?? '').trim(),
				url: `https://dart.fss.or.kr/dsaf001/main.do?rcpNo=${rceptNo}`
			});
		}
		result.sort((a, b) => b.rceptDate.localeCompare(a.rceptDate) || b.rceptNo.localeCompare(a.rceptNo));
		return result; // 전 이력 — slice 캡 없음(레일/우측패널 완결성). 캐시/dedup 은 코어.
	} catch {
		return [];
	}
}

// 워치 신선도 — 여러 종목을 한 read 로 ($in:[codes]). 단일판과 동일 HF 파일·정규화, code→목록 그룹핑.
// 공개/로컬 공통배선(둘 다 이 함수 호출 → 백엔드 0). 캐시·dedup 은 fetch 코어(data/fetch) 담당 —
// 신선도 데이터라 짧은 TTL(10분). 자체 batchCache Map 폐기(데이터 워크벤치 SSOT 이관 P1).
export async function loadRecentFilingsForCodes(
	core: DataCore,
	codes: string[]
): Promise<Record<string, NonRegularFiling[]>> {
	const valid = [...new Set(codes.map((c) => String(c).trim()).filter((c) => /^\d{6}$/.test(c)))];
	if (!valid.length) return {};
	try {
		const rows = await core.requestParquetRows<RecentRow>({
			origin: 'hfRange',
			path: 'dart/allFilings/recent.parquet',
			columns: COLS,
			filter: { stock_code: { $in: valid } },
			cacheKey: `allFilings.recent:${valid.slice().sort().join(',')}`,
			cache: { scope: 'memory', ttlMs: 10 * 60_000, maxEntries: 32 }
		});
		const wanted = new Set(valid);
		const out: Record<string, NonRegularFiling[]> = {};
		const seen = new Set<string>(); // code:rceptNo 중복 제거
		for (const r of rows) {
			const code = String(r.stock_code ?? '').trim();
			if (!wanted.has(code)) continue;
			const rceptNo = String(r.rcept_no ?? '').trim();
			const reportNm = String(r.report_nm ?? '').trim();
			const dk = code + ':' + rceptNo;
			if (!rceptNo || seen.has(dk) || REGULAR.some((n) => reportNm.includes(n))) continue;
			seen.add(dk);
			(out[code] ??= []).push({
				rceptNo,
				reportNm,
				rceptDate: fmtDate(String(r.rcept_dt ?? '')),
				filer: String(r.flr_nm ?? '').trim(),
				url: `https://dart.fss.or.kr/dsaf001/main.do?rcpNo=${rceptNo}`
			});
		}
		for (const arr of Object.values(out)) arr.sort((a, b) => b.rceptDate.localeCompare(a.rceptDate) || b.rceptNo.localeCompare(a.rceptNo));
		return out;
	} catch {
		return {};
	}
}

// 시장 공시 피드(좌측 터미널) — 전상장사 최근 3개월 수시공시 시간순. 우측 단일기업 경로(stock_code
// 필터 row-group)와 *경로 분리*: 이건 전체시장이라 필터가 없고, 전용 bake 파일(market_recent.parquet,
// rcept_dt 내림차순·~656KB)을 통파일 1 GET 으로 읽는다(govRecent 동형). recent.parquet 은 stock_code
// 정렬이라 날짜순을 못 뽑으므로 재사용 금지. category 는 UI 가 report_nm 으로 분류(여기선 원본만).
const FEED_COLS = ['stock_code', 'corp_name', 'rcept_dt', 'report_nm', 'rcept_no', 'flr_nm'];
interface FeedRow extends RecentRow {
	corp_name?: unknown;
}

export async function loadMarketFeed(core: DataCore): Promise<MarketFiling[]> {
	try {
		// HF 누적 bake(3개월) + 라이브 당일 전체 공시 동시 — 라이브가 배치(14:30) 사이 갭(당일) 메움.
		const [rows, live, edgar] = await Promise.all([
			core.requestParquetWholeFile<FeedRow>({
				origin: 'hf',
				path: 'dart/allFilings/market_recent.parquet',
				columns: FEED_COLS,
				cacheKey: 'allFilings.marketFeed',
				cache: { scope: 'memory', ttlMs: 10 * 60_000, maxEntries: 2 } // 일일 cron 갱신 — 신선도 우선 10분 TTL(worker 엣지 600s 와 일치)
			}),
			loadLiveMarketFilings(core),
			loadEdgarMarketFeed(core) // US 수시공시 피드 병합(KR dart + US edgar, rceptNo 무충돌)
		]);
		const seen = new Set<string>();
		const result: MarketFiling[] = [];
		// 라이브(오늘 전체 시장) 먼저 — 최신 우선 dedup(rceptNo)
		for (const r of live) {
			const rceptNo = String(r.rceptNo ?? '').trim();
			const stockCode = String(r.stockCode ?? '').trim();
			const reportNm = String(r.reportNm ?? '').trim();
			if (!rceptNo || !stockCode || seen.has(rceptNo) || REGULAR.some((n) => reportNm.includes(n))) continue;
			seen.add(rceptNo);
			result.push({ rceptNo, rceptDate: fmtDate(String(r.rceptDate ?? '')), stockCode, corpName: String(r.corpName ?? '').trim(), reportNm, filer: String(r.filer ?? '').trim(), url: `https://dart.fss.or.kr/dsaf001/main.do?rcpNo=${rceptNo}` });
		}
		for (const r of rows ?? []) {
			const rceptNo = String(r.rcept_no ?? '').trim();
			const stockCode = String(r.stock_code ?? '').trim();
			const reportNm = String(r.report_nm ?? '').trim();
			// bake 가 정기보고서·dedup 을 이미 했으나 belt-and-suspenders
			if (!rceptNo || !stockCode || seen.has(rceptNo) || REGULAR.some((n) => reportNm.includes(n))) continue;
			seen.add(rceptNo);
			result.push({
				rceptNo,
				rceptDate: fmtDate(String(r.rcept_dt ?? '')),
				stockCode,
				corpName: String(r.corp_name ?? '').trim(),
				reportNm,
				filer: String(r.flr_nm ?? '').trim(),
				url: `https://dart.fss.or.kr/dsaf001/main.do?rcpNo=${rceptNo}`
			});
		}
		// US(edgar) 시장 피드 병합 — rceptNo(accession) 가 KR rcept_no 와 무충돌이라 같은 seen 으로 dedup.
		for (const f of edgar) {
			if (seen.has(f.rceptNo)) continue;
			seen.add(f.rceptNo);
			result.push(f);
		}
		// 라이브(오늘) + HF(bake desc) + US 합침 → rceptDate desc 재정렬(라이브 오늘이 위로). 캐시·dedup 은 코어/위.
		result.sort((a, b) => b.rceptDate.localeCompare(a.rceptDate) || b.rceptNo.localeCompare(a.rceptNo));
		return result;
	} catch {
		return [];
	}
}
