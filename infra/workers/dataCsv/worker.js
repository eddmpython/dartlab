// DartLab 라이브 데이터 API — HF parquet 를 요청 시점에 CSV/TSV 로 온더플라이 디코드.
//
// 목적: 구글시트 `=IMPORTDATA(".../v1/dart/finance/005930.csv")` · 엑셀 Power Query(데이터→웹에서)가
// dartlab 공동작업대(HF parquet SSOT)를 **런타임 소스로 라이브** 사용. CSV 사본을 HF 에 굽지 않는다
// (no-build, SSOT 직독). mainPlan/data-download-center 01·03·04 계약 구현.
//
// ── 호스트 메모리 (실측 게이트) ───────────────────────────────────────────────────────────
// 디코드 메모리는 parquet 압축해제 비용. 실측: gov/prices/company 70MB · dart/finance 119MB ·
// macro/fred 210MB · dart/panel 927MB(본문 contentRaw). CF Workers 는 128MB 고정(전 플랜)이라 큰
// 파일을 못 올린다. → 본 워커는 footer 의 컬럼별 total_uncompressed_size 합으로 **디코드 전에**
// 예산(MAX_DECODE_BYTES)을 검사해 초과면 413(+`cols` 투영 안내). cols 투영이 진짜 탈출구다
// (panel 본문 제외 시 927→83MB, 실측). 예산은 호스트별 env 한 줄: CF=~90MB(작은 파일만 라이브),
// ~1GB 서버리스(Vercel/Netlify 함수)=~700MB(전 카탈로그 라이브). 코드는 호스트 무관 — 같은 핸들러가
// node(dev.mjs)·CF·서버리스 함수에서 동일 동작.
//
// 보안: allowlist.js(public·flat·표형 dir) 단일 게이트. private 6종은 same-repo 라 코드 게이트가
// 유일 방어. {id} 정규식으로 경로주입·절대URL passthrough 차단. hfProxy 의 무게이트 /hf 복제 금지.
//
// 재사용(hfProxy): 403/429/5xx backoff 재시도 · CORS. 신규: allowlist · hyparquet 디코드 ·
// CSV/TSV emit(BOM·en-US 숫자) · 셀cap 헤더 신호 · footer 예산 가드 · /v1 카탈로그 · schema.json.

import { asyncBufferFromUrl, parquetMetadataAsync, parquetReadObjects, parquetSchema } from 'hyparquet';
import { compressors } from 'hyparquet-compressors';
import { ALLOW, RELEASES, isTier2 } from './allowlist.js';

const UPSTREAM_DEFAULT = 'https://huggingface.co/datasets/eddmpython/dartlab-data/resolve/main';
// {id} 가드 — 유니코드 글자/숫자/._- 만(예 'KOSPI-코스피' 지수 stem 허용). '/'·'\'·공백·':'·'?' 등은
// 문자집합에서 배제돼 경로주입·절대URL passthrough 차단. '..' 는 명시 거부(이중 방어).
const ID_RE = /^[\p{L}\p{N}._-]+$/u;
const validId = (id) => ID_RE.test(id) && !id.includes('..');
const FREQS = new Set(['d', 'w', 'm', 'q', 'y']);

// macro 벌크 레이아웃 — fred/ecos/customs 는 per-series 파일이 아니라 observations.parquet 단일 파일
// (seriesId 컬럼으로 전 시리즈 1파일). 사용자는 한 시리즈(예 FRED DGS10)를 원하므로 {id}=seriesId 로
// 보고 observations 를 읽어 그 시리즈만 필터한다. 날짜샤드(decode 후 prune=326MB OOM)와 달리 어차피
// 1파일이라 post-decode 필터가 안전 — spec killList 의 근거가 여기엔 안 걸림. {id}='manifest' 는 시리즈
// 카탈로그(manifest.parquet) 직읽기로 어떤 seriesId 가 있는지 탐색.
const BULK_OBS = new Map([
	['macro/fred', 'seriesId'],
	['macro/ecos', 'seriesId'],
	['macro/customs', 'seriesId']
]);
function resolvePhysical(dir, id) {
	const idCol = BULK_OBS.get(dir);
	if (!idCol) return { stem: id, seriesFilter: null };
	if (id === 'manifest') return { stem: 'manifest', seriesFilter: null };
	return { stem: 'observations', seriesFilter: { col: idCol, value: id } };
}

