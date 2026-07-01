// 카드 캐러셀 브랜디드 OG 이미지 배치 렌더러.
//
// build_carousel_contracts.py 가 호출한다(subprocess). 각 카드의 첫 슬라이드를 dartlab 에디토리얼 카드로
// 1080x1350 JPEG 렌더한다: 그레이톤 배경 + 좌상단 아바타/dartlab + 로즈 아이브로(name) + 헤드라인(line,
// [[..]] 로즈 강조). landing CardSlide 의 에디토리얼 룩 재현(별도 SSOT 아님, 같은 팔레트/구도).
//
// URL 필터(wsrv)로는 텍스트/로고 합성이 안 되고, 엣지 런타임 생성(Satori+resvg+한글폰트)은 무료 CF 워커
// 용량 한계를 넘는다. 그래서 발행 시점에 이 이미지를 렌더해 HF 에 올리고 og:image 가 그걸 가리킨다.
//
// 사용: node render_og_cards.mjs <manifestPath> <avatarPath>
//   manifest = [{ slug, name, line, bg, out }]  (bg = file:// 또는 https:// · out = 출력 JPEG 절대경로)
//   전부 렌더 성공하면 exit 0. 개별 실패는 stderr 경고 후 계속(그 카드만 산출 없음).

import { fileURLToPath, pathToFileURL } from 'node:url';
import { dirname, resolve } from 'node:path';
import { readFileSync } from 'node:fs';

const [manifestPath, avatarPath] = process.argv.slice(2);
if (!manifestPath || !avatarPath) {
	console.error('usage: node render_og_cards.mjs <manifestPath> <avatarPath>');
	process.exit(2);
}

// playwright-core 는 ui/web 에 있다(리포 상대경로 · 머신 무관). blog/_scripts → ../../ui/web.
const here = dirname(fileURLToPath(import.meta.url));
const PW = pathToFileURL(resolve(here, '../../ui/web/node_modules/playwright-core/index.js')).href;
const pwMod = await import(PW);
const chromium = pwMod.chromium ?? pwMod.default?.chromium;
if (!chromium) {
	console.error('playwright chromium unavailable');
	process.exit(3);
}

const jobs = JSON.parse(readFileSync(manifestPath, 'utf-8'));
const avatarB64 = readFileSync(avatarPath).toString('base64');
const avatarUri = `data:image/png;base64,${avatarB64}`;

// 헤드라인 길이 인지 폰트(긴 문장도 프레임 안, CardSlide eLine 결). 공백 제외 글자 수 기준.
function headlineSize(line) {
	const n = String(line).replace(/\[\[|\]\]/g, '').replace(/\s/g, '').length;
	if (n <= 22) return 82;
	if (n <= 30) return 74;
	if (n <= 40) return 64;
	if (n <= 52) return 56;
	return 50;
}

function esc(s) {
	return String(s == null ? '' : s)
		.replace(/&/g, '&amp;')
		.replace(/</g, '&lt;')
		.replace(/>/g, '&gt;');
}

// [[..]] → 로즈 강조 span (esc 후 마커만 치환).
function lineHtml(line) {
	return esc(line).replace(/\[\[(.+?)\]\]/g, '<span class="hl">$1</span>');
}

