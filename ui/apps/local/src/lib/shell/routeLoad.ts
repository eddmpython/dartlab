// 로컬 터미널 RawData 조립(createEngine 씨드) — 셸 글루.
// 랜딩(공표) 터미널과 동일한 전체 시장 데이터셋 8종(전 종목 finance·prices·eco·macro·quarters·search-index·
// meta·industryStats)을 로드한다 — loadJson 의 publicJsonPolicy 가 퍼블릭과 동일한 HF-first 정책을 적용하므로 로컬도
// 같은 공유 자산을 받는다. 그 결과 스크리너·생태계맵·매크로 오버레이·동종비교·전종목 검색이 랜딩과 동일하게
// 동작한다(옛 단일회사 빈 씨드는 이 시장 기능을 전부 죽였다 — 로컬 터미널이 랜딩과 "달라" 보이던 근본 원인).
// 회사 단위 실시간 상세(차트 캔들·패널 격자·AI)는 /api 포트가, 시장 씨드는 HF 가 공급 — 각자 단일 경로
// (정책 외 silent fallback 없음). 로컬앱의 정적 사본 부재도 registry 의 HF-first 순서에서 일관되게 처리된다.
import { getLocalRuntime } from '$lib/runtime/localRuntime';
import { loadJson } from '@dartlab/ui-runtime/data/dartlabData';
import {
	warmCompany,
	type FinanceFile,
	type MacroFile,
	type MetaFile,
	type PricesFile,
	type IndexRow,
	type EcosystemFile,
	type QuartersFile,
	type IndustryStatsFile,
	type RawData
} from '@dartlab/ui-surfaces/terminal';

export async function loadTerminalRaw(
	code: string,
	fetchFn: typeof fetch
): Promise<{ raw: RawData; code: string }> {
	// 현재 종목 주가·재무 조기 워밍 — /api price 포트 + HF finance 포트 (씨드 로드와 병렬, in-flight dedup).
	warmCompany(getLocalRuntime(), code);

	const [finance, macro, meta, prices, index, eco, quarters, industryStats] = await Promise.all([
		loadJson<FinanceFile>('dashboards/finance.json', { fetchFn }),
		loadJson<MacroFile>('dashboards/macro.json', { fetchFn }),
		loadJson<MetaFile>('dashboards/meta.json', { fetchFn }),
		loadJson<PricesFile>('map/prices-snapshot.json', { fetchFn }),
		loadJson<IndexRow[]>('map/search-index.json', { fetchFn }),
		loadJson<EcosystemFile>('map/ecosystem.json', { fetchFn }),
		loadJson<QuartersFile>('dashboards/quarters.json', { fetchFn }),
		loadJson<IndustryStatsFile>('map/industryStats.json', { fetchFn })
	]);

	return {
		code,
		raw: {
			finance: finance ?? { years: [], companies: {} },
			macro: macro ?? null,
			meta: meta ?? null,
			prices: prices ?? { data: {} },
			index: index ?? [],
			eco: eco ?? null,
			quarters: quarters ?? null,
			industryStats: industryStats ?? null
		} as RawData
	};
}
