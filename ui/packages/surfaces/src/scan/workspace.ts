/**
 * Scan Studio 사용자 컬럼셋 LocalStorage CRUD.
 *
 * 12 컬럼셋 cap, 가장 오래된 것부터 evict. 각 컬럼셋은 cols + filters + sort 보존.
 */

import type { SavedColumnSet } from './types';

const STORAGE_KEY = 'dartlab.scan.workspace.v1';
const MAX_SETS = 12;

function read(): SavedColumnSet[] {
	if (typeof window === 'undefined' || !window.localStorage) return [];
	try {
		const raw = window.localStorage.getItem(STORAGE_KEY);
		if (!raw) return [];
		const parsed = JSON.parse(raw);
		if (!Array.isArray(parsed)) return [];
		return parsed.filter(
			(s) =>
				s && typeof s.id === 'string' && typeof s.name === 'string' && Array.isArray(s.cols)
		);
	} catch {
		return [];
	}
}

function write(sets: SavedColumnSet[]): void {
	if (typeof window === 'undefined' || !window.localStorage) return;
	try {
		window.localStorage.setItem(STORAGE_KEY, JSON.stringify(sets));
	} catch (err) {
		console.warn('[scan] workspace LocalStorage 저장 실패', err);
	}
}

export function listColumnSets(): SavedColumnSet[] {
	return read().sort((a, b) => b.createdAt - a.createdAt);
}

export function saveColumnSet(set: Omit<SavedColumnSet, 'id' | 'createdAt'>): SavedColumnSet {
	const sets = read();
	const now = Date.now();
	const newSet: SavedColumnSet = {
		id: `cs_${now}_${Math.random().toString(36).slice(2, 7)}`,
		createdAt: now,
		...set
	};
	sets.push(newSet);
	// 최대 cap · 가장 오래된 것 evict
	while (sets.length > MAX_SETS) {
		sets.sort((a, b) => a.createdAt - b.createdAt);
		sets.shift();
	}
	write(sets);
	return newSet;
}

export function removeColumnSet(id: string): void {
	const sets = read().filter((s) => s.id !== id);
	write(sets);
}

export function renameColumnSet(id: string, name: string): void {
	const sets = read();
	const t = sets.find((s) => s.id === id);
	if (t) {
		t.name = name;
		write(sets);
	}
}
