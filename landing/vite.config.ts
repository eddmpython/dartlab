import tailwindcss from '@tailwindcss/vite';
import { sveltekit } from '@sveltejs/kit/vite';
import { defineConfig, type ViteDevServer } from 'vite';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const blogDir = path.resolve(__dirname, '..', 'blog');
const skillsDir = path.resolve(__dirname, '..', 'src', 'dartlab', 'skills');
const pyodideDir = path.resolve(__dirname, '..', 'pyodide');
const sharedChartDir = path.resolve(__dirname, '..', 'ui', 'shared', 'chart');
const uiPackagesDir = path.resolve(__dirname, '..', 'ui', 'packages');

const pyprojectText = fs.readFileSync(path.resolve(__dirname, '..', 'pyproject.toml'), 'utf-8');
const versionMatch = pyprojectText.match(/^version\s*=\s*"([^"]+)"/m);
if (!versionMatch) throw new Error('pyproject.toml version not found');
const dartlabVersion = versionMatch[1];

// 종목 뉴스 워커 프록시 기본값(secret 아님) — news 는 private 라 HF 직독 fallback 이 없어 env 미설정 시 빈 섹션.
// dev/직접빌드도 공개와 "공통 배선"으로 워커 /news 를 쓰게 한다. deploy-landing step env 가 우선(??= 가역).
// ⚠ HF_RESOLVE/NAVER 는 여기서 안 건드린다 — dev 는 원래 HF 직독 + /__gov·/__naver dev 플러그인 경로라,
//    워커로 강제하면 dev 데이터 로드 흐름이 바뀐다. news 만 fallback 부재라 기본값이 필요하다.
process.env.VITE_DARTLAB_NEWS_PROXY ??= 'https://dartlab-hf-proxy.eddmpython.workers.dev/news';
// 시장 전반 뉴스 라이브 오버레이 워커(/market-news, 네이버 검색). HF 누적 shard 위에 머지되는 오버레이라 미설정/실패 시
// HF base 만 — fallback 부재 아님(news 와 다름). 공통 배선으로 dev/직접빌드도 워커를 그대로 쓰게 기본값 부여(가역).
process.env.VITE_DARTLAB_MARKET_NEWS_PROXY ??= 'https://dartlab-hf-proxy.eddmpython.workers.dev/market-news';
// 당일 공시 라이브 오버레이 워커(/market-filings, DART list). HF 누적 위 머지, 공통 배선 기본값(가역).
process.env.VITE_DARTLAB_MARKET_FILINGS_PROXY ??= 'https://dartlab-hf-proxy.eddmpython.workers.dev/market-filings';
// IPO 발굴 라이브 워커(/ipo-filings, DART list corp_cls=E). 상장 전 발행사는 HF bake 에 없어 이 라이브가
// 퍼블릭 유일 데이터원 · 미설정/실패 시 발굴 목록만 빈값(무중단). 공통 배선 기본값(가역).
process.env.VITE_DARTLAB_IPO_FILINGS_PROXY ??= 'https://dartlab-hf-proxy.eddmpython.workers.dev/ipo-filings';

function contentType(filePath: string): string {
	const ext = path.extname(filePath).toLowerCase();
	if (ext === '.svg') return 'image/svg+xml';
	if (ext === '.png') return 'image/png';
	if (ext === '.jpg' || ext === '.jpeg') return 'image/jpeg';
	if (ext === '.webp') return 'image/webp';
	return 'application/octet-stream';
}

