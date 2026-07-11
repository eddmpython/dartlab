export interface CellOutput {
	type: 'text' | 'html' | 'image' | 'error' | 'dataframe' | 'widget';
	data: string;
	executedAt: string;
}

export interface CompletionItem {
	label: string;
	type: string;
}

export interface VariableInfo {
	name: string;
	type: string;
	value: string;
}

export interface PackageInfo {
	name: string;
	version: string;
	requested?: boolean;
	requirement?: string;
	missing?: boolean;
	error?: string;
}

export interface DocResult {
	name: string;
	signature: string;
	docstring: string;
}

export interface FileEntry {
	name: string;
	path: string;
	isDir: boolean;
	size?: number;
}

/** browser-as-server: 브라우저 안 dartlab FastAPI 응답. Service Worker 가 진짜 HTTP Response 로 변환. */
export interface PyApiResponse {
	status: number;
	headers: Record<string, string>;
	body: string;
}

export interface RuntimeCapabilities {
	persistentWorkspace: boolean;
	interrupt: 'soft' | 'hard';
	memoryTransactions: 'experimental';
	packagePersistence?: 'workspace-manifest';
}

export interface CheckpointInfo {
	id: string;
	parentId: string | null;
	label: string;
	pageCount: number;
	changedPages: number;
	deltaBytes: number;
	baseBytes: number;
}

export interface ExecutionEngine {
	name: string;
	isReady: boolean;

	initialize(): Promise<void>;
	/** 사전 로딩: dartlab wheel 설치 + import 까지 미리(첫 셀 실행 대기 제거). 실패해도 치명적이지 않다. */
	warm?(): Promise<void>;
	/** browser-as-server: 같은 커널의 dartlab FastAPI 로 HTTP 요청 서빙(Service Worker relay). */
	serveApi?(req: { method: string; path: string; body?: string }): Promise<PyApiResponse>;
	attachWorkspace?(workspaceId: string): Promise<boolean>;
	restoreWorkspacePackages?(): Promise<void>;
	getRuntimeCapabilities?(): Promise<RuntimeCapabilities>;
	createCheckpoint?(label: string): Promise<CheckpointInfo>;
	restoreCheckpoint?(id: string): Promise<{ id: string; pagesWritten: number; bytesWritten: number }>;
	listCheckpoints?(): Promise<CheckpointInfo[]>;
	clearCheckpoints?(): Promise<void>;
	execute(code: string): Promise<CellOutput>;
	interrupt(): void;
	destroy(): void;

	getVariable(name: string): Promise<unknown>;
	getVariableNames(): Promise<string[]>;
	getVariablesWithInfo(): Promise<VariableInfo[]>;
	getCompletions(objName: string): Promise<CompletionItem[]>;
	installPackage(packageName: string): Promise<void>;
	getInstalledPackages(): Promise<PackageInfo[]>;
	getDocstring(name: string): Promise<DocResult | null>;

	updateWidgetValue(widgetId: string, value: unknown): Promise<void>;
	listFiles(path: string): Promise<FileEntry[]>;
	readFile(path: string): Promise<string>;
	writeFile(path: string, content: string): Promise<void>;
	mkdir(path: string): Promise<void>;
	removeFile(path: string): Promise<void>;
}
