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

export interface ExecutionEngine {
	name: string;
	isReady: boolean;

	initialize(): Promise<void>;
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
