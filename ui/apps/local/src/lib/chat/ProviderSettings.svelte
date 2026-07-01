<script lang="ts">
	// AI 공급자 설정 본문(로직 + 카드). settings/providers 라우트와 챗의 공급자 다이얼로그가 공유(중복 제거).
	// provider 설정은 로컬 서버 admin(/api) 직접 호출. 챗 advanced tier(LLM provider 구성)의 전제다.
	interface ProviderInfo {
		available?: boolean;
		model?: string;
		label?: string;
		desc?: string;
		selected?: boolean;
		auth?: 'oauth' | 'api_key' | string;
		envKey?: string;
		signupUrl?: string;
		secretConfigured?: boolean;
	}

	let { onChange }: { onChange?: () => void } = $props();

	let providers = $state<Record<string, ProviderInfo>>({});
	let loading = $state(true);
	let loadError = $state('');
	let keyInputs = $state<Record<string, string>>({});
	let busy = $state<Record<string, string>>({});

	async function loadStatus(): Promise<void> {
		loading = true;
		loadError = '';
		try {
			const r = await fetch('/api/status');
			if (!r.ok) throw new Error(`HTTP ${r.status}`);
			const data = (await r.json()) as { providers?: Record<string, ProviderInfo> };
			providers = data.providers ?? {};
		} catch (e) {
			loadError = e instanceof Error ? e.message : String(e);
			providers = {};
		} finally {
			loading = false;
		}
	}

	async function selectProvider(key: string): Promise<void> {
		const r = await fetch('/api/ai/profile', {
			method: 'PUT',
			headers: { 'Content-Type': 'application/json' },
			body: JSON.stringify({ provider: key })
		});
		if (!r.ok) throw new Error(`HTTP ${r.status}`);
	}

	async function onSelect(key: string): Promise<void> {
		busy[key] = 'select';
		try {
			await selectProvider(key);
			await loadStatus();
			onChange?.();
		} catch (e) {
			loadError = e instanceof Error ? e.message : String(e);
		} finally {
			busy[key] = '';
		}
	}

	// API key 저장 후 자동 선택(사용자 두 번 클릭 방지).
	async function onSaveKey(key: string): Promise<void> {
		const apiKey = (keyInputs[key] ?? '').trim();
		if (!apiKey) return;
		busy[key] = 'save';
		try {
			const r = await fetch('/api/ai/profile/secrets', {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({ provider: key, apiKey })
			});
			if (!r.ok) throw new Error(`HTTP ${r.status}: ${await r.text().catch(() => '')}`);
			if (!providers[key]?.selected) {
				try {
					await selectProvider(key);
				} catch {
					/* 키는 저장됨. 선택 실패 시 수동 사용 가능 */
				}
			}
			keyInputs[key] = '';
			await loadStatus();
			onChange?.();
		} catch (e) {
			loadError = e instanceof Error ? e.message : String(e);
		} finally {
			busy[key] = '';
		}
	}

	async function onOauthLogin(key: string): Promise<void> {
		busy[key] = 'oauth';
		try {
			const r = await fetch('/api/oauth/authorize');
			if (!r.ok) throw new Error(`HTTP ${r.status}`);
			const { authUrl } = (await r.json()) as { authUrl: string };
			window.open(authUrl, '_blank', 'noopener,noreferrer');
			for (let i = 0; i < 150; i++) {
				await new Promise((res) => setTimeout(res, 2000));
				try {
					const s = (await fetch('/api/oauth/status').then((x) => x.json())) as {
						done?: boolean;
						error?: string;
					};
					if (s.done) {
						if (s.error) throw new Error(s.error);
						break;
					}
				} catch {
					/* 다음 폴링까지 */
				}
			}
			if (!providers[key]?.selected) {
				try {
					await selectProvider(key);
				} catch {
					/* 선택 실패. 수동 사용 가능 */
				}
			}
			await loadStatus();
			onChange?.();
		} catch (e) {
			loadError = e instanceof Error ? e.message : String(e);
		} finally {
			busy[key] = '';
		}
	}

	async function onOauthLogout(key: string): Promise<void> {
		busy[key] = 'logout';
		try {
			const r = await fetch('/api/oauth/logout', { method: 'POST' });
			if (!r.ok) throw new Error(`HTTP ${r.status}`);
			await loadStatus();
			onChange?.();
		} catch (e) {
			loadError = e instanceof Error ? e.message : String(e);
		} finally {
			busy[key] = '';
		}
	}

	function badge(p: ProviderInfo): string {
		return p.selected ? 'SELECTED' : p.available ? 'AVAILABLE' : 'NEEDS SETUP';
	}

	$effect(() => {
		void loadStatus();
	});

	const entries = $derived(Object.entries(providers));
</script>

