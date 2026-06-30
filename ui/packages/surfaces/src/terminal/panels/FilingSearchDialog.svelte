<script lang="ts">
	// 전역 공시 본문 검색 다이얼로그 · 커맨드 팔레트(⌘⇧F). cmdBar(종목 점프)와 분리된 *본문* BM25 검색.
	// 공통배선: useDartLabRuntime().search(=createSearchPort) · 퍼블릭/로컬 동일 코어·HF sidecar byte-range.
	// 콜드 1회(~10MB stats)는 첫 질의 시 lazy 로드(검색 안 쓰면 비용 0). 행 클릭 → 회사 soft-swap(onPick) +
	// dart/edgar 원문 외부 링크(정직 floor · 본문 직행 불가). 회사 인덱스 검색은 cmdBar 담당(여기 아님).
	import { Search, X } from 'lucide-svelte';
	import { useDartLabRuntime } from '@dartlab/ui-runtime';
	import type { FilingHit } from '@dartlab/ui-contracts';
	import type { Lang } from '../lib/types';

	interface Props {
		lang: Lang;
		onPick: (code: string) => void;
		onClose: () => void;
	}
	let { lang, onPick, onClose }: Props = $props();

	const rt = useDartLabRuntime();
	const RECENT_KEY = 'dl.filingSearch.recent';

	let q = $state('');
	let hits = $state<FilingHit[]>([]);
	let busy = $state(false);
	let err = $state(false);
	let coldFirst = $state(true); // 첫 질의 = 콜드 stats 로드(스피너 카피 분기)
	let selIdx = $state(0);
	let inputEl = $state<HTMLInputElement | null>(null);
	let bodyEl = $state<HTMLDivElement | null>(null); // 결과 스크롤 컨테이너 · 키보드 이동 시 선택행 추적
	let seq = 0; // in-flight 토큰 · stale 응답 폐기
	let debounceTimer: ReturnType<typeof setTimeout> | null = null;

	const recent = $state<string[]>(readRecent());
	let builtAt = $state<string | null>(null); // 인덱스 빌드시점(as-of) · manifest 만 읽어 콜드 stats 무관

	function readRecent(): string[] {
		if (typeof localStorage === 'undefined') return [];
		try {
			const raw = JSON.parse(localStorage.getItem(RECENT_KEY) || '[]');
			return Array.isArray(raw) ? raw.filter((x): x is string => typeof x === 'string').slice(0, 8) : [];
		} catch {
			return [];
		}
	}
	function pushRecent(text: string): void {
		const t = text.trim();
		if (!t) return;
		const next = [t, ...recent.filter((x) => x !== t)].slice(0, 8);
		recent.splice(0, recent.length, ...next);
		if (typeof localStorage !== 'undefined') {
			try {
				localStorage.setItem(RECENT_KEY, JSON.stringify(next));
			} catch {
				// localStorage 불가(프라이빗 모드 등) · 최근검색 칩만 미저장, 검색 자체는 정상.
			}
		}
	}

	async function run(text: string): Promise<void> {
		const t = text.trim();
		if (!t) {
			hits = [];
			busy = false;
			err = false;
			return;
		}
		const my = ++seq;
		busy = true;
		err = false;
		try {
			const res = await rt.search.queryFilings({ text: t, limit: 30 });
			if (my !== seq) return; // 더 새 질의가 출발 → 폐기
			hits = res;
			selIdx = 0;
			coldFirst = false;
		} catch {
			if (my !== seq) return;
			hits = [];
			err = true;
		} finally {
			if (my === seq) busy = false;
		}
	}

	function onInput(): void {
		if (debounceTimer) clearTimeout(debounceTimer);
		const text = q;
		debounceTimer = setTimeout(() => run(text), 140);
	}

	function submitRecent(text: string): void {
		q = text;
		run(text);
		inputEl?.focus();
	}

	// dart=특정 공시 viewer(rcpNo) · edgar=회사 공시 브라우즈(이름) · http sourceRef=직접. 없으면 '' (버튼 숨김).
	function externalUrl(hit: FilingHit): string {
		const src = hit.source || '';
		const ref = hit.sourceRef || '';
		if (ref.startsWith('http')) return ref;
		if (/^\d{14}$/.test(hit.rceptNo) && !src.includes('edgar')) {
			return `https://dart.fss.or.kr/dsaf001/main.do?rcpNo=${hit.rceptNo}`;
		}
		if (src.includes('edgar') && hit.corpName) {
			return `https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&company=${encodeURIComponent(hit.corpName)}&type=&dateb=&owner=include&count=40`;
		}
		return '';
	}

	function srcBadge(src: string): { label: string; cls: string } {
		if (src.includes('edgar')) return { label: 'EDGAR', cls: 'bEdgar' };
		if (src.includes('news')) return { label: lang === 'en' ? 'NEWS' : '뉴스', cls: 'bNews' };
		return { label: 'DART', cls: 'bDart' };
	}

	function jump(hit: FilingHit): void {
		if (!hit.stockCode) return; // 뉴스 등 회사키 없음 → 점프 불가(외부 링크만)
		pushRecent(q);
		onPick(hit.stockCode);
		onClose();
	}

	function onKey(e: KeyboardEvent): void {
		if (e.key === 'Escape') {
			e.preventDefault();
			onClose();
			return;
		}
		if (!hits.length) return;
		if (e.key === 'ArrowDown') {
			e.preventDefault();
			selIdx = (selIdx + 1) % hits.length;
		} else if (e.key === 'ArrowUp') {
			e.preventDefault();
			selIdx = (selIdx - 1 + hits.length) % hits.length;
		} else if (e.key === 'Enter') {
			e.preventDefault();
			const hit = hits[selIdx];
			if (hit) jump(hit);
		}
	}

	$effect(() => {
		inputEl?.focus();
	});

	// 키보드 ↑↓ 이동 시 선택 행을 뷰포트로 스크롤(리스트가 선택을 따라가지 않던 버그 수정).
	$effect(() => {
		selIdx;
		if (typeof document === 'undefined') return;
		const row = bodyEl?.querySelectorAll<HTMLElement>('.fsRow')[selIdx];
		row?.scrollIntoView({ block: 'nearest' });
	});

	// 인덱스 as-of 라벨 · 다이얼로그 열릴 때 manifest builtAt 만 경량 조회(콜드 stats ~10MB 강제 안 함).
	$effect(() => {
		rt.search
			.indexBuiltAt()
			.then((b) => (builtAt = b))
			.catch(() => {});
	});