function collectBlogAssets(dir: string, result = new Map<string, string>()) {
	for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
		const fullPath = path.resolve(dir, entry.name);
		if (entry.isDirectory()) {
			// underscore 특수폴더(_issues 캐러셀·_reference·_scripts)는 평면 /blog/assets/ 서빙 대상이 아니다.
			// 특히 _issues 캐러셀 자산은 build_carousel_contracts.py 가 HF 콘텐츠 주소 객체로 발행하므로
			// 캐러셀마다 scene-NN 재시작이 정상이다(평면 basename 충돌로 dev 부팅을 깨면 안 됨).
			if (entry.name.startsWith('_')) continue;
			if (entry.name === 'assets') {
				for (const asset of fs.readdirSync(fullPath, { withFileTypes: true })) {
					if (!asset.isFile()) continue;
					// 임시 게시 자산은 이미지(.webp/.svg/.png/.jpg/.gif/.avif)만 수집한다.
					// 출처·생성 메타데이터는 글 루트에 있으므로 assets 서빙 대상이 아니다.
					if (!/\.(webp|svg|png|jpe?g|gif|avif)$/i.test(asset.name)) continue;
					// 썸네일 합성 소스(원본 배경) — markdown 미참조, 출력은 /thumbnails/. 카테고리마다 NN 재시작이라
					// basename(01-thumbnail-bg.webp 등)이 전역 충돌 → 서빙 대상 아니므로 스킵.
					if (/thumbnail-bg\.webp$/i.test(asset.name)) continue;
					const assetPath = path.resolve(fullPath, asset.name);
					const duplicate = result.get(asset.name);
					if (duplicate) {
						throw new Error(`Duplicate blog asset filename detected: ${asset.name}\n- ${duplicate}\n- ${assetPath}`);
					}
					result.set(asset.name, assetPath);
				}
				continue;
			}
			collectBlogAssets(fullPath, result);
		}
	}
	return result;
}

function blogAssetsPlugin() {
	return {
		name: 'blog-assets-plugin',
		configureServer(server: ViteDevServer) {
			const assetMap = collectBlogAssets(blogDir);
			server.middlewares.use('/blog/assets', (req, res, next) => {
				const rawPath = req.url?.split('?')[0] ?? '/';
				const fileName = path.basename(rawPath);
				const filePath = assetMap.get(fileName);
				if (!filePath || !fs.existsSync(filePath) || !fs.statSync(filePath).isFile()) {
					next();
					return;
				}
				res.setHeader('Content-Type', contentType(filePath));
				fs.createReadStream(filePath).pipe(res);
			});
		}
	};
}

function skillCatalogPlugin() {
	return {
		name: 'skill-catalog-plugin',
		configureServer(server: ViteDevServer) {
			server.middlewares.use('/__dartlab_skills', (req, res, next) => {
				const rawPath = req.url?.split('?')[0] ?? '/';
				const fileName = path.basename(rawPath);
				if (!['catalog.json', 'pyodide.json'].includes(fileName)) {
					next();
					return;
				}
				const filePath = path.resolve(skillsDir, fileName);
				if (!filePath.startsWith(skillsDir + path.sep) || !fs.existsSync(filePath) || !fs.statSync(filePath).isFile()) {
					next();
					return;
				}
				res.setHeader('Content-Type', 'application/json; charset=utf-8');
				fs.createReadStream(filePath).pipe(res);
			});
		}
	};
}

