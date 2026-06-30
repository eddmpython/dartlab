<script lang="ts">
	// 터미널 헤더 「데이터」 다이얼로그 — 원하는 데이터셋을 체크해서 *한 번에* 받는다(하나하나 X).
	// 선택분 → 단일 Excel 워크북(데이터셋별 시트 분할) 또는 CSV 묶음(zip). 브라우저 parquet/포트 직독→변환(서버 0).
	// 전종목 180만행 횡단은 시트 한도 초과라 묶음 불가 → 개별 CSV. 뉴스는 언론사 저작권이라 다운로드 미제공.
	import type { DartLabRuntime, StmtKind } from '@dartlab/ui-contracts';
	import { KR_INDEX_PRESETS } from '@dartlab/ui-contracts';
	import { DOWNLOAD_CATALOG } from '@dartlab/ui-runtime/data/catalog/downloadCatalog';
	import { readParquetRows } from '@dartlab/ui-runtime/data/parquet/hfRange';
	import { objectsToWorkbook, downloadBlob, downloadCsv, toCsv, ZipStore, type ObjectSheet } from '../../downloadExport';
	import type { Lang } from '../lib/types';

	interface Props {
		runtime: DartLabRuntime;
		code: string;
		corpName: string;
		lang: Lang;
	}
	let { runtime, code, corpName, lang }: Props = $props();

	const XLSX_MIME = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet';
	const en = $derived(lang === 'en');
	const base = $derived(runtime?.env?.basePath ?? ''); // 데이터 센터 바로가기 base 경로
	const isUs = $derived(!/^\d{6}$/.test(code));
	const termsUrl = $derived(
		isUs ? 'https://www.sec.gov/os/accessing-edgar-data' : 'https://opendart.fss.or.kr/intro/terms.do'
	);

	const LABELS: Record<string, string> = $derived.by(() => ({
		'dart/finance': en ? 'Financials (raw)' : '재무 데이터 (원본)',
		'dart/panel': en ? 'Disclosure (wide)' : '공시 수평화',
		'dart/report': en ? 'Periodic reports' : '정기보고서',
		'gov/prices/company': en ? 'Daily prices + cap' : '일별 시세·시총',
		'edgar/financeStmt': en ? 'Financials (raw)' : '재무 데이터 (원본)',
		'edgar/panel': en ? 'Disclosure (wide)' : '공시 수평화',
		'edgar/prices/company': en ? 'Daily prices (OHLCV)' : '일별 시세 (OHLCV)'
	}));
	// 기술 경로 대신 "무엇을 받는지" 한 줄 설명(일반인용).
	const DESC: Record<string, string> = $derived.by(() => ({
		'dart/finance': en ? 'all accounts, all periods' : '전 계정·전기간 숫자',
		'dart/panel': en ? 'disclosure body, structured' : '공시 본문 구조화 표',
		'dart/report': en ? 'annual/half/quarter reports' : '사업·반기·분기보고서',
		'gov/prices/company': en ? 'daily OHLCV + market cap' : '일별 OHLCV·시가총액',
		'edgar/financeStmt': en ? 'all accounts (raw)' : '전 계정 raw',
		'edgar/panel': en ? 'disclosure body, structured' : '공시 본문 구조화 표',
		'edgar/prices/company': en ? 'daily OHLCV' : '일별 OHLCV'
	}));
	// 회사 단위 parquet 데이터셋(카탈로그 자동). krx/prices/company 제외(gov 중복·404).
	const parquetSets = $derived(
		DOWNLOAD_CATALOG.filter(
			(e) =>
				e.shardKind === 'company' &&
				e.dir !== 'krx/prices/company' &&
				LABELS[e.dir] &&
				(isUs ? e.dir.startsWith('edgar/') : e.dir.startsWith('dart/') || e.dir.startsWith('gov/'))
		)
	);

	// 전역 거시·지수(회사 무관). krx/indices·krx/prices·edgar/meta 는 HF 미발행이라 제외.
	const MARKET_FILES = $derived([
		{ path: 'macro/fred/observations.parquet', label: en ? 'FRED macro series' : 'FRED 거시 시계열', desc: en ? 'US macro indicators' : '美 거시지표 (금리·물가 등)' },
		{ path: 'macro/ecos/observations.parquet', label: en ? 'ECOS (BOK) macro' : 'ECOS 한은 거시', desc: en ? 'Bank of Korea macro' : '한은 거시지표' },
		{ path: 'macro/customs/observations.parquet', label: en ? 'Customs trade (KR)' : '관세청 수출입', desc: en ? 'monthly trade stats' : '월별 수출입 통계' },
		{ path: 'edgar/tickers/tickers.parquet', label: en ? 'SEC ticker↔CIK map' : 'SEC ticker↔CIK 맵', desc: en ? 'US ticker mapping' : '美 종목코드 매핑' }
	]);

	let open = $state(false);
	let busy = $state('');
	let err = $state('');
	let sel = $state(new Set<string>());

	const clean = (s: string) => s.replace(/[/ ()·]/g, '');
	const stem = (label: string) => `${corpName || code}_${clean(label)}`;

	// 일반인용 컬럼 정리 — pick: 내부 엔진 컬럼(atocId·xbrlMatchScore 등) 제거. ko: raw 소스 코드(BAS_DD 등)→한글.
	// 원본(dart/finance·edgar/financeStmt)은 비포함 → raw 유지(시계열이 가공본).
	const COL_SPEC: Record<string, { pick?: string[]; ko?: Record<string, string>; trunc?: Record<string, number> }> = {
		'dart/panel': {
			pick: ['corp', 'period', 'rceptNo', 'chapter', 'sectionPath', 'sectionLeaf', 'contentRaw'],
			ko: { corp: '회사', period: '기간', rceptNo: '접수번호', chapter: '장', sectionPath: '섹션경로', sectionLeaf: '항목', contentRaw: '내용(발췌)' },
			trunc: { contentRaw: 200 } // 본문 전체는 셀당 수KB → 파일 수백MB·엑셀 무용. 200자 발췌(전문은 DART 접수번호로)
		},
		'edgar/panel': {
			pick: ['corp', 'period', 'rceptNo', 'chapter', 'sectionPath', 'sectionLeaf', 'contentRaw'],
			ko: { corp: '회사', period: '기간', rceptNo: '접수번호', chapter: '장', sectionPath: '섹션경로', sectionLeaf: '항목', contentRaw: '내용(발췌)' },
			trunc: { contentRaw: 200 }
		},
		'gov/indices/index': {
			ko: { BAS_DD: '기준일', IDX_CLSS: '지수분류', IDX_NM: '지수명', CLSPRC_IDX: '종가', CMPPREVDD_IDX: '전일대비', FLUC_RT: '등락률(%)', OPNPRC_IDX: '시가', HGPRC_IDX: '고가', LWPRC_IDX: '저가', ACC_TRDVOL: '거래량', ACC_TRDVAL: '거래대금', MKTCAP: '시가총액', MARKET_GROUP: '시장' }
		},
		'gov/prices/company': {
			ko: { date: '날짜', name: '종목명', market: '시장', open: '시가', high: '고가', low: '저가', close: '종가', priceChange: '전일대비', fluctuationRate: '등락률(%)', volume: '거래량', tradedValue: '거래대금', marketCap: '시가총액', listedShares: '상장주식수', stockCode: '종목코드' }
		},
		'edgar/prices/company': {
			ko: { date: '날짜', open: '시가', high: '고가', low: '저가', close: '종가', volume: '거래량' }
		}
	};
	function reshape(rows: Record<string, unknown>[], dir: string): Record<string, unknown>[] {
		const spec = COL_SPEC[dir];
		if (!spec || !rows.length) return rows;
		const cols = (spec.pick ?? Object.keys(rows[0])).filter((c) => c in rows[0]);
		return rows.map((r) => {
			const o: Record<string, unknown> = {};
			for (const c of cols) {
				let v = r[c];
				const lim = spec.trunc?.[c];
				if (lim && typeof v === 'string' && v.length > lim) v = v.slice(0, lim) + '…';
				o[spec.ko?.[c] ?? c] = v;
			}
			return o;
		});
	}

	// 다파일 샤드 concat — HF tree API 는 CORS 차단이라 경로를 런타임 지식으로 생성, 404 skip.
	const RESERVED = /[/\\:*?"<>|]/g;
	const indexKey = (market: string, name: string) =>
		`${market}-${name.normalize('NFC').trim().replace(RESERVED, '_').replace(/\s+/g, '_').replace(/_+/g, '_').replace(/^_+|_+$/g, '')}`;
	async function readShards(paths: string[], cap = 6): Promise<Record<string, unknown>[]> {
		const chunks: Record<string, unknown>[][] = [];
		for (let i = 0; i < paths.length; i += cap) {
			const res = await Promise.allSettled(paths.slice(i, i + cap).map((p) => readParquetRows(p)));
			for (const r of res) if (r.status === 'fulfilled') chunks.push(r.value.rows as Record<string, unknown>[]);
		}
		return chunks.flat(); // push(...rows) 는 33만+ 행에서 콜스택 초과 — flat() 안전
	}

	const sheet = (label: string, rows: Record<string, unknown>[]): ObjectSheet => ({ label, columns: rows.length ? Object.keys(rows[0]) : [], rows });

	// ── 데이터 소스 통일 모델 — 각 소스는 fetch()→시트[]. 개별 다운로드도 묶음도 같은 fetch 재사용.
	//    bulk=180만행(시트 한도 초과·묶음 불가, 개별 CSV). bare=전역(파일명 회사 접두 없음).
	interface Src {
		key: string;
		label: string;
		desc: string;
		group: 'co' | 'scan' | 'mkt';
		bulk?: boolean;
		bare?: boolean;
		fetch: () => Promise<ObjectSheet[]>;
	}
	const SOURCES = $derived.by<Src[]>(() => {
		const out: Src[] = [];
		// 재무제표 시계열 — 가공 IS/BS/CF(+비율) 계정×기간(이미 멀티시트).
		out.push({
			key: 'finTs', label: en ? 'Financials — time series' : '재무제표 시계열', desc: 'IS·BS·CF', group: 'co',
			fetch: async () => {
				const bundle = await runtime.finance.bundle(code);
				const view = bundle?.views[bundle.defaultMode] ?? bundle?.views.annual ?? bundle?.views.quarter ?? null;
				if (!view) return [];
				const periods = view.periods;
				const toRows = (stmt: { kr: string; en: string; values: (number | null)[] }[]) =>
					stmt.map((r) => {
						const o: Record<string, unknown> = { [en ? 'Account' : '계정']: en ? r.en : r.kr };
						periods.forEach((p, i) => (o[p] = r.values[i]));
						return o;
					});
				const kinds: { k: StmtKind; label: string }[] = [
					{ k: 'IS', label: en ? 'Income' : '손익계산서' },
					{ k: 'BS', label: en ? 'Balance' : '재무상태표' },
					{ k: 'CF', label: en ? 'Cashflow' : '현금흐름표' }
				];
				const sheets = kinds
					.map(({ k, label }) => ({ label, columns: [en ? 'Account' : '계정', ...periods], rows: toRows(view.statements[k] ?? []) }))
					.filter((s) => s.rows.length);
				if (view.ratios?.length) sheets.push({ label: en ? 'Ratios' : '주요비율', columns: [en ? 'Metric' : '지표', ...periods], rows: toRows(view.ratios) });
				return sheets;
			}
		});
		// 회사 parquet 데이터셋
		for (const d of parquetSets)
			out.push({
				key: d.dir, label: LABELS[d.dir], desc: DESC[d.dir] ?? d.dir, group: 'co',
				fetch: async () => [sheet(LABELS[d.dir], reshape((await readParquetRows(`${d.dir}/${code}.parquet`)).rows, d.dir))]
			});
		// 공시 리스트
		out.push({
			key: 'filings', label: en ? 'Filings list' : '공시 리스트', desc: en ? 'regular + events' : '정기 + 수시', group: 'co',
			fetch: async () => {
				const [reg, non] = await Promise.all([runtime.filing.regular(code, 300), runtime.filing.nonRegular(code, 1000)]);
				const rows: Record<string, unknown>[] = [
					...reg.map((f) => ({ 구분: en ? 'regular' : '정기', 접수일: f.rceptDate, 보고서: f.reportType, 사업연도: f.year, 제출인: '', 접수번호: f.rceptNo, URL: f.url })),
					...non.map((f) => ({ 구분: en ? 'event' : '수시', 접수일: f.rceptDate, 보고서: f.reportNm, 사업연도: '', 제출인: f.filer, 접수번호: f.rceptNo, URL: f.url }))
				];
				rows.sort((a, b) => String(b.접수일).localeCompare(String(a.접수일)));
				return [sheet(en ? 'Filings' : '공시리스트', rows)];
			}
		});
		// scan 전종목 — valuation(작음·묶음 가능), finance-lite·changes(180만행·개별 CSV)
		out.push({ key: 'scan:val', label: en ? 'Valuation (PER·PBR·cap)' : '밸류에이션 (PER·PBR·시총)', desc: en ? 'all listed firms' : '상장 전종목', group: 'scan', bare: true, fetch: async () => [sheet(en ? 'Valuation' : '밸류에이션', (await readParquetRows('dart/scan/valuation.parquet')).rows)] });
		out.push({ key: 'scan:fin', label: en ? 'Finance-lite (all · 1.8M)' : '재무 라이트 (전종목·180만행)', desc: en ? 'all firms, key accounts' : '전종목 주요계정', group: 'scan', bare: true, bulk: true, fetch: async () => [sheet('finance-lite', (await readParquetRows('dart/scan/finance-lite.parquet')).rows)] });
		out.push({ key: 'scan:chg', label: en ? 'Disclosure changes (all · 1.8M)' : '공시 변경 (전종목·180만행)', desc: en ? '1Y disclosure diffs' : '1년 공시 변경', group: 'scan', bare: true, bulk: true, fetch: async () => [sheet('changes', (await readParquetRows('dart/scan/changes.parquet')).rows)] });
		// 시장·거시 전역
		for (const m of MARKET_FILES)
			out.push({ key: 'mkt:' + m.path, label: m.label, desc: m.desc, group: 'mkt', bare: true, fetch: async () => [sheet(m.label, (await readParquetRows(m.path)).rows)] });
		out.push({
			key: 'idx', label: en ? 'Market indices (KOSPI·KOSDAQ…)' : '시장지수 (KOSPI·KOSDAQ 등)', desc: en ? 'daily index levels' : '지수별 일별 시계열', group: 'mkt', bare: true,
			fetch: async () => [sheet(en ? 'indices' : '시장지수', reshape(await readShards(KR_INDEX_PRESETS.map((p) => `gov/indices/index/${indexKey(p.market, p.name)}.parquet`)), 'gov/indices/index'))]
		});
		out.push({
			key: 'brk', label: en ? 'Brokerage research (monthly)' : '증권사 리서치 (월별)', desc: en ? 'report link index' : '리포트 링크 인덱스', group: 'mkt', bare: true,
			fetch: async () => {
				const now = new Date();
				const months: string[] = [];
				for (let y = 2019; y <= now.getFullYear(); y += 1)
					for (let m = 1; m <= 12; m += 1) {
						if (y === now.getFullYear() && m > now.getMonth() + 1) break;
						months.push(`research/brokerage/${y}${String(m).padStart(2, '0')}.parquet`);
					}
				return [sheet(en ? 'brokerage' : '증권사리서치', await readShards(months))];
			}
		});
		out.push({
			key: 'pxy', label: en ? 'All-stock daily prices (latest yr)' : '전종목 일별시세 (최근연도)', desc: en ? 'latest year · 670k rows' : '최근연도 · 67만행', group: 'mkt', bare: true,
			fetch: async () => {
				const y = new Date().getFullYear();
				for (const yr of [y, y - 1, y - 2]) {
					const rows = await readShards([`gov/prices/date/${yr}.parquet`]);
					if (rows.length) return [sheet((en ? 'all_stock_daily_' : '전종목일별시세_') + yr, rows)];
				}
				return [];
			}
		});
		return out;
	});

	const byGroup = (g: Src['group']) => SOURCES.filter((s) => s.group === g);
	const combinable = $derived(SOURCES.filter((s) => !s.bulk).map((s) => s.key));
	const selCount = $derived(combinable.filter((k) => sel.has(k)).length);
	const allSel = $derived(combinable.length > 0 && selCount === combinable.length);

	function toggle(key: string) {
		if (sel.has(key)) sel.delete(key);
		else sel.add(key);
		sel = new Set(sel);
	}
	function selectAll() {
		sel = allSel ? new Set() : new Set(combinable);
	}

	const EXCEL_MAX = 1_000_000; // 엑셀 시트 행 한도(1,048,575) 이하로 분할 → 각 파일이 엑셀에서 열린다.
	function zipCsvs(sheets: ObjectSheet[]): Uint8Array {
		const zip = new ZipStore();
		const te = new TextEncoder();
		const used = new Set<string>();
		const add = (label: string, cols: string[], rows: Record<string, unknown>[]) => {
			let base = clean(label) || 'sheet';
			let nm = base;
			let n = 2;
			while (used.has(nm)) nm = `${base}_${n++}`;
			used.add(nm);
			zip.addEntry(`${nm}.csv`, te.encode(toCsv(cols, rows)));
		};
		for (const s of sheets) {
			if (s.rows.length > EXCEL_MAX)
				for (let i = 0, part = 1; i < s.rows.length; i += EXCEL_MAX, part += 1) add(`${s.label}_${part}`, s.columns, s.rows.slice(i, i + EXCEL_MAX));
			else add(s.label, s.columns, s.rows);
		}
		return zip.finalize();
	}

	// 개별 다운로드(주로 bulk) — 한 소스만.
	async function dlOne(src: Src, fmt: 'xlsx' | 'csv') {
		if (busy) return;
		busy = src.key;
		err = '';
		try {
			const sheets = (await src.fetch()).filter((s) => s.rows.length);
			if (!sheets.length) {
				err = en ? 'no data' : '데이터 없음';
				return;
			}
			const name = src.bare ? clean(src.label) : stem(src.label);
			if (fmt === 'xlsx') downloadBlob(objectsToWorkbook(sheets), `${name}.xlsx`, XLSX_MIME);
			else if (sheets.length === 1 && sheets[0].rows.length <= EXCEL_MAX) downloadCsv(name, sheets[0].columns, sheets[0].rows);
			else downloadBlob(zipCsvs(sheets), `${name}.zip`, 'application/zip'); // 180만행 → 104만행 이하로 분할
		} catch (e) {
			err = e instanceof Error ? e.message : String(e);
		} finally {
			busy = '';
		}
	}

	// 묶음 다운로드 — 선택한 소스(비-bulk) 전부 → 단일 Excel(시트 분할) 또는 CSV(zip).
	async function dlBundle(fmt: 'xlsx' | 'csv') {
		const chosen = SOURCES.filter((s) => sel.has(s.key) && !s.bulk);
		if (!chosen.length || busy) return;
		busy = 'bundle';
		err = '';
		try {
			const all = await Promise.all(chosen.map((s) => s.fetch().catch(() => [] as ObjectSheet[])));
			const sheets = all.flat().filter((s) => s.rows.length);
			if (!sheets.length) {
				err = en ? 'no data' : '데이터 없음';
				return;
			}
			const name = `${corpName || code}_${en ? 'data' : '데이터'}`;
			if (fmt === 'xlsx') downloadBlob(objectsToWorkbook(sheets), `${name}.xlsx`, XLSX_MIME);
			else downloadBlob(zipCsvs(sheets), `${name}.zip`, 'application/zip');
		} catch (e) {
			err = e instanceof Error ? e.message : String(e);
		} finally {
			busy = '';
		}
	}
</script>

<svelte:window onkeydown={(e) => { if (open && e.key === 'Escape') open = false; }} />
<div class="dataDl">
	<button class={'hdrLink' + (open ? ' on' : '')} onclick={() => (open = !open)} title={en ? 'Download data for this company' : '이 회사 데이터 다운로드'}>
		{en ? 'Data' : '데이터'}
	</button>
</div>
{#if open}
	<button class="dlgBackdrop" aria-label={en ? 'close' : '닫기'} onclick={() => (open = false)}></button>
	<div class="dlg" role="dialog" aria-modal="true" aria-label={en ? 'Data download' : '데이터 다운로드'}>
		<div class="dlgHead">
			<span class="dlgTitle">{corpName || code} <span class="dlgSub">{en ? 'data download' : '데이터 다운로드'}</span></span>
			<button class="dlgClose" aria-label={en ? 'close' : '닫기'} onclick={() => (open = false)}>✕</button>
		</div>

		<div class="dlgHint">{en ? 'Tick the datasets you want, then download them together as one Excel (sheet per dataset) or CSV zip.' : '원하는 데이터셋을 체크하고 한 번에 받으세요 — 하나의 엑셀(데이터셋별 시트) 또는 CSV 묶음(zip).'}</div>

		<a class="dcGo" href="{base}/lab/data-center" target="_blank" rel="noopener">{en ? 'Data Center — browse all files, preview & live API (Sheets·Python·curl) ↗' : '데이터 센터 — 전체 파일 탐색·미리보기·라이브 API (시트·Python·curl) ↗'}</a>

		<div class="dlgBody">
			<div class="dlgCol">
				<div class="dpDiv">{en ? 'this company' : '이 회사'}</div>
				{#each byGroup('co') as s (s.key)}
					<label class="dsRow rowSel">
						<input type="checkbox" checked={sel.has(s.key)} onchange={() => toggle(s.key)} />
						<span class="dsLabel">{s.label}<span class="dsDir">{s.desc}</span></span>
					</label>
				{/each}

				<div class="dpDiv">{en ? 'cross-section (all firms)' : '전종목 프리빌드'}</div>
				{#each byGroup('scan') as s (s.key)}
					{#if s.bulk}
						<div class="dsRow">
							<span class="dsLabel dsLabelPad">{s.label}<span class="dsDir">{s.desc} · {en ? 'split CSV zip (Excel-openable)' : '엑셀로 열리게 분할 zip'}</span></span>
							<button class="dsBtn" onclick={() => dlOne(s, 'csv')} disabled={!!busy}>{busy === s.key ? '…' : (en ? 'CSV zip' : 'CSV 분할')}</button>
						</div>
					{:else}
						<label class="dsRow rowSel">
							<input type="checkbox" checked={sel.has(s.key)} onchange={() => toggle(s.key)} />
							<span class="dsLabel">{s.label}<span class="dsDir">{s.desc}</span></span>
						</label>
					{/if}
				{/each}
			</div>

			<div class="dlgCol">
				<div class="dpDiv">{en ? 'market & macro (global)' : '시장·거시 (전역)'}</div>
				{#each byGroup('mkt') as s (s.key)}
					<label class="dsRow rowSel">
						<input type="checkbox" checked={sel.has(s.key)} onchange={() => toggle(s.key)} />
						<span class="dsLabel">{s.label}<span class="dsDir">{s.desc}</span></span>
					</label>
				{/each}
			</div>
		</div>

		{#if err}<div class="dsErr">⚠ {err}</div>{/if}

		<div class="dlgFoot">
			<button class="footSel" onclick={selectAll}>{allSel ? (en ? 'Clear' : '선택 해제') : (en ? 'Select all' : '전체 선택')}</button>
			<span class="footN">{en ? `${selCount} selected` : `${selCount}개 선택`}</span>
			<span class="footBtns">
				<button class="dsBtn dsBtnGo" disabled={!selCount || !!busy} onclick={() => dlBundle('xlsx')}>{busy === 'bundle' ? '…' : (en ? 'Excel' : 'Excel 묶음')}</button>
				<button class="dsBtn" disabled={!selCount || !!busy} onclick={() => dlBundle('csv')}>{busy === 'bundle' ? '…' : (en ? 'CSV zip' : 'CSV 묶음')}</button>
			</span>
		</div>

		<div class="dpPolicy">
			<div>
				{en ? 'Source' : '원자료'} <b>{isUs ? 'SEC EDGAR' : 'DART'}</b> · {en ? 'processed by' : '가공'} <b>dartlab</b> · HuggingFace · {en ? 'public data, free to use & redistribute' : '공공데이터·영리/비영리 자유 이용·재배포 가능'}.
			</div>
			<div class="dpWarn">⚠ {en ? 'Not investment advice. News is live-only (press copyright, no redistribution).' : '투자 자문 아님. 뉴스는 라이브 표시 전용(언론사 저작권·재배포 불가)'}.</div>
			<a class="dpTerms" href={termsUrl} target="_blank" rel="noreferrer">{isUs ? 'SEC EDGAR' : 'DART'} {en ? 'terms' : '이용약관'} ↗</a>
		</div>
	</div>
{/if}

<style>
	.dataDl {
		position: relative;
		display: inline-flex;
	}
	.dlgBackdrop {
		position: fixed;
		inset: 0;
		z-index: 200;
		background: rgba(2, 6, 16, 0.66);
		border: 0;
		cursor: default;
	}
	.dlg {
		position: fixed;
		top: 50%;
		left: 50%;
		transform: translate(-50%, -50%);
		z-index: 201;
		width: min(780px, 94vw);
		max-height: 88vh;
		display: flex;
		flex-direction: column;
		overflow: hidden;
		background: #0a0e18;
		border: 1px solid #263145;
		border-radius: 10px;
		box-shadow: 0 24px 64px rgba(0, 0, 0, 0.6);
	}
	.dlgHead {
		display: flex;
		align-items: center;
		justify-content: space-between;
		padding: 11px 16px;
		border-bottom: 1px solid #1e2433;
		flex-shrink: 0;
	}
	.dlgTitle {
		font-size: 13px;
		font-weight: 600;
		color: #e2e8f0;
	}
	.dlgSub {
		color: #64748b;
		font-weight: 400;
		margin-left: 6px;
	}
	.dlgClose {
		border: 0;
		background: transparent;
		color: #64748b;
		font-size: 15px;
		line-height: 1;
		cursor: pointer;
		padding: 3px 7px;
		border-radius: 4px;
	}
	.dlgClose:hover {
		color: #e2e8f0;
		background: rgba(255, 255, 255, 0.06);
	}
	.dlgHint {
		flex-shrink: 0;
		padding: 7px 16px;
		font-size: 11px;
		color: #94a3b8;
		background: rgba(245, 158, 11, 0.05);
		border-bottom: 1px solid #1e2433;
	}
	.dcGo {
		flex-shrink: 0;
		display: block;
		padding: 9px 16px;
		font-size: 12px;
		font-weight: 600;
		color: var(--amber, #f59e0b);
		text-decoration: none;
		background: rgba(var(--amber-rgb, 245, 158, 11), 0.08);
		border-bottom: 1px solid #1e2433;
	}
	.dcGo:hover {
		background: rgba(var(--amber-rgb, 245, 158, 11), 0.16);
		text-decoration: underline;
	}
	.dlgBody {
		display: grid;
		grid-template-columns: 1fr 1fr;
		gap: 0 24px;
		padding: 8px 16px 12px;
		overflow-y: auto;
	}
	.dlgCol {
		display: flex;
		flex-direction: column;
		gap: 1px;
		min-width: 0;
	}
	@media (max-width: 600px) {
		.dlgBody {
			grid-template-columns: 1fr;
		}
	}
	.dpDiv {
		margin-top: 10px;
		margin-bottom: 2px;
		font-size: 10px;
		font-weight: 600;
		color: #9fb0c6;
		text-transform: uppercase;
		letter-spacing: 0.04em;
	}
	.dlgCol > .dpDiv:first-child {
		margin-top: 2px;
	}
	.dsRow {
		display: flex;
		align-items: center;
		gap: 9px;
		padding: 4px 2px;
		border-radius: 5px;
	}
	.rowSel {
		cursor: pointer;
	}
	.rowSel:hover {
		background: rgba(245, 158, 11, 0.06);
	}
	.dsRow input[type='checkbox'] {
		flex-shrink: 0;
		width: 15px;
		height: 15px;
		accent-color: #f59e0b;
		cursor: pointer;
		margin: 0;
	}
	.dsLabel {
		display: flex;
		flex-direction: column;
		flex: 1;
		min-width: 0;
		font-size: 12px;
		color: #e2e8f0;
		line-height: 1.25;
	}
	.dsLabelPad {
		padding-left: 0;
	}
	.dsDir {
		font-size: 10px;
		color: #8493a8;
	}
	.dsBtn {
		flex-shrink: 0;
		min-width: 46px;
		padding: 5px 10px;
		border: 1px solid rgba(245, 158, 11, 0.4);
		border-radius: 5px;
		background: rgba(245, 158, 11, 0.1);
		color: #fbbf24;
		font: inherit;
		font-size: 11px;
		font-weight: 600;
		cursor: pointer;
		text-align: center;
	}
	.dsBtn:hover:not(:disabled) {
		background: rgba(245, 158, 11, 0.2);
	}
	.dsBtn:disabled {
		opacity: 0.45;
		cursor: default;
	}
	.dsBtnGo {
		background: #f59e0b;
		color: #0a0e18;
		border-color: #f59e0b;
	}
	.dsBtnGo:hover:not(:disabled) {
		background: #fbbf24;
	}
	.dsErr {
		font-size: 11px;
		color: #fca5a5;
		padding: 3px 16px;
		flex-shrink: 0;
	}
	.dlgFoot {
		display: flex;
		align-items: center;
		gap: 12px;
		flex-shrink: 0;
		padding: 9px 16px;
		border-top: 1px solid #1e2433;
		background: #0c1120;
	}
	.footSel {
		border: 1px solid #334155;
		background: transparent;
		color: #cbd5e1;
		font: inherit;
		font-size: 11px;
		font-weight: 600;
		padding: 5px 11px;
		border-radius: 5px;
		cursor: pointer;
	}
	.footSel:hover {
		background: rgba(255, 255, 255, 0.05);
	}
	.footN {
		font-size: 11px;
		color: #94a3b8;
	}
	.footBtns {
		margin-left: auto;
		display: flex;
		gap: 6px;
	}
	.dpPolicy {
		display: flex;
		flex-direction: column;
		gap: 3px;
		flex-shrink: 0;
		padding: 9px 16px 12px;
		border-top: 1px solid #1e2433;
		font-size: 10.5px;
		line-height: 1.5;
		color: #a8b4c6;
	}
	.dpPolicy b {
		color: #cbd5e1;
		font-weight: 600;
	}
	.dpWarn {
		color: #fbbf24;
	}
	.dpTerms {
		align-self: flex-start;
		color: var(--amber, #f59e0b);
		text-decoration: none;
	}
	.dpTerms:hover {
		text-decoration: underline;
	}
</style>
