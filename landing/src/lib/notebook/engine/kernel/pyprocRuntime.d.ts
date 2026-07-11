// pyproc/runtime 앰비언트 타입. pyproc 은 순수 JS(index.d.ts 는 barrel 용)라 서브모듈
// import 에 타입이 없다. 우리가 쓰는 표면(Runtime + enableAsgiServer)만 최소 선언한다.
// 전체 계약은 pyproc index.d.ts 참조. mainPlan/pyproc-runtime-ssot 01-architecture.
declare module 'pyproc/runtime' {
	export interface PyprocAsgiServer {
		install(): Promise<{ app: string; transport: string }>;
		serve(
			method: string,
			path: string,
			body: string | null,
			query: string
		): Promise<{ status: number; headers: [string, string][]; body: string }>;
	}
	export class Runtime {
		constructor(py: unknown);
		run(code: string): unknown;
		runAsync(code: string): Promise<unknown>;
		setGlobal(name: string, value: unknown): void;
		enableAsgiServer(cfg?: { app?: string }): PyprocAsgiServer;
	}
	export function boot(opts?: Record<string, unknown>): Promise<Runtime>;
}
