<script lang="ts">
	// 공시 워치 · 좌측 레일 패널(스크리너·히트맵과 동급). 행 = 회사명 + 30거래일 스파크 + 1Y + 수시공시 신선도 배지.
	// 신선도 = 절대시각 기준(현재 − 접수일) Tier 1, 기기 무관·무상태. 데이터: recentMap(가격, LeftRail 공유) +
	// filing.nonRegular(회사당 기존 per-code 캐시 재사용). 워치 집합이 작아(목표 10~30) per-company 로 충분 ·
	// 다중코드 배치 read 는 후속 최적화(포트 표면 1 메서드 신설 필요). 정직 라벨: "이 기기 저장"·완결성 단정 없음.
	import type { Candle } from '@dartlab/ui-contracts';
	import { useDartLabRuntime } from '@dartlab/ui-runtime';
	import type { Engine } from '../lib/engine';
	import type { EcoNode, Lang } from '../lib/types';
	import Panel from '../ui/Panel.svelte';
	import { watchlist } from '../lib/watchlist.svelte';
	import { chgClass, sign, sparkPts } from '../ui/helpers';

	interface Props {
		eng: Engine;
		lang: Lang;
		active: string;
		onPick: (code: string) => void;
		recentMap: Record<string, Candle[]> | null; // 30거래일 스파크 (LeftRail 과 어댑터 캐시 공유, 추가 다운로드 0)
		bare?: boolean; // 탭 모드 · Panel 크롬(헤더·테두리) 없이 본문만. 하단 탭(LeftRail)이 헤더·제목 제공.
	}
	let { eng, lang, active, onPick, recentMap, bare = false }: Props = $props();
	const rt = useDartLabRuntime();

	// 신선도 · 수시공시(allFilings) 접수일 기준 최근 7/30 일 건수 + 최신일. 회사당 1 회 비동기 로드(요청 중복 가드).
	interface Fresh {
		new7: number;
		new30: number;
		latest: string | null;
	}
	const DAY = 86_400_000;
	function computeFresh(rows: { rceptDate: string }[]): Fresh {
		const now = Date.now();
		let new7 = 0;
		let new30 = 0;
		let latest: string | null = null;
		for (const r of rows) {
			const t = Date.parse(r.rceptDate);
			if (Number.isNaN(t)) continue;
			if (!latest || r.rceptDate > latest) latest = r.rceptDate;
			const days = (now - t) / DAY;
			if (days <= 7) new7++;
			if (days <= 30) new30++;
		}
		return { new7, new30, latest };
	}
	let fresh = $state<Record<string, Fresh>>({});
	// 신선도 = HF allFilings 배치 read 1 회(공개·로컬 공통배선, 백엔드 0). 워치 집합 변동 시 재호출(소스 캐시).
	$effect(() => {
		const codes = watchlist.codes;
		if (!codes.length) return;
		let cancelled = false;
		rt.filing.recentForCodes(codes).then((map) => {
			if (cancelled) return;
			const next = { ...fresh };
			for (const c of codes) next[c] = computeFresh(map[c] ?? []);
			fresh = next;
		});
		return () => {
			cancelled = true;
		};
	});

	const nodeById = $derived(new Map((eng.raw.eco?.nodes || []).map((n) => [n.id, n])));
	interface Row {
		code: string;
		node: EcoNode | undefined;
		r1y: number | null;
		f: Fresh | null;
	}
	const rows = $derived.by<Row[]>(() => {
		const list = watchlist.codes.map((code): Row => {
			const px = eng.priceOf(code);
			return { code, node: nodeById.get(code), r1y: px ? ((px.return1y as number | null) ?? null) : null, f: fresh[code] ?? null };
		});
		// 신선도순 · 7일 신규 > 30일 신규 > 최신 공시일. 미로드(f=null)는 후순위.
		return list.sort((a, b) => {
			const sa = a.f ? a.f.new7 * 1000 + a.f.new30 : -1;
			const sb = b.f ? b.f.new7 * 1000 + b.f.new30 : -1;
			if (sa !== sb) return sb - sa;
			return (b.f?.latest ?? '').localeCompare(a.f?.latest ?? '');
		});
	});
</script>

