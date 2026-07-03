// HF 데이터셋 parquet 레인지 프록시 Cloudflare Worker (무료 티어).
//
// 정적 프런트(GitHub Pages)는 HF `resolve/main` 을 직접 range-fetch 한다. 콜드 HF CDN 은 엣지
// 캐시 미스 시 간헐 403/429/5xx 를 돌려주는데(프런트 로그에 'Failed to load resource: 403'),
// 이 Worker 가 그 사이에서:
//   1) 403/429/5xx 를 엣지에서 재시도 흡수 (프런트 fetchResilient 와 이중 방어, 서버측이라 왕복 빠름),
//   2) HF resolve/main URL 을 단일 SSOT 로 — 프런트는 VITE_DARTLAB_HF_RESOLVE=https://<worker>/hf 한 줄로 전체 전환,
//   3) CF 글로벌 네트워크 경로로 first-byte 개선.
//
// hyparquet 이 의존하는 헤더(Range / Content-Range / Accept-Ranges / Content-Length / x-linked-size / 206)
// 를 그대로 보존·재발급한다 (landing/src/lib/data/hfRange.ts 가 이 헤더로 파일 크기·청크를 읽음).
//
// 캐싱 정책 2층:
//   - 레인지(206) 응답은 *브라우저 캐시* 에 맡긴다(URL+Range 키로 정확). 부분응답 CF Cache put 금지.
//   - 전체 GET(Range 없음 — 프론트 소형 parquet 통파일 경로)은 *엣지 캐시*(caches.default) —
//     콜드 HF first-byte ~2s 를 글로벌 엣지 히트 수십 ms 로. TTL 은 파일 갱신 주기별
//     (recent.parquet 10분[일일 갱신 tail] / 그 외 1시간).
//
// 무료 티어: Workers 10만 req/day. nodejs_compat 불필요(순수 fetch). 배포·전환은 README.md.

const UPSTREAM = 'https://huggingface.co/datasets/eddmpython/dartlab-data/resolve/main';
// 종목 뉴스(네이버 헤드라인+스니펫) 전용 private 데이터셋 — 언론사 저작권이라 공개 dartlab-data 안 감.
// 워커가 토큰으로 서버사이드 read 해 화면에 표시하는 것은 "라이브 표시"(의도된 용도) — 공개 벌크 재배포 아님.
const NEWS_UPSTREAM = 'https://huggingface.co/datasets/eddmpython/dartlab-news-private/resolve/main';
// 캐러셀/회사 이미지(공개 dartlab-media) — 파일명에 콘텐츠해시가 박혀 불변(immutable). 브라우저가 HF
// resolve 를 직접 다량 요청해 익명 throttle 당하던 것을 엣지 캐시(1년)로 흡수 → HF 직타 0, 빠름·안정.
const MEDIA_UPSTREAM = 'https://huggingface.co/datasets/eddmpython/dartlab-media/resolve/main';
const PASS_HEADERS = ['Content-Type', 'Content-Length', 'Content-Range', 'Accept-Ranges', 'ETag', 'Last-Modified', 'x-linked-size'];

function cacheControlFor(path) {
	if (path.endsWith('recent.parquet')) return 'public, max-age=600';
	return 'public, max-age=3600';
}

