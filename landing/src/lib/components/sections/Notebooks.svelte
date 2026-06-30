<script lang="ts">
	import { Card } from '$lib/components/ui/card';
	import { Copy, Check, ExternalLink } from 'lucide-svelte';

	type Notebook = {
		slug: string;
		title: string;
		subtitle: string;
	};

	const notebooks: Notebook[] = [
		{ slug: '01_company', title: 'Company', subtitle: '종목코드 하나로 재무/공시' },
		{ slug: '02_gather', title: 'gather', subtitle: '가격 · 수급 · 매크로 · 뉴스' },
		{ slug: '03_scan', title: 'scan', subtitle: '전종목 횡단' },
		{ slug: '04_quant', title: 'quant', subtitle: '25지표 + 9신호' },
		{ slug: '05_analysis', title: 'analysis', subtitle: '14축 + 전망 · 가치평가' },
		{ slug: '06_macro', title: 'macro', subtitle: '사이클 · 금리 · 자산' },
		{ slug: '07_credit', title: 'credit', subtitle: 'dCR 7축 등급' },
		{ slug: '08_story', title: 'story', subtitle: '구조화 보고서' },
		{ slug: '09_ai', title: 'ai', subtitle: 'ask · chat' },
		{ slug: '10_search', title: 'search', subtitle: '공시 검색' },
		{ slug: '11_listing', title: 'listing', subtitle: '법인 · 공시 목록' }
	];

	const colabBase =
		'https://colab.research.google.com/github/eddmpython/dartlab/blob/master/notebooks/colab/';
	const molabBase =
		'https://molab.marimo.io/github/eddmpython/dartlab/blob/master/notebooks/marimo/';

	const localCmd = 'uv run --with marimo marimo edit notebooks/marimo/01_company.py';

	let copied = $state(false);

	async function copy() {
		await navigator.clipboard.writeText(localCmd);
		copied = true;
		setTimeout(() => (copied = false), 2000);
	}
</script>

<section id="notebooks" class="py-24 px-6">
	<div class="mx-auto max-w-4xl">
		<div class="text-center mb-12">
			<span
				class="text-xs font-semibold uppercase tracking-widest text-dl-primary mb-3 block"
				>노트북</span
			>
			<h2 class="text-3xl md:text-4xl font-bold text-dl-text mb-4">실습 노트북</h2>
			<p class="text-dl-text-muted text-lg">
				11개 주제, Colab · Molab · 로컬 마리모 · 같은 코드로 돌려볼 수 있다.
			</p>
		</div>

		<div class="grid sm:grid-cols-2 gap-4">
			{#each notebooks as nb (nb.slug)}
				<div
					class="rounded-xl border border-dl-border bg-dl-bg-card p-5 flex flex-col gap-4"
				>
					<div>
						<div class="flex items-baseline gap-2">
							<span class="font-mono text-xs text-dl-text-dim"
								>{nb.slug.split('_')[0]}</span
							>
							<h3 class="text-lg font-bold text-dl-text">{nb.title}</h3>
						</div>
						<p class="text-sm text-dl-text-muted mt-1">{nb.subtitle}</p>
					</div>
					<div class="flex gap-2 mt-auto">
						<a
							href="{colabBase}{nb.slug}.ipynb"
							target="_blank"
							rel="noopener noreferrer"
							class="flex-1 inline-flex items-center justify-center gap-1.5 px-3 py-2 rounded-lg bg-dl-primary/15 hover:bg-dl-primary/25 border border-dl-primary/40 text-dl-primary text-sm font-semibold transition-colors"
						>
							Colab
							<ExternalLink class="w-3.5 h-3.5" />
						</a>
						<a
							href="{molabBase}{nb.slug}.py"
							target="_blank"
							rel="noopener noreferrer"
							class="flex-1 inline-flex items-center justify-center gap-1.5 px-3 py-2 rounded-lg bg-dl-bg-darker hover:bg-dl-bg-darker/60 border border-dl-border text-dl-text text-sm font-semibold transition-colors"
						>
							Molab
							<ExternalLink class="w-3.5 h-3.5" />
						</a>
					</div>
				</div>
			{/each}
		</div>

		<Card class="mt-12">
			<div class="text-xs font-mono text-dl-primary mb-3">로컬 마리모 편집</div>
			<p class="text-sm text-dl-text-muted leading-relaxed mb-4">
				Marimo 노트북은 <span class="text-dl-text">로컬</span>에서 편집하는 게 가장 빠르다.
				아래 명령어를 실행하면 브라우저에 편집기가 자동으로 뜬다. 파일 이름만 바꾸면 다른
				노트북도 같은 방식.
			</p>
			<div
				class="rounded-lg border border-dl-border bg-dl-bg-darker/80 overflow-hidden"
			>
				<div
					class="flex items-center justify-between px-4 py-2.5 border-b border-dl-border"
				>
					<span class="text-xs font-mono text-dl-text-dim">shell</span>
					<button
						onclick={copy}
						class="flex items-center gap-1 px-2 py-0.5 rounded text-xs text-dl-text-dim hover:text-dl-text transition-colors cursor-pointer"
					>
						{#if copied}
							<Check class="w-3.5 h-3.5 text-dl-success" />
						{:else}
							<Copy class="w-3.5 h-3.5" />
						{/if}
					</button>
				</div>
				<div class="p-4 font-mono text-sm overflow-x-auto">
					<span class="text-dl-text-dim select-none">$ </span>
					<span class="text-dl-text">{localCmd}</span>
				</div>
			</div>
			<p class="text-xs text-dl-text-dim mt-3 leading-relaxed">
				Marimo 는 코드만, Colab 은 마크다운 설명 + 코드 · 같은 구성을 두 포맷으로 유지한다.
			</p>
		</Card>
	</div>
</section>