</script>

<div class="scrimWrap" role="presentation" onclick={onClose}>
	<!-- svelte-ignore a11y_no_static_element_interactions -->
	<div
		class="scrModal fsModal"
		role="dialog"
		aria-modal="true"
		aria-label={lang === 'en' ? 'Filing full-text search' : '공시 본문 검색'}
		onclick={(e) => e.stopPropagation()}
		onkeydown={onKey}
	>
		<div class="scrHead">
			<span class="scrTitle">{lang === 'en' ? 'FILING SEARCH' : '공시 검색'}</span>
			<span class="fsSub">{lang === 'en' ? 'all companies · full text' : '전 종목 공시 본문'}{#if builtAt}<span class="fsAsOf">{lang === 'en' ? ` · as of ${builtAt.slice(0, 10)}` : ` · ~${builtAt.slice(0, 10)} 기준`}</span>{/if}</span>
			<span class="fsKbd">⌘⇧F</span>
			<button class="scrClose" onclick={onClose} aria-label="close"><X size={14} /></button>
		</div>

		<div class="fsSearchRow">
			<span class="fsIcon"><Search size={14} /></span>
			<!-- svelte-ignore a11y_autofocus -->
			<input
				bind:this={inputEl}
				bind:value={q}
				oninput={onInput}
				class="fsInput"
				type="text"
				autocomplete="off"
				spellcheck="false"
				placeholder={lang === 'en' ? 'e.g. rights issue, treasury cancellation, convertible bond…' : '예: 유상증자 자사주 소각, 전환사채, 합병…'}
			/>
		</div>

		{#if recent.length && !q.trim()}
			<div class="fsRecent">
				<span class="fsRecentLbl">{lang === 'en' ? 'recent' : '최근'}</span>
				{#each recent as r (r)}
					<button class="fsChip" onclick={() => submitRecent(r)}>{r}</button>
				{/each}
			</div>
		{/if}

		<div class="fsBody" bind:this={bodyEl}>
			{#if busy}
				<div class="fsState">
					<span class="fsSpin">◴</span>
					{#if coldFirst}
						{lang === 'en' ? 'Preparing search (first time only)…' : '공시 검색 준비 중(최초 1회)…'}
					{:else}
						{lang === 'en' ? 'Searching…' : '검색 중…'}
					{/if}
				</div>
			{:else if err}
				<div class="fsState fsErr">{lang === 'en' ? 'Could not load the search index.' : '검색 색인을 불러오지 못했습니다.'}</div>
			{:else if q.trim() && !hits.length}
				<div class="fsState">{lang === 'en' ? 'No results.' : '결과 없음.'}</div>
			{:else}
				{#each hits as hit, i (hit.rceptNo + ':' + i)}
					{@const ext = externalUrl(hit)}
					{@const badge = srcBadge(hit.source)}
					<!-- svelte-ignore a11y_click_events_have_key_events a11y_no_static_element_interactions -->
					<div
						class={'fsRow' + (i === selIdx ? ' sel' : '') + (hit.stockCode ? '' : ' noJump')}
						onclick={() => jump(hit)}
						onmouseenter={() => (selIdx = i)}
						title={hit.stockCode ? (lang === 'en' ? 'Enter → company' : 'Enter → 회사로 점프') : (lang === 'en' ? 'no linked company (news)' : '회사 연결 없음(뉴스)')}
					>
						<span class="fsCorp">
							<b>{hit.corpName || '·'}</b>
							{#if hit.stockCode}<i class="fsCode">{hit.stockCode}</i>{/if}
						</span>
						<span class="fsReport">{hit.reportNm || '·'}</span>
						<span class="fsDate">{hit.rceptDt}</span>
						<span class={'fsBadge ' + badge.cls}>{badge.label}</span>
						{#if hit.snippet}<span class="fsSnippet">{hit.snippet}</span>{/if}
						{#if ext}
							<!-- svelte-ignore a11y_click_events_have_key_events -->
							<a class="fsExt" href={ext} target="_blank" rel="noopener" onclick={(e) => e.stopPropagation()}>{lang === 'en' ? 'source ↗' : '원문 ↗'}</a>
						{/if}
					</div>
				{/each}
			{/if}
		</div>

		<div class="fsFoot">
			<span><b class="tAmber">↑↓</b> {lang === 'en' ? 'move' : '이동'}</span>
			<span><b class="tAmber">Enter</b> {lang === 'en' ? 'company' : '회사로'}</span>
			<span><b class="tAmber">Esc</b> {lang === 'en' ? 'close' : '닫기'}</span>
			{#if hits.length}<span class="fsCount">{hits.length}{lang === 'en' ? ' hits' : '건'}</span>{/if}
		</div>
	</div>
</div>

<style>
	.fsModal { width: min(960px, 96vw); max-height: 88vh; }
	.fsSub { font-size: 10px; color: #c2cad6; font-style: italic; }
	.fsKbd { margin-left: auto; font-size: 10px; color: #c2cad6; border: 1px solid var(--dl-line, #2a3142); border-radius: 3px; padding: 1px 6px; }
	.fsSearchRow { display: flex; align-items: center; gap: 7px; padding: 10px 14px 6px; }
	.fsIcon { display: inline-flex; align-items: center; color: var(--dim, #c2cad6); opacity: 0.85; }
	.fsInput { flex: 1 1 auto; background: rgba(255, 255, 255, 0.04); border: 1px solid var(--dl-line, #2a3142); border-radius: 4px; color: var(--dl-ink, #c8cfdb); font-size: 13px; font-family: inherit; padding: 6px 10px; outline: none; }
	.fsInput:focus { border-color: var(--amber, var(--amber)); }
	.fsRecent { display: flex; flex-wrap: wrap; align-items: center; gap: 5px; padding: 0 14px 8px; }
	.fsRecentLbl { font-size: 9px; color: #c2cad6; text-transform: uppercase; }
	.fsChip { font-size: 10px; padding: 2px 8px; border-radius: 10px; border: 1px solid var(--dl-line, #2a3142); background: rgba(255, 255, 255, 0.03); color: #c2cad6; cursor: pointer; }
	.fsChip:hover { color: var(--dl-ink, #c8cfdb); border-color: var(--amber, var(--amber)); }
	.fsBody { flex: 1 1 auto; min-height: 0; overflow-y: auto; border-top: 1px solid var(--dl-line, #1b2130); }
	.fsState { padding: 22px 14px; font-size: 12px; color: #c2cad6; text-align: center; }
	.fsErr { color: var(--dn, #f85149); }
	.fsSpin { display: inline-block; margin-right: 6px; animation: fsspin 0.9s linear infinite; }
	@keyframes fsspin { to { transform: rotate(360deg); } }
	.fsRow {
		display: grid;
		grid-template-columns: minmax(140px, 200px) minmax(120px, 1fr) 72px 52px;
		grid-template-areas: 'corp report date badge' 'snip snip snip ext';
		align-items: center;
		gap: 2px 10px;
		padding: 5px 14px 5px 12px;
		border-left: 2px solid transparent;
		border-bottom: 1px solid var(--dl-line, #1b2130);
		cursor: pointer;
	}
	.fsRow.sel { border-left-color: var(--amber, var(--amber)); background: rgba(var(--amber-rgb), 0.1); }
	.fsRow.noJump { cursor: default; opacity: 0.82; }
	.fsCorp { grid-area: corp; font-size: 11.5px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
	.fsCorp b { color: var(--dl-ink, #c8cfdb); font-weight: 600; }
	.fsCode { font-style: normal; font-size: 10px; color: #c2cad6; margin-left: 5px; font-variant-numeric: tabular-nums; }
	.fsReport { grid-area: report; font-size: 11px; color: #aab2bf; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
	.fsDate { grid-area: date; font-size: 10px; color: #c2cad6; text-align: right; font-variant-numeric: tabular-nums; }
	.fsBadge { grid-area: badge; font-size: 8.5px; font-weight: 700; text-align: center; border-radius: 3px; padding: 1px 0; }
	.bDart { color: #6cb6ff; background: rgba(108, 182, 255, 0.12); }
	.bEdgar { color: #d2a8ff; background: rgba(210, 168, 255, 0.12); }
	.bNews { color: #d29922; background: rgba(210, 153, 34, 0.12); }
	.fsSnippet { grid-area: snip; font-size: 10px; color: #8b93a0; line-height: 1.4; max-height: 2.8em; overflow: hidden; }
	.fsExt { grid-area: ext; font-size: 9.5px; color: var(--amber, var(--amber)); text-decoration: none; text-align: right; white-space: nowrap; }
	.fsExt:hover { text-decoration: underline; }
	.fsFoot { display: flex; gap: 14px; align-items: center; padding: 6px 14px; border-top: 1px solid var(--dl-line, #1b2130); font-size: 10px; color: #c2cad6; }
	.fsFoot .tAmber { color: var(--amber, var(--amber)); }
	.fsCount { margin-left: auto; font-variant-numeric: tabular-nums; }
</style>
