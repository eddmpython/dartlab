// 브라우저: HF panel parquet 하나 직접 read → PanelBundle (와이드 빌드 0, 온더플라이).
// 순수 코어 `buildPanelBundle`(panelWide.ts)와 분리 · IO 만 담당(테스트는 코어 단독).

import { readParquetRows } from '@dartlab/ui-runtime/data/parquet/hfRange';
import { marketForCode } from './dartUrl';
import { buildPanelBundle } from './panelWide';
import type { LeafRow, PanelBundle } from './types';
import noteTaxonomy from './noteTaxonomy.json';

export const READ_COLUMNS = [
	'chapter', 'sectionLeaf', 'sectionPath', 'blockLeaf', 'leafType',
	'disclosureKey', 'xbrlClass', 'blockOrder', 'contentRaw', 'period', 'rceptNo'
];

// 번들 LRU 캐시 · 한 번 읽은 회사는 재다운로드·재파싱 0(비교 추가/빼기·회사 재방문 즉시).
// promise 를 캐시해 동시 호출 중복 제거. 실패하면 무효화(재시도 가능). panel 은 정적이라 staleness 없음.
// 비교 최대 6사 + 최근 방문 여유 → 8. 번들이 커서(수 MB) 무한 보관은 메모리 부담이라 LRU 로 경계.
const BUNDLE_CACHE_MAX = 8;
const bundleCache = new Map<string, Promise<PanelBundle>>();

export function loadPanelBundle(code: string, opts: { corpName?: string } = {}): Promise<PanelBundle> {
	const hit = bundleCache.get(code);
	if (hit) {
		bundleCache.delete(code); // LRU: 최근 사용으로 끌어올림
		bundleCache.set(code, hit);
		return hit;
	}
	const base = marketForCode(code) === 'US' ? 'edgar' : 'dart';
	const path = `${base}/panel/${code}.parquet`;
	const p = readParquetRows(path, { columns: READ_COLUMNS }).then(({ rows }) =>
		buildPanelBundle(rows as unknown as LeafRow[], {
			code,
			corpName: opts.corpName,
			noteTaxonomy: noteTaxonomy as Record<string, string>
		})
	);
	bundleCache.set(code, p);
	if (bundleCache.size > BUNDLE_CACHE_MAX) {
		const oldest = bundleCache.keys().next().value;
		if (oldest !== undefined) bundleCache.delete(oldest);
	}
	// 실패 시 캐시에서 제거 · 다음 호출이 재시도하도록.
	void p.catch(() => {
		if (bundleCache.get(code) === p) bundleCache.delete(code);
	});
	return p;
}
