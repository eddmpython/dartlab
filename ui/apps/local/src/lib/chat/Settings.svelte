<script lang="ts">
	/**
	 * 설정 창. 데스크탑 앱 규범대로 좌측 탭 레일 + 우측 패널이다.
	 *
	 * 예전에는 Runtime Center 카드 목록 하나가 모달 전체였고, 데이터 키나 앱 정보는
	 * 갈 곳이 없었다. 탭으로 나누면 각 항목이 자기 자리를 갖고 카드가 쌓이지 않는다.
	 */
	import { onMount } from 'svelte';
	import RuntimeCenter from '$lib/chat/RuntimeCenter.svelte';
	import {
		clearDartKey,
		getDataStats,
		getOpenDartStatus,
		saveDartKey,
		type OpenDartStatus
	} from '$lib/runtime/agentRuntimeApi';

	let { onChange = () => undefined }: { onChange?: () => void | Promise<void> } = $props();

	type TabKey = 'runtime' | 'data' | 'about';
	const TABS: Array<{ key: TabKey; label: string; hint: string }> = [
		{ key: 'runtime', label: '런타임', hint: '설치된 CLI와 연결' },
		{ key: 'data', label: '데이터', hint: '공시 API 키와 로컬 데이터' },
		{ key: 'about', label: '정보', hint: '버전과 링크' }
	];

	let tab = $state<TabKey>('runtime');
	let dart = $state<OpenDartStatus | null>(null);
	let keyDraft = $state('');
	let busy = $state(false);
	let notice = $state<string | null>(null);
	let error = $state<string | null>(null);
	let stats = $state<Record<string, unknown> | null>(null);
	let version = $state('');

	onMount(() => {
		void loadData();
	});

	async function loadData(): Promise<void> {
		try {
			dart = await getOpenDartStatus();
		} catch (reason) {
			error = reason instanceof Error ? reason.message : String(reason);
		}
		try {
			const value = (await getDataStats()) as Record<string, unknown>;
			stats = value;
			version = String((value.version as string) ?? '');
		} catch {
			stats = null;
		}
	}

	async function submitKey(): Promise<void> {
		const value = keyDraft.trim();
		if (!value || busy) return;
		busy = true;
		error = null;
		notice = null;
		try {
			const result = await saveDartKey(value);
			dart = result.openDart;
			keyDraft = '';
			notice = `키를 저장했습니다 (${result.envPath})`;
		} catch (reason) {
			error = reason instanceof Error ? reason.message : String(reason);
		} finally {
			busy = false;
		}
	}

	async function removeKey(): Promise<void> {
		if (busy) return;
		busy = true;
		error = null;
		notice = null;
		try {
			const result = await clearDartKey();
			dart = result.openDart;
			notice = '키를 제거했습니다';
		} catch (reason) {
			error = reason instanceof Error ? reason.message : String(reason);
		} finally {
			busy = false;
		}
	}

	const statRows = $derived.by(() => {
		if (!stats) return [] as Array<[string, string]>;
		const labels: Record<string, string> = {
			companies: '수집 종목',
			panels: '재무 패널',
			filings: '공시',
			totalSizeMb: '로컬 용량(MB)',
			dataDir: '데이터 경로'
		};
		return Object.entries(stats)
			.filter(([key]) => key in labels)
			.map(([key, value]) => [labels[key], String(value)] as [string, string]);
	});
</script>