// bg 를 data URI 로 확정(setContent 페이지는 file:// 리소스 접근이 차단되고, networkidle 은 file:// 을
// 안 기다린다 → 배경 검정 회귀). http 는 Node fetch(302 추종), 로컬은 readFile 후 base64. 실패하면 throw
// (그 카드는 산출 없음 → 파이썬이 ogImage 제거해 평사진 폴백).
async function bgDataUri(bg) {
	if (/^https?:/i.test(bg)) {
		const r = await fetch(bg, { headers: { 'User-Agent': 'dartlab-og/1.0' } });
		if (!r.ok) throw new Error(`bg fetch ${r.status}`);
		const buf = Buffer.from(await r.arrayBuffer());
		return `data:${r.headers.get('content-type') || 'image/webp'};base64,${buf.toString('base64')}`;
	}
	const p = bg.replace(/^file:\/\//, '');
	const ext = p.split('.').pop().toLowerCase();
	const mime = ext === 'png' ? 'image/png' : ext === 'jpg' || ext === 'jpeg' ? 'image/jpeg' : 'image/webp';
	return `data:${mime};base64,${readFileSync(p).toString('base64')}`;
}

function pageHtml(job, bgUri) {
	const size = headlineSize(job.line);
	return `<!doctype html><html lang="ko"><head><meta charset="utf-8">
<link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/static/pretendard.css">
<style>
  * { margin:0; padding:0; box-sizing:border-box; }
  html,body { width:1080px; height:1350px; }
  .card { position:relative; width:1080px; height:1350px; overflow:hidden; background:#050811;
    font-family:'Pretendard',system-ui,sans-serif; color:#f6f8fb; }
  .bg { position:absolute; inset:0; width:100%; height:100%; object-fit:cover;
    filter:grayscale(1) contrast(1.05) brightness(1.02); opacity:0.96; }
  .scrim { position:absolute; inset:0; background:linear-gradient(180deg,
     rgba(3,5,9,0.30) 0%, rgba(3,5,9,0.30) 42%, rgba(3,5,9,0.90) 100%); }
  .brand { position:absolute; top:64px; left:76px; display:flex; align-items:center; gap:18px; z-index:2; }
  .brand img { width:72px; height:72px; border-radius:50%; }
  .brand .wm { font-size:40px; font-weight:800; letter-spacing:-0.01em; color:#f6f8fb; }
  .body { position:absolute; left:76px; right:76px; bottom:118px; z-index:2; }
  .eyebrow { font-size:34px; font-weight:800; letter-spacing:0.02em; color:#ff3f6f; margin-bottom:22px;
    white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
  .line { font-size:${size}px; font-weight:900; line-height:1.14; letter-spacing:-0.01em;
    color:#f6f8fb; word-break:keep-all;
    display:-webkit-box; -webkit-box-orient:vertical; -webkit-line-clamp:5; overflow:hidden; }
  .line .hl { color:#ff3f6f; }
</style></head>
<body><div class="card">
  <img class="bg" src="${bgUri}">
  <div class="scrim"></div>
  <div class="brand"><img src="${avatarUri}"><span class="wm">dartlab</span></div>
  <div class="body">
    <div class="eyebrow">${esc(job.name)}</div>
    <div class="line">${lineHtml(job.line)}</div>
  </div>
</div></body></html>`;
}

const browser = await chromium.launch({ headless: true });
const ctx = await browser.newContext({ viewport: { width: 1080, height: 1350 }, deviceScaleFactor: 1 });
let ok = 0;
let fail = 0;
for (const job of jobs) {
	const page = await ctx.newPage();
	try {
		const bgUri = await bgDataUri(job.bg); // 실패 시 throw → catch → 산출 없음(폴백)
		await page.setContent(pageHtml(job, bgUri), { waitUntil: 'networkidle', timeout: 45000 });
		await page.evaluate(() => document.fonts.ready);
		// bg(data URI) 실제 로드 확정 후 스크린샷(검정 배경 회귀 가드).
		await page.evaluate(
			() =>
				new Promise((res) => {
					const img = document.querySelector('img.bg');
					if (!img || (img.complete && img.naturalWidth)) return res();
					img.addEventListener('load', res, { once: true });
					img.addEventListener('error', res, { once: true });
					setTimeout(res, 6000);
				})
		);
		await page.waitForTimeout(300);
		await page.screenshot({ path: job.out, type: 'jpeg', quality: 90 });
		ok++;
	} catch (e) {
		fail++;
		console.error(`render fail ${job.slug}: ${e.message}`);
	} finally {
		await page.close();
	}
}
await browser.close();
console.error(`rendered ${ok} ok, ${fail} fail`);
process.exit(fail && !ok ? 4 : 0);