{#if loadError}
	<div class="err">연결 오류: {loadError}</div>
{/if}

{#if loading}
	<div class="muted">확인 중…</div>
{:else if entries.length === 0}
	<div class="muted">가용 공급자 없음. 로컬 서버(/api) 연결을 확인하세요.</div>
{:else}
	<div class="cards">
		{#each entries as [key, p] (key)}
			{@const canSelect = !!p.available && !p.selected}
			<div class="card" class:selected={p.selected}>
				<div class="head">
					<span class="label">{p.label || key}</span>
					<span class="badge" class:on={p.selected} class:warn={!p.available}>{badge(p)}</span>
				</div>
				{#if p.desc}<div class="desc">{p.desc}</div>{/if}
				{#if p.model}<div class="model">{p.model}</div>{/if}

				<div class="actions">
					{#if canSelect}
						<button class="btn" disabled={!!busy[key]} onclick={() => onSelect(key)}>
							{busy[key] === 'select' ? '…' : '사용'}
						</button>
					{/if}

					{#if p.auth === 'oauth'}
						{#if p.available}
							<button class="btn ghost" disabled={!!busy[key]} onclick={() => onOauthLogout(key)}>
								{busy[key] === 'logout' ? '…' : '로그아웃'}
							</button>
						{:else}
							<button class="btn" disabled={!!busy[key]} onclick={() => onOauthLogin(key)}>
								{busy[key] === 'oauth' ? '브라우저 로그인 대기 중…' : '브라우저로 로그인'}
							</button>
						{/if}
					{:else if p.auth === 'api_key'}
						<div class="keyrow">
							<input
								type="password"
								bind:value={keyInputs[key]}
								placeholder={p.envKey || 'API Key'}
								autocomplete="off"
							/>
							<button
								class="btn"
								disabled={!!busy[key] || !(keyInputs[key] ?? '').trim()}
								onclick={() => onSaveKey(key)}
							>
								{busy[key] === 'save' ? '…' : '저장'}
							</button>
						</div>
						{#if p.signupUrl}
							<a class="signup" href={p.signupUrl} target="_blank" rel="noopener noreferrer">키 발급 ↗</a>
						{/if}
					{/if}
				</div>
			</div>
		{/each}
	</div>
{/if}

<style>
	.err {
		color: #f87171;
		font-size: 0.82rem;
		margin-bottom: 1rem;
	}
	.muted {
		color: var(--dl-ink-mute, #6b7280);
		font-size: 0.85rem;
		padding: 2rem 0;
	}
	.cards {
		display: flex;
		flex-direction: column;
		gap: 0.6rem;
	}
	.card {
		border: 1px solid var(--dl-line, #2a2c31);
		border-radius: 8px;
		padding: 0.85rem;
	}
	.card.selected {
		border-color: color-mix(in srgb, #10b981 40%, transparent);
		background: color-mix(in srgb, #10b981 6%, transparent);
	}
	.head {
		display: flex;
		align-items: center;
		gap: 0.5rem;
	}
	.label {
		font-size: 0.92rem;
		font-weight: 600;
	}
	.badge {
		margin-left: auto;
		font-family: var(--dl-font-mono, ui-monospace, monospace);
		font-size: 10px;
		color: var(--dl-ink-mute, #6b7280);
	}
	.badge.on {
		color: #34d399;
	}
	.badge.warn {
		color: #d1a054;
	}
	.desc {
		margin-top: 0.25rem;
		font-size: 0.8rem;
		color: var(--dl-ink-dim, #9aa0aa);
	}
	.model {
		margin-top: 0.2rem;
		font-family: var(--dl-font-mono, ui-monospace, monospace);
		font-size: 11px;
		color: var(--dl-ink-mute, #6b7280);
	}
	.actions {
		margin-top: 0.6rem;
		display: flex;
		flex-wrap: wrap;
		align-items: center;
		gap: 0.5rem;
	}
	.keyrow {
		display: flex;
		flex: 1 1 100%;
		gap: 0.4rem;
	}
	input {
		flex: 1;
		height: 32px;
		padding: 0 0.6rem;
		background: var(--dl-bg-base, #0f0f10);
		border: 1px solid var(--dl-line, #2a2c31);
		border-radius: 6px;
		color: var(--dl-ink, #e5e7eb);
		font-family: var(--dl-font-mono, ui-monospace, monospace);
		font-size: 12px;
	}
	.btn {
		height: 32px;
		padding: 0 0.8rem;
		border: 1px solid var(--dl-line, #2a2c31);
		border-radius: 6px;
		background: var(--dl-accent, #ff5a36);
		color: #fff;
		font-size: 0.82rem;
		cursor: pointer;
	}
	.btn.ghost {
		background: transparent;
		color: var(--dl-ink-dim, #9aa0aa);
	}
	.btn:disabled {
		opacity: 0.5;
		cursor: default;
	}
	.signup {
		font-size: 0.78rem;
		color: var(--dl-ink-dim, #9aa0aa);
		text-decoration: none;
	}
</style>