// ── 네이버 검색 API 라이브 파싱 (gather/sources/naverNews.py 규칙 동일) ──
// Google News RSS 는 CF Workers outbound IP 에서 503(데이터센터 봇 차단)이라 라이브 소스로 못 씀(실측 확인).
// 라이브 = 네이버 검색 API: byCompany 아카이브와 동일 소스(naver)·스니펫 O. fchart(/naver 라우트)처럼
// 네이버 outbound 는 CF 에서 동작(인증 헤더로 식별돼 IP 차단 없음). 화면 표시 스키마는 클라와 동일 필드.
function htmlUnescape(s) {
	return s
		.replace(/&#x([0-9a-fA-F]+);/g, (_, n) => String.fromCodePoint(parseInt(n, 16)))
		.replace(/&#(\d+);/g, (_, n) => String.fromCodePoint(Number(n)))
		.replace(/&lt;/g, '<')
		.replace(/&gt;/g, '>')
		.replace(/&quot;/g, '"')
		.replace(/&apos;/g, "'")
		.replace(/&amp;/g, '&');
}

const NAVER_TAG_RE = /<[^>]+>/g;
const naverClean = (s) => htmlUnescape(String(s || '').replace(NAVER_TAG_RE, '')).trim(); // <b> 하이라이트·HTML 엔티티 제거
const naverDate = (s) => { const d = new Date(s); return Number.isNaN(d.getTime()) ? '' : d.toISOString().slice(0, 10); }; // RFC822 +0900
const naverSource = (link) => { try { const h = new URL(link).hostname; return h.startsWith('www.') ? h.slice(4) : h; } catch { return ''; } };

// 네이버 검색 응답 → [{date,title,source,url,description}] (원문링크 dedup, 빈 title/url 제외).
function parseNaverNews(json) {
	const out = [];
	const seen = new Set();
	for (const it of (json && json.items) || []) {
		const url = it.originallink || it.link || '';
		const title = naverClean(it.title);
		if (!url || !title || seen.has(url)) continue;
		seen.add(url);
		out.push({ date: naverDate(it.pubDate), title, source: naverSource(url), url, description: naverClean(it.description) });
	}
	return out;
}

// 네이버 검색 1회 — 시크릿 미설정([])·실패(throw). display 최신순(sort=date). id/secret 은 워커 시크릿.
async function naverSearch(env, query, display) {
	const id = env.NAVER_CLIENT_ID || '';
	const secret = env.NAVER_CLIENT_SECRET || '';
	if (!id || !secret) return [];
	const u = `https://openapi.naver.com/v1/search/news.json?query=${encodeURIComponent(query)}&display=${display}&sort=date`;
	const r = await fetch(u, { headers: { 'X-Naver-Client-Id': id, 'X-Naver-Client-Secret': secret } });
	if (!r.ok) throw new Error(`naver ${r.status}`);
	return parseNaverNews(await r.json());
}

// market 별 "시장 전반" 라이브 검색어 — 종목 단위(HF 누적본이 넓게 커버)가 아니라 cron 사이 갭 메울 최신
// 시장 헤드라인용. 소수 키워드 fan-out 후 머지(네이버는 OR 약해 단일 쿼리보다 분리 검색이 정확).
const MARKET_QUERIES = { KR: ['증시', '코스피', '환율'], US: ['뉴욕증시', '나스닥', '미국증시'] };

// ── DART 공시목록 라이브 (gather/dart/disclosure.py::listFilings 와 동일 list.json) ──
// 배치(allFilingsBackfill 14:30)가 못 잡은 당일 공시를 조회시점에 DART list.json 으로 메움. corp_code 없이
// 당일 호출 = 전체 시장 공시(stock_code 포함, market_recent 와 동일 스키마). 종목 필터는 클라가 stock_code 로.
// DART 는 CF Workers 기본 UA 를 봇으로 보고 error1.html 로 무한 리다이렉트 — 브라우저 UA 로 우회(로컬 선례).
const DART_UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36';
const dartYmd = (s) => { const t = String(s || ''); return t.length === 8 ? `${t.slice(0, 4)}-${t.slice(4, 6)}-${t.slice(6, 8)}` : t; };
async function dartList(key, ymd, page) {
	const u = `https://opendart.fss.or.kr/api/list.json?crtfc_key=${key}&bgn_de=${ymd}&end_de=${ymd}&page_no=${page}&page_count=100&sort=date&sort_mth=desc`;
	const r = await fetch(u, { headers: { 'User-Agent': DART_UA } });
	if (!r.ok) throw new Error(`dart ${r.status}`);
	const j = await r.json();
	if (j.status !== '000') return []; // 013=무자료 등 정상 빈
	return (j.list || []).map((it) => ({
		rceptNo: it.rcept_no || '',
		rceptDate: dartYmd(it.rcept_dt),
		stockCode: it.stock_code || '',
		corpName: it.corp_name || '',
		reportNm: (it.report_nm || '').trim(),
		filer: it.flr_nm || ''
	}));
}
// KST(UTC+9) 오늘 YYYYMMDD — DART 는 KST 접수일 기준(워커 Date 는 UTC).
function kstToday() {
	const d = new Date(Date.now() + 9 * 3600000);
	return `${d.getUTCFullYear()}${String(d.getUTCMonth() + 1).padStart(2, '0')}${String(d.getUTCDate()).padStart(2, '0')}`;
}
function kstDaysAgo(days) {
	const d = new Date(Date.now() + 9 * 3600000 - days * 86400000);
	return `${d.getUTCFullYear()}${String(d.getUTCMonth() + 1).padStart(2, '0')}${String(d.getUTCDate()).padStart(2, '0')}`;
}
// IPO(상장 전, corp_cls=E) 증권신고 지분증권 목록 라이브. pblntf_detail_ty=C001 upstream 필터라 3개월
// ~30행(실측 2026-07) 소량. 판별(3조건 classifyIpo 미러)·발행사 그룹핑은 클라(ipoFilingsSource) 담당,
// 워커는 upstream 파라미터 필터만(엔진 로직 0). corp_code 는 발행사 그룹핑 키.
// ⚠ 윈도우는 85일 고정. corp_code 없는 list.json 은 3개월 제한(92일 → status 100 빈 응답, 라이브 실측).
async function dartListIpo(key, bgn, end, page) {
	const u = `https://opendart.fss.or.kr/api/list.json?crtfc_key=${key}&bgn_de=${bgn}&end_de=${end}&corp_cls=E&pblntf_detail_ty=C001&page_no=${page}&page_count=100&sort=date&sort_mth=desc`;
	const r = await fetch(u, { headers: { 'User-Agent': DART_UA } });
	if (!r.ok) throw new Error(`dart ${r.status}`);
	const j = await r.json();
	if (j.status !== '000') return { rows: [], totalPage: 0 }; // 013=무자료 등 정상 빈
	const rows = (j.list || []).map((it) => ({
		rceptNo: it.rcept_no || '',
		rceptDate: dartYmd(it.rcept_dt),
		corpCode: it.corp_code || '',
		corpCls: it.corp_cls || '',
		stockCode: it.stock_code || '',
		corpName: it.corp_name || '',
		reportNm: (it.report_nm || '').trim(),
		filer: it.flr_nm || ''
	}));
	return { rows, totalPage: Number(j.total_page || 1) };
}

export default {
	async fetch(req, env, ctx) {
		// CORS allowlist: 프로덕션 origin(env.ALLOW_ORIGIN) + 로컬 dev(localhost/127.0.0.1). 일치 시 그 origin echo.
		const reqOrigin = req.headers.get('Origin') || '';
		const allowOrigin =
			reqOrigin && (reqOrigin === env.ALLOW_ORIGIN || /^https?:\/\/(localhost|127\.0\.0\.1)(:\d+)?$/.test(reqOrigin))
				? reqOrigin
				: env.ALLOW_ORIGIN || '*';
		const cors = {
			'Access-Control-Allow-Origin': allowOrigin,
			'Vary': 'Origin',
			'Access-Control-Allow-Methods': 'GET, HEAD, OPTIONS',
			'Access-Control-Allow-Headers': 'Range, If-Range, If-None-Match',
			'Access-Control-Expose-Headers': 'Content-Range, Content-Length, Accept-Ranges, ETag, x-linked-size',
			'Access-Control-Max-Age': '86400'
		};
		if (req.method === 'OPTIONS') return new Response(null, { headers: cors });
		if (req.method !== 'GET' && req.method !== 'HEAD') return new Response('method not allowed', { status: 405, headers: cors });

		const url = new URL(req.url);

		// /naver?code=XXXXXX — 네이버 fchart 일별 OHLCV 프록시. gov(공공데이터, T+1 영업일 지연)가 아직
		// 발행 안 한 최신 거래일(금요일치=월요일 발행)을 프론트가 표시용 fresh-tail 로 채우게 한다. 정적
		// 사이트는 브라우저 CORS 로 네이버를 직접 못 부르므로 서버측(엣지) fetch 가 우회. 키 불필요(공개
		// 차트 API), 재배포 아님(사용자 세션 표시용). 10분 캐시 — EOD 갭 채움이라 분 단위 신선도면 충분.
		if (url.pathname === '/naver') {
			const jsonHeaders = { ...cors, 'Content-Type': 'application/json; charset=utf-8' };
			const code = (url.searchParams.get('code') || '').replace(/[^0-9A-Za-z]/g, '');
			if (!code) return new Response(JSON.stringify({ error: 'code required' }), { status: 400, headers: jsonHeaders });
			let txt = '';
			try {
				const fr = await fetch(
					`https://fchart.stock.naver.com/sise.nhn?symbol=${code}&timeframe=day&count=30&requestType=0`,
					{ headers: { 'User-Agent': 'Mozilla/5.0' } }
				);
				if (!fr.ok) throw new Error(`naver ${fr.status}`);
				txt = await fr.text(); // EUC-KR XML — data="..." 필드는 ASCII 라 regex 안전
			} catch (e) {
				return new Response(JSON.stringify({ error: String(e) }), { status: 502, headers: jsonHeaders });
			}
			const candles = [];
			for (const it of txt.matchAll(/data="([^"]+)"/g)) {
				const p = it[1].split('|');
				if (p.length < 6) continue;
				const c = Number(p[4]);
				if (!Number.isFinite(c) || c <= 0) continue;
				candles.push({ t: p[0], o: Number(p[1]) || c, h: Number(p[2]) || c, l: Number(p[3]) || c, c, v: Number(p[5]) || 0 });
			}
			candles.sort((a, b) => a.t.localeCompare(b.t));
			return new Response(
				JSON.stringify({ source: 'fchart.stock.naver.com', code, asOf: candles.at(-1)?.t ?? '', candles }),
				{ headers: { ...jsonHeaders, 'Cache-Control': 'public, max-age=600' } }
			);
		}
		// /news?code=XXXXXX — 종목 뉴스 헤드라인(제목+스니펫+원문링크) 프록시. private 데이터셋(언론사 저작권)을
		// 워커가 read-only 토큰(env.HF_NEWS_TOKEN)으로 서버사이드 read → 화면 표시(라이브 표시 = 의도된 용도).
		// 가드: ① code 형식 검증(영숫자 ≤12, 경로 주입 차단) ② 10분 엣지 캐시(토큰 달린 공개 엔드포인트라
		// 같은 종목 반복 호출이 HF·쿼터를 두드리지 않게 — 남용 방어 핵심) ③ 토큰 미설정 시 빈배열 noop(배선 안전).
		// 토큰은 dartlab-news-private read 전용으로 발급 → 피해 범위 최소.
		if (url.pathname === '/news') {
			const jsonHeaders = { ...cors, 'Content-Type': 'application/json; charset=utf-8' };
			const code = (url.searchParams.get('code') || '').replace(/[^0-9A-Za-z]/g, '').slice(0, 12);
			if (!code) return new Response(JSON.stringify({ error: 'code required' }), { status: 400, headers: jsonHeaders });
			const q = (url.searchParams.get('q') || '').trim().slice(0, 40); // 회사명(라이브 RSS 검색어, 옵션)
			// 캐시 키 = code+q+10분 버킷(회사명 다르면 라이브분도 다름·버킷 회전으로 일시실패 고착 방지). auth 비포함 엣지 캐시.
			const cacheKey = new Request(`https://dl-news.cache/${code}?q=${encodeURIComponent(q)}&b=${Math.floor(Date.now() / 600000)}`);
			const hit = await caches.default.match(cacheKey);
			if (hit) {
				const h2 = new Headers(hit.headers);
				for (const [k, v] of Object.entries(jsonHeaders)) h2.set(k, v);
				h2.set('x-dl-edge', 'HIT');
				return new Response(hit.body, { status: hit.status, headers: h2 });
			}
			// base: byCompany 아카이브(네이버 스니펫, private). 토큰 있을 때만 — 없으면 라이브 RSS 만으로 동작.
			let baseItems = [];
			const token = env.HF_NEWS_TOKEN || '';
			if (token) {
				try {
					const fr = await fetch(`${NEWS_UPSTREAM}/news/private/naver/byCompany/${code}.json`, { headers: { Authorization: `Bearer ${token}` } });
					if (fr.ok) {
						const j = JSON.parse(await fr.text()); // {code, asOf, items:[{date,title,source,url,description,track}]}
						if (Array.isArray(j.items)) baseItems = j.items;
					} // 404(시총 상위 외) → []
				} catch (e) { /* 아카이브 실패해도 라이브로 진행 */ }
			}
			// live: 네이버 검색 API(회사명 q) — byCompany cron(일 1회)이 못 채운 조회시점 최신(아카이브와 동일 소스·스니펫 O).
			let liveItems = [];
			if (q) {
				try {
					liveItems = (await naverSearch(env, q, 40)).map((it) => ({ ...it, track: 'naver' }));
				} catch (e) { /* 라이브 실패해도 base 로 진행 */ }
			}
			// 머지: 라이브(최신) 우선 + base(스니펫), url dedup keep-first, date desc, 상한 60.
			const seen = new Set();
			const items = [];
			for (const it of [...liveItems, ...baseItems]) {
				const u = String(it.url || '');
				if (!u || seen.has(u)) continue;
				seen.add(u);
				items.push(it);
			}
			items.sort((a, b) => String(b.date || '').localeCompare(String(a.date || '')));
			const resp = new Response(JSON.stringify({ code, items: items.slice(0, 60) }), {
				headers: { ...jsonHeaders, 'Cache-Control': 'public, max-age=600' }
			});
			if (ctx && items.length) ctx.waitUntil(caches.default.put(cacheKey, resp.clone())); // 빈 결과는 캐시 안 함
			return resp;
		}
		// /market-news?market=KR|US — 시장 전반 최신 헤드라인 라이브 오버레이. HF rss 아카이브(일 2회 cron)가
		// 못 채우는 cron 사이 갭을 Google News RSS 라이브 fetch 로 메운다(가격 /naver fresh-tail 과 동형 패턴).
		// 무인증·CORS 무관(서버측 fetch). 10분 엣지 캐시로 같은 분 반복 호출이 Google 을 두드리지 않게(남용 방어).
		// 클라(marketNewsSource)가 HF 누적 shard 위에 url-dedup 머지 → 넓이(HF)+신선도(라이브) 동시.
		if (url.pathname === '/market-news') {
			const jsonHeaders = { ...cors, 'Content-Type': 'application/json; charset=utf-8' };
			const market = (url.searchParams.get('market') || 'KR').toUpperCase() === 'US' ? 'US' : 'KR';
			// 10분 버킷으로 캐시 키 회전 — 일시 실패(빈 결과)가 캐시에 고착되지 않게 자동 무효화.
			const cacheKey = new Request(`https://dl-market-news.cache/${market}/${Math.floor(Date.now() / 600000)}`);
			const hit = await caches.default.match(cacheKey);
			if (hit) {
				const h2 = new Headers(hit.headers);
				for (const [k, v] of Object.entries(jsonHeaders)) h2.set(k, v);
				h2.set('x-dl-edge', 'HIT');
				return new Response(hit.body, { status: hit.status, headers: h2 });
			}
			let items = [];
			try {
				const lists = await Promise.all(MARKET_QUERIES[market].map((kw) => naverSearch(env, kw, 30).catch(() => [])));
				const seen = new Set();
				for (const it of lists.flat()) { if (!it.url || seen.has(it.url)) continue; seen.add(it.url); items.push(it); }
				items.sort((a, b) => String(b.date || '').localeCompare(String(a.date || '')));
				items = items.slice(0, 80); // 렌더 상한 충분(클라 CAP=300 과 머지)
			} catch (e) {
				return new Response(JSON.stringify({ market, items: [], error: String(e) }), { status: 502, headers: jsonHeaders });
			}
			const resp = new Response(JSON.stringify({ market, asOf: items[0]?.date ?? '', items }), {
				headers: { ...jsonHeaders, 'Cache-Control': 'public, max-age=600' }
			});
			if (ctx && items.length) ctx.waitUntil(caches.default.put(cacheKey, resp.clone())); // 빈 결과(일시 실패)는 캐시 안 함
			return resp;
		}
		// /market-filings — 당일 시장 전체 공시 라이브 오버레이. DART list.json(corp_code 없이 당일=전체 시장,
		// market_recent 동일 스키마). 배치(14:30) 사이 갭을 조회시점으로 메움. DART_API_KEY 시크릿. 10분 캐시.
		// 종목 필터는 클라가 stockCode 로(시장+종목 한 소스). page 1·2 = 최근 200, rceptNo desc 최신순.
		if (url.pathname === '/market-filings') {
			const jsonHeaders = { ...cors, 'Content-Type': 'application/json; charset=utf-8' };
			const key = env.DART_API_KEY || '';
			if (!key) {
				return new Response(JSON.stringify({ items: [], note: 'dart key not configured' }), {
					headers: { ...jsonHeaders, 'Cache-Control': 'public, max-age=600' }
				});
			}
			const ymd = kstToday();
			const cacheKey = new Request(`https://dl-market-filings.cache/${ymd}/${Math.floor(Date.now() / 600000)}`);
			const hit = await caches.default.match(cacheKey);
			if (hit) {
				const h2 = new Headers(hit.headers);
				for (const [k, v] of Object.entries(jsonHeaders)) h2.set(k, v);
				h2.set('x-dl-edge', 'HIT');
				return new Response(hit.body, { status: hit.status, headers: h2 });
			}
			let items = [];
			try {
				const pages = await Promise.all([1, 2].map((p) => dartList(key, ymd, p).catch(() => [])));
				const seen = new Set();
				for (const it of pages.flat()) { if (!it.rceptNo || seen.has(it.rceptNo)) continue; seen.add(it.rceptNo); items.push(it); }
				items.sort((a, b) => String(b.rceptNo).localeCompare(String(a.rceptNo))); // 접수번호 desc = 최신순
				items = items.slice(0, 200);
			} catch (e) {
				return new Response(JSON.stringify({ items: [], error: String(e) }), { status: 502, headers: jsonHeaders });
			}
			const resp = new Response(JSON.stringify({ asOf: items[0]?.rceptDate ?? '', items }), {
				headers: { ...jsonHeaders, 'Cache-Control': 'public, max-age=600' }
			});
			if (ctx && items.length) ctx.waitUntil(caches.default.put(cacheKey, resp.clone()));
			return resp;
		}
		// /ipo-filings . 신규상장 IPO 발굴 라이브(최근 85일 · list.json 3개월 제한 여유). allFilings HF bake 는 상장사(Y/K) 한정이라
		// 상장 전 발행사(corp_cls=E)는 이 라이브 read-through 가 유일한 퍼블릭 데이터원(베이크 0).
		// upstream 필터(corp_cls=E + pblntf_detail_ty=C001)만 워커가 담당, 3조건 판별은 클라 미러. 30분 캐시.
		if (url.pathname === '/ipo-filings') {
			const jsonHeaders = { ...cors, 'Content-Type': 'application/json; charset=utf-8' };
			const key = env.DART_API_KEY || '';
			if (!key) {
				return new Response(JSON.stringify({ items: [], note: 'dart key not configured' }), {
					headers: { ...jsonHeaders, 'Cache-Control': 'public, max-age=1800' }
				});
			}
			const bgn = kstDaysAgo(85);
			const end = kstToday();
			const cacheKey = new Request(`https://dl-ipo-filings.cache/${end}/${Math.floor(Date.now() / 1800000)}`);
			const hit = await caches.default.match(cacheKey);
			if (hit) {
				const h2 = new Headers(hit.headers);
				for (const [k, v] of Object.entries(jsonHeaders)) h2.set(k, v);
				h2.set('x-dl-edge', 'HIT');
				return new Response(hit.body, { status: hit.status, headers: h2 });
			}
			let items = [];
			try {
				const first = await dartListIpo(key, bgn, end, 1);
				items = first.rows;
				const lastPage = Math.min(first.totalPage, 4); // 실측 3개월 1페이지 · 4페이지(400행) 안전캡
				if (lastPage > 1) {
					const pages = await Promise.all(
						Array.from({ length: lastPage - 1 }, (_, i) => dartListIpo(key, bgn, end, i + 2).then((p) => p.rows).catch(() => []))
					);
					items = items.concat(pages.flat());
				}
				const seen = new Set();
				items = items.filter((it) => it.rceptNo && !seen.has(it.rceptNo) && !!seen.add(it.rceptNo));
				items.sort((a, b) => String(b.rceptNo).localeCompare(String(a.rceptNo))); // 접수번호 desc = 최신순
			} catch (e) {
				return new Response(JSON.stringify({ items: [], error: String(e) }), { status: 502, headers: jsonHeaders });
			}
			const resp = new Response(JSON.stringify({ asOf: end, items }), {
				headers: { ...jsonHeaders, 'Cache-Control': 'public, max-age=1800' }
			});
			if (ctx && items.length) ctx.waitUntil(caches.default.put(cacheKey, resp.clone()));
			return resp;
		}
		// /media/<path> — dartlab-media(이미지) 엣지 캐시 프록시. 불변 파일명(콘텐츠해시) → 1년 immutable.
		// <img> 전체 GET 은 엣지 캐시 히트(HF 직타 0). Range 요청도 통과(파셜은 캐시 put 안 함).
		const mm = url.pathname.match(/^\/media\/(.+)$/);
		if (mm) {
			const mpath = mm[1].replace(/^\/+/, '').replace(/\.\.+/g, '');
			const mUrl = `${MEDIA_UPSTREAM}/${mpath}`;
			const mRange = req.headers.get('Range');
			const mFull = req.method === 'GET' && !mRange;
			const mKey = new Request(mUrl);
			if (mFull) {
				const hit = await caches.default.match(mKey);
				if (hit) {
					const h2 = new Headers(hit.headers);
					for (const [k, v] of Object.entries(cors)) h2.set(k, v);
					h2.set('x-dl-edge', 'HIT');
					return new Response(hit.body, { status: hit.status, headers: h2 });
				}
			}
			const mfwd = new Headers();
			if (mRange) mfwd.set('Range', mRange);
			let mup = null;
			for (let attempt = 0; attempt < 4; attempt++) {
				mup = await fetch(mUrl, { method: req.method, headers: mfwd });
				if (mup.ok || mup.status === 206 || mup.status === 304) break;
				if (mup.status !== 403 && mup.status !== 429 && mup.status < 500) break;
				await new Promise((r) => setTimeout(r, 180 * (attempt + 1)));
			}
			const mh = new Headers();
			for (const k of ['Content-Type', 'Content-Length', 'Content-Range', 'Accept-Ranges', 'ETag', 'Last-Modified']) { const v = mup.headers.get(k); if (v) mh.set(k, v); }
			// 콘텐츠해시 박힌 이미지(name.<8hex>.webp)만 1년 immutable. 가변 JSON(carousels/*.json·index)은
			// 재게시 갱신돼야 하므로 10분(엣지·브라우저가 곧 새 버전 받게).
			const mImmutable = /\.[0-9a-f]{8}\.(webp|png|jpe?g|gif|svg|avif)$/i.test(mpath);
			mh.set('Cache-Control', mImmutable ? 'public, max-age=31536000, immutable' : 'public, max-age=600');
			for (const [k, v] of Object.entries(cors)) mh.set(k, v);
			const mresp = new Response(req.method === 'HEAD' ? null : mup.body, { status: mup.status, headers: mh });
			if (mFull && mup.status === 200 && ctx) ctx.waitUntil(caches.default.put(mKey, mresp.clone()));
			return mresp;
		}

		const m = url.pathname.match(/^\/hf\/(.+)$/);
		if (!m) return new Response('not found — use /hf/<dataset-path>', { status: 404, headers: cors });
		const path = m[1].replace(/^\/+/, '').replace(/\.\.+/g, ''); // 경로 정규화 (상위 디렉터리 탈출 차단)
		const upstreamUrl = `${UPSTREAM}/${path}`;

		const fwd = new Headers();
		const range = req.headers.get('Range'); if (range) fwd.set('Range', range);
		const ifRange = req.headers.get('If-Range'); if (ifRange) fwd.set('If-Range', ifRange);
		const inm = req.headers.get('If-None-Match'); if (inm) fwd.set('If-None-Match', inm);

		// 전체 GET 엣지 캐시 조회 — 키는 업스트림 URL (Range/조건부 요청은 제외, 부분응답 오염 방지)
		const isFullGet = req.method === 'GET' && !range && !inm && !ifRange;
		const cacheKey = new Request(upstreamUrl);
		if (isFullGet) {
			const hit = await caches.default.match(cacheKey);
			if (hit) {
				const h2 = new Headers(hit.headers);
				for (const [k, v] of Object.entries(cors)) h2.set(k, v);
				h2.set('x-dl-edge', 'HIT');
				return new Response(hit.body, { status: hit.status, headers: h2 });
			}
		}

		let up = null;
		for (let attempt = 0; attempt < 4; attempt++) {
			up = await fetch(upstreamUrl, { method: req.method, headers: fwd });
			if (up.ok || up.status === 206 || up.status === 304) break;
			if (up.status !== 403 && up.status !== 429 && up.status < 500) break;
			await new Promise((r) => setTimeout(r, 180 * (attempt + 1)));
		}

		const h = new Headers();
		for (const k of PASS_HEADERS) { const v = up.headers.get(k); if (v) h.set(k, v); }
		if (!h.has('Accept-Ranges')) h.set('Accept-Ranges', 'bytes');
		// x-linked-size: HF LFS 실제 파일 크기. 없으면 Content-Range 총길이 또는 200 의 Content-Length 로 보강.
		if (!h.has('x-linked-size')) {
			const cr = h.get('Content-Range');
			const total = cr ? cr.split('/')[1] : null;
			if (total && total !== '*') h.set('x-linked-size', total);
			else if (up.status === 200 && h.get('Content-Length')) h.set('x-linked-size', h.get('Content-Length'));
		}
		h.set('Cache-Control', cacheControlFor(path));
		for (const [k, v] of Object.entries(cors)) h.set(k, v);

		const resp = new Response(req.method === 'HEAD' ? null : up.body, { status: up.status, headers: h });
		if (isFullGet && up.status === 200 && ctx) ctx.waitUntil(caches.default.put(cacheKey, resp.clone()));
		return resp;
	}
};
