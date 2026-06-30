<script lang="ts">
	// 후원·기여 센터 · 감사-우선 단일 스크롤(좁은 편지형). 진입 = 헤더 SNS ♥ 버튼.
	// 순서: 소개 → 터미널을 만들게 해준 분들(Threads) → 후원해주신 분들 → 함께하는 법(의견·이슈 + 후원 박스).
	// 후원금 캡션·계좌/스폰서는 셸 주입(TerminalBrandLinks). 미주입 항목은 줄 숨김(가짜 금지).
	import type { Lang } from '../lib/types';
	import type { TerminalBrandLinks, SupportPerson } from '../lib/hosts';
	import { Heart, Coffee, Landmark, MessageCircle, MessagesSquare, Bug, Copy, Check, ArrowUpRight } from 'lucide-svelte';
	import { fetchGithubContributors } from '../lib/githubStars';

	interface Props {
		lang: Lang;
		open: boolean;
		onClose: () => void;
		links: TerminalBrandLinks;
		base: string; // 아바타 에셋 경로(runtime.env.basePath)
	}
	let { lang, open, onClose, links, base }: Props = $props();
	const T = (kr: string, en: string) => (lang === 'en' ? en : kr);

	// ── 사람들 (♦ 영감 · ♥ 후원 · ♣ 기여) ──
	// 영감·후원 = 셸 주입 SSOT(links.people, DARTLAB_BRAND_LINKS 정본). 기여 = GitHub contributors API 자동.
	const BADGE: Record<SupportPerson['kind'], { sym: string; cls: string; kr: string; en: string }> = {
		insp: { sym: '♦', cls: 'supRoleInsp', kr: '영감', en: 'inspiration' },
		support: { sym: '♥', cls: 'supRoleSupport', kr: '후원', en: 'support' },
		contrib: { sym: '♣', cls: 'supRoleContrib', kr: '기여', en: 'contributor' }
	};
	const curated = $derived(links.people ?? []); // 영감·후원 큐레이션(SSOT)
	const donors = $derived(links.donors ?? []); // 후원해주신 분 · 비면 섹션 숨김

	const monogram = (h: string) => (h.replace(/^@/, '')[0] ?? '?').toUpperCase();

	// GitHub 기여자 자동 · 다이얼로그 첫 오픈 시 1회(localStorage 6h 캐시). 봇·소유자 제외.
	let ghPeople = $state<SupportPerson[]>([]);
	let ghFetched = false;
	$effect(() => {
		if (!open || ghFetched) return;
		ghFetched = true;
		void fetchGithubContributors(links.repo).then((list) => {
			ghPeople = list.map((c) => ({ handle: '@' + c.login, url: c.url, image: c.avatar, kind: 'contrib' as const }));
		});
	});
	// 큐레이션 + GitHub 자동, 핸들 중복 제거(큐레이션 우선).
	const people = $derived.by<SupportPerson[]>(() => {
		const seen = new Set(curated.map((p) => p.handle.toLowerCase()));
		return [...curated, ...ghPeople.filter((p) => !seen.has(p.handle.toLowerCase()))];
	});

	let copied = $state(false);
	let copyTimer: ReturnType<typeof setTimeout> | null = null;
	async function copyAccount() {
		if (!links.account) return;
		try {
			await navigator.clipboard.writeText(links.account.number);
			copied = true;
			if (copyTimer) clearTimeout(copyTimer);
			copyTimer = setTimeout(() => (copied = false), 1500);
		} catch { /* 클립보드 권한 거부 등 · 무시 */ }
	}

	function onKey(e: KeyboardEvent) { if (e.key === 'Escape') onClose(); }

	// 모달을 document.body 로 portal. 조상의 transform·backdrop-filter(예: 스크롤 시 fixed 헤더의
	// backdrop-blur)가 position:fixed 의 containing block 을 가로채 모달이 헤더 박스 기준으로 잘리던 것을
	// 근본 차단. 어느 표면(터미널·랜딩 헤더·report·cards)에서 열든 항상 viewport 기준으로 고정된다.
	function portal(node: HTMLElement) {
		document.body.appendChild(node);
		return { destroy() { node.parentNode?.removeChild(node); } };
	}
</script>

<svelte:window onkeydown={open ? onKey : undefined} />

