/**
 * browser-as-server 페이지 브리지.
 *
 * Service Worker 가 `/pyapi/*` fetch 를 가로채 컨트롤 페이지로 postMessage 하면, 이 브리지가
 * 그 요청을 pyodide 워커의 dartlab FastAPI(executionStore.serveApi)로 넘기고 응답을 MessageChannel
 * 로 돌려준다. SW <-> 워커의 유일한 relay 지점(덕지덕지 방지: 표면 컴포넌트는 fetch 만 쓴다).
 *
 * 루트 레이아웃 onMount 에서 한 번 설치한다. 워커는 첫 /pyapi 요청 때 lazy 기동된다.
 */
import { serveApi } from '$lib/notebook/stores/executionStore';

let installed = false;

/** SW message('pyapi') 수신 -> serveApi -> port 응답. 브라우저에서만, 한 번만. */
export function installPyapiBridge(): void {
	if (installed || typeof navigator === 'undefined' || !('serviceWorker' in navigator)) return;
	installed = true;
	navigator.serviceWorker.addEventListener('message', async (event) => {
		const data = event.data as { type?: string; method?: string; path?: string; body?: string } | undefined;
		if (!data || data.type !== 'pyapi') return;
		const port = event.ports[0];
		if (!port) return;
		try {
			const res = await serveApi({ method: data.method ?? 'GET', path: data.path ?? '/', body: data.body });
			port.postMessage(res);
		} catch (e) {
			port.postMessage({
				status: 500,
				headers: { 'content-type': 'application/json' },
				body: JSON.stringify({ error: String(e) })
			});
		}
	});
}
