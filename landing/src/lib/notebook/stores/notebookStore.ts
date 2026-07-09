import { writable, derived, get } from 'svelte/store';
import { putNotebook } from '../storage/localStore';

export interface CellOutput {
	type: 'text' | 'html' | 'image' | 'error' | 'dataframe' | 'widget';
	data: string;
	executedAt: string;
}

// 셀은 코드와 마크다운 둘뿐이다. 옛 `guide`·`study` 타입은 서버가 있는 다른 학습 플랫폼에서
// 옮겨온 잔재였다. 렌더러(GuideCell·StudyCell)가 없어 화면에 그려지지 않았고, 진행 저장은
// 존재하지 않는 `/api/notebook/save` 를 불렀다(landing 은 adapter-static 무서버). 전부 제거했다.
export interface Cell {
	id: string;
	type: 'code' | 'markdown';
	content: string;
	output?: CellOutput;
	executionCount?: number;
	executionTime?: number;
}

export interface WorkspaceFile {
	path: string;
	content: string;
	isDir: boolean;
}

export interface Notebook {
	id: string;
	title: string;
	description?: string;
	cells: Cell[];
	workspaceFiles?: WorkspaceFile[];
	metadata: {
		category?: string;
		contentId?: string;
		notebookFilePath?: string;
		layout?: string;
		createdAt: string;
		updatedAt: string;
	};
}

function generateId(): string {
	return crypto.randomUUID();
}

function createEmptyNotebook(): Notebook {
	return {
		id: generateId(),
		title: 'Untitled',
		cells: [{ id: generateId(), type: 'code', content: '' }],
		metadata: {
			createdAt: new Date().toISOString(),
			updatedAt: new Date().toISOString()
		}
	};
}

export type CellWidth = 'compact' | 'medium' | 'full';

const VALID_WIDTHS: CellWidth[] = ['compact', 'medium', 'full'];

function readLocalStorage<T extends string>(key: string, validValues: T[], fallback: T): T {
	if (typeof localStorage === 'undefined') return fallback;
	const raw = localStorage.getItem(key);
	if (raw && (validValues as string[]).includes(raw)) return raw as T;
	return fallback;
}

export const notebook = writable<Notebook>(createEmptyNotebook());
export const activeCellId = writable<string | null>(null);
export const editMode = writable<boolean>(true);
export const cellWidth = writable<CellWidth>(readLocalStorage('chaniCellWidth', VALID_WIDTHS, 'medium'));

export const cellCount = derived(notebook, ($nb) => $nb.cells.length);
export const executionCounter = writable<number>(0);

export const cellOutputs = writable<Map<string, CellOutput>>(new Map());
export const cellErrors = writable<Map<string, string[]>>(new Map());

export function setCellErrors(errors: Map<string, string[]>): void {
	cellErrors.set(errors);
}

export function getCellOutput(cellId: string): CellOutput | undefined {
	return get(cellOutputs).get(cellId);
}

export function setCellOutput(cellId: string, output: CellOutput): void {
	cellOutputs.update((map) => {
		const next = new Map(map);
		next.set(cellId, output);
		return next;
	});
}

export function clearCellOutput(cellId: string): void {
	cellOutputs.update((map) => {
		if (!map.has(cellId)) return map;
		const next = new Map(map);
		next.delete(cellId);
		return next;
	});
}

export function clearAllCellOutputs(): void {
	cellOutputs.set(new Map());
}

let saveDebounceTimer: ReturnType<typeof setTimeout> | null = null;

export async function loadFromStorage(): Promise<boolean> {
	// 개별 노트북 로딩은 라우트(/notebooks/[id])가 localStore.getNotebook + loadNotebook 으로 처리.
	// 이 훅은 initialNotebook 이 없는 경우의 폴백일 뿐이라 no-op(빈 노트북 유지).
	return false;
}

function buildSavePayload(): Notebook {
	const nb = get(notebook);
	const outputs = get(cellOutputs);
	const cells = nb.cells.map((c) => {
		const output = outputs.get(c.id);
		return output ? { ...c, output } : c;
	});
	return {
		...nb,
		cells,
		metadata: { ...nb.metadata, updatedAt: new Date().toISOString() }
	};
}

export function saveToStorage(): void {
	// 자동저장 = 디바운스 후 IndexedDB put (서버 없음). 셀 편집·실행마다 호출됨.
	if (saveDebounceTimer) clearTimeout(saveDebounceTimer);
	saveDebounceTimer = setTimeout(() => {
		void putNotebook(buildSavePayload());
	}, 800);
}

export async function saveToServer(): Promise<{ ok: boolean; cloud: boolean }> {
	// Ctrl+S = 즉시 IndexedDB 저장 (클라우드 없음).
	if (saveDebounceTimer) clearTimeout(saveDebounceTimer);
	await putNotebook(buildSavePayload());
	return { ok: true, cloud: false };
}

export function setTitle(title: string): void {
	notebook.update((nb) => ({ ...nb, title }));
	saveToStorage();
}

export function setDescription(description: string): void {
	notebook.update((nb) => ({ ...nb, description }));
	saveToStorage();
}

