// /terminal(본진) · /lab/terminal-dev(격리 개발) 공용 라우트 로더 SSOT · 복사 드리프트 차단.
// landing 셸 글루: getPublicRuntime(컴포지션 루트)·$app 의존이라 surface 패키지로 못 옮긴다 (단계-4b).
// 씨데이터 JSON 7종 병렬 로드 + 마지막 본 종목 워밍업(주가·재무·제품맵 · public runtime 포트 경유).
import { browser } from '$app/environment';
import { base } from '$app/paths';
import { loadJson, setStaticBase } from '@dartlab/ui-runtime/data/dartlabData';
import { getPublicRuntime } from '$lib/runtime/publicRuntime';
import {
	LAST_SYM_KEY,
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

// base 주입은 모듈 평가 시점에 강제한다. +layout.svelte 보다 +page.ts load 가 먼저 실행돼도
// registry 가 HF 장애 시 선택하는 GitHub Pages 정적 폴백 경로가 base 를 지켜야 한다.
setStaticBase(base);

export async function loadTerminalRaw(fetchFn: typeof fetch): Promise<{ raw: RawData }> {
	// 일별시세 조기 워밍 · 마지막 본 종목(없으면 기본 005930)의 주가·재무를 씨데이터 JSON 로드와
	// 병렬로 시작 (in-flight dedup 이라 패널 호출과 중복 fetch 0). 차트 첫 페인트 ~2s 단축.
	if (browser) {
		const last = localStorage.getItem(LAST_SYM_KEY) || '005930';
		warmCompany(getPublicRuntime(), last);
	}
	const opt = { fetchFn };
	const [finance, macro, meta, prices, index, eco, quarters, industryStats, financeUs, pricesUs, searchUs] =
		await Promise.all([
			loadJson<FinanceFile>('dashboards/finance.json', opt),
			loadJson<MacroFile>('dashboards/macro.json', opt),
			loadJson<MetaFile>('dashboards/meta.json', opt),
			loadJson<PricesFile>('map/prices-snapshot.json', opt),
			loadJson<IndexRow[]>('map/search-index.json', opt),
			loadJson<EcosystemFile>('map/ecosystem.json', opt),
			loadJson<QuartersFile>('dashboards/quarters.json', opt),
			// 업종 분포 밴드 · map 이 쓰던 자산(p10~p90), 스캔등급 다이얼로그 분포 컨텍스트용. 정적 동결 OK(일배치 무관).
			loadJson<IndustryStatsFile>('map/industryStats.json', opt),
			// ── US(EDGAR) 번들 · 별도 산출물(finance=companyfacts·prices=gather·search=tickers)을 같은
			// raw 위에 추가 병합(KR 무영향). currency='USD' 태그로 엔진/표시가 통화 분기. 없으면 빈값(KR-only). ──
			loadJson<FinanceFile>('dashboards/finance-us.json', opt),
			loadJson<PricesFile>('map/prices-snapshot-us.json', opt),
			loadJson<IndexRow[]>('map/search-index-us.json', opt)
		]);
	// US 회사를 KR 생태계 raw 에 합류 · buildCompany 는 finance+prices 가 있어야 co 를 만든다(둘 다 병합).
	const mergedFinance: FinanceFile = finance
		? { ...finance, companies: { ...finance.companies, ...(financeUs?.companies ?? {}) } }
		: (financeUs ?? { years: [], companies: {} });
	const mergedPrices: PricesFile = prices
		? { ...prices, data: { ...prices.data, ...(pricesUs?.data ?? {}) } }
		: (pricesUs ?? { data: {} });
	const mergedIndex: IndexRow[] = [...(index ?? []), ...(searchUs ?? [])];
	return {
		raw: {
			finance: mergedFinance,
			macro: macro ?? null,
			meta: meta ?? null,
			prices: mergedPrices,
			index: mergedIndex,
			eco: eco ?? null,
			quarters: quarters ?? null,
			industryStats: industryStats ?? null
		} as RawData
	};
}
