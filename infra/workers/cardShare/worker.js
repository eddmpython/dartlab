// 캐러셀 공유/OG 동적 엔드포인트 Cloudflare Worker (무료 티어).
//
// 정공법 = SSOT(hfMedia)에서 라이브로 읽어 파생뷰(OG)만 낸다. 정적 사이트(GitHub Pages)에 캐러셀마다
// HTML 을 굽지 않는다. 그건 라이브 데이터를 정적 빌드에 복사·박제(drift + 캐러셀마다 재배포)라 우회.
// 이 워커는 /cards 가 브라우저에서 hfMedia 를 라이브로 읽는 것과 동일 원리를, 크롤러용으로 서버사이드에서
// 한다. hfProxy·news 워커가 "정적 사이트가 못 하는 라이브 HF 브리지"를 하는 것과 같은 패턴.
//
// 라우트: GET /c/<slug>
//   1. carousels/index.json 라이브 read(엣지 캐시 10분, index 는 가변).
//   2. slug 로 캐러셀 → og:title(제목) · og:description(캡션 첫 문단) · og:image(첫 슬라이드).
//   3. 크롤러는 메타만 읽고 워커 페이지에 머문다(canonical=self). 사람은 JS(location.replace)로만
//      LANDING_BASE/cards?post=<slug> 로 이동. 없는 slug 는 그 딥링크로 302.
//
// ⚠ OG 이미지 2 가지 회귀 가드:
//   (A) 크롤러 리다이렉트 금지: <meta http-equiv="refresh"> 를 쓰면 크롤러가 따라가서 OG 없는 landing
//       SPA(github.io/cards)로 넘어가 미리보기가 빈다. 사람 이동은 JS 로만, canonical 도 self.
//   (B) og:image = wsrv.nl 변환 JPEG 직접 링크. hfMedia 원본은 webp 인데 (1) 일부 크롤러(카톡 등)가
//       WebP OG 를 안 띄우고, (2) HF 는 Xet 이관 후 resolve 가 302 크로스도메인·Expires 서명·no-store 라
//       크롤러가 이미지로 인식·캐시 못 한다. wsrv 가 HF resolve 302 를 서버사이드에서 풀고 1080x1350 4:5
//       baseline JPEG 로 변환해 안정 200 image/jpeg 로 서빙한다. 크롤러(Meta 등)는 wsrv 에서 바로 받는다.
//       (워커가 직접 프록시하려 했으나 Cloudflare Worker → wsrv 아웃바운드가 막혀 폴백만 돼 제거함.)
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

// hfMedia URL → og:image 용 wsrv.nl JPEG 링크(1080x1350 4:5, baseline). 크롤러 호환 위해 JPEG 통일.
// grey=true 면 그레이톤 필터(평사진 폴백용). 발행 시 구운 브랜디드 OG 는 이미 그레이톤이라 grey=false.
function ogImageUrl(src, grey = true) {
	const f = grey ? '&filt=greyscale' : '';
	return `https://wsrv.nl/?url=${encodeURIComponent(src)}&output=jpg&w=1080&h=1350&fit=cover&q=88${f}`;
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

export default {
	async fetch(req, env, ctx) {
		const LANDING_BASE = (env.LANDING_BASE || 'https://eddmpython.github.io/dartlab').replace(/\/+$/, '');
		const url = new URL(req.url);
		if (req.method !== 'GET' && req.method !== 'HEAD') return new Response('method not allowed', { status: 405 });

		const m = url.pathname.match(/^\/c\/([^/]+)\/?$/);
		if (!m) return Response.redirect(`${LANDING_BASE}/cards`, 302);
		const slug = cleanSlug(m[1]);
		const target = `${LANDING_BASE}/cards?post=${encodeURIComponent(slug)}`;

		const post = await loadPost(slug, ctx);
		if (!post) return Response.redirect(target, 302); // 없는 슬러그 → 그냥 피드/딥링크로

		// og:image 우선순위: (1) 발행 시 구운 브랜디드 OG(og/<slug>.<hash>.jpg, 그레이톤+아바타/dartlab+헤드라인)
		// → (2) 없으면 첫 슬라이드 평사진(그레이톤 필터). 둘 다 wsrv.nl JPEG 링크(위 ⚠ B, HF resolve 직접 금지).
		let ogImage = null;
		const ogPath = typeof post.ogImage === 'string' && post.ogImage ? post.ogImage : null;
		if (ogPath) {
			ogImage = ogImageUrl(`${MEDIA_BASE}/${ogPath}`, false); // 구운 OG 는 이미 그레이톤
		} else {
			const companies = post.code ? await cachedJson(`${MEDIA_BASE}/companies/index.json`, 600, ctx) : null;
			const ogSrc = await resolveOgImage(post, companies);
			ogImage = ogSrc ? ogImageUrl(ogSrc, true) : null;
		}
		const title = String(post.title || post.name || 'DartLab 카드').trim();
		const desc = ogDescription(post);
		const shareUrl = `${url.origin}/c/${encodeURIComponent(slug)}`;

		// 크롤러용 OG/twitter 메타 + 사람용 JS 리다이렉트(meta refresh 금지, 위 ⚠ A). body 는 폴백 링크.
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
<meta property="og:image:type" content="image/jpeg">
<meta property="og:image:width" content="1080">
<meta property="og:image:height" content="1350">
<meta property="og:image:alt" content="${esc(title)}">` : ''}
<meta name="twitter:card" content="${ogImage ? 'summary_large_image' : 'summary'}">
<meta name="twitter:title" content="${esc(title)}">
<meta name="twitter:description" content="${esc(desc)}">
${ogImage ? `<meta name="twitter:image" content="${esc(ogImage)}">` : ''}
<link rel="canonical" href="${esc(shareUrl)}">
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
