<script lang="ts">
	import { onMount } from 'svelte';
	import type {
		UniverseCatalogCoverage,
		UniverseCatalogMarket,
		UniverseConformanceObservation,
		UniverseEntityProfile,
		UniverseEntitySearchRequest,
		UniverseEntitySearchResult,
		UniverseGlobalEntity,
		UniversePairComparison
	} from '@dartlab/ui-contracts';

	interface Props {
		loadCoverage: () => Promise<UniverseCatalogCoverage>;
		searchEntities: (request: UniverseEntitySearchRequest) => Promise<UniverseEntitySearchResult>;
		loadProfile: (entityId: string) => Promise<UniverseEntityProfile>;
		compareEntities: (krEntityId: string, usEntityId: string) => Promise<UniversePairComparison>;
	}

	let { loadCoverage, searchEntities, loadProfile, compareEntities }: Props = $props();
	let coverage = $state<UniverseCatalogCoverage | null>(null);
	let catalogLoading = $state(true);
	let catalogError = $state<string | null>(null);
	let query = $state('');
	let market = $state<UniverseCatalogMarket>('ALL');
	let searchResult = $state<UniverseEntitySearchResult | null>(null);
	let searchLoading = $state(false);
	let searchError = $state<string | null>(null);
	let selectedEntity = $state<UniverseGlobalEntity | null>(null);
	let profile = $state<UniverseEntityProfile | null>(null);
	let profileLoading = $state(false);
	let profileError = $state<string | null>(null);
	let krSlot = $state<UniverseEntityProfile | null>(null);
	let usSlot = $state<UniverseEntityProfile | null>(null);
	let comparison = $state<UniversePairComparison | null>(null);
	let comparisonLoading = $state(false);
	let comparisonError = $state<string | null>(null);
	let timer: ReturnType<typeof setTimeout> | null = null;
	let searchRevision = 0;
	let profileRevision = 0;

	const keyMetricIds = [
		'revenue', 'operatingProfit', 'netIncome', 'totalAssets', 'operatingCashFlow',
		'revenueGrowth', 'operatingMargin', 'returnOnEquity', 'debtRatio', 'currentRatio'
	] as const;
	const metricLabel: Readonly<Record<string, string>> = {
		revenue: '매출',
		operatingProfit: '영업이익',
		netIncome: '순이익',
		totalAssets: '총자산',
		totalLiabilities: '총부채',
		operatingCashFlow: '영업현금흐름',
		investingCashFlow: '투자현금흐름',
		financingCashFlow: '재무현금흐름',
		capitalExpenditure: '자본적지출',
		cash: '현금성자산',
		shortTermDebt: '단기차입금',
		longTermDebt: '장기차입금',
		interestExpense: '이자비용',
		revenueGrowth: '매출 성장률',
		operatingMargin: '영업이익률',
		returnOnEquity: '자기자본이익률',
		debtRatio: '부채비율',
		currentRatio: '유동비율',
		latestPeriodicFiling: '최근 정기공시',
		filingAvailableAt: '공시 이용 가능 시점'
	};

	let observationsByMetric = $derived(new Map((profile?.observations ?? []).map((row) => [row.metricId, row])));
	let keyObservations = $derived(keyMetricIds.map((metricId) => observationsByMetric.get(metricId)).filter((row): row is UniverseConformanceObservation => Boolean(row)));

	function message(error: unknown, fallback: string): string {
		return error instanceof Error && error.message ? error.message : fallback;
	}

	function marketBadge(entity: UniverseGlobalEntity): string {
		return entity.market === 'KR' ? 'DART' : 'EDGAR';
	}

	function formatValue(observation: UniverseConformanceObservation | null): string {
		if (!observation || observation.value === null || !observation.unit) return '결손';
		const value = observation.value;
		if (observation.unit === '%') return `${value.toLocaleString('ko-KR', { maximumFractionDigits: 1 })}%`;
		if (observation.unit === 'unix-ms') return new Date(value).toISOString().slice(0, 10);
		const absolute = Math.abs(value);
		if (observation.unit === 'KRW') {
			if (absolute >= 1e12) return `${(value / 1e12).toLocaleString('ko-KR', { maximumFractionDigits: 2 })}조원`;
			if (absolute >= 1e8) return `${(value / 1e8).toLocaleString('ko-KR', { maximumFractionDigits: 0 })}억원`;
			return `${value.toLocaleString('ko-KR')}원`;
		}
		if (observation.unit === 'USD') {
			if (absolute >= 1e12) return `$${(value / 1e12).toLocaleString('en-US', { maximumFractionDigits: 2 })}T`;
			if (absolute >= 1e9) return `$${(value / 1e9).toLocaleString('en-US', { maximumFractionDigits: 2 })}B`;
			if (absolute >= 1e6) return `$${(value / 1e6).toLocaleString('en-US', { maximumFractionDigits: 1 })}M`;
			return `$${value.toLocaleString('en-US')}`;
		}
		return `${value.toLocaleString('ko-KR')} ${observation.unit}`;
	}

	async function hydrateCoverage(): Promise<void> {
		catalogLoading = true;
		catalogError = null;
		try {
			coverage = await loadCoverage();
		} catch (error) {
			catalogError = message(error, '글로벌 법인 카탈로그를 불러오지 못했습니다.');
		} finally {
			catalogLoading = false;
		}
	}

	async function runSearch(): Promise<void> {
		if (timer) { clearTimeout(timer); timer = null; }
		const revision = ++searchRevision;
		const requestedQuery = query.trim();
		if (requestedQuery.length < 2) {
			searchResult = null;
			searchError = null;
			searchLoading = false;
			return;
		}
		searchLoading = true;
		searchError = null;
		try {
			const next = await searchEntities({ query: requestedQuery, market, limit: 30 });
			if (revision === searchRevision) {
				searchResult = next;
				coverage = next.coverage;
			}
		} catch (error) {
			if (revision === searchRevision) searchError = message(error, '법인 검색에 실패했습니다.');
		} finally {
			if (revision === searchRevision) searchLoading = false;
		}
	}

	function scheduleSearch(): void {
		if (timer) clearTimeout(timer);
		timer = setTimeout(() => void runSearch(), 180);
	}

	function setMarket(next: UniverseCatalogMarket): void {
		market = next;
		if (query.trim().length >= 2) void runSearch();
	}

	function usePreset(value: string): void {
		query = value;
		void runSearch();
	}

	async function selectEntity(entity: UniverseGlobalEntity): Promise<void> {
		selectedEntity = entity;
		profile = null;
		profileError = null;
		profileLoading = true;
		const revision = ++profileRevision;
		try {
			const next = await loadProfile(entity.entityId);
			if (revision === profileRevision) profile = next;
		} catch (error) {
			if (revision === profileRevision) profileError = message(error, '법인 프로필을 불러오지 못했습니다.');
		} finally {
			if (revision === profileRevision) profileLoading = false;
		}
	}

	async function runComparison(): Promise<void> {
		if (!krSlot || !usSlot) return;
		comparisonLoading = true;
		comparisonError = null;
		comparison = null;
		try {
			comparison = await compareEntities(krSlot.entity.entityId, usSlot.entity.entityId);
		} catch (error) {
			comparisonError = message(error, '한미 20문항 비교를 컴파일하지 못했습니다.');
		} finally {
			comparisonLoading = false;
		}
	}

	function addToComparison(): void {
		if (!profile) return;
		if (profile.entity.market === 'KR') krSlot = profile;
		else usSlot = profile;
		comparison = null;
		comparisonError = null;
		if ((profile.entity.market === 'KR' && usSlot) || (profile.entity.market === 'US' && krSlot)) void runComparison();
	}

	onMount(() => {
		void hydrateCoverage();
		return () => { if (timer) clearTimeout(timer); };
	});
