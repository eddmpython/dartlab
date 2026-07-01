// 캐러셀 공유/OG 동적 엔드포인트 Cloudflare Worker (무료 티어).
//
// 정공법 = SSOT(hfMedia)에서 라이브로 읽어 파생뷰(OG)만 낸다. 정적 사이트(GitHub Pages)에 캐러셀마다
// HTML 을 굽지 않는다. 그건 라이브 데이터를 정적 빌드에 복사·박제(drift + 캐러셀마다 재배포)라 우회.
// 이 워커는 /cards 가 브라우저에서 hfMedia 를 라이브로 읽는 것과 동일 원리를, 크롤러용으로 서버사이드에서
// 한다. hfProxy·news 워커가 "정적 사이트가 못 하는 라이브 HF 브리지"를 하는 것과 같은 패턴.
//
// 라우트:
//   GET /c/<slug>   : 크롤러용 OG 메타 HTML + 사람용 즉시 리다이렉트(LANDING_BASE/cards?post=<slug>).
//   GET /og/<slug>  : 첫 슬라이드 이미지를 워커가 직접 프록시(안정 200 image/webp).
//
// ⚠ og:image 는 워커 자기 오리진의 /og/<slug> 를 가리킨다. hfMedia resolve URL 을 직접 og:image 로 쓰면
//   크롤러(카톡·페북·스레드·X)가 못 읽는다. HF Xet 이관 후 resolve 는 (1) 302 크로스도메인 리다이렉트,
//   (2) 리다이렉트 응답 Content-Type=text/plain, (3) 최종 URL 은 Expires 서명 + Cache-Control:no-store 라
//   크롤러가 이미지로 인식·캐시하지 못한다. 워커가 서버사이드에서 리다이렉트를 풀어 이미지 바이트를 안정
//   Content-Type/Cache 로 재서빙하면 이 문제가 사라진다(리다이렉트·만료·no-store·크로스도메인 제거).
//
// 새 캐러셀을 데이터로만 올려도(carousels/index.json 재게시) 그 공유 링크가 즉시 작동. 워커·landing 재배포 0.
//
// 무료 티어: 순수 fetch, nodejs_compat 불필요. 배포·도메인은 README.md.

const MEDIA_BASE = 'https://huggingface.co/datasets/eddmpython/dartlab-media/resolve/main';