export function addCell(type: Cell['type'], afterId?: string, beforeId?: string): string {
	const newCell: Cell = { id: generateId(), type, content: '' };

	notebook.update((nb) => {
		const cells = [...nb.cells];
		if (beforeId) {
			const idx = cells.findIndex((c) => c.id === beforeId);
			if (idx >= 0) {
				cells.splice(idx, 0, newCell);
			} else {
				cells.push(newCell);
			}
		} else if (afterId) {
			const idx = cells.findIndex((c) => c.id === afterId);
			if (idx >= 0) {
				cells.splice(idx + 1, 0, newCell);
			} else {
				cells.push(newCell);
			}
		} else {
			cells.push(newCell);
		}
		return { ...nb, cells };
	});

	activeCellId.set(newCell.id);
	saveToStorage();
	return newCell.id;
}

export function removeCell(cellId: string): void {
	let adjacentId: string | null = null;

	notebook.update((nb) => {
		if (nb.cells.length <= 1) return nb;
		const idx = nb.cells.findIndex((c) => c.id === cellId);
		if (idx >= 0) {
			const cells = nb.cells.filter((c) => c.id !== cellId);
			adjacentId = cells[Math.min(idx, cells.length - 1)]?.id ?? null;
			return { ...nb, cells };
		}
		return nb;
	});

	clearCellOutput(cellId);

	if (get(activeCellId) === cellId && adjacentId) {
		activeCellId.set(adjacentId);
	}
	saveToStorage();
}

export function updateCellContent(cellId: string, content: string): void {
	notebook.update((nb) => ({
		...nb,
		cells: nb.cells.map((c) => (c.id === cellId ? { ...c, content } : c))
	}));
	saveToStorage();
}

export function updateCellOutput(cellId: string, output: CellOutput): void {
	setCellOutput(cellId, output);
	saveToStorage();
}

export interface CellExecutionResult {
	output: CellOutput;
	executionCount: number;
	executionTime: number;
}

export function applyCellExecutionResult(cellId: string, result: CellExecutionResult): void {
	setCellOutput(cellId, result.output);
	notebook.update((nb) => ({
		...nb,
		cells: nb.cells.map((c) =>
			c.id === cellId
				? { ...c, executionCount: result.executionCount, executionTime: result.executionTime }
				: c
		)
	}));
	saveToStorage();
}

export function nextExecutionCount(): number {
	let count = 0;
	executionCounter.update((n) => {
		count = n + 1;
		return count;
	});
	return count;
}

export function updateCellExecutionCount(cellId: string, count: number): void {
	notebook.update((nb) => ({
		...nb,
		cells: nb.cells.map((c) => (c.id === cellId ? { ...c, executionCount: count } : c))
	}));
}

export function updateCellExecutionTime(cellId: string, timeMs: number): void {
	notebook.update((nb) => ({
		...nb,
		cells: nb.cells.map((c) => (c.id === cellId ? { ...c, executionTime: timeMs } : c))
	}));
}

export function moveCell(cellId: string, direction: 'up' | 'down'): void {
	notebook.update((nb) => {
		const cells = [...nb.cells];
		const idx = cells.findIndex((c) => c.id === cellId);
		if (idx < 0) return nb;

		const targetIdx = direction === 'up' ? idx - 1 : idx + 1;
		if (targetIdx < 0 || targetIdx >= cells.length) return nb;

		[cells[idx], cells[targetIdx]] = [cells[targetIdx], cells[idx]];
		return { ...nb, cells };
	});
	saveToStorage();
}

export function changeCellType(cellId: string, newType: Cell['type']): void {
	notebook.update((nb) => ({
		...nb,
		cells: nb.cells.map((c) => (c.id === cellId ? { ...c, type: newType } : c))
	}));
	saveToStorage();
}

export function focusNextCell(currentId: string): void {
	const nb = get(notebook);
	const idx = nb.cells.findIndex((c) => c.id === currentId);
	if (idx < nb.cells.length - 1) {
		activeCellId.set(nb.cells[idx + 1].id);
	} else {
		addCell('code', currentId);
	}
}

export function focusPrevCell(currentId: string): void {
	const nb = get(notebook);
	const idx = nb.cells.findIndex((c) => c.id === currentId);
	if (idx > 0) {
		activeCellId.set(nb.cells[idx - 1].id);
	}
}

export function loadNotebook(data: Notebook): void {
	const outputMap = new Map<string, CellOutput>();
	for (const cell of data.cells) {
		if (cell.output) {
			outputMap.set(cell.id, cell.output);
		}
	}
	const cleanCells = data.cells.map(({ output: _o, ...rest }) => rest as Cell);
	notebook.set({ ...data, cells: cleanCells });
	cellOutputs.set(outputMap);

	if (data.cells.length > 0) {
		activeCellId.set(data.cells[0].id);
	}
	saveToStorage();
}

export function resetNotebook(): void {
	const nb = createEmptyNotebook();
	clearAllCellOutputs();
	notebook.set(nb);
	activeCellId.set(nb.cells[0].id);
	saveToStorage();
}

export function setCellWidth(width: CellWidth): void {
	cellWidth.set(width);
	if (typeof localStorage !== 'undefined') {
		localStorage.setItem('chaniCellWidth', width);
	}
}
