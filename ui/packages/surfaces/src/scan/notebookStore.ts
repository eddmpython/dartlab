/**
 * SQL Notebook LocalStorage CRUD · 사용자 다중 노트북 저장.
 */

export interface NotebookCell {
	id: string;
	type: 'sql' | 'md';
	code: string;
}

export interface SavedNotebook {
	id: string;
	name: string;
	cells: NotebookCell[];
	createdAt: number;
	updatedAt: number;
}

const STORAGE_KEY = 'dartlab.scan.notebooks.v1';
const MAX_NOTEBOOKS = 20;

function read(): SavedNotebook[] {
	if (typeof window === 'undefined' || !window.localStorage) return [];
	try {
		const raw = window.localStorage.getItem(STORAGE_KEY);
		if (!raw) return [];
		const parsed = JSON.parse(raw);
		if (!Array.isArray(parsed)) return [];
		return parsed.filter(
			(n) => n && typeof n.id === 'string' && typeof n.name === 'string' && Array.isArray(n.cells)
		);
	} catch {
		return [];
	}
}

function write(list: SavedNotebook[]): void {
	if (typeof window === 'undefined' || !window.localStorage) return;
	try {
		window.localStorage.setItem(STORAGE_KEY, JSON.stringify(list));
	} catch (err) {
		console.warn('[scan/notebook] LocalStorage 저장 실패', err);
	}
}

/** 모든 notebook list (최신 updated 순). */
export function listNotebooks(): SavedNotebook[] {
	return read().sort((a, b) => b.updatedAt - a.updatedAt);
}

/** 새 notebook 저장 (또는 같은 id 면 update). */
export function saveNotebook(
	input: Omit<SavedNotebook, 'id' | 'createdAt' | 'updatedAt'> & { id?: string }
): SavedNotebook {
	const list = read();
	const now = Date.now();
	const existingIdx = input.id ? list.findIndex((n) => n.id === input.id) : -1;
	if (existingIdx >= 0) {
		const updated: SavedNotebook = {
			...list[existingIdx],
			name: input.name,
			cells: input.cells,
			updatedAt: now
		};
		list[existingIdx] = updated;
		write(list);
		return updated;
	}
	const created: SavedNotebook = {
		id: input.id ?? `nb_${now}_${Math.random().toString(36).slice(2, 7)}`,
		name: input.name,
		cells: input.cells,
		createdAt: now,
		updatedAt: now
	};
	list.push(created);
	while (list.length > MAX_NOTEBOOKS) {
		list.sort((a, b) => a.updatedAt - b.updatedAt);
		list.shift();
	}
	write(list);
	return created;
}

export function getNotebook(id: string): SavedNotebook | null {
	return read().find((n) => n.id === id) ?? null;
}

export function deleteNotebook(id: string): void {
	write(read().filter((n) => n.id !== id));
}

export function renameNotebook(id: string, name: string): void {
	const list = read();
	const t = list.find((n) => n.id === id);
	if (t) {
		t.name = name;
		t.updatedAt = Date.now();
		write(list);
	}
}