const CORS = {
	'Access-Control-Allow-Origin': '*', // public 데이터 — Sheets/Excel 임의 origin fetch
	'Access-Control-Allow-Methods': 'GET, HEAD, OPTIONS',
	'Access-Control-Allow-Headers': 'Range',
	'Access-Control-Max-Age': '86400'
};

function num(v, dflt) {
	const n = Number(v);
	return Number.isFinite(n) && n > 0 ? n : dflt;
}

function json(obj, status, extra) {
	return new Response(JSON.stringify(obj, null, status >= 400 ? 0 : 2), {
		status,
		headers: { 'Content-Type': 'application/json; charset=utf-8', ...CORS, ...(extra || {}) }
	});
}

// 403/429/5xx 백오프 재시도 (hfProxy 패턴). 404 등 최종 비-OK 은 그대로 반환 → 호출측 처리.
async function retryFetch(url, init, baseFetch) {
	let up = null;
	for (let attempt = 0; attempt < 4; attempt++) {
		up = await baseFetch(url, init);
		if (up.ok || up.status === 206 || up.status === 304) break;
		if (up.status !== 403 && up.status !== 429 && up.status < 500) break;
		await new Promise((r) => setTimeout(r, 180 * (attempt + 1)));
	}
	return up;
}

// HF LFS 실제 파일 크기 — Range bytes=0-0 으로 x-linked-size/Content-Range/Content-Length 추출.
async function probeSize(url, baseFetch) {
	const r = await retryFetch(url, { headers: { Range: 'bytes=0-0' } }, baseFetch);
	if (r.status === 404) return { status: 404 };
	if (!r.ok && r.status !== 206) return { status: r.status };
	const linked = Number(r.headers.get('x-linked-size'));
	const cr = r.headers.get('content-range');
	const fromCr = cr ? Number(cr.split('/')[1]) : NaN;
	const cl = Number(r.headers.get('content-length'));
	const size = linked > 0 ? linked : fromCr > 0 ? fromCr : cl;
	try { await r.arrayBuffer(); } catch { /* drain */ }
	if (!Number.isFinite(size) || size <= 0) return { status: 502 };
	return { status: 206, size };
}

// footer 의 선택 컬럼 압축해제 바이트 합 — 디코드 메모리 추정(예산 가드의 load-bearing 입력).
// row group 전체 합산(단일 row group 파일이 대부분이라 tail 로는 안 줄지만 cols 투영으로는 준다).
function decodeBytesEstimate(meta, cols) {
	const want = new Set(cols);
	let total = 0;
	for (const rg of meta.row_groups || []) {
		for (const col of rg.columns || []) {
			const md = col.meta_data || col.metaData || {};
			const pathArr = md.path_in_schema || md.pathInSchema || [];
			const name = Array.isArray(pathArr) && pathArr.length ? pathArr[pathArr.length - 1] : md.name || '';
			if (want.has(name)) total += Number(md.total_uncompressed_size || md.totalUncompressedSize || 0);
		}
	}
	return total;
}

