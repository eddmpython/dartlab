<script lang="ts">
	// 터미널 상단(헤더) 「데이터」 — 공개 데이터를 Excel·CSV 로. 브라우저 parquet/포트 직독→변환(서버 0).
	// 회사별: 재무(원본 long + 시계열 가공 IS/BS/CF 시트분할)·공시수평화·정기보고서·일별시세·공시리스트.
	// 전종목: scan 프리빌드. 전역(회사 무관, 헤더라 상시): 거시(FRED·ECOS·관세청)·SEC ticker맵·시장지수·증권사
	// 리서치·전종목 시세. 뉴스는 언론사 저작권(재배포 불가)이라 라이브 표시 전용 — 다운로드 미제공.
	import type { DartLabRuntime, StmtKind } from '@dartlab/ui-contracts';
	import { KR_INDEX_PRESETS } from '@dartlab/ui-contracts';
	import { DOWNLOAD_CATALOG } from '@dartlab/ui-runtime/data/catalog/downloadCatalog';
	import { readParquetRows } from '@dartlab/ui-runtime/data/parquet/hfRange';
	import { objectsToWorkbook, downloadBlob, downloadCsv, type ObjectSheet } from '../../downloadExport';
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
	// 회사 단위 parquet 데이터셋 (카탈로그 자동 — 새 회사 dir 추가 시 자동 노출). krx/prices/company 제외(gov 중복·404).
	const parquetSets = $derived(
		DOWNLOAD_CATALOG.filter(
			(e) =>
				e.shardKind === 'company' &&
				e.dir !== 'krx/prices/company' &&
				LABELS[e.dir] &&
				(isUs ? e.dir.startsWith('edgar/') : e.dir.startsWith('dart/') || e.dir.startsWith('gov/'))
		)
	);

	// scan 프리빌드 — 전종목 횡단 파일. valuation 은 작아(2.5천행) Excel/CSV, finance-lite·changes 는 180만행이라
	// Excel 한도(104만) 초과 → CSV 만(parquet 안 줌 — 일반인용). csvOnly=Excel 버튼 숨김.
	const SCAN_FILES = $derived([
		{ path: 'dart/scan/valuation.parquet', label: en ? 'Valuation (PER·PBR·cap)' : '밸류에이션 (PER·PBR·시총)', csvOnly: false },
		{ path: 'dart/scan/finance-lite.parquet', label: en ? 'Finance-lite (all · 1.8M rows)' : '재무 라이트 (전종목·180만행)', csvOnly: true },
		{ path: 'dart/scan/changes.parquet', label: en ? 'Disclosure changes (all · 1.8M)' : '공시 변경 (전종목·180만행)', csvOnly: true }
	]);

	let open = $state(false);
	let busy = $state('');
	let err = $state('');

	const clean = (s: string) => s.replace(/[/ ()·]/g, '');
	function stem(label: string): string {
		return `${corpName || code}_${clean(label)}`;
	}
	// fileStem 미지정 = 회사 접두(회사 데이터). 전역(거시·지수) 데이터는 회사명 접두 없이 label 그대로.
	function emit(label: string, rows: Record<string, unknown>[], fmt: 'xlsx' | 'csv', fileStem?: string) {
		if (!rows.length) {
			err = en ? 'no data' : '데이터 없음';
			return;
		}
		const cols = Object.keys(rows[0]);
		const name = fileStem ?? stem(label);
		if (fmt === 'csv') downloadCsv(name, cols, rows);
		else downloadBlob(objectsToWorkbook([{ label, columns: cols, rows }]), `${name}.xlsx`, XLSX_MIME);
	}

	async function run(key: string, fn: () => Promise<void>) {
		if (busy) return;
		busy = key;
		err = '';
		try {
			await fn();
		} catch (e) {
			err = e instanceof Error ? e.message : String(e);
		} finally {
			busy = '';
		}
	}

	// 일반인용 컬럼 정리 — pick: 내부 엔진 컬럼(atocId·xbrlMatchScore 등) 제거하고 사용자 컬럼만. ko: raw 소스
	// 코드(BAS_DD·CLSPRC_IDX 등)를 한글로. 원본(dart/finance·edgar/financeStmt)은 비포함 → raw 유지(시계열이 가공본).
	const COL_SPEC: Record<string, { pick?: string[]; ko?: Record<string, string> }> = {
		'dart/panel': {
			pick: ['corp', 'period', 'rceptNo', 'chapter', 'sectionPath', 'sectionLeaf', 'contentRaw'],
			ko: { corp: '회사', period: '기간', rceptNo: '접수번호', chapter: '장', sectionPath: '섹션경로', sectionLeaf: '항목', contentRaw: '내용' }
		},
		'edgar/panel': {
			pick: ['corp', 'period', 'rceptNo', 'chapter', 'sectionPath', 'sectionLeaf', 'contentRaw'],
			ko: { corp: '회사', period: '기간', rceptNo: '접수번호', chapter: '장', sectionPath: '섹션경로', sectionLeaf: '항목', contentRaw: '내용' }
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
			for (const c of cols) o[spec.ko?.[c] ?? c] = r[c];
			return o;
		});
	}

	const dlParquet = (dir: string, fmt: 'xlsx' | 'csv') =>
		run(`${dir}:${fmt}`, async () => {
			const { rows } = await readParquetRows(`${dir}/${code}.parquet`);
			emit(LABELS[dir] ?? dir, reshape(rows, dir), fmt);
		});

	// 재무제표 시계열 — 가공된 IS/BS/CF(+비율) 를 계정×기간으로, 시트 분할.
	const dlFinanceTs = () =>
		run('finTs', async () => {
			const bundle = await runtime.finance.bundle(code);
			const view = bundle?.views[bundle.defaultMode] ?? bundle?.views.annual ?? bundle?.views.quarter ?? null;
			if (!view) {
				err = en ? 'no financials' : '재무 데이터 없음';
				return;
			}
			const periods = view.periods;
			const kinds: { k: StmtKind; label: string }[] = [
				{ k: 'IS', label: en ? 'Income' : '손익계산서' },
				{ k: 'BS', label: en ? 'Balance' : '재무상태표' },
				{ k: 'CF', label: en ? 'Cashflow' : '현금흐름표' }
			];
			const toRows = (stmt: { kr: string; en: string; values: (number | null)[] }[]) =>
				stmt.map((r) => {
					const o: Record<string, unknown> = { [en ? 'Account' : '계정']: en ? r.en : r.kr };
					periods.forEach((p, i) => (o[p] = r.values[i]));
					return o;
				});
			const sheets: ObjectSheet[] = kinds
				.map(({ k, label }) => ({ label, columns: [en ? 'Account' : '계정', ...periods], rows: toRows(view.statements[k] ?? []) }))
				.filter((s) => s.rows.length);
			if (view.ratios?.length)
				sheets.push({ label: en ? 'Ratios' : '주요비율', columns: [en ? 'Metric' : '지표', ...periods], rows: toRows(view.ratios) });
			if (!sheets.length) {
				err = en ? 'no financials' : '재무 데이터 없음';
				return;
			}
			const cur = bundle?.currency === 'USD' ? 'USD-bil' : '조원';
			downloadBlob(objectsToWorkbook(sheets), `${stem((en ? 'financials_timeseries_' : '재무제표_시계열_') + cur)}.xlsx`, XLSX_MIME);
		});

	// 공시 리스트 — 정기 + 수시 공시 목록(접수일·보고서·접수번호·URL).
	const dlFilings = (fmt: 'xlsx' | 'csv') =>
		run(`filings:${fmt}`, async () => {
			const [reg, non] = await Promise.all([runtime.filing.regular(code, 300), runtime.filing.nonRegular(code, 1000)]);
			const rows: Record<string, unknown>[] = [
				...reg.map((f) => ({ 구분: en ? 'regular' : '정기', 접수일: f.rceptDate, 보고서: f.reportType, 사업연도: f.year, 제출인: '', 접수번호: f.rceptNo, URL: f.url })),
				...non.map((f) => ({ 구분: en ? 'event' : '수시', 접수일: f.rceptDate, 보고서: f.reportNm, 사업연도: '', 제출인: f.filer, 접수번호: f.rceptNo, URL: f.url }))
			];
			rows.sort((a, b) => String(b.접수일).localeCompare(String(a.접수일)));
			emit(en ? 'filings' : '공시리스트', rows, fmt);
		});

	const dlScan = (file: { path: string; label: string }, fmt: 'xlsx' | 'csv') =>
		run(`scan:${file.path}:${fmt}`, async () => {
			const { rows } = await readParquetRows(file.path);
			emit(file.label, rows, fmt, clean(file.label)); // 전종목 — 회사명 접두 없이
		});

	// 시장·거시 전역 데이터 — 회사 무관(헤더라 상시 노출). 모두 Excel/CSV 직변환(행수 ≤104만 안전 실측).
	// krx/indices·krx/prices·edgar/meta 는 HF 미발행이라 제외.
	const MARKET_FILES = $derived([
		{ path: 'macro/fred/observations.parquet', label: en ? 'FRED macro series' : 'FRED 거시 시계열' },
		{ path: 'macro/ecos/observations.parquet', label: en ? 'ECOS (BOK) macro' : 'ECOS 한은 거시' },
		{ path: 'macro/customs/observations.parquet', label: en ? 'Customs trade (KR)' : '관세청 수출입' },
		{ path: 'edgar/tickers/tickers.parquet', label: en ? 'SEC ticker↔CIK map' : 'SEC ticker↔CIK 맵' }
	]);
	const dlMarket = (m: { path: string; label: string }, fmt: 'xlsx' | 'csv') =>
		run(`mkt:${m.path}:${fmt}`, async () => {
			const { rows } = await readParquetRows(m.path);
			emit(m.label, rows, fmt, clean(m.label));
		});

	// 다파일 데이터셋 → 일반인용 Excel/CSV (개발자용 parquet 폴더 대신). HF tree API 는 CORS 차단이라 브라우저
	// 나열 불가 → 샤드 경로를 런타임 지식(지수 프리셋·월/연 범위)으로 생성, 404 샤드는 skip 후 concat.
	const RESERVED = /[/\\:*?"<>|]/g;
	const indexKey = (market: string, name: string) =>
		`${market}-${name.normalize('NFC').trim().replace(RESERVED, '_').replace(/\s+/g, '_').replace(/_+/g, '_').replace(/^_+|_+$/g, '')}`;
	async function readShards(paths: string[], cap = 6): Promise<Record<string, unknown>[]> {
		const out: Record<string, unknown>[] = [];
		for (let i = 0; i < paths.length; i += cap) {
			const res = await Promise.allSettled(paths.slice(i, i + cap).map((p) => readParquetRows(p)));
			for (const r of res) if (r.status === 'fulfilled') out.push(...(r.value.rows as Record<string, unknown>[]));
		}
		return out;
	}
	// 시장지수 — KR 프리셋 5종 per-index(전이력) concat.
	const dlIndices = (fmt: 'xlsx' | 'csv') =>
		run(`idx:${fmt}`, async () => {
			const rows = await readShards(KR_INDEX_PRESETS.map((p) => `gov/indices/index/${indexKey(p.market, p.name)}.parquet`));
			emit(en ? 'Market indices' : '시장지수', reshape(rows, 'gov/indices/index'), fmt, en ? 'market_indices' : '시장지수');
		});
	// 증권사 리서치 — 201901~현재월 probe(월 sparse·인덱스 없음), 존재분 concat.
	const dlBrokerage = (fmt: 'xlsx' | 'csv') =>
		run(`brk:${fmt}`, async () => {
			const now = new Date();
			const months: string[] = [];
			for (let y = 2019; y <= now.getFullYear(); y += 1)
				for (let m = 1; m <= 12; m += 1) {
					if (y === now.getFullYear() && m > now.getMonth() + 1) break;
					months.push(`research/brokerage/${y}${String(m).padStart(2, '0')}.parquet`);
				}
			emit(en ? 'Brokerage research' : '증권사 리서치', await readShards(months), fmt, en ? 'brokerage_research' : '증권사리서치');
		});
	// 전종목 일별시세 — 최근 가용연도 1개(전체는 67만행×N년이라 폴더 ↗). CSV 권장.
	const dlPricesYear = (fmt: 'xlsx' | 'csv') =>
		run(`pxy:${fmt}`, async () => {
			const y = new Date().getFullYear();
			for (const yr of [y, y - 1, y - 2]) {
				const rows = await readShards([`gov/prices/date/${yr}.parquet`]);
				if (rows.length) return emit(en ? 'All-stock daily' : '전종목 일별시세', rows, fmt, (en ? 'all_stock_daily_' : '전종목일별시세_') + yr);
			}
			err = en ? 'no data' : '데이터 없음';
		});
</script>

<svelte:window onkeydown={(e) => { if (open && e.key === 'Escape') open = false; }} />
<div class="dataDl">
	<button class={'hdrLink' + (open ? ' on' : '')} onclick={() => (open = !open)} title={en ? 'Download all data for this company' : '이 회사 전체 데이터 다운로드'}>
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

		<div class="dlgBody">
			<div class="dlgCol">
				<div class="dpDiv">{en ? 'this company' : '이 회사'}</div>
				<div class="dsRow">
					<span class="dsLabel">{en ? 'Financials — time series' : '재무제표 — 시계열'}<span class="dsDir">IS·BS·CF{en ? ' (sheets)' : ' (시트 분할)'}</span></span>
					<span class="dsBtns"><button class="dsBtn" onclick={dlFinanceTs} disabled={!!busy}>{busy === 'finTs' ? '…' : 'Excel'}</button></span>
				</div>
				{#each parquetSets as d (d.dir)}
					<div class="dsRow">
						<span class="dsLabel">{LABELS[d.dir]}<span class="dsDir">{d.dir}</span></span>
						<span class="dsBtns">
							<button class="dsBtn" onclick={() => dlParquet(d.dir, 'xlsx')} disabled={!!busy}>{busy === `${d.dir}:xlsx` ? '…' : 'Excel'}</button>
							<button class="dsBtn" onclick={() => dlParquet(d.dir, 'csv')} disabled={!!busy}>{busy === `${d.dir}:csv` ? '…' : 'CSV'}</button>
						</span>
					</div>
				{/each}
				<div class="dsRow">
					<span class="dsLabel">{en ? 'Filings list' : '공시 리스트'}<span class="dsDir">{en ? 'regular + events' : '정기 + 수시'}</span></span>
					<span class="dsBtns">
						<button class="dsBtn" onclick={() => dlFilings('xlsx')} disabled={!!busy}>{busy === 'filings:xlsx' ? '…' : 'Excel'}</button>
						<button class="dsBtn" onclick={() => dlFilings('csv')} disabled={!!busy}>{busy === 'filings:csv' ? '…' : 'CSV'}</button>
					</span>
				</div>

				<div class="dpDiv">{en ? 'cross-section prebuild (all)' : '전종목 프리빌드'}</div>
				{#each SCAN_FILES as s (s.path)}
					<div class="dsRow">
						<span class="dsLabel">{s.label}<span class="dsDir">{s.path.replace('.parquet', '')}</span></span>
						<span class="dsBtns">
							{#if !s.csvOnly}<button class="dsBtn" onclick={() => dlScan(s, 'xlsx')} disabled={!!busy}>{busy === `scan:${s.path}:xlsx` ? '…' : 'Excel'}</button>{/if}
							<button class="dsBtn" onclick={() => dlScan(s, 'csv')} disabled={!!busy}>{busy === `scan:${s.path}:csv` ? '…' : 'CSV'}</button>
						</span>
					</div>
				{/each}
			</div>

			<div class="dlgCol">
				<div class="dpDiv">{en ? 'market & macro (global)' : '시장·거시 (전역)'}</div>
				{#each MARKET_FILES as m (m.path)}
					<div class="dsRow">
						<span class="dsLabel">{m.label}<span class="dsDir">{m.path.replace('.parquet', '')}</span></span>
						<span class="dsBtns">
							<button class="dsBtn" onclick={() => dlMarket(m, 'xlsx')} disabled={!!busy}>{busy === `mkt:${m.path}:xlsx` ? '…' : 'Excel'}</button>
							<button class="dsBtn" onclick={() => dlMarket(m, 'csv')} disabled={!!busy}>{busy === `mkt:${m.path}:csv` ? '…' : 'CSV'}</button>
						</span>
					</div>
				{/each}
				<div class="dsRow">
					<span class="dsLabel">{en ? 'Market indices (KOSPI·KOSDAQ…)' : '시장지수 (KOSPI·KOSDAQ 등)'}<span class="dsDir">gov/indices/index</span></span>
					<span class="dsBtns">
						<button class="dsBtn" onclick={() => dlIndices('xlsx')} disabled={!!busy}>{busy === 'idx:xlsx' ? '…' : 'Excel'}</button>
						<button class="dsBtn" onclick={() => dlIndices('csv')} disabled={!!busy}>{busy === 'idx:csv' ? '…' : 'CSV'}</button>
					</span>
				</div>
				<div class="dsRow">
					<span class="dsLabel">{en ? 'Brokerage research (monthly)' : '증권사 리서치 (월별)'}<span class="dsDir">research/brokerage</span></span>
					<span class="dsBtns">
						<button class="dsBtn" onclick={() => dlBrokerage('xlsx')} disabled={!!busy}>{busy === 'brk:xlsx' ? '…' : 'Excel'}</button>
						<button class="dsBtn" onclick={() => dlBrokerage('csv')} disabled={!!busy}>{busy === 'brk:csv' ? '…' : 'CSV'}</button>
					</span>
				</div>
				<div class="dsRow">
					<span class="dsLabel">{en ? 'All-stock daily prices (latest yr)' : '전종목 일별시세 (최근연도)'}<span class="dsDir">gov/prices/date · 67만행</span></span>
					<span class="dsBtns">
						<button class="dsBtn" onclick={() => dlPricesYear('csv')} disabled={!!busy}>{busy === 'pxy:csv' ? '…' : 'CSV'}</button>
					</span>
				</div>
			</div>
		</div>

		{#if err}<div class="dsErr">⚠ {err}</div>{/if}

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
		width: min(760px, 94vw);
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
	@media (max-width: 580px) {
		.dlgBody {
			grid-template-columns: 1fr;
		}
	}
	.dpDiv {
		margin-top: 9px;
		font-size: 9px;
		color: #475569;
		text-transform: uppercase;
		letter-spacing: 0.04em;
	}
	.dlgCol > .dpDiv:first-child {
		margin-top: 2px;
	}
	.dsRow {
		display: flex;
		align-items: center;
		justify-content: space-between;
		gap: 8px;
		padding: 4px 0 4px 2px;
	}
	.dsLabel {
		display: flex;
		flex-direction: column;
		font-size: 12px;
		color: #e2e8f0;
		line-height: 1.25;
	}
	.dsDir {
		font-size: 9px;
		color: #475569;
		font-family: ui-monospace, monospace;
	}
	.dsBtns {
		display: flex;
		gap: 5px;
		flex-shrink: 0;
	}
	.dsBtn {
		min-width: 46px;
		padding: 5px 9px;
		border: 1px solid rgba(245, 158, 11, 0.4);
		border-radius: 5px;
		background: rgba(245, 158, 11, 0.1);
		color: #fbbf24;
		font: inherit;
		font-size: 11px;
		font-weight: 600;
		cursor: pointer;
		text-decoration: none;
		text-align: center;
	}
	.dsBtn:hover:not(:disabled) {
		background: rgba(245, 158, 11, 0.2);
	}
	.dsBtn:disabled {
		opacity: 0.5;
		cursor: default;
	}
	.dsErr {
		font-size: 11px;
		color: #fca5a5;
		padding: 3px 16px;
		flex-shrink: 0;
	}
	.dpPolicy {
		display: flex;
		flex-direction: column;
		gap: 3px;
		flex-shrink: 0;
		padding: 9px 16px 12px;
		border-top: 1px solid #1e2433;
		font-size: 10px;
		line-height: 1.5;
		color: #94a3b8;
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
