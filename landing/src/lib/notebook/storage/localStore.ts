// 노트북 로컬 저장 = 브라우저 IndexedDB (서버 없음. dartlab landing 무서버 원칙).
// 단일 DB `dartlab-notebooks` · 단일 store `notebooks`(keyPath=id, value=Notebook 전체).
// 노트북 문서(셀·코드·출력)는 IndexedDB 에 영속되어 새로고침·재시작 후에도 남는다.
// 공유·이식은 파일 export/import(notebookFormat.ts)로.
import { browser } from '$app/environment';
import type { Notebook } from '../stores/notebookStore';

const DB_NAME = 'dartlab-notebooks';
const STORE = 'notebooks';
const VERSION = 1;

export interface NotebookSummary {
	id: string;
	title: string;
	description: string;
	updatedAt: string;
	cellCount: number;
}

let _dbPromise: Promise<IDBDatabase> | null = null;

function openDb(): Promise<IDBDatabase> {
	if (!browser) return Promise.reject(new Error('no browser'));
	if (_dbPromise) return _dbPromise;
	_dbPromise = new Promise((resolve, reject) => {
		const req = indexedDB.open(DB_NAME, VERSION);
		req.onupgradeneeded = () => {
			const db = req.result;
			if (!db.objectStoreNames.contains(STORE)) db.createObjectStore(STORE, { keyPath: 'id' });
		};
		req.onsuccess = () => resolve(req.result);
		req.onerror = () => reject(req.error);
	});
	return _dbPromise;
}

function store(db: IDBDatabase, mode: IDBTransactionMode): IDBObjectStore {
	return db.transaction(STORE, mode).objectStore(STORE);
}

export async function putNotebook(nb: Notebook): Promise<void> {
	if (!browser) return;
	const db = await openDb();
	// JSON round-trip 으로 IDB structured-clone 불가 값(Svelte $state proxy·함수 등)을 순수 데이터로 정규화.
	const record: Notebook = JSON.parse(
		JSON.stringify({ ...nb, metadata: { ...nb.metadata, updatedAt: new Date().toISOString() } })
	);
	await new Promise<void>((resolve, reject) => {
		const r = store(db, 'readwrite').put(record);
		r.onsuccess = () => resolve();
		r.onerror = () => reject(r.error);
	});
}

export async function getNotebook(id: string): Promise<Notebook | null> {
	if (!browser) return null;
	const db = await openDb();
	return new Promise((resolve, reject) => {
		const r = store(db, 'readonly').get(id);
		r.onsuccess = () => resolve((r.result as Notebook | undefined) ?? null);
		r.onerror = () => reject(r.error);
	});
}

export async function deleteNotebook(id: string): Promise<void> {
	if (!browser) return;
	const db = await openDb();
	await new Promise<void>((resolve, reject) => {
		const r = store(db, 'readwrite').delete(id);
		r.onsuccess = () => resolve();
		r.onerror = () => reject(r.error);
	});
}

export async function listNotebooks(): Promise<NotebookSummary[]> {
	if (!browser) return [];
	const db = await openDb();
	const all: Notebook[] = await new Promise((resolve, reject) => {
		const r = store(db, 'readonly').getAll();
		r.onsuccess = () => resolve((r.result as Notebook[]) ?? []);
		r.onerror = () => reject(r.error);
	});
	return all
		.map((nb) => ({
			id: nb.id,
			title: nb.title || 'Untitled',
			description: nb.description ?? '',
			updatedAt: nb.metadata?.updatedAt ?? '',
			cellCount: nb.cells?.length ?? 0
		}))
		.sort((a, b) => (a.updatedAt < b.updatedAt ? 1 : -1));
}
