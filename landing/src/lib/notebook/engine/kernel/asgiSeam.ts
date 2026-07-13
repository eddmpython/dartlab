/// <reference lib="webworker" />
// 커널 seam (ASGI arm). browser-as-server dispatch 를 손수(_dl_dispatch)와 pyproc(AsgiServer)
// 두 impl 중 플래그로 고른다. USE_PYPROC_ASGI=false(기본)면 오늘 경로와 바이트 동일.
// mainPlan/pyproc-runtime-ssot P1. dartlab 라우팅(/pyapi 접두·query)·설치는 seam 위 워커 소유.
import type { Runtime as PyprocRuntime, PyprocAsgiServer } from 'pyproc/runtime';

interface PyLike {
	runPython: (code: string) => unknown;
	runPythonAsync: (code: string) => Promise<unknown>;
	globals: { get: (name: string) => unknown; set: (name: string, value: unknown) => void };
	_module: unknown;
}

export interface AsgiResult {
	status: number;
	body: string;
}

export interface AsgiKernel {
	readonly name: 'pyproc' | 'legacy'; // 실제 서빙한 커널(라이브 확인용 x-dartlab-kernel 헤더)
	install(): Promise<void>;
	serve(method: string, path: string, body: string | null): Promise<AsgiResult>;
}

// dartlab FastAPI 앱 빌드 preamble. fastapi lazy install + typing-extensions 4.12 승격.
// (dartlab 을 먼저 설치하면 typing-extensions 4.11 이 고정되나 fastapi 는 >=4.12 요구.
// pyodide micropip 은 reinstall 인자가 없어 uninstall 후 재설치로 올린다.)
// dartlab 자체 설치(micropip install dartlab)는 seam 위에서 ensureDartlab 이 먼저 끝낸다.
const APP_SETUP = `
import micropip
try:
    import fastapi  # noqa: F401
except ImportError:
    try:
        micropip.uninstall("typing-extensions")
    except Exception:
        pass
    await micropip.install("typing-extensions>=4.12.0")
    await micropip.install("fastapi")
import dartlab.webapi as _dl_webapi
_dl_app = _dl_webapi.buildBrowserApi()
`;

// 손수 dispatch. 현 pyodideWorker.ts 의 _dl_dispatch verbatim. 기본 경로(무회귀).
const HANDROLLED_DISPATCH = `
async def _dl_dispatch(method, path, body_text):
    route = path[6:] if path.startswith("/pyapi") else path
    qs = b""
    if "?" in route:
        route, q = route.split("?", 1); qs = q.encode()
    scope = {"type": "http", "asgi": {"version": "3.0"}, "http_version": "1.1",
             "method": method, "path": route or "/", "raw_path": (route or "/").encode(),
             "query_string": qs, "headers": [(b"content-type", b"application/json")]}
    sent = {"status": None, "body": []}
    async def recv():
        return {"type": "http.request", "body": (body_text or "").encode(), "more_body": False}
    async def send(msg):
        if msg["type"] == "http.response.start": sent["status"] = msg["status"]
        elif msg["type"] == "http.response.body": sent["body"].append(msg.get("body", b""))
    await _dl_app(scope, recv, send)
    return [sent["status"] or 500, b"".join(sent["body"]).decode("utf-8")]
`;

// 기본 경로: 손수 dispatch. 오늘과 동일한 파이썬을 실행한다.
export class HandRolledAsgi implements AsgiKernel {
	readonly name = 'legacy' as const;
	private ready = false;
	constructor(private py: PyLike) {}

	async install(): Promise<void> {
		if (this.ready) return;
		await this.py.runPythonAsync(APP_SETUP + HANDROLLED_DISPATCH);
		this.ready = true;
	}

	async serve(method: string, path: string, body: string | null): Promise<AsgiResult> {
		const res = (await this.py.runPythonAsync(
			`await _dl_dispatch(${JSON.stringify(method)}, ${JSON.stringify(path)}, ${JSON.stringify(body ?? '')})`
		)) as { get(i: number): unknown; destroy(): void };
		const status = res.get(0) as number;
		const bodyText = res.get(1) as string;
		res.destroy();
		return { status, body: bodyText };
	}
}

// pyproc 경로. 워커가 init 에서 만든 공유 Runtime(rt = new Runtime(pyodide)) 을 그대로 받는다.
// 워커의 FS·run·출력·인터럽트도 같은 rt 를 쓰므로 커널·셀실행이 단일 런타임 SSOT 를 공유한다.
// enableAsgiServer 로 dispatch. 설치(fastapi 등) 실패 시 워커가 HandRolledAsgi(raw pyodide) 로 폴백.
export class PyprocAsgi implements AsgiKernel {
	readonly name = 'pyproc' as const;
	private ready = false;
	private asgi: PyprocAsgiServer | null = null;
	constructor(private rt: PyprocRuntime) {}

	async install(): Promise<void> {
		if (this.ready) return;
		await this.rt.runAsync(APP_SETUP);
		this.asgi = this.rt.enableAsgiServer({ app: '_dl_app' });
		await this.asgi.install();
		this.ready = true;
	}

	async serve(method: string, path: string, body: string | null): Promise<AsgiResult> {
		// /pyapi 접두 제거 + query 분리(dartlab 라우팅). pyproc AsgiServer 는 route·query 분리 입력.
		let route = path.startsWith('/pyapi') ? path.slice(6) : path;
		let query = '';
		const qi = route.indexOf('?');
		if (qi >= 0) {
			query = route.slice(qi + 1);
			route = route.slice(0, qi);
		}
		const res = await this.asgi!.serve(method, route || '/', body, query);
		return { status: res.status, body: res.body };
	}
}