<!-- 본문 · Panel 모드와 bare(탭) 모드가 공유. 헤더/테두리만 모드별로 다름. -->
{#snippet inner()}
	{#if !watchlist.count}
		<div class="watchEmpty">{lang === 'en' ? 'Add companies with the header ☆ to monitor their filings here.' : '헤더의 ☆ 로 회사를 담으면 공시 신선도를 한눈에 모읍니다.'}</div>
	{:else}
		<div class="watchList">
			{#each rows as r (r.code)}
				{@const sp = recentMap?.[r.code]}
				<div class={'watchRow' + (active === r.code ? ' on' : '')} role="button" tabindex="0" onclick={() => onPick(r.code)} onkeydown={(e) => e.key === 'Enter' && onPick(r.code)}>
					<span class="wName"><b>{eng.nameOf(r.code) || r.code}</b><span class="wInd">{r.node?.industryName || r.code}</span></span>
					<span class="wSpark">{#if sp && sp.length > 1}<svg class={chgClass(r.r1y)} viewBox="0 0 34 11" preserveAspectRatio="none" aria-hidden="true"><polyline points={sparkPts(sp.map((k) => k.c))} fill="none" stroke="currentColor" stroke-width="1.1" /></svg>{/if}</span>
					<span class={'wR1y mono ' + chgClass(r.r1y)}>{r.r1y == null ? '·' : sign(r.r1y, 0) + '%'}</span>
					<span class="wFresh">
						{#if r.f == null}<span class="wfDim mono">·</span>
						{:else if r.f.new7 > 0}<span class="wfHot mono" title={lang === 'en' ? 'new non-regular filings within 7 days' : '최근 7일 신규 수시공시'}>{lang === 'en' ? '7D ' : '7일 '}{r.f.new7}</span>
						{:else if r.f.new30 > 0}<span class="wfWarm mono" title={lang === 'en' ? 'within 30 days' : '최근 30일'}>{lang === 'en' ? '30D ' : '30일 '}{r.f.new30}</span>
						{:else if r.f.latest}<span class="wfDim mono" title={lang === 'en' ? 'latest filing date' : '최근 공시일'}>{r.f.latest.slice(2)}</span>
						{:else}<span class="wfDim mono">·</span>{/if}
					</span>
					<button class="wDel" title={lang === 'en' ? 'remove from watch' : '워치에서 제거'} aria-label="remove" onclick={(e) => { e.stopPropagation(); watchlist.remove(r.code); }}>✕</button>
				</div>
			{/each}
		</div>
		<div class="watchNote">{lang === 'en' ? 'freshness = absolute calendar time · count = allFilings non-regular' : '신선도 = 절대 시각 기준(기기 무관) · 카운트 = allFilings 수시공시'}</div>
	{/if}
{/snippet}

{#if bare}
	<div class="watchBare">{@render inner()}</div>
{:else}
	<Panel {lang} className="eWatch" prov="real" title={{ kr: '공시 워치', en: 'DISCLOSURE WATCH' }} sub={{ kr: watchlist.count + '종목 · 수시공시 신선도', en: 'n=' + watchlist.count + ' · filing freshness' }} flush>
		{@render inner()}
	</Panel>
{/if}

<style>
	.watchEmpty {
		padding: 10px 8px;
		font-size: 10.5px;
		line-height: 1.5;
		color: var(--dim, #8b919e);
	}
	.watchList {
		display: flex;
		flex-direction: column;
	}
	/* 탭 모드 · 패널 잔여 높이를 채우고 목록만 내부 스크롤(무한 증가가 다른 패널을 밀지 않음). */
	.watchBare {
		display: flex;
		flex-direction: column;
		flex: 1;
		min-height: 0;
	}
	.watchBare .watchList {
		flex: 1;
		overflow-y: auto;
		min-height: 0;
	}
	.watchRow {
		display: grid;
		grid-template-columns: 1fr 36px 42px 46px 16px;
		align-items: center;
		gap: 6px;
		padding: 4px 6px;
		border-bottom: 1px solid var(--bd, rgba(48, 58, 78, 0.4));
		cursor: pointer;
	}
	.watchRow:hover {
		background: rgba(91, 155, 240, 0.08);
	}
	.watchRow.on {
		background: rgba(91, 155, 240, 0.14);
	}
	.wName {
		display: flex;
		flex-direction: column;
		min-width: 0;
	}
	.wName b {
		font-size: 11px;
		color: var(--fg, #cfd3dc);
		white-space: nowrap;
		overflow: hidden;
		text-overflow: ellipsis;
	}
	.wInd {
		font-size: 9px;
		color: var(--dimmer, #6b7280);
		white-space: nowrap;
		overflow: hidden;
		text-overflow: ellipsis;
	}
	.wSpark {
		display: flex;
		align-items: center;
	}
	.wSpark svg {
		width: 34px;
		height: 11px;
	}
	.wR1y {
		font-size: 10px;
		text-align: right;
	}
	.wFresh {
		font-size: 9px;
		text-align: right;
	}
	.wfHot {
		color: var(--amber, var(--amber));
		font-weight: 700;
	}
	.wfWarm {
		color: var(--good, #6ee7b7);
	}
	.wfDim {
		color: var(--dimmer, #6b7280);
	}
	.wDel {
		border: 0;
		background: transparent;
		color: var(--dimmer, #6b7280);
		font-size: 11px;
		line-height: 1;
		cursor: pointer;
		padding: 0;
	}
	.wDel:hover {
		color: var(--dn, #f87171);
	}
	.watchNote {
		padding: 4px 6px 6px;
		font-size: 8.5px;
		color: var(--dimmer, #6b7280);
		line-height: 1.4;
	}
</style>
