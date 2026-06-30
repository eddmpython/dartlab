// dedupKeyed · keyed 행 (disclosureKey,scope,leafType,period) 당 1개 (xbrlClass 있음·긴 본문 우선).
// Python mapper.dedupKeyed 1:1. narrative(null key)는 보존.

import { SEP, scopeOf } from '../keys';
import type { LeafRow } from '../types';

export function dedupKeyed(rows: LeafRow[]): LeafRow[] {
	const seen = new Map<string, LeafRow>();
	const out: LeafRow[] = [];
	for (const r of rows) {
		if (r.disclosureKey == null) {
			out.push(r); // narrative 보존
			continue;
		}
		const scope = scopeOf(r.xbrlClass);
		const k = [r.disclosureKey, scope, r.leafType ?? '', r.period ?? ''].join(SEP);
		const prev = seen.get(k);
		if (!prev) {
			seen.set(k, r);
			out.push(r);
			continue;
		}
		// 우선: xbrlClass 있음 > 없음, 그다음 본문 길이.
		const score = (x: LeafRow) => [x.xbrlClass != null ? 1 : 0, (x.contentRaw ?? '').length];
		const [pa, pb] = score(prev);
		const [ca, cb] = score(r);
		if (ca > pa || (ca === pa && cb > pb)) {
			const idx = out.indexOf(prev);
			if (idx >= 0) out[idx] = r;
			seen.set(k, r);
		}
	}
	return out;
}
