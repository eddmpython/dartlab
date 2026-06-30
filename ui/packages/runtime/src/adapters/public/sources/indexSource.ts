// IndexPort public 조립 · KR(gov/indices 직독) + US(FRED) 라우팅 단일 분기.
// gov·fred 모두 HF 공개 데이터 브라우저 직독(백엔드 0)이라 local 셸도 그대로 재사용(createLocalRuntime).
import type { Candle, IndexPort, IndexRef } from '@dartlab/ui-contracts';
import { KR_INDEX_PRESETS, US_INDEX_PRESETS } from '@dartlab/ui-contracts';
import { loadGovIndexCandles, scanGovIndexNames, loadGovIndexUniverse } from './govIndexSource';
import { loadFredIndexCandles, searchUsIndexPresets } from './fredIndexSource';
import type { DataCore } from '../../../data/fetch/request';

// core 는 어댑터(createXRuntime)가 주입(전역 싱글턴 금지). 미주입(ui/web 레거시 직접 호출)이면 gov/fred 소스의
// 모듈 폴백 코어를 쓴다 · core 를 그대로 하위 소스에 흘려 보낸다(undefined 면 각 소스가 폴백 코어 선택).
export function createPublicIndexPort(core?: DataCore): IndexPort {
	return {
		async catalog(): Promise<IndexRef[]> {
			// 전체 카탈로그 · KR gov 전 지수(universe, 165종) + US preset. picker select 가 시장군 그룹으로 브라우징.
			// universe 로드 실패(404·오프라인) 시 큐레이트 presets 로 폴백(빈 select 방지).
			const kr = await loadGovIndexUniverse(core);
			return [...(kr.length ? kr : KR_INDEX_PRESETS), ...US_INDEX_PRESETS];
		},
		async search(query: string, limit = 12): Promise<IndexRef[]> {
			const q = query.trim();
			if (!q) return [];
			const us = searchUsIndexPresets(q); // US preset 4종 라벨/ID 매칭(확장 0)
			const kr = await scanGovIndexNames(q, Math.max(0, limit - us.length), core); // 잔여 한도만 KR 에(이중 limit 압착 방지)
			return [...us, ...kr].slice(0, limit);
		},
		series(ref: IndexRef): Promise<Candle[] | null> {
			return ref.market === 'US' ? loadFredIndexCandles(ref, core) : loadGovIndexCandles(ref, core); // 분기 단일 지점
		}
	};
}