// ── 셀 직렬화 — 숫자 정직성(en-US invariant)·결손=빈셀(0 대체 금지)·BOM 선두 ──
function cell(v) {
	if (v === null || v === undefined) return '';
	if (typeof v === 'number') return Number.isFinite(v) ? String(v) : '';
	if (typeof v === 'bigint') return v.toString();
	if (typeof v === 'boolean') return v ? 'true' : 'false';
	if (v instanceof Date) return v.toISOString().slice(0, 10);
	return String(v);
}
// Content-Disposition 파일명 — HTTP 헤더는 Latin1 만이라 한글 stem(예 'KOSPI-코스피')은 헤더 set 시
// throw. RFC 5987: ASCII fallback filename + filename*=UTF-8''<퍼센트인코딩>(전부 ASCII) 동시 제공.
function contentDisposition(id, ext) {
	const name = `${id}.${ext}`;
	const ascii = (id.replace(/[^\x20-\x7E]/g, '_').replace(/"/g, '') || 'data') + '.' + ext;
	return `attachment; filename="${ascii}"; filename*=UTF-8''${encodeURIComponent(name)}`;
}

const csvCell = (v) => { const s = cell(v); return /["\n\r,]/.test(s) ? '"' + s.replace(/"/g, '""') + '"' : s; };
const tsvCell = (v) => cell(v).replace(/[\t\r\n]+/g, ' '); // TSV 는 인용 표준 없음 → 탭·개행을 공백으로

function serialize(rows, cols, ext) {
	const sep = ext === 'tsv' ? '\t' : ',';
	const esc = ext === 'tsv' ? tsvCell : csvCell;
	const out = [cols.map(esc).join(sep)];
	for (const r of rows) out.push(cols.map((c) => esc(r[c])).join(sep));
	return '﻿' + out.join('\r\n') + '\r\n'; // UTF-8 BOM + RFC4180 CRLF
}

// freq 다운샘플 — last-of-period 단일 규칙. date 컬럼 자동탐지, period 버킷별 최신 1행.
function detectDateCol(cols) {
	return cols.find((c) => /(^date$|날짜|기준일|^month$|pub_?date|기간)/i.test(c)) || null;
}
// 날짜값 → YYYYMMDD 숫자열. parquet DATE 논리타입은 hyparquet 가 Date 객체로 주는데(FRED 등)
// String(Date)='Mon Jun 22 2026…' 라 day 가 앞에 와 digits 가 깨진다 → cell() 과 동일하게 ISO 정규화.
// 'YYYYMMDD'·'YYYY-MM-DD' 문자열(gov·brokerage)은 그대로 숫자만 추출.
function dateDigits(v) {
	if (v instanceof Date) return v.toISOString().slice(0, 10).replace(/-/g, '');
	return String(v ?? '').replace(/[^0-9]/g, '');
}

function downsample(rows, dateCol, freq) {
	const bucket = new Map();
	for (const r of rows) {
		const digits = dateDigits(r[dateCol]);
		if (digits.length < 4) continue;
		const y = digits.slice(0, 4);
		const mo = digits.slice(4, 6) || '01';
		const da = digits.slice(6, 8) || '01';
		let key;
		if (freq === 'y') key = y;
		else if (freq === 'q') key = `${y}Q${Math.ceil(Number(mo) / 3)}`;
		else if (freq === 'm') key = `${y}${mo}`;
		else if (freq === 'w') {
			const dt = new Date(Number(y), Number(mo) - 1, Number(da));
			const jan1 = new Date(Number(y), 0, 1);
			const wk = Math.ceil((((dt - jan1) / 86400000) + jan1.getDay() + 1) / 7);
			key = `${y}W${String(wk).padStart(2, '0')}`;
		} else key = digits; // d — 동일 날짜 중복만 last 로
		const prev = bucket.get(key);
		if (!prev || digits >= prev.k) bucket.set(key, { k: digits, row: r });
	}
	return [...bucket.values()].sort((a, b) => a.k.localeCompare(b.k)).map((x) => x.row);
}

function catalog() {
	return {
		service: 'dartlab live data API',
		about: 'HF parquet → CSV/TSV on-the-fly. Use in Google Sheets =IMPORTDATA() or Excel Power Query.',
		url_syntax: '/v1/{dir}/{id}.{csv|tsv}?cols=&tail=&head=&freq=',
		params: {
			cols: 'comma-separated column projection (also output order)',
			tail: 'last N rows',
			head: 'first N rows (mutually exclusive with tail)',
			freq: 'downsample d|w|m|q|y (last-of-period)'
		},
		schema_probe: '/v1/{dir}/{id}/schema.json',
		datasets: RELEASES.map((e) => ({
			dir: e.dir,
			label: e.label,
			shardKind: e.shardKind,
			tier2: isTier2(e.shardKind),
			examplePath: isTier2(e.shardKind) ? `/v1/${e.dir}/{id}.tsv` : null,
			// macro 벌크 observations: {id}=seriesId, manifest 로 시리즈 카탈로그 탐색
			...(BULK_OBS.has(e.dir) ? { idMeaning: 'seriesId', catalogPath: `/v1/${e.dir}/manifest.csv` } : {})
		}))
	};
}

export default {
	async fetch(req, env, ctx) {
		const baseFetch = (env && env.FETCH) || globalThis.fetch;
		const UPSTREAM = ((env && env.UPSTREAM) || UPSTREAM_DEFAULT).replace(/\/+$/, '');
		const MAX_DECODE_BYTES = num(env && env.MAX_DECODE_BYTES, 700 * 1024 * 1024); // 실제 RSS 예산
		const DECODE_EXPANSION = num(env && env.DECODE_EXPANSION, 6); // 텍스트 payload 팽창(실측 panel 155MB×6≈927MB)
		const CELL_OBJ = num(env && env.CELL_OBJ, 120); // 디코드 셀당 JS 객체 오버헤드 — many-small-rows(fred 33만행) 가드
		const MAX_DECODE_ROWS = num(env && env.MAX_DECODE_ROWS, 2_000_000);
		const CELL_CAP = num(env && env.CELL_CAP, 45_000);
		const indexLink = { Link: '</v1/>; rel="index"' };
		const cacheH = { 'Cache-Control': 'public, max-age=3600' };

		if (req.method === 'OPTIONS') return new Response(null, { headers: CORS });
		if (req.method !== 'GET' && req.method !== 'HEAD') return json({ error: 'method not allowed' }, 405);

		const url = new URL(req.url);
		const p = url.pathname;

		// ── /v1 카탈로그 (자기기술) ──
		if (p === '/v1' || p === '/v1/' || p === '/v1/index.json') {
			return json(catalog(), 200, { ...cacheH, ...indexLink });
		}
		if (!p.startsWith('/v1/')) return json({ error: 'not found — see /v1/' }, 404);
		const rest = p.slice('/v1/'.length);

		// ── schema.json (footer만 — cols/tail 추측용, 동일 allowlist 게이트) ──
		if (rest.endsWith('/schema.json')) {
			const sd = splitDirId(rest.slice(0, -'/schema.json'.length));
			if (!sd) return json({ error: 'not found' }, 404, indexLink);
			const entry = ALLOW.get(sd.dir);
			if (!entry) return json({ error: 'not found' }, 404, indexLink); // private·미존재 동일(누설 0)
			if (!validId(sd.id)) return json({ error: 'invalid id' }, 400, indexLink);
			const physS = resolvePhysical(sd.dir, sd.id);
			const fileUrl = `${UPSTREAM}/${sd.dir}/${physS.stem}.parquet`;
			const probe = await probeSize(fileUrl, baseFetch);
			if (probe.status === 404) return json({ error: 'not found' }, 404, indexLink);
			if (probe.status >= 500) return json({ error: 'upstream error', status: probe.status }, 502, indexLink);
			try {
				const file = await asyncBufferFromUrl({ url: fileUrl, byteLength: probe.size, fetch: (u, i) => retryFetch(u, i, baseFetch) });
				const meta = await parquetMetadataAsync(file);
				const schema = parquetSchema(meta);
				const columns = schema.children.map((c) => ({ name: c.element.name, type: c.element.type || c.element.converted_type || 'unknown' }));
				return json(
					{
						dir: sd.dir,
						id: sd.id,
						size: probe.size,
						rows: Number(meta.num_rows),
						rowGroups: meta.row_groups?.length ?? 0,
						columns,
						tier2: isTier2(entry.shardKind),
						...(physS.seriesFilter ? { layout: 'bulk-observations', seriesColumn: physS.seriesFilter.col, note: 'rows = all series; this id selects one series within observations' } : {})
					},
					200,
					{ ...cacheH, ...indexLink }
				);
			} catch (e) {
				return json({ error: 'schema read failed', detail: String(e && e.message || e) }, 502, indexLink);
			}
		}

		// ── 데이터 /v1/{dir}/{id}.{csv|tsv} ──
		const mExt = rest.match(/^(.+)\.(csv|tsv)$/);
		if (!mExt) return json({ error: 'path must end with .csv or .tsv', hint: '/v1/{dir}/{id}.tsv' }, 400, indexLink);
		const ext = mExt[2];
		const dd = splitDirId(mExt[1]);
		if (!dd) return json({ error: 'not found' }, 404, indexLink);
		const entry = ALLOW.get(dd.dir);
		if (!entry) return json({ error: 'not found' }, 404, indexLink); // private·미등록 dir = 404(누설 0)
		if (!validId(dd.id)) return json({ error: 'invalid id' }, 400, indexLink);

		// Tier2 부적격(날짜샤드·전종목 대형) → 413 + Tier1 안내
		if (!isTier2(entry.shardKind)) {
			return json(
				{
					error: 'too large for live API — use browser download (Tier1) or a company-level file',
					shardKind: entry.shardKind,
					hint: entry.shardKind === 'dateShard' ? 'request a specific company file (e.g. gov/prices/company/{code}) instead of the date shard' : 'this dataset is a single bulk file; download it from the data center',
					tier1Url: `${UPSTREAM}/${dd.dir}/${dd.id}.parquet`
				},
				413,
				indexLink
			);
		}

		// 파라미터
		const sp = url.searchParams;
		const colsParam = (sp.get('cols') || '').trim();
		const tailParam = sp.get('tail');
		const headParam = sp.get('head');
		const freqParam = (sp.get('freq') || '').trim().toLowerCase();
		if (tailParam != null && headParam != null) return json({ error: 'head and tail are mutually exclusive' }, 400, indexLink);
		if (freqParam && !FREQS.has(freqParam)) return json({ error: `invalid freq '${freqParam}'`, allowed: [...FREQS] }, 400, indexLink);

		// 물리 파일·시리즈 필터 해소 (macro 벌크 observations: {id}=seriesId, manifest=카탈로그)
		const phys = resolvePhysical(dd.dir, dd.id);
		const fileUrl = `${UPSTREAM}/${dd.dir}/${phys.stem}.parquet`;
		const probe = await probeSize(fileUrl, baseFetch);
		if (probe.status === 404) return json({ error: 'not found' }, 404, indexLink);
		if (probe.status >= 500) return json({ error: 'upstream error', status: probe.status }, 502, indexLink);

		try {
			const file = await asyncBufferFromUrl({ url: fileUrl, byteLength: probe.size, fetch: (u, i) => retryFetch(u, i, baseFetch) });
			const meta = await parquetMetadataAsync(file);
			const schema = parquetSchema(meta);
			const allCols = schema.children.map((c) => c.element.name);
			const totalRows = Number(meta.num_rows);

			// cols 투영 검증
			let cols = allCols;
			if (colsParam) {
				const want = colsParam.split(',').map((s) => s.trim()).filter(Boolean);
				const missing = want.filter((c) => !allCols.includes(c));
				if (missing.length) return json({ error: `unknown column(s): ${missing.join(', ')}`, available_columns: allCols, hint: 'fix ?cols=' }, 400, indexLink);
				cols = want;
			}

			// 읽을 컬럼 — 시리즈 필터 시 idCol 을 반드시 포함(출력에서 빠져도 필터엔 필요)
			const readCols = phys.seriesFilter && !cols.includes(phys.seriesFilter.col) ? [...cols, phys.seriesFilter.col] : cols;

			// 메모리 예산 가드 (디코드 전) — 텍스트 payload(압축해제×팽창) + 셀당 객체 오버헤드(행수×컬럼수×CELL_OBJ).
			// 두 항이 panel(텍스트 거대)·fred(행 多 작음) 양쪽을 잡는다. cols 투영이 양 항 모두 줄이는 탈출구(실측).
			// 초과면 413(+cols 안내). 카테고리 분기 0 — 전부 footer 메타데이터에서 도출.
			const estBytes = decodeBytesEstimate(meta, readCols);
			const estRss = estBytes * DECODE_EXPANSION + totalRows * readCols.length * CELL_OBJ;
			if (estRss > MAX_DECODE_BYTES || totalRows > MAX_DECODE_ROWS) {
				return json(
					{
						error: 'estimated decode exceeds this host memory budget',
						estimated_uncompressed_bytes: estBytes,
						estimated_rss_bytes: estRss,
						budget_bytes: MAX_DECODE_BYTES,
						total_rows: totalRows,
						hint: 'project fewer columns with ?cols=a,b (drops large text columns), or use the Tier1 browser download',
						tier1Url: fileUrl
					},
					413,
					indexLink
				);
			}

			const tailN = tailParam != null ? num(tailParam, 0) : 0;
			const headN = headParam != null ? num(headParam, 0) : 0;
			// freq 는 전 구간 다운샘플 후 tail/head 슬라이스해야 의미가 맞다(tail 먼저면 마지막 N 일만 버킷팅).
			// date 컬럼은 출력 cols 에 있어야 함(없으면 400).
			const freqDateCol = freqParam ? detectDateCol(cols) : null;
			if (freqParam && !freqDateCol) return json({ error: `freq=${freqParam} requires a date column in the projection`, available_columns: allCols, hint: 'add the date column to ?cols= or drop ?freq=' }, 400, indexLink);

			let rows;
			let seriesTotal; // X-DartLab-Total-Rows — 시리즈/파일의 원본(다운샘플·슬라이스 전) 행수
			// parquet 레벨 슬라이스(진짜 prune)는 단일파일 + freq 없음일 때만. 시리즈 필터·freq 는 전량 디코드 필요.
			if (!phys.seriesFilter && !freqParam) {
				let rowStart, rowEnd;
				if (tailN > 0) { rowStart = Math.max(0, totalRows - tailN); rowEnd = totalRows; }
				else if (headN > 0) { rowStart = 0; rowEnd = Math.min(totalRows, headN); }
				rows = await parquetReadObjects({ file, compressors, columns: cols, rowStart, rowEnd });
				seriesTotal = totalRows;
			} else {
				const all = await parquetReadObjects({ file, compressors, columns: readCols });
				if (phys.seriesFilter) {
					const col = phys.seriesFilter.col, val = phys.seriesFilter.value;
					rows = all.filter((r) => String(r[col]) === val);
					if (!rows.length) return json({ error: 'not found', hint: `unknown series id; GET /v1/${dd.dir}/manifest.csv for the catalog` }, 404, indexLink);
				} else {
					rows = all;
				}
				seriesTotal = rows.length;
				if (freqParam) rows = downsample(rows, freqDateCol, freqParam); // 전 구간 다운샘플 먼저
				if (tailN > 0) rows = rows.slice(Math.max(0, rows.length - tailN)); // 그다음 슬라이스
				else if (headN > 0) rows = rows.slice(0, headN);
			}

			// 셀cap — 미지정(head/tail/freq 없음) + cols×rows 초과 시 최근행 우선 자동 tail + 헤더 신호
			let capped = false;
			const explicitSlice = tailN > 0 || headN > 0 || !!freqParam;
			const cellsBefore = rows.length * cols.length;
			if (!explicitSlice && cellsBefore > CELL_CAP) {
				const keep = Math.max(1, Math.floor(CELL_CAP / cols.length));
				rows = rows.slice(Math.max(0, rows.length - keep));
				capped = true;
			}

			const body = serialize(rows, cols, ext);
			const headers = {
				'Content-Type': ext === 'tsv' ? 'text/tab-separated-values; charset=utf-8' : 'text/csv; charset=utf-8',
				'Content-Disposition': contentDisposition(dd.id, ext),
				...cacheH,
				...indexLink,
				'X-DartLab-Total-Rows': String(seriesTotal),
				'X-DartLab-Cells-Returned': String(rows.length * cols.length)
			};
			if (capped) {
				// ⚠ HTTP 헤더 값은 Latin1(ByteString)만 — 비-ASCII(예 '…' U+2026) 넣으면 throw. ASCII 고정.
				headers['X-DartLab-Capped'] = 'true';
				headers['X-DartLab-Hint'] = 'add ?tail=N | ?cols=a,b | ?freq=m to widen';
			}
			return new Response(req.method === 'HEAD' ? null : body, { status: 200, headers });
		} catch (e) {
			return json({ error: 'decode failed', detail: String(e && e.message || e) }, 502, indexLink);
		}
	}
};

// 마지막 '/' 로 dir/id 분리 후 퍼센트 디코드 — URL.pathname 은 %xx 를 안 푼다(한글 stem 'KOSPI-코스피'
// 는 'KOSPI-%EC%BD%94…' 로 옴). 디코드 후 validId 가 %2F→'/' 등 주입을 차단. raw '/' 로 먼저 split 해
// 세그먼트 경계는 보존(%2F 는 split 안 됨). 깨진 % 시퀀스는 null → 호출측 404/400.
function splitDirId(s) {
	const i = s.lastIndexOf('/');
	if (i < 0) return null;
	try {
		return { dir: decodeURIComponent(s.slice(0, i)), id: decodeURIComponent(s.slice(i + 1)) };
	} catch {
		return null;
	}
}
