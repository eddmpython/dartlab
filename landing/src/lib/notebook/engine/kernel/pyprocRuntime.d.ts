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
	// 엔진-무관 파일 IO(rt.fs). readFile 기본 binary(Uint8Array), { encoding:'utf8' }면 문자열.
	// writeFile 은 문자열→utf8 자동. stat 은 정규화 최소형(mode 비트 없음). readdir 은 ./.. 이미 필터.
	export interface PyprocFs {
		readFile(path: string, opts?: { encoding?: string }): string | Uint8Array;
		writeFile(path: string, data: string | Uint8Array, opts?: { encoding?: string }): void;
		mkdir(path: string): void;
		mkdirTree(path: string): void;
		readdir(path: string): string[];
		stat(path: string): { size: number; isDir: boolean; isFile: boolean; mtimeMs: number | null };
		exists(path: string): boolean;
		unlink(path: string): void;
		rmdir(path: string): void;
	}
	export class Runtime {
		constructor(py: unknown);
		readonly fs: PyprocFs;
		run(code: string): unknown;
		runAsync(code: string): Promise<unknown>;
		setGlobal(name: string, value: unknown): void;
		// handler 는 문자열 청크 수신(batched, 개행 flush). null = 기본 복원.
		setStdout(handler: ((text: string) => void) | null): void;
		setStderr(handler: ((text: string) => void) | null): void;
		// SAB 를 받아 엔진이 Uint8Array 뷰로 감싼다. 미지원 엔진이면 false.
		setInterruptBuffer(sab: SharedArrayBuffer | ArrayBufferLike): boolean;
		loadPackagesFromImports(code: string): Promise<void>;
		loadPackages(pkgs: string | string[]): Promise<unknown>;
		enableAsgiServer(cfg?: { app?: string }): PyprocAsgiServer;
	}
	export function boot(opts?: Record<string, unknown>): Promise<Runtime>;
}
