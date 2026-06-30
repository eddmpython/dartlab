// alignNotes · 옛 split 주석행(null key) → (scope,정규화제목) 표준 NT_ 정렬 (회사 own 뼈대 우선, 전역 fallback).
// Python read.alignNotes 1:1.

import { NOTE_TITLE_NORM } from '../keys';
import type { LeafRow } from '../types';

const SUFFIX_CAP = /[--―]\s*(연결|별도)\s*$/; // native 접미사 scope
const SUFFIX_STRIP = /\s*[--―]\s*(연결|별도)\s*$/; // 접미사 제거

export function alignNotes(rows: LeafRow[], noteTaxonomy: Record<string, string>): void {
	const meta = rows.map((r) => {
		const bl = r.blockLeaf ?? '';
		const m = bl.match(SUFFIX_CAP);
		const suf = m ? m[1] : null;
		const bare = bl.replace(SUFFIX_STRIP, '');
		const secMark = (r.chapter ?? '') + (r.sectionLeaf ?? '');
		const scope = suf === '연결' ? 'consolidated' : suf === '별도' ? 'standalone' : secMark.includes('연결') ? 'consolidated' : 'standalone';
		const title = bare.replace(NOTE_TITLE_NORM, '');
		return { key: scope + '|' + title, titleLen: [...title].length, isNote: (r.sectionLeaf ?? '').includes('주석') };
	});
	// 자기 native NT_ 주석 뼈대 · ownStd(_U 제외 표준) + own(전체, fallback). 첫 등장 우선.
	const ownStd = new Map<string, string>();
	const own = new Map<string, string>();
	for (let i = 0; i < rows.length; i++) {
		const dk = rows[i].disclosureKey;
		if (dk == null || !dk.startsWith('NT_') || meta[i].titleLen <= 1) continue;
		const k = meta[i].key;
		if (!own.has(k)) own.set(k, dk);
		if (!dk.includes('_U') && !ownStd.has(k)) ownStd.set(k, dk);
	}
	// 부여 · Python when/then 순서: 주석&표준 → 표준 / 기존키 보존 / 주석&own / 주석&전역.
	for (let i = 0; i < rows.length; i++) {
		const r = rows[i];
		const { key, isNote } = meta[i];
		if (isNote && ownStd.has(key)) r.disclosureKey = ownStd.get(key)!;
		else if (r.disclosureKey != null) continue;
		else if (isNote && own.has(key)) r.disclosureKey = own.get(key)!;
		else if (isNote && noteTaxonomy[key] != null) r.disclosureKey = noteTaxonomy[key];
	}
}
