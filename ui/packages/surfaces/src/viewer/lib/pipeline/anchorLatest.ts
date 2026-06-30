// anchorLatest · scope era-안정 + keyed 라벨 최신통일 (narrative 보존). Python read.anchorLatest 1:1.

import { SEP } from '../keys';
import type { LeafRow } from '../types';
import { scopeOf } from './scope';

export function anchorLatest(rows: LeafRow[]): void {
	// scope 부착.
	for (const r of rows) (r as LeafRow & { scope: string }).scope = scopeOf(r.xbrlClass);
	const anchorKey = (r: LeafRow) => r.disclosureKey ?? r.xbrlClass;

	// scope era-안정 · anchorKey & xbrlClass 보유 행의 최신 period scope 를 같은 anchorKey 전 era 에 전파.
	const scopeByAnchor = new Map<string, { period: string; scope: string }>();
	for (const r of rows) {
		const ak = anchorKey(r);
		if (ak == null || r.xbrlClass == null) continue;
		const cur = scopeByAnchor.get(ak);
		const p = r.period ?? '';
		if (!cur || p > cur.period) scopeByAnchor.set(ak, { period: p, scope: scopeOf(r.xbrlClass) });
	}
	for (const r of rows) {
		const ak = anchorKey(r);
		if (ak != null) {
			const s = scopeByAnchor.get(ak);
			if (s) (r as LeafRow & { scope: string }).scope = s.scope;
		}
	}

	// keyed 라벨 통일 · (anchorKey, scope) 최신 period 라벨. 같은 period 면 (첨부) 먼저 → canonical 채택.
	type Label = { chapter: string | null; sectionLeaf: string | null; blockLeaf: string | null };
	const labelByGroup = new Map<string, { period: string; attach: boolean; label: Label }>();
	for (const r of rows) {
		const ak = anchorKey(r);
		if (ak == null) continue;
		const scope = (r as LeafRow & { scope: string }).scope;
		const gk = ak + SEP + scope;
		const p = r.period ?? '';
		const attach = (r.chapter ?? '').includes('(첨부)');
		const cur = labelByGroup.get(gk);
		// sort period asc + attach 먼저(desc) → last = (최신 period, 비첨부). 즉 최신 우선, 동 period 면 비첨부.
		const better = !cur || p > cur.period || (p === cur.period && cur.attach && !attach);
		if (better) labelByGroup.set(gk, { period: p, attach, label: { chapter: r.chapter, sectionLeaf: r.sectionLeaf, blockLeaf: r.blockLeaf } });
	}
	for (const r of rows) {
		const ak = anchorKey(r);
		if (ak == null) continue;
		const scope = (r as LeafRow & { scope: string }).scope;
		const g = labelByGroup.get(ak + SEP + scope);
		if (g) {
			if (g.label.chapter != null) r.chapter = g.label.chapter;
			if (g.label.sectionLeaf != null) r.sectionLeaf = g.label.sectionLeaf;
			if (g.label.blockLeaf != null) r.blockLeaf = g.label.blockLeaf;
		}
	}
}