<div class="settings" data-qa="settings">
	<nav class="rail" aria-label="설정 분류">
		{#each TABS as item (item.key)}
			<button
				type="button"
				class:on={tab === item.key}
				data-qa={`settings-tab-${item.key}`}
				onclick={() => (tab = item.key)}
				aria-current={tab === item.key ? 'page' : undefined}
			>
				<strong>{item.label}</strong>
				<small>{item.hint}</small>
			</button>
		{/each}
	</nav>

	<section class="panel" data-qa={`settings-panel-${tab}`}>
		{#if tab === 'runtime'}
			<RuntimeCenter {onChange} />
		{:else if tab === 'data'}
			<div class="stack">
				<div class="block">
					<h3>OpenDART API 키</h3>
					<p>공시 원문과 재무 수집에 씁니다. 키는 이 PC 의 프로젝트 환경 파일에만 저장됩니다.</p>
					{#if dart}
						<div class="statusLine" class:ok={dart.configured}>
							<span class="dot" aria-hidden="true"></span>
							{#if dart.configured}
								<span>연결됨 · 키 {dart.keyCount}개 · 출처 {dart.source}</span>
							{:else}
								<span>미설정</span>
							{/if}
						</div>
					{/if}
					<form
						class="keyRow"
						onsubmit={(event) => {
							event.preventDefault();
							void submitKey();
						}}
					>
						<input
							type="password"
							bind:value={keyDraft}
							placeholder="DART API 키 입력"
							aria-label="DART API 키"
							autocomplete="off"
						/>
						<button type="submit" disabled={!keyDraft.trim() || busy}>저장</button>
						{#if dart?.configured}
							<button type="button" class="ghost" onclick={removeKey} disabled={busy}>제거</button>
						{/if}
					</form>
					{#if notice}<p class="ok">{notice}</p>{/if}
					{#if error}<p class="bad">{error}</p>{/if}
					<a href="https://opendart.fss.or.kr/" target="_blank" rel="noreferrer">키 발급 페이지 열기</a>
				</div>

				{#if statRows.length}
					<div class="block">
						<h3>로컬 데이터</h3>
						<dl class="kv">
							{#each statRows as [label, value] (label)}
								<div><dt>{label}</dt><dd>{value}</dd></div>
							{/each}
						</dl>
					</div>
				{/if}
			</div>
		{:else}
			<div class="stack">
				<div class="block">
					<h3>DartLab</h3>
					<p>설치된 에이전트 CLI 에 공시·재무 근거 도구를 연결하는 로컬 작업대입니다.</p>
					<dl class="kv">
						{#if version}<div><dt>버전</dt><dd>{version}</dd></div>{/if}
						<div><dt>실행</dt><dd>로컬 (127.0.0.1:8400)</dd></div>
					</dl>
				</div>
				<div class="block">
					<h3>링크</h3>
					<div class="links">
						<a href="https://github.com/eddmpython/dartlab" target="_blank" rel="noreferrer">GitHub 저장소</a>
						<a href="https://eddmpython.github.io/dartlab" target="_blank" rel="noreferrer">문서</a>
					</div>
				</div>
			</div>
		{/if}
	</section>
</div>

<style>
	.settings {
		display: grid;
		grid-template-columns: 11rem minmax(0, 1fr);
		min-height: 24rem;
		max-height: min(70vh, 34rem);
	}
	.rail {
		display: flex;
		flex-direction: column;
		gap: .12rem;
		padding-right: .75rem;
		border-right: 1px solid var(--dl-line, #2a2c33);
	}
	.rail button {
		display: grid;
		gap: .08rem;
		padding: .45rem .55rem;
		border: 0;
		border-radius: 7px;
		background: none;
		color: var(--dl-ink-dim, #9aa0aa);
		text-align: left;
		cursor: pointer;
	}
	.rail button:hover { background: color-mix(in srgb, var(--dl-bg-raised, #16171a) 70%, transparent); }
	.rail button.on { background: var(--dl-bg-raised, #16171a); color: var(--dl-ink, #e7e7ea); }
	.rail strong { font-size: .82rem; font-weight: 600; }
	.rail small { color: var(--dl-ink-mute, #6b7280); font-size: .68rem; }
	.panel { padding-left: 1.1rem; overflow-y: auto; scrollbar-width: thin; }
	.stack { display: grid; gap: 1.1rem; align-content: start; }
	.block { display: grid; gap: .5rem; }
	h3 { margin: 0; font-size: .88rem; font-weight: 600; color: var(--dl-ink, #e7e7ea); }
	p { margin: 0; color: var(--dl-ink-dim, #9aa0aa); font-size: .78rem; line-height: 1.55; }
	p.ok { color: #70d6a5; }
	p.bad { color: #ff8c8c; }
	.statusLine { display: flex; align-items: center; gap: .4rem; font-size: .76rem; color: var(--dl-ink-dim, #9aa0aa); }
	.statusLine .dot { width: .4rem; height: .4rem; border-radius: 50%; background: var(--dl-ink-mute, #6b7280); }
	.statusLine.ok { color: #70d6a5; }
	.statusLine.ok .dot { background: #70d6a5; }
	.keyRow { display: flex; gap: .4rem; flex-wrap: wrap; }
	.keyRow input {
		flex: 1 1 12rem;
		min-width: 0;
		height: 2rem;
		padding: 0 .6rem;
		border: 1px solid var(--dl-line, #2a2c33);
		border-radius: 7px;
		background: var(--dl-bg-base, #0f0f10);
		color: var(--dl-ink, #e7e7ea);
		font-size: .78rem;
	}
	.keyRow input:focus { outline: none; border-color: color-mix(in srgb, var(--dl-accent, #ff5a36) 55%, var(--dl-line, #2a2c33)); }
	.keyRow button {
		height: 2rem;
		padding: 0 .8rem;
		border: 0;
		border-radius: 7px;
		background: var(--dl-accent, #ff5a36);
		color: white;
		font-size: .76rem;
		cursor: pointer;
	}
	.keyRow button.ghost { background: transparent; border: 1px solid var(--dl-line, #2a2c33); color: var(--dl-ink-dim, #9aa0aa); }
	.keyRow button:disabled { opacity: .45; cursor: default; }
	.kv { display: grid; gap: .3rem; margin: 0; }
	.kv div { display: grid; grid-template-columns: 7rem minmax(0, 1fr); gap: .5rem; align-items: baseline; }
	dt { color: var(--dl-ink-mute, #6b7280); font-size: .72rem; }
	dd { margin: 0; color: var(--dl-ink-dim, #9aa0aa); font-size: .78rem; overflow-wrap: anywhere; }
	.links { display: grid; gap: .3rem; }
	a { color: var(--dl-ink-dim, #9aa0aa); font-size: .76rem; text-decoration: underline; text-underline-offset: 2px; width: fit-content; }
	a:hover { color: var(--dl-ink, #e7e7ea); }
	@media (max-width: 640px) {
		.settings { grid-template-columns: minmax(0, 1fr); max-height: 74vh; }
		.rail { flex-direction: row; overflow-x: auto; padding: 0 0 .6rem; border-right: 0; border-bottom: 1px solid var(--dl-line, #2a2c33); }
		.rail button { flex: none; }
		.rail small { display: none; }
		.panel { padding: .9rem 0 0; }
	}
</style>
