import { get } from 'svelte/store';
import { currentUser } from './userStore';
import type { Notebook } from './notebookStore';

export async function cloudSave(notebookData: Notebook): Promise<boolean> {
	if (!get(currentUser)) return false;
	try {
		const res = await fetch('/api/notebook/save', {
			method: 'POST',
			headers: { 'Content-Type': 'application/json' },
			credentials: 'include',
			body: JSON.stringify(notebookData),
		});
		if (!res.ok) return false;
		const data = await res.json();
		return data.ok === true || data.cloud === true;
	} catch {
		return false;
	}
}

export async function cloudLoad(notebookId: string): Promise<Notebook | null> {
	if (!get(currentUser)) return null;
	try {
		const res = await fetch(`/api/notebook/${notebookId}`, {
			credentials: 'include',
		});
		if (!res.ok) return null;
		const data = await res.json();
		if (data.error) return null;
		return data as Notebook;
	} catch {
		return null;
	}
}

export async function cloudList(): Promise<{ id: string; title: string; cellCount: number; updatedAt: string }[]> {
	if (!get(currentUser)) return [];
	try {
		const res = await fetch('/api/notebook/list', {
			credentials: 'include',
		});
		if (!res.ok) return [];
		return await res.json();
	} catch {
		return [];
	}
}

export async function cloudDelete(notebookId: string): Promise<boolean> {
	if (!get(currentUser)) return false;
	try {
		const res = await fetch(`/api/notebook/${notebookId}`, {
			method: 'DELETE',
			credentials: 'include',
		});
		if (!res.ok) return false;
		const data = await res.json();
		return data.ok === true;
	} catch {
		return false;
	}
}