// HTML 속성에 안전하게 박기. &, <, >, ", ' 이스케이프(메타 content 주입 방지).
function esc(s) {
	return String(s == null ? '' : s)
		.replace(/&/g, '&amp;')
		.replace(/</g, '&lt;')
		.replace(/>/g, '&gt;')
		.replace(/"/g, '&quot;')
		.replace(/'/g, '&#39;');
}

// sym(6자리 코드 또는 티커) → canonical media key (landing media.ts mediaKey 와 동일 규칙).
function mediaKey(sym) {
	return /^\d{6}$/.test(sym) ? sym : String(sym || '').toUpperCase();
}

// 슬러그 위생. 경로 주입 방지, 한글·영숫자·-_. 만.
function cleanSlug(raw) {
	return decodeURIComponent(raw).replace(/[^0-9a-zA-Z가-힣\-_.]/g, '').slice(0, 80);
}

// 캐러셀 첫 슬라이드 이미지 → 절대 hfMedia URL. 이슈(image 에 '/' 포함)는 hfMedia 상대경로 직접,
// 회사(semantic 파일명)는 companies/index.json 으로 해석. 못 풀면 null(브랜드 폴백).
async function resolveOgImage(post, companiesIndex) {
	const slide = (post.slides || []).find((s) => s && s.image);
	const image = slide && slide.image;
	if (!image) return null;
	if (image.includes('/')) return `${MEDIA_BASE}/${image.replace(/^\/+/, '')}`; // 이슈: issues/<slug>/cover.<hash>.webp
	const key = mediaKey(post.code || '');
	const company = companiesIndex && companiesIndex.companies && companiesIndex.companies[key];
	const asset = company && (company.assets || []).find((a) => a.name === image || a.name.startsWith(image + '.'));
	return asset ? `${MEDIA_BASE}/companies/${key}/${asset.name}` : null;
}

// 캡션 산문 첫 문단 → og:description(180자 이하). 없으면 첫 슬라이드 line.
function ogDescription(post) {
	const cap = String(post.caption || '').split(/\n\s*\n/)[0].replace(/\s+/g, ' ').trim();
	if (cap) return cap.slice(0, 180);
	const slide = (post.slides || []).find((s) => s && (s.line || s.context));
	return String((slide && (slide.line || slide.context)) || post.name || '').replace(/\s+/g, ' ').trim().slice(0, 180);
}

// 엣지 캐시 헬퍼. index 같은 가변 파일을 워커 엣지에 10분 보관(매 요청 HF 직타 방지).
async function cachedJson(url, ttl, ctx) {
	const key = new Request(url);
	const hit = await caches.default.match(key);
	if (hit) return hit.json();
	const r = await fetch(url, { headers: { 'User-Agent': 'dartlab-card-share/1.0' } });
	if (!r.ok) return null;
	const body = await r.text();
	const resp = new Response(body, { headers: { 'Content-Type': 'application/json', 'Cache-Control': `public, max-age=${ttl}` } });
	if (ctx) ctx.waitUntil(caches.default.put(key, resp.clone()));
	try { return JSON.parse(body); } catch { return null; }
}

// slug → 캐러셀 post(SSOT 라이브). 없으면 null.
async function loadPost(slug, ctx) {
	const index = await cachedJson(`${MEDIA_BASE}/carousels/index.json`, 600, ctx);
	return (index && Array.isArray(index.posts) && index.posts.find((p) => p.slug === slug)) || null;
}

// /og/<slug>: 첫 슬라이드 이미지를 워커가 프록시. HF resolve 302(서명·만료·no-store·text/plain)를
// 서버사이드에서 풀어, 안정된 image/webp + 장수명 캐시로 재서빙한다. 크롤러가 바로 읽고 캐시할 수 있게.
async function serveOgImage(url, slug, ctx) {
	const cacheKey = new Request(`${url.origin}/og/${slug}`); // 확장자·쿼리 무관 단일 캐시 키
	const cached = await caches.default.match(cacheKey);
	if (cached) return cached;

	const post = await loadPost(slug, ctx);
	if (!post) return new Response('not found', { status: 404 });
	const companies = post.code ? await cachedJson(`${MEDIA_BASE}/companies/index.json`, 600, ctx) : null;
	const src = await resolveOgImage(post, companies);
	if (!src) return new Response('no image', { status: 404 });

	// HF resolve 302 를 따라가 이미지 바이트 확보(서버사이드는 서명 URL·no-store 무관, 즉시 소비).
	const upstream = await fetch(src, { headers: { 'User-Agent': 'dartlab-card-share/1.0', Accept: 'image/webp,image/*' } });
	if (!upstream.ok) return new Response('upstream error', { status: 502 });

	// Content-Type 은 실제 응답 우선, 없으면 확장자로 추정(hfMedia 는 .webp 위주).
	const ct = upstream.headers.get('Content-Type') || (/\.png($|\?)/i.test(src) ? 'image/png' : /\.jpe?g($|\?)/i.test(src) ? 'image/jpeg' : 'image/webp');
	const resp = new Response(upstream.body, {
		headers: {
			'Content-Type': ct,
			// 콘텐츠 해시 파일명이라 장수명 캐시 안전. 재게시로 slug→새 이미지 바뀌면 최대 1h 후 갱신.
			'Cache-Control': 'public, max-age=3600, s-maxage=3600',
			'Access-Control-Allow-Origin': '*',
			'X-Content-Type-Options': 'nosniff'
		}
	});
	if (ctx) ctx.waitUntil(caches.default.put(cacheKey, resp.clone()));
	return resp;
}

export default {
	async fetch(req, env, ctx) {
		const LANDING_BASE = (env.LANDING_BASE || 'https://eddmpython.github.io/dartlab').replace(/\/+$/, '');
		const url = new URL(req.url);
		if (req.method !== 'GET' && req.method !== 'HEAD') return new Response('method not allowed', { status: 405 });

		// 이미지 프록시. /og/<slug> 또는 /og/<slug>.webp.
		const ogm = url.pathname.match(/^\/og\/([^/]+?)(?:\.(?:webp|png|jpe?g))?\/?$/);
		if (ogm) {
			const slug = cleanSlug(ogm[1]);
			if (!slug) return new Response('bad slug', { status: 400 });
			return serveOgImage(url, slug, ctx);
		}

		const m = url.pathname.match(/^\/c\/([^/]+)\/?$/);
		if (!m) return Response.redirect(`${LANDING_BASE}/cards`, 302);
		const slug = cleanSlug(m[1]);
		const target = `${LANDING_BASE}/cards?post=${encodeURIComponent(slug)}`;

		const post = await loadPost(slug, ctx);
		if (!post) return Response.redirect(target, 302); // 없는 슬러그 → 그냥 피드/딥링크로

		const companies = post.code ? await cachedJson(`${MEDIA_BASE}/companies/index.json`, 600, ctx) : null;
		const hasImage = !!(await resolveOgImage(post, companies));
		// og:image 는 워커 자기 오리진 프록시(/og/<slug>.webp). 안정 200 image/webp, 리다이렉트·만료 없음.
		const ogImage = hasImage ? `${url.origin}/og/${encodeURIComponent(slug)}.webp` : null;
		const title = String(post.title || post.name || 'DartLab 카드').trim();
		const desc = ogDescription(post);
		const shareUrl = `${url.origin}/c/${encodeURIComponent(slug)}`;

		// 크롤러용 OG/twitter 메타 + 사람용 즉시 리다이렉트. body 는 폴백 링크만(JS 꺼져도 이동 가능).
		const html = `<!doctype html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>${esc(title)} · DartLab</title>
<meta name="description" content="${esc(desc)}">
<meta property="og:type" content="article">
<meta property="og:site_name" content="DartLab">
<meta property="og:title" content="${esc(title)}">
<meta property="og:description" content="${esc(desc)}">
<meta property="og:url" content="${esc(shareUrl)}">
${ogImage ? `<meta property="og:image" content="${esc(ogImage)}">
<meta property="og:image:secure_url" content="${esc(ogImage)}">
<meta property="og:image:type" content="image/webp">
<meta property="og:image:width" content="1080">
<meta property="og:image:height" content="1350">
<meta property="og:image:alt" content="${esc(title)}">` : ''}
<meta name="twitter:card" content="${ogImage ? 'summary_large_image' : 'summary'}">
<meta name="twitter:title" content="${esc(title)}">
<meta name="twitter:description" content="${esc(desc)}">
${ogImage ? `<meta name="twitter:image" content="${esc(ogImage)}">` : ''}
<link rel="canonical" href="${esc(target)}">
<meta http-equiv="refresh" content="0; url=${esc(target)}">
<script>location.replace(${JSON.stringify(target)});</script>
</head>
<body style="background:#030509;color:#f1f5f9;font-family:system-ui,sans-serif;text-align:center;padding:18vh 8vw">
<p>카드를 여는 중…</p>
<p><a href="${esc(target)}" style="color:#fb923c">${esc(title)} 보러 가기 →</a></p>
</body>
</html>`;
		return new Response(req.method === 'HEAD' ? null : html, {
			headers: { 'Content-Type': 'text/html; charset=utf-8', 'Cache-Control': 'public, max-age=600' }
		});
	}
};
