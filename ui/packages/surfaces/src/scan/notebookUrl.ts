/**
 * SQL Notebook URL share · `?nb=base64(cells)` encode/decode.
 */

import type { NotebookCell } from './notebookStore';

interface UrlPayload {
	v: 1;
	name?: string;
	cells: NotebookCell[];
}

function b64encode(s: string): string {
	if (typeof window === 'undefined') return '';
	return window.btoa(unescape(encodeURIComponent(s)));
}

function b64decode(s: string): string {
	if (typeof window === 'undefined') return '';
	return decodeURIComponent(escape(window.atob(s)));
}

export function encodeNotebook(cells: NotebookCell[], name?: string): string {
	const payload: UrlPayload = { v: 1, name, cells };
	return b64encode(JSON.stringify(payload));
}

export function decodeNotebook(b64: string): UrlPayload | null {
	if (!b64) return null;
	try {
		const obj = JSON.parse(b64decode(b64));
		if (!obj || obj.v !== 1 || !Array.isArray(obj.cells)) return null;
		const cells: NotebookCell[] = obj.cells.filter(
			(c: any) =>
				c &&
				typeof c.id === 'string' &&
				(c.type === 'sql' || c.type === 'md') &&
				typeof c.code === 'string'
		);
		return {
			v: 1,
			name: typeof obj.name === 'string' ? obj.name : undefined,
			cells
		};
	} catch (err) {
		console.warn('[scan/notebook-url] decode 실패', err);
		return null;
	}
}

/** 현재 page URL 에 ?nb= 추가한 share link. */
export function buildShareUrl(cells: NotebookCell[], name?: string): string {
	if (typeof window === 'undefined') return '';
	const url = new URL(window.location.href);
	url.searchParams.set('nb', encodeNotebook(cells, name));
	url.searchParams.set('explore', '1');
	url.searchParams.delete('q');
	url.searchParams.delete('preset');
	return url.toString();
}