// repo 루트 .env 직독 (Vite 는 비-VITE_ 변수를 process.env 에 안 넣음 → dev 미들웨어용으로 직접 파싱).
function readRepoEnv(): Record<string, string> {
	try {
		const txt = fs.readFileSync(path.resolve(__dirname, '..', '.env'), 'utf-8');
		const out: Record<string, string> = {};
		for (const line of txt.split(/\r?\n/)) {
			const m = line.match(/^([A-Za-z_][A-Za-z0-9_]*)=(.*)$/);
			if (m) out[m[1]] = m[2].replace(/^["']|["']$/g, '').trim();
		}
		return out;
	} catch {
		return {};
	}
}

// 공공데이터포털 금융위원회_주식시세정보 (디코딩 키 → encodeURIComponent). 전체 이력 → Candle[] 정규화.
const GOV_ENDPOINT = 'https://apis.data.go.kr/1160100/service/GetStockSecuritiesInfoService/getStockPriceInfo';
async function fetchGovCandles(code: string, key: string) {
	const candles: { t: string; o: number; h: number; l: number; c: number; v: number }[] = [];
	const seen = new Set<string>();
	for (let page = 1; page <= 6; page++) {
		const url = `${GOV_ENDPOINT}?serviceKey=${encodeURIComponent(key)}&resultType=json&numOfRows=4000&pageNo=${page}&likeSrtnCd=${encodeURIComponent(code)}`;
		const res = await fetch(url);
		if (!res.ok) throw new Error(`gov api ${res.status}`);
		const j: any = await res.json();
		const item = j?.response?.body?.items?.item;
		const arr = Array.isArray(item) ? item : item ? [item] : [];
		if (!arr.length) break;
		for (const r of arr) {
			if (String(r.srtnCd) !== code) continue; // likeSrtnCd = LIKE → 정확 매칭만 채택
			const t = String(r.basDt);
			const c = Number(r.clpr);
			if (seen.has(t) || !Number.isFinite(c) || c <= 0) continue;
			seen.add(t);
			candles.push({ t, o: Number(r.mkp) || c, h: Number(r.hipr) || c, l: Number(r.lopr) || c, c, v: Number(r.trqu) || 0 });
		}
		const total = Number(j?.response?.body?.totalCount) || 0;
		if (page * 4000 >= total) break;
	}
	candles.sort((a, b) => a.t.localeCompare(b.t));
	return candles;
}

// save-later: 회사별 parquet 영속화를 buildGovData --stock 로 백그라운드 spawn (응답 후, 차트 비차단).
// gov 전체이력 fetch + 기존 parquet merge + HF 업로드를 Python(검증된 생산기)에 위임 — Node parquet 쓰기 회피.
function spawnGovPersist(code: string, server: ViteDevServer): void {
	import('node:child_process')
		.then(({ spawn }) => {
			const child = spawn(
				'uv',
				['run', 'python', '-X', 'utf8', '.github/scripts/sync/buildGovData.py', '--stock', code],
				{ cwd: path.resolve(__dirname, '..'), detached: true, stdio: 'ignore' }
			);
			child.on('error', (e) => server.config.logger.warn(`[gov] parquet 저장 spawn 실패 ${code}: ${e}`));
			child.unref();
		})
		.catch(() => {});
}

// 프론트-먼저 HF 캐시-필 미들웨어 — /__gov?code=XXXXXX (dev only, 토큰 Node 서버측 보관).
// draw-first-save-later: gov fetch → 캔들 즉시 반환(차트 먼저 그림) → 백그라운드 parquet 영속화.
function govPriceDevPlugin() {
	return {
		name: 'gov-price-dev',
		configureServer(server: ViteDevServer) {
			server.middlewares.use('/__gov', async (req, res) => {
				const send = (status: number, obj: unknown) => {
					if (res.writableEnded) return;
					res.statusCode = status;
					res.setHeader('Content-Type', 'application/json; charset=utf-8');
					res.end(JSON.stringify(obj));
				};
				const url = new URL(req.url ?? '', 'http://localhost');
				const code = (url.searchParams.get('code') ?? '').replace(/[^0-9A-Za-z]/g, '');
				if (!code) return send(400, { error: 'code 필요' });
				const env = readRepoEnv();
				if (!env.DATA_GO_KR_KEY) return send(503, { error: 'DATA_GO_KR_KEY 미설정(.env)' });
				let candles: { t: string; o: number; h: number; l: number; c: number; v: number }[] = [];
				try {
					candles = await fetchGovCandles(code, env.DATA_GO_KR_KEY);
				} catch (e) {
					return send(502, { error: String(e) });
				}
				send(200, { source: 'data.go.kr/금융위원회·한국거래소', code, asOf: candles.at(-1)?.t ?? '', candles });
				if (candles.length && env.HF_TOKEN) spawnGovPersist(code, server);
			});
		}
	};
}

// 네이버 fchart fresh-tail 미들웨어 — /__naver?code=XXXXXX (dev only). gov(T+1 지연)가 아직 발행 안 한
// 최신 거래일을 표시용으로 채운다(재배포 아님, 사용자 세션 표시용 fetch). 서버측 fetch라 브라우저 CORS 우회.
const NAVER_FCHART = 'https://fchart.stock.naver.com/sise.nhn';
async function fetchNaverCandles(code: string) {
	const url = `${NAVER_FCHART}?symbol=${encodeURIComponent(code)}&timeframe=day&count=30&requestType=0`;
	const res = await fetch(url, { headers: { 'User-Agent': 'Mozilla/5.0' } });
	if (!res.ok) throw new Error(`naver fchart ${res.status}`);
	const txt = await res.text(); // EUC-KR XML — 단, data="..." 필드는 순수 ASCII 라 regex 안전
	const candles: { t: string; o: number; h: number; l: number; c: number; v: number }[] = [];
	for (const m of txt.matchAll(/data="([^"]+)"/g)) {
		const p = m[1].split('|');
		if (p.length < 6) continue;
		const c = Number(p[4]);
		if (!Number.isFinite(c) || c <= 0) continue;
		candles.push({ t: p[0], o: Number(p[1]) || c, h: Number(p[2]) || c, l: Number(p[3]) || c, c, v: Number(p[5]) || 0 });
	}
	candles.sort((a, b) => a.t.localeCompare(b.t));
	return candles;
}

function naverPriceDevPlugin() {
	return {
		name: 'naver-price-dev',
		configureServer(server: ViteDevServer) {
			server.middlewares.use('/__naver', async (req, res) => {
				const send = (status: number, obj: unknown) => {
					if (res.writableEnded) return;
					res.statusCode = status;
					res.setHeader('Content-Type', 'application/json; charset=utf-8');
					res.end(JSON.stringify(obj));
				};
				const url = new URL(req.url ?? '', 'http://localhost');
				const code = (url.searchParams.get('code') ?? '').replace(/[^0-9A-Za-z]/g, '');
				if (!code) return send(400, { error: 'code 필요' });
				try {
					const candles = await fetchNaverCandles(code);
					send(200, { source: 'fchart.stock.naver.com', code, asOf: candles.at(-1)?.t ?? '', candles });
				} catch (e) {
					send(502, { error: String(e) });
				}
			});
		}
	};
}

// 종목 뉴스 미들웨어 — /__news?code=XXXXXX (dev only). 프로덕션은 CF 워커 /news 라우트(private 토큰 read).
// dev 는 토큰 없이 로컬 byCompany json(buildNaverCompanyNews 산출)을 직독 — 없으면 빈 섹션(무해).
function newsDevPlugin() {
	const byCompanyDir = path.resolve(__dirname, '..', 'data', 'news', 'private', 'naver', 'byCompany');
	return {
		name: 'news-dev',
		configureServer(server: ViteDevServer) {
			server.middlewares.use('/__news', (req, res) => {
				const send = (status: number, obj: unknown) => {
					if (res.writableEnded) return;
					res.statusCode = status;
					res.setHeader('Content-Type', 'application/json; charset=utf-8');
					res.end(JSON.stringify(obj));
				};
				const url = new URL(req.url ?? '', 'http://localhost');
				const code = (url.searchParams.get('code') ?? '').replace(/[^0-9A-Za-z]/g, '').slice(0, 12);
				if (!code) return send(400, { error: 'code 필요' });
				const file = path.join(byCompanyDir, `${code}.json`);
				if (!fs.existsSync(file)) return send(200, { code, items: [] }); // 로컬 인덱스 미빌드 → 빈 섹션
				try {
					send(200, JSON.parse(fs.readFileSync(file, 'utf-8')));
				} catch (e) {
					send(502, { code, items: [], error: String(e) });
				}
			});
		}
	};
}

// 로컬 카드 프리뷰 전용 HF 미디어 폴백. VITE_DARTLAB_HF_MEDIA_RESOLVE='' 로 미디어 base 를 로컬로 돌려
// 미발행 manifests/carousels.json 을 끼워 보는 동안에도, 실제 콘텐츠 주소 객체는 HF 에서 그대로
// 보이게 한다. 로컬 static 에 있는 파일(새 카드의 신규 이미지)은 정적 서빙이 우선, 없으면 HF 로 302.
// 정상 dev(base=HF 기본)에서는 이미지가 huggingface.co 절대 URL 로 직접 가므로 이 미들웨어는 발동하지 않는다(무영향).
function hfMediaFallbackPlugin() {
	const HF = 'https://huggingface.co/datasets/eddmpython/dartlab-media/resolve/main';
	const staticDir = path.resolve(__dirname, 'static');
	const MEDIA_RE = /^\/objects\/sha256\/[0-9a-f]{2}\/[0-9a-f]{64}\.(webp|png|jpe?g)$/i;
	return {
		name: 'hf-media-fallback',
		configureServer(server: ViteDevServer) {
			server.middlewares.use((req, res, next) => {
				const url = (req.url ?? '').split('?')[0];
				if (!MEDIA_RE.test(url)) return next();
				const local = path.join(staticDir, decodeURIComponent(url));
				if (fs.existsSync(local)) return next(); // 로컬에 있으면(새 카드) 정적 서빙
				res.statusCode = 302;
				res.setHeader('Location', HF + url);
				res.end();
			});
		}
	};
}

export default defineConfig({
	plugins: [tailwindcss(), blogAssetsPlugin(), skillCatalogPlugin(), govPriceDevPlugin(), naverPriceDevPlugin(), newsDevPlugin(), hfMediaFallbackPlugin(), sveltekit()],
	define: {
		__DARTLAB_VERSION__: JSON.stringify(dartlabVersion)
	},
	worker: {
		format: 'es'
	},
	build: {
		emptyOutDir: true
	},
	resolve: {
		alias: {
			'@blog': blogDir,
			'$chart': sharedChartDir,
			'$skills': skillsDir
		},
		// CodeMirror/lezer 는 단일 인스턴스여야 언어 확장과 syntaxHighlighting 이 연결된다.
		// (@codemirror/language 가 두 버전 깔리면 python() 트리와 하이라이트 facet 이 어긋나 하이라이트 무력화)
		dedupe: [
			'@codemirror/state',
			'@codemirror/view',
			'@codemirror/language',
			'@codemirror/commands',
			'@codemirror/autocomplete',
			'@lezer/common',
			'@lezer/highlight',
			'@lezer/lr'
		]
	},
	ssr: {
		// 워크스페이스 @dartlab/* 는 src .ts 를 그대로 export(빌드 dist 없음) → Node ESM 가 확장자 없는
		// barrel(`export * from './runtime'`)을 못 풀어 SSR 500. vite 가 변환하도록 noExternal 강제.
		noExternal: [/^d3-/, /^@dartlab\//]
	},
	optimizeDeps: {
		// d3 + 뷰어가 *동적 import* 하는 무거운 deps 를 시작 시 미리 최적화. 안 넣으면 뷰어 로드 중 뒤늦게 최적화되며
		// "optimized dependencies changed. reloading" → 옛 청크 무효화 → 504(Outdated Optimize Dep) → 빈 화면 churn.
		include: [
			'd3-scale',
			'd3-selection',
			'd3-shape',
			'd3-array',
			'lucide-svelte',
			'hyparquet',
			'hyparquet-compressors',
			'dompurify',
			'@mlc-ai/web-llm',
			'klinecharts'
		]
	},
	server: {
		host: '127.0.0.1',
		port: 5173,
		strictPort: true,
		fs: {
			allow: [
				blogDir,
				pyodideDir,
				sharedChartDir,
				skillsDir,
				uiPackagesDir
			]
		}
	}
});
