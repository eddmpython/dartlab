// Per-bundle disclosureKey index · 절번호 drift(회사마다 같은 공시가 다른 절번호)로 같은
// sectionKey 가 없는 회사를 disclosureKey 로 전역 조회해 비교 누락을 막는다.

import type { PanelBundle, PanelRow } from '../types';

interface BundleIndex {
	byDisclosureKey: Map<string, PanelRow[]>; // dk → all rows across sections
}

const cache = new WeakMap<PanelBundle, BundleIndex>();

function buildIndex(b: PanelBundle): BundleIndex {
	const byDisclosureKey = new Map<string, PanelRow[]>();
	for (const rows of b.gridBySection.values()) {
		for (const r of rows) {
			if (!r.disclosureKey) continue;
			let d = byDisclosureKey.get(r.disclosureKey);
			if (!d) byDisclosureKey.set(r.disclosureKey, (d = []));
			d.push(r);
		}
	}
	return { byDisclosureKey };
}

export function bundleIndex(b: PanelBundle): BundleIndex {
	let idx = cache.get(b);
	if (!idx) cache.set(b, (idx = buildIndex(b)));
	return idx;
}
