import type { ExecutionEngine, CellOutput, CompletionItem, VariableInfo, PackageInfo, DocResult, FileEntry, PyApiResponse, RuntimeCapabilities, CheckpointInfo } from './executionEngine';

let msgId = 0;

function nextId() {
	return String(++msgId);
}

export class WorkerEngine implements ExecutionEngine {
	name = 'pyodide-worker';
	isReady = false;

	private worker: Worker | null = null;
	private interruptBuffer: Uint8Array | null = null;
	private pending = new Map<string, { resolve: (v: unknown) => void; reject: (e: Error) => void }>();

	async initialize(): Promise<void> {
		if (this.isReady) return;

		this.worker = new Worker(new URL('./pyodideWorker.ts', import.meta.url), { type: 'module' });

		this.worker.onmessage = (e: MessageEvent) => {
			const { id, result, error } = e.data as { id: string; result: unknown; error?: string };
			const p = this.pending.get(id);
			if (!p) return;
			this.pending.delete(id);
			if (error) {
				p.reject(new Error(error));
			} else {
				p.resolve(result);
			}
		};

		this.worker.onerror = (e) => {
			console.error('[WorkerEngine] Worker error:', e.message, e);
			for (const p of this.pending.values()) {
				p.reject(new Error(e.message));
			}
			this.pending.clear();
		};

		this.worker.onmessageerror = (e) => {
			console.error('[WorkerEngine] Message error:', e);
		};

		if (globalThis.crossOriginIsolated && typeof SharedArrayBuffer !== 'undefined') {
			this.interruptBuffer = new Uint8Array(new SharedArrayBuffer(1));
		}
		await this.call('initialize', this.interruptBuffer);
		this.isReady = true;
	}

	/** dartlab wheel 설치 + import 를 미리 끝낸다(허브에서 사전 호출). 실패는 삼킨다. */
	async warm(): Promise<void> {
		if (!this.worker) return;
		await this.call('warm').catch(() => undefined);
	}

	/**
	 * browser-as-server: 같은 커널의 dartlab FastAPI 로 HTTP 요청을 보낸다. Service Worker 가
	 * 페이지 fetch('/pyapi/*')를 이 메서드로 relay 한다. 노트북 execute 와 한 워커 커널을 공유.
	 */
	async serveApi(req: { method: string; path: string; body?: string }): Promise<PyApiResponse> {
		return this.call('pyapi', req) as Promise<PyApiResponse>;
	}

	async attachWorkspace(workspaceId: string): Promise<boolean> {
		return this.call('attachWorkspace', workspaceId) as Promise<boolean>;
	}

	async getRuntimeCapabilities(): Promise<RuntimeCapabilities> {
		return this.call('getRuntimeCapabilities') as Promise<RuntimeCapabilities>;
	}

	async createCheckpoint(label: string): Promise<CheckpointInfo> {
		return this.call('createCheckpoint', label) as Promise<CheckpointInfo>;
	}

	async restoreCheckpoint(id: string): Promise<{ id: string; pagesWritten: number; bytesWritten: number }> {
		return this.call('restoreCheckpoint', id) as Promise<{ id: string; pagesWritten: number; bytesWritten: number }>;
	}

	async listCheckpoints(): Promise<CheckpointInfo[]> {
		return this.call('listCheckpoints') as Promise<CheckpointInfo[]>;
	}

	async clearCheckpoints(): Promise<void> {
		await this.call('clearCheckpoints');
	}

	private call(cmd: string, ...args: unknown[]): Promise<unknown> {
		return new Promise((resolve, reject) => {
			if (!this.worker) { reject(new Error('Worker not started')); return; }
			const id = nextId();
			this.pending.set(id, { resolve, reject });
			this.worker.postMessage({ id, cmd, args });
		});
	}

	async execute(code: string): Promise<CellOutput> {
		return this.call('execute', code) as Promise<CellOutput>;
	}

	interrupt(): void {
		if (this.interruptBuffer) {
			this.interruptBuffer[0] = 2;
			return;
		}
		this.worker?.terminate();
		this.worker = null;
		this.isReady = false;
		for (const pending of this.pending.values()) pending.reject(new Error('Execution interrupted'));
		this.pending.clear();
	}

	destroy(): void {
		this.worker?.terminate();
		this.worker = null;
		this.interruptBuffer = null;
		this.isReady = false;
		for (const p of this.pending.values()) {
			p.reject(new Error('Engine destroyed'));
		}
		this.pending.clear();
	}

	async getVariable(_name: string): Promise<unknown> {
		return undefined;
	}

	async getVariableNames(): Promise<string[]> {
		return this.call('getVariableNames') as Promise<string[]>;
	}

	async getVariablesWithInfo(): Promise<VariableInfo[]> {
		return this.call('getVariablesWithInfo') as Promise<VariableInfo[]>;
	}

	async getCompletions(objName: string): Promise<CompletionItem[]> {
		return this.call('getCompletions', objName) as Promise<CompletionItem[]>;
	}

	async installPackage(packageName: string): Promise<void> {
		await this.call('installPackage', packageName);
	}

	async getInstalledPackages(): Promise<PackageInfo[]> {
		return this.call('getInstalledPackages') as Promise<PackageInfo[]>;
	}

	async getDocstring(name: string): Promise<DocResult | null> {
		return this.call('getDocstring', name) as Promise<DocResult | null>;
	}

	async updateWidgetValue(widgetId: string, value: unknown): Promise<void> {
		await this.call('updateWidgetValue', widgetId, value);
	}

	async listFiles(path: string): Promise<FileEntry[]> {
		return this.call('listFiles', path) as Promise<FileEntry[]>;
	}

	async readFile(path: string): Promise<string> {
		return this.call('readFile', path) as Promise<string>;
	}

	async writeFile(path: string, content: string): Promise<void> {
		await this.call('writeFile', path, content);
	}

	async mkdir(path: string): Promise<void> {
		await this.call('mkdir', path);
	}

	async removeFile(path: string): Promise<void> {
		await this.call('removeFile', path);
	}
}