{#if open}
	<div class="scrimWrap" use:portal role="presentation" onclick={onClose}>
		<div class="scrModal supModal" role="dialog" aria-modal="true" aria-label={T('후원·기여', 'Support & contribute')} onclick={(e) => e.stopPropagation()}>
			<div class="scrHead">
				<span class="scrTitle">{T('함께 만들기', 'BUILD TOGETHER')}</span>
				<button class="scrClose" onclick={onClose} aria-label="close">✕</button>
			</div>
			<div class="supBody">
				<!-- ① 소개 -->
				<div class="supHero">
					<picture>
						<source srcset="{base}/avatar-celebrate.webp" type="image/webp" />
						<img src="{base}/avatar-celebrate.png" alt="" width="60" height="60" onerror={(e) => ((e.currentTarget as HTMLImageElement).src = `${base}/avatar.png`)} />
					</picture>
					<p class="supIntro">
						{T(
							'DartLab은 전자공시(DART·EDGAR) 데이터로 다양한 금융 연구를 오픈소스로 공개하는 연구소입니다. 터미널·라이브러리·블로그 모두 무료입니다.',
							'DartLab is an open-source lab running financial research on DART·EDGAR filings. The terminal, library, and blog are all free.'
						)}
					</p>
				</div>

				<!-- ② 터미널을 만들게 해준 분들 -->
				{#if people.length}
					<section class="supSec supSecCenter">
						<div class="supSecLabel">{T('터미널을 만들게 해준 분들', 'PEOPLE BEHIND THIS TERMINAL')}</div>
						<p class="supSecNote">{T('이 터미널은 Threads에서 받은 피드백에서 시작됐고, GitHub에서 함께 만들어집니다.', 'It began with feedback on Threads and is built together on GitHub.')}</p>
						{#each people.filter((p) => p.postUrl) as p (p.handle)}
							<a class="supPostLink" href={p.postUrl} target="_blank" rel="noopener">{T('영감을 준 스레드 보기', 'See the inspiring thread')} <ArrowUpRight size={11} /></a>
						{/each}
						<div class="supChips">
							{#each people as p (p.handle)}
								<a class="supPerson" href={p.url} target="_blank" rel="noopener">
									{#if p.image}
										<img class="supAv" src={p.image} alt="" width="30" height="30" />
									{:else}
										<span class="supAv supMono">{monogram(p.handle)}</span>
									{/if}
									<span class="supHandle">{p.handle}</span>
									<span class={'supRole ' + BADGE[p.kind].cls} title={T(BADGE[p.kind].kr, BADGE[p.kind].en)}>{BADGE[p.kind].sym}</span>
								</a>
							{/each}
						</div>
					</section>
				{/if}

				<!-- ③ 후원해주신 분들 -->
				{#if donors.length}
					<section class="supSec">
						<div class="supSecLabel">{T('후원해주신 분들', 'SUPPORTERS')}</div>
						<div class="supChips">
							{#each donors as d (d.name)}
								{#if d.url}
									<a class="supDonor" href={d.url} target="_blank" rel="noopener"><Heart size={12} /> {d.name}</a>
								{:else}
									<span class="supDonor"><Heart size={12} /> {d.name}</span>
								{/if}
							{/each}
						</div>
					</section>
				{/if}

				<!-- ④ 함께하는 법 -->
				<section class="supSec">
					<div class="supSecLabel">{T('함께하는 법', 'WAYS TO JOIN')}</div>
					<div class="supActs">
						<a class="supAct" href={links.threads} target="_blank" rel="noopener"><MessageCircle size={14} /> {T('스레드 의견', 'Threads')}</a>
						<a class="supAct" href={`${links.repo}/discussions`} target="_blank" rel="noopener"><MessagesSquare size={14} /> {T('토론', 'Discuss')}</a>
						<a class="supAct" href={`${links.repo}/issues/new`} target="_blank" rel="noopener"><Bug size={14} /> {T('이슈·제보', 'Issue')}</a>
					</div>
					<div class="supDonate">
						<a class="supPay supCoffee" href={links.coffee} target="_blank" rel="noopener">
							<Coffee size={15} /> <span class="supPayName">Buy Me a Coffee</span> <span class="supPayArr"><ArrowUpRight size={13} /></span>
						</a>
						{#if links.sponsors}
							<a class="supPay supSponsor" href={links.sponsors} target="_blank" rel="noopener">
								<Heart size={15} /> <span class="supPayName">GitHub Sponsors</span> <span class="supPayArr"><ArrowUpRight size={13} /></span>
							</a>
						{/if}
						{#if links.account}
							<div class="supPay supAccount">
								<Landmark size={15} />
								<span class="supPayName supAcct">
									<b>{links.account.bank}</b> <span class="mono">{links.account.number}</span> <span class="supAcctHolder">{links.account.holder}</span>
								</span>
								<button class="supCopy" onclick={copyAccount} aria-label={T('계좌번호 복사', 'copy account number')}>
									{#if copied}<Check size={13} /> {T('복사됨', 'copied')}{:else}<Copy size={13} /> {T('복사', 'copy')}{/if}
								</button>
							</div>
						{/if}
						<p class="supDonateNote">{T('후원금은 데이터 비용과 온디바이스 AI 연구에 보탬이 됩니다.', 'Support goes to data costs and on-device AI research.')}</p>
					</div>
				</section>
			</div>
		</div>
	</div>
{/if}

<style>
	/* 자기완결 모달 크롬 · terminal.css 없는 셸(landing 헤더 등)에서도 동작하도록 베이스 포함(var 폴백 필수).
	   터미널 안에선 global terminal.css 와 값 동일(중복 무해). */
	/* 호스트(라이트/다크) 테마와 무관하게 모달은 자기 다크 팔레트로 고정 · 랜딩 라이트모드가 --dl-bg-raised·
	   --dl-ink 만 라이트로 덮고 --dl-bg(칩·후원박스)는 다크 폴백이라 흰배경+검은박스로 깨지던 것 차단. 값은
	   terminal.css 다크와 동일(터미널 안에선 재선언=무해). amber=accent(브랜드색 추종). */
	.scrimWrap { position: fixed; inset: 0; z-index: 200; background: rgba(4, 7, 13, 0.72); backdrop-filter: blur(2px); display: flex; align-items: center; justify-content: center; padding: 28px; --dl-bg: #0a0e16; --dl-bg-raised: #0e141f; --dl-ink: #e2e8f0; --dl-ink-mute: #8a93a3; --dl-ink-dim: #5b6473; --dl-line: #1b2130; --dl-line-strong: #2a3142; --amber: var(--dl-accent); }
	.scrModal { width: min(960px, 96vw); max-height: 88vh; display: flex; flex-direction: column; background: var(--dl-bg-raised, #0e141f); border: 1px solid var(--dl-line-strong, #2a3142); border-radius: 8px; box-shadow: 0 24px 80px rgba(0, 0, 0, 0.6); overflow: hidden; font-family: var(--dl-font-ui, 'Pretendard Variable', 'Inter', ui-sans-serif, system-ui, sans-serif); color: var(--dl-ink, #e2e8f0); }
	.scrHead { display: flex; align-items: center; gap: 12px; padding: 7px 12px; border-bottom: 1px solid var(--dl-line, #1b2130); }
	.scrTitle { font-family: var(--dl-font-mono, 'JetBrains Mono', ui-monospace, monospace); font-weight: 700; font-size: 12px; letter-spacing: 0.14em; color: var(--amber, var(--amber)); text-transform: uppercase; }
	.scrClose { margin-left: auto; background: none; border: none; color: var(--dl-ink-dim, #5b6473); font-size: 14px; line-height: 1; cursor: pointer; padding: 2px 6px; border-radius: 3px; }
	.scrClose:hover { color: var(--dl-ink, #e2e8f0); background: rgba(255, 255, 255, 0.06); }

	/* 좁은 편지형 · 폭만 560 으로 좁힘(.scrModal 뒤 선언 → 우선) */
	.supModal { width: min(560px, 94vw); }
	/* flex:1+min-height:0 · 88vh 모달 안에서 본문이 줄어들어 내부 스크롤되게(헤더 고정). 없으면 본문이
	   콘텐츠 높이로 안 줄고 모달 overflow:hidden 에 잘려 헤더까지 밀리며 클립되던 것 교정. */
	.supBody { flex: 1 1 auto; min-height: 0; padding: 16px 18px 18px; overflow-y: auto; display: flex; flex-direction: column; gap: 18px; }

	.supHero { display: flex; gap: 12px; align-items: flex-start; }
	.supHero picture img { border-radius: 50%; flex: 0 0 auto; }
	.supIntro { margin: 2px 0 0; font-size: 12.5px; line-height: 1.65; color: var(--dl-ink, #e2e8f0); }

	.supSec { display: flex; flex-direction: column; gap: 8px; }
	.supSecCenter { align-items: center; text-align: center; }
	.supSecCenter .supChips { justify-content: center; }
	.supSecCenter .supPostLink { align-self: center; }
	.supSecLabel { font-family: var(--dl-font-mono, 'JetBrains Mono', ui-monospace, monospace); font-size: 10.5px; font-weight: 700; letter-spacing: 0.12em; text-transform: uppercase; color: var(--dl-ink-mute, #8a93a3); }
	.supSecNote { margin: -2px 0 2px; font-size: 11.5px; line-height: 1.5; color: var(--dl-ink-mute, #8a93a3); }

	.supChips { display: flex; flex-wrap: wrap; gap: 7px; }
	.supPerson { display: inline-flex; align-items: center; gap: 8px; padding: 4px 10px 4px 4px; border: 1px solid var(--dl-line, #1b2130); border-radius: 999px; background: var(--dl-bg, #0a0e16); color: var(--dl-ink, #e2e8f0); text-decoration: none; transition: border-color 0.15s, background 0.15s; }
	.supPerson:hover { border-color: var(--dl-line-strong, #2a3142); background: rgba(255, 255, 255, 0.04); }
	.supAv { width: 30px; height: 30px; border-radius: 50%; flex: 0 0 auto; object-fit: cover; }
	.supMono { display: flex; align-items: center; justify-content: center; font-family: var(--dl-font-mono, 'JetBrains Mono', ui-monospace, monospace); font-size: 13px; font-weight: 700; color: #0a0e16; background: linear-gradient(135deg, var(--dl-accent-light), #fb7185); }
	.supHandle { font-size: 12.5px; display: inline-flex; align-items: center; gap: 4px; }
	.supRole { font-size: 11px; line-height: 1; }
	.supRoleInsp { color: var(--amber, var(--amber)); }
	.supRoleSupport { color: #fb7185; }
	.supRoleContrib { color: #4ade80; }
	.supPostLink { display: inline-flex; align-items: center; gap: 3px; align-self: flex-start; font-size: 11px; color: var(--amber, var(--amber)); text-decoration: none; opacity: 0.9; }
	.supPostLink:hover { text-decoration: underline; }

	.supDonor { display: inline-flex; align-items: center; gap: 5px; padding: 4px 11px; border: 1px solid var(--dl-line, #1b2130); border-radius: 999px; font-size: 12px; color: var(--dl-ink, #e2e8f0); text-decoration: none; }
	.supDonor :global(svg) { color: #fb7185; }

	.supActs { display: grid; grid-template-columns: repeat(3, 1fr); gap: 7px; }
	.supAct { display: inline-flex; align-items: center; justify-content: center; gap: 6px; padding: 7px 8px; border: 1px solid var(--dl-line, #1b2130); border-radius: 6px; font-size: 12px; color: var(--dl-ink, #e2e8f0); text-decoration: none; transition: border-color 0.15s, background 0.15s; }
	.supAct:hover { border-color: var(--dl-line-strong, #2a3142); background: rgba(255, 255, 255, 0.04); }

	.supDonate { display: flex; flex-direction: column; gap: 7px; margin-top: 2px; }
	.supPay { display: flex; align-items: center; gap: 10px; padding: 10px 12px; border: 1px solid var(--dl-line, #1b2130); border-radius: 7px; background: var(--dl-bg, #0a0e16); color: var(--dl-ink, #e2e8f0); text-decoration: none; font-size: 12.5px; transition: border-color 0.15s, background 0.15s; }
	.supPay:hover { border-color: var(--dl-line-strong, #2a3142); background: rgba(255, 255, 255, 0.04); }
	.supPayName { font-weight: 600; }
	.supPayArr { margin-left: auto; color: var(--dl-ink-dim, #5b6473); display: inline-flex; }
	.supCoffee :global(svg:first-child) { color: #ffdd00; }
	.supSponsor :global(svg:first-child) { color: #fb7185; }
	.supAccount { cursor: default; }
	.supAccount :global(svg:first-child) { color: var(--amber, var(--amber)); }
	.supAcct { display: inline-flex; align-items: baseline; gap: 7px; flex-wrap: wrap; font-weight: 400; }
	.supAcct .mono { font-family: var(--dl-font-mono, 'JetBrains Mono', ui-monospace, monospace); font-variant-numeric: tabular-nums; letter-spacing: 0.02em; }
	.supAcctHolder { color: var(--dl-ink-mute, #8a93a3); font-size: 11.5px; }
	.supCopy { margin-left: auto; display: inline-flex; align-items: center; gap: 4px; padding: 5px 9px; border: 1px solid var(--dl-line-strong, #2a3142); border-radius: 5px; background: transparent; color: var(--dl-ink-mute, #8a93a3); font-size: 11px; font-family: var(--dl-font-mono, 'JetBrains Mono', ui-monospace, monospace); cursor: pointer; transition: color 0.15s, border-color 0.15s; }
	.supCopy:hover { color: var(--dl-ink, #e2e8f0); border-color: var(--dl-ink-dim, #5b6473); }
	.supDonateNote { margin: 4px 2px 0; font-size: 11px; line-height: 1.55; color: var(--dl-ink-mute, #8a93a3); }
</style>
