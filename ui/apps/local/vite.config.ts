import { sveltekit } from '@sveltejs/kit/vite';
import { defineConfig } from 'vite';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
// 워크스페이스 패키지 소스(@dartlab/ui-*)는 ui/packages 아래 심볼릭링크 — dev fs.allow 로 읽기 허용.
const uiPackagesDir = path.resolve(__dirname, '..', '..', 'packages');

// dev: 로컬 Python API 서버(`dartlab ai`) 기본 포트 8400(HF Spaces 7860). SvelteKit dev 가 /api → 서버로 프록시.
// 빌드(정적 SPA)에서는 같은 오리진(Python 서버 서빙)이라 apiBase='' — 프록시는 dev 전용.
const apiTarget = process.env.DARTLAB_API_BASE || 'http://127.0.0.1:8400';

// 종목 뉴스 워커 프록시 기본값(secret 아님) — news 는 private 라 HF 직독 fallback 이 없어 env 미설정 시 빈 섹션.
// 로컬도 공개와 "공통 배선"으로 워커 /news 를 쓰게 한다(??= 라 operator 명시값 우선·가역).
// ⚠ HF_RESOLVE/NAVER 는 안 건드린다 — fallback(HF 직독) 있어 불필요, dev 데이터 흐름 보존.
process.env.VITE_DARTLAB_NEWS_PROXY ??= 'https://dartlab-hf-proxy.eddmpython.workers.dev/news';
// 시장 전반 뉴스 라이브 오버레이 워커(/market-news, 네이버 검색) — HF 누적 위 머지, 공통 배선 기본값(가역).
process.env.VITE_DARTLAB_MARKET_NEWS_PROXY ??= 'https://dartlab-hf-proxy.eddmpython.workers.dev/market-news';
// 당일 공시 라이브 오버레이 워커(/market-filings, DART list) — HF 누적 위 머지, 공통 배선 기본값(가역).
process.env.VITE_DARTLAB_MARKET_FILINGS_PROXY ??= 'https://dartlab-hf-proxy.eddmpython.workers.dev/market-filings';
// IPO 발굴 라이브 워커(/ipo-filings, DART list corp_cls=E) · 상장 전 발행사(HF bake 부재) 라이브 데이터원.
process.env.VITE_DARTLAB_IPO_FILINGS_PROXY ??= 'https://dartlab-hf-proxy.eddmpython.workers.dev/ipo-filings';

export default defineConfig({
	plugins: [sveltekit()],
	server: {
		host: '127.0.0.1',
		port: 5174,
		strictPort: true,
		proxy: {
			'/api': { target: apiTarget, changeOrigin: true }
		},
		fs: {
			allow: [uiPackagesDir]
		}
	},
	optimizeDeps: {
		// 터미널 surface 가 동적 import 하는 무거운 dep 를 시작 시 미리 최적화(landing 동일 — 뒤늦은 재최적화 504 churn 회피).
		include: ['klinecharts']
	}
});