</script>

<section class="globalLab" aria-label="DART EDGAR 글로벌 법인 우주">
	<header class="globalHead">
		<div>
			<span>GLOBAL ENTITY INTELLIGENCE</span>
			<h2>DART와 EDGAR를 하나의 법인 우주로 질의합니다.</h2>
			<p>화면에는 검색 결과만 제한해 그리지만, 질의 대상은 원본 Parquet 전체입니다. 종목코드가 없는 DART 법인과 ticker가 없는 EDGAR CIK도 숨기지 않습니다.</p>
		</div>
		<div class="sourcePulse"><i></i><b>{catalogLoading ? 'LOADING SSOT' : catalogError ? 'SOURCE ERROR' : '4 SOURCES LIVE'}</b></div>
	</header>

	{#if coverage}
		<div class="coverage" aria-label="글로벌 카탈로그 범위">
			<div><span>DART LEGAL ENTITIES</span><strong>{coverage.krLegalEntityCount.toLocaleString()}</strong><small>등록 법인 전체</small></div>
			<div><span>DART SECURITY IDS</span><strong>{coverage.krSecurityCount.toLocaleString()}</strong><small>종목코드 보유</small></div>
			<div><span>EDGAR LEGAL ENTITIES</span><strong>{coverage.usLegalEntityCount.toLocaleString()}</strong><small>ticker와 재무 CIK 합집합</small></div>
			<div><span>EDGAR FINANCIALS</span><strong>{coverage.usFinanceEntityCount.toLocaleString()}</strong><small>재무 이력 CIK</small></div>
			<div><span>QUERYABLE UNIVERSE</span><strong>{coverage.entityCount.toLocaleString()}</strong><small>법인 기준 중복 제거</small></div>
		</div>
	{:else if catalogError}
		<div class="loadError"><strong>카탈로그 연결 실패</strong><p>{catalogError}</p><button onclick={() => void hydrateCoverage()}>다시 연결</button></div>
	{:else}
		<div class="catalogSkeleton"><i></i><span>DART 등록부와 SEC ticker, EDGAR 재무 인덱스를 병렬로 읽는 중입니다.</span></div>
	{/if}

	<div class="searchDeck">
		<form onsubmit={(event) => { event.preventDefault(); void runSearch(); }}>
			<label for="global-entity-search">법인명, 종목코드, ticker, DART corpCode, SEC CIK</label>
			<div class="searchInput">
				<input id="global-entity-search" bind:value={query} oninput={scheduleSearch} autocomplete="off" spellcheck="false" placeholder="삼성전자 · 005930 · Apple · AAPL · 0000320193" />
				<button type="submit">우주 검색</button>
			</div>
		</form>
		<div class="marketFilter" aria-label="시장 범위">
			<button class:active={market === 'ALL'} onclick={() => setMarket('ALL')}>ALL</button>
			<button class:active={market === 'KR'} onclick={() => setMarket('KR')}>DART</button>
			<button class:active={market === 'US'} onclick={() => setMarket('US')}>EDGAR</button>
		</div>
	</div>

	<div class="presetRow">
		<span>즉시 탐색</span>
		<button onclick={() => usePreset('삼성전자')}>삼성전자</button>
		<button onclick={() => usePreset('AAPL')}>AAPL</button>
		<button onclick={() => usePreset('0000320193')}>CIK 0000320193</button>
		<button onclick={() => usePreset('LG스포츠')}>비상장 DART 법인</button>
	</div>

	<div class="entityWorkspace">
		<section class="resultsPane">
			<header><span>ENTITY RESULTS</span><b>{searchLoading ? 'SEARCHING' : `${searchResult?.matches.length ?? 0} HITS`}</b></header>
			{#if searchError}
				<div class="paneMessage error">{searchError}</div>
			{:else if query.trim().length < 2}
				<div class="paneMessage"><b>두 글자부터 검색합니다.</b><p>전체 10만개 이상 법인을 캔버스에 밀어 넣지 않고, 검색과 선택으로 장면을 제한합니다.</p></div>
			{:else if searchLoading && !searchResult}
				<div class="paneMessage">글로벌 인덱스를 질의하는 중입니다.</div>
			{:else if searchResult?.matches.length === 0}
				<div class="paneMessage"><b>일치하는 법인이 없습니다.</b><p>corpCode 또는 CIK 원문으로 다시 확인해 보세요.</p></div>
			{:else}
				<div class="resultList">
					{#each searchResult?.matches ?? [] as entity (entity.entityId)}
						<button class:selected={selectedEntity?.entityId === entity.entityId} onclick={() => void selectEntity(entity)}>
							<span class:kr={entity.market === 'KR'}>{marketBadge(entity)}</span>
							<div><strong>{entity.label}</strong><small>{entity.ticker ?? entity.legalEntityId} · {entity.exchange ?? entity.industryName ?? '분류 없음'}</small></div>
							<i class:ready={entity.financialCoverage !== 'identityOnly'}>{entity.financialCoverage === 'indexed' ? 'FIN' : entity.financialCoverage === 'onDemand' ? 'LOAD' : 'ID'}</i>
						</button>
					{/each}
				</div>
			{/if}
		</section>

		<section class="profilePane">
			<header><span>ENTITY DOSSIER</span><b>{profile ? `${profile.answeredQuestionCount}/${profile.questionCount}` : 'NO SELECTION'}</b></header>
			{#if profileLoading}
				<div class="paneMessage">기업별 재무 Parquet와 법인 식별자를 결속하는 중입니다.</div>
			{:else if profileError}
				<div class="paneMessage error">{profileError}</div>
			{:else if profile}
				<div class="profileTitle">
					<div><span class:kr={profile.entity.market === 'KR'}>{marketBadge(profile.entity)}</span><h3>{profile.entity.label}</h3></div>
					<button onclick={addToComparison}>{profile.entity.market} 비교 슬롯에 담기</button>
				</div>
				<div class="identityGrid">
					<div><span>LEGAL ID</span><code>{profile.entity.legalEntityId}</code></div>
					<div><span>SECURITY</span><code>{profile.entity.securityId ?? profile.entity.ticker ?? '없음'}</code></div>
					<div><span>CLASSIFICATION</span><code>{profile.entity.industryName ?? '미분류'}</code></div>
					<div><span>COVERAGE</span><code>{profile.status.toUpperCase()}</code></div>
				</div>
				<div class="metricGrid">
					{#each keyObservations as observation (observation.metricId)}
						<div><span>{metricLabel[observation.metricId] ?? observation.metricId}</span><strong>{formatValue(observation)}</strong><small>{observation.dataAsOf}</small></div>
					{/each}
				</div>
				{#if keyObservations.length === 0}
					<div class="identityOnly"><b>식별자 우주에는 존재하지만 재무 관측은 없습니다.</b><p>비상장 법인과 CIK-only filer를 삭제하지 않고 identity-only 상태로 유지합니다.</p></div>
				{/if}
				<details class="evidenceRefs"><summary>원천 참조 {profile.entity.sourceRefs.length}개</summary>{#each profile.entity.sourceRefs as source}<code>{source}</code>{/each}</details>
			{:else}
				<div class="paneMessage"><b>법인을 선택하세요.</b><p>DART corpCode와 SEC CIK를 중심으로 식별하고, 가능한 경우 기업별 재무 원천을 지연 로드합니다.</p></div>
			{/if}
		</section>
	</div>

	<section class="compareDeck">
		<header>
			<div><span>KR · US TWIN COMPILER</span><h3>20개 고정 질문으로 한미 법인을 대조합니다.</h3></div>
			<div class="compareScore">{#if comparison}<strong>{comparison.readyCount}</strong><span>READY</span><b>{comparison.blockedCount} BLOCKED</b>{:else}<span>WAITING FOR PAIR</span>{/if}</div>
		</header>
		<div class="pairSlots">
			<div class:filled={krSlot}><span>KR · DART</span><strong>{krSlot?.entity.label ?? '한국 법인을 선택하세요'}</strong><small>{krSlot?.entity.legalEntityId ?? 'corpCode'}</small></div>
			<i>↔</i>
			<div class:filled={usSlot}><span>US · EDGAR</span><strong>{usSlot?.entity.label ?? '미국 법인을 선택하세요'}</strong><small>{usSlot?.entity.legalEntityId ?? 'CIK'}</small></div>
			<button disabled={!krSlot || !usSlot || comparisonLoading} onclick={() => void runComparison()}>{comparisonLoading ? '컴파일 중' : '20문항 재컴파일'}</button>
		</div>
		{#if comparisonError}<div class="compareError">{comparisonError}</div>{/if}
		{#if comparison}
			<div class="comparisonTable" role="table" aria-label="한미 20문항 비교 결과">
				<div class="comparisonRow tableHead" role="row"><span>질문</span><span>KR</span><span>US</span><span>판정</span></div>
				{#each comparison.results as result (result.question.questionId)}
					<div class="comparisonRow" role="row">
						<span><b>{result.question.questionId.slice(-2)}</b>{result.question.label}</span>
						<span>{formatValue(result.kr)}</span>
						<span>{formatValue(result.us)}</span>
						<span class:ready={result.status === 'ready'} title={result.gaps.map((gap) => gap.reasonCode).join(', ')}>{result.status === 'ready' ? 'READY' : result.gaps.map((gap) => gap.reasonCode).join(' · ')}</span>
					</div>
				{/each}
			</div>
			<p class="compareRule">KRW와 USD 절대금액은 환율·기준시점이 일치하지 않으면 직접 우열 판정을 하지 않습니다. 비율과 시점도 dataAsOf가 다르면 BLOCKED로 남깁니다.</p>
		{:else}
			<div class="compareEmpty">검색 결과에서 한국 법인과 미국 법인을 하나씩 열어 비교 슬롯에 담으세요. CIK-only filer도 재무 관측이 있으면 비교할 수 있습니다.</div>
		{/if}
	</section>
</section>

<style>
	.globalLab { display: grid; gap: 15px; color: #dce5f2; }
	.globalHead { display: flex; justify-content: space-between; gap: 32px; padding: 7px 4px 2px; }
	.globalHead span, .resultsPane header span, .profilePane header span, .compareDeck header span { color: #5d708a; font: 650 8px/1 ui-monospace, monospace; letter-spacing: .14em; }
	.globalHead h2 { margin: 7px 0 5px; color: #eff4fa; font-size: 18px; letter-spacing: -.02em; }
	.globalHead p { max-width: 780px; margin: 0; color: #71839a; font-size: 11px; line-height: 1.6; }
	.sourcePulse { display: flex; align-items: center; gap: 8px; flex-shrink: 0; color: #6bd3a2; font: 650 8px/1 ui-monospace, monospace; letter-spacing: .1em; }
	.sourcePulse i { width: 7px; height: 7px; border-radius: 50%; background: currentColor; box-shadow: 0 0 0 4px rgba(76, 210, 153, .12); }
	.coverage { display: grid; grid-template-columns: repeat(5, 1fr); border: 1px solid #1d2a3c; border-radius: 13px; overflow: hidden; background: #0b111b; }
	.coverage > div { padding: 14px; border-right: 1px solid #1a2637; }
	.coverage > div:last-child { border-right: 0; background: rgba(62, 113, 184, .08); }
	.coverage span { color: #5d7088; font: 600 7px/1 ui-monospace, monospace; letter-spacing: .08em; }
	.coverage strong { display: block; margin: 8px 0 4px; color: #f0f5fb; font: 550 22px/1 ui-monospace, monospace; letter-spacing: -.04em; }
	.coverage small { color: #63758c; font-size: 9px; }
	.catalogSkeleton, .loadError { display: flex; align-items: center; gap: 11px; min-height: 76px; padding: 17px; border: 1px solid #1d2a3b; border-radius: 13px; color: #7688a0; background: #0b111a; font-size: 11px; }
	.catalogSkeleton i { width: 14px; height: 14px; border: 2px solid #28384f; border-top-color: #6ea9f5; border-radius: 50%; animation: spin .9s linear infinite; }
	.loadError { display: block; border-color: rgba(232, 99, 108, .3); }
	.loadError p { color: #986f77; }
	.loadError button { border: 1px solid #51333b; border-radius: 7px; padding: 7px 9px; color: #e9a3aa; background: #1a1116; cursor: pointer; }
	.searchDeck { display: grid; grid-template-columns: minmax(0, 1fr) auto; gap: 14px; align-items: end; padding: 15px; border: 1px solid #203047; border-radius: 13px; background: linear-gradient(120deg, rgba(26, 48, 77, .28), rgba(10, 15, 24, .9)); }
	.searchDeck label { display: block; margin-bottom: 7px; color: #72859e; font-size: 9px; }
	.searchInput { display: flex; }
	.searchInput input { width: 100%; border: 1px solid #2b3e58; border-right: 0; border-radius: 9px 0 0 9px; padding: 12px 13px; outline: none; color: #edf3fa; background: #080d15; font-size: 12px; }
	.searchInput input:focus { border-color: #5680b7; }
	.searchInput button { min-width: 88px; border: 1px solid #345278; border-radius: 0 9px 9px 0; color: #d7e7fa; background: #19304d; cursor: pointer; }
	.marketFilter { display: flex; gap: 3px; padding: 3px; border: 1px solid #26374e; border-radius: 9px; background: #080d15; }
	.marketFilter button { border: 0; border-radius: 6px; padding: 9px 11px; color: #657890; background: transparent; font: 600 9px/1 ui-monospace, monospace; cursor: pointer; }
	.marketFilter button.active { color: #e6eef8; background: #20334d; }
	.presetRow { display: flex; align-items: center; gap: 6px; padding: 0 4px; }
	.presetRow span { margin-right: 3px; color: #55677f; font-size: 9px; }
	.presetRow button { border: 1px solid #1d2c40; border-radius: 999px; padding: 5px 9px; color: #778aa2; background: #0b111a; font-size: 9px; cursor: pointer; }
	.presetRow button:hover { color: #cbd8e8; border-color: #334a69; }
	.entityWorkspace { display: grid; grid-template-columns: minmax(300px, .82fr) minmax(420px, 1.18fr); min-height: 420px; border: 1px solid #1d2a3b; border-radius: 14px; overflow: hidden; background: #090e16; }
	.resultsPane { border-right: 1px solid #1a2636; }
	.resultsPane, .profilePane { min-width: 0; }
	.resultsPane > header, .profilePane > header { display: flex; justify-content: space-between; padding: 13px 14px; border-bottom: 1px solid #182434; background: #0c131e; }
	.resultsPane header b, .profilePane header b { color: #6f829a; font: 600 8px/1 ui-monospace, monospace; }
	.resultList { max-height: 510px; overflow-y: auto; }
	.resultList > button { display: grid; grid-template-columns: auto minmax(0, 1fr) auto; align-items: center; gap: 10px; width: 100%; border: 0; border-bottom: 1px solid #131e2c; padding: 11px 13px; color: #cbd6e4; background: transparent; text-align: left; cursor: pointer; }
	.resultList > button:hover, .resultList > button.selected { background: #111c2b; }
	.resultList > button.selected { box-shadow: inset 2px 0 #5e98df; }
	.resultList button > span, .profileTitle span { min-width: 42px; border: 1px solid rgba(97, 150, 220, .3); border-radius: 5px; padding: 4px 5px; color: #74a9e9; font: 650 7px/1 ui-monospace, monospace; text-align: center; }
	.resultList button > span.kr, .profileTitle span.kr { border-color: rgba(230, 98, 103, .28); color: #e57d82; }
	.resultList button div { min-width: 0; }
	.resultList strong { display: block; overflow: hidden; color: #dce5ef; font-size: 11px; text-overflow: ellipsis; white-space: nowrap; }
	.resultList small { display: block; margin-top: 5px; overflow: hidden; color: #60738b; font: 500 8px/1 ui-monospace, monospace; text-overflow: ellipsis; white-space: nowrap; }
	.resultList i { color: #5f6f84; font: 600 7px/1 ui-monospace, monospace; font-style: normal; }
	.resultList i.ready { color: #64c596; }
	.paneMessage { display: grid; align-content: center; min-height: 300px; padding: 28px; color: #6b7d94; text-align: center; font-size: 11px; line-height: 1.6; }
	.paneMessage b { color: #aab8c9; }
	.paneMessage p { max-width: 360px; margin: 8px auto 0; }
	.paneMessage.error { color: #d48189; }
	.profilePane { padding-bottom: 15px; }
	.profilePane > header { margin-bottom: 17px; }
	.profileTitle { display: flex; align-items: center; justify-content: space-between; gap: 15px; padding: 0 17px; }
	.profileTitle > div { display: flex; align-items: center; gap: 10px; min-width: 0; }
	.profileTitle h3 { margin: 0; overflow: hidden; color: #f0f4f9; font-size: 20px; text-overflow: ellipsis; white-space: nowrap; }
	.profileTitle button { flex-shrink: 0; border: 1px solid #345277; border-radius: 8px; padding: 8px 10px; color: #b9d3f3; background: #15263c; font-size: 9px; cursor: pointer; }
	.identityGrid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 6px; margin: 16px 17px 10px; }
	.identityGrid div { min-width: 0; padding: 9px; border: 1px solid #192638; border-radius: 8px; background: #0c141f; }
	.identityGrid span, .metricGrid span { display: block; color: #5d718a; font: 600 7px/1 ui-monospace, monospace; letter-spacing: .06em; }
	.identityGrid code { display: block; margin-top: 6px; overflow: hidden; color: #a4b4c8; font-size: 8px; text-overflow: ellipsis; white-space: nowrap; }
	.metricGrid { display: grid; grid-template-columns: repeat(5, 1fr); gap: 6px; padding: 0 17px; }
	.metricGrid div { min-width: 0; padding: 11px 9px; border: 1px solid #1a283a; border-radius: 9px; background: #0e1723; }
	.metricGrid strong { display: block; margin: 8px 0 4px; overflow: hidden; color: #e3ebf5; font: 550 12px/1 ui-monospace, monospace; text-overflow: ellipsis; white-space: nowrap; }
	.metricGrid small { color: #53667e; font: 500 7px/1 ui-monospace, monospace; }
	.identityOnly { margin: 18px; padding: 16px; border: 1px dashed #3c3540; border-radius: 10px; color: #9c8b9a; background: rgba(92, 58, 77, .08); }
	.identityOnly b { color: #c3adb9; font-size: 11px; }
	.identityOnly p { margin: 7px 0 0; font-size: 10px; line-height: 1.6; }
	.evidenceRefs { margin: 15px 17px 0; border-top: 1px solid #172333; padding-top: 10px; color: #667991; font-size: 9px; }
	.evidenceRefs summary { cursor: pointer; }
	.evidenceRefs code { display: block; margin-top: 7px; overflow-wrap: anywhere; color: #596c83; font-size: 8px; }
	.compareDeck { border: 1px solid #223047; border-radius: 14px; overflow: hidden; background: #0a1019; }
	.compareDeck > header { display: flex; justify-content: space-between; align-items: end; gap: 20px; padding: 15px 17px; border-bottom: 1px solid #1b2839; background: linear-gradient(90deg, rgba(84, 42, 49, .11), rgba(31, 66, 110, .12)); }
	.compareDeck h3 { margin: 6px 0 0; color: #dfe7f1; font-size: 14px; }
	.compareScore { display: flex; align-items: end; gap: 7px; color: #667a92; font: 600 8px/1 ui-monospace, monospace; }
	.compareScore strong { color: #69ce9b; font-size: 24px; }
	.compareScore b { margin-left: 7px; color: #d4877b; font-weight: 600; }
	.pairSlots { display: grid; grid-template-columns: 1fr auto 1fr auto; align-items: center; gap: 9px; padding: 13px 17px; border-bottom: 1px solid #162232; }
	.pairSlots > div { padding: 10px 12px; border: 1px dashed #2b3b50; border-radius: 9px; }
	.pairSlots > div.filled { border-style: solid; border-color: #375474; background: #101b29; }
	.pairSlots span { color: #5b7089; font: 600 7px/1 ui-monospace, monospace; }
	.pairSlots strong { display: block; margin: 5px 0 3px; color: #cbd7e5; font-size: 10px; }
	.pairSlots small { color: #60728a; font: 500 8px/1 ui-monospace, monospace; }
	.pairSlots > i { color: #53677f; font-style: normal; }
	.pairSlots > button { border: 1px solid #354a66; border-radius: 8px; padding: 10px 12px; color: #b5c7dc; background: #142033; font-size: 9px; cursor: pointer; }
	.pairSlots > button:disabled { opacity: .4; cursor: default; }
	.comparisonTable { max-height: 520px; overflow-y: auto; }
	.comparisonRow { display: grid; grid-template-columns: 1.25fr 1fr 1fr 1.1fr; border-bottom: 1px solid #14202e; }
	.comparisonRow > span { min-width: 0; padding: 9px 11px; overflow: hidden; border-right: 1px solid #14202e; color: #8798ad; font-size: 9px; text-overflow: ellipsis; white-space: nowrap; }
	.comparisonRow > span:last-child { border-right: 0; color: #c37f78; font: 600 8px/1.2 ui-monospace, monospace; }
	.comparisonRow > span:last-child.ready { color: #61c38f; }
	.comparisonRow > span:first-child { color: #b2bfce; }
	.comparisonRow > span:first-child b { margin-right: 8px; color: #566a82; font: 600 7px/1 ui-monospace, monospace; }
	.comparisonRow.tableHead { position: sticky; z-index: 1; top: 0; background: #0e1722; }
	.comparisonRow.tableHead span { color: #5c7089; font: 600 7px/1 ui-monospace, monospace; letter-spacing: .08em; }
	.compareRule, .compareEmpty, .compareError { margin: 0; padding: 12px 17px; color: #60738a; font-size: 9px; line-height: 1.6; }
	.compareEmpty { padding: 28px 17px; text-align: center; }
	.compareError { color: #d28188; }
	@keyframes spin { to { transform: rotate(360deg); } }
	@media (max-width: 1080px) { .coverage { grid-template-columns: repeat(3, 1fr); } .coverage > div:nth-child(3) { border-right: 0; } .coverage > div:nth-child(-n+3) { border-bottom: 1px solid #1a2637; } .metricGrid { grid-template-columns: repeat(3, 1fr); } }
	@media (max-width: 780px) { .globalHead, .compareDeck > header { display: block; } .sourcePulse, .compareScore { margin-top: 12px; } .searchDeck { grid-template-columns: 1fr; } .marketFilter { width: fit-content; } .entityWorkspace { grid-template-columns: 1fr; } .resultsPane { border-right: 0; border-bottom: 1px solid #1a2636; } .identityGrid { grid-template-columns: repeat(2, 1fr); } .pairSlots { grid-template-columns: 1fr; } .pairSlots > i { transform: rotate(90deg); text-align: center; } .comparisonRow { grid-template-columns: 1fr 1fr; } .comparisonRow > span:nth-child(2) { border-right: 0; } }
	@media (max-width: 560px) { .coverage { grid-template-columns: repeat(2, 1fr); } .coverage > div { border-bottom: 1px solid #1a2637; } .coverage > div:nth-child(2n) { border-right: 0; } .coverage > div:last-child { grid-column: 1 / -1; border-bottom: 0; } .presetRow { overflow-x: auto; } .presetRow button { flex-shrink: 0; } .metricGrid { grid-template-columns: repeat(2, 1fr); } .profileTitle { align-items: flex-start; } .profileTitle h3 { white-space: normal; } }
</style>
