<script lang="ts">
	import { Card } from '$lib/components/ui/card';
	import { ArrowDown, Copy, Check } from 'lucide-svelte';

	let copied = $state(false);

	const snippet = `import dartlab

c = dartlab.Company("005930")   # 삼성전자
c.panel("IS")                   # 손익계산서 전 분기
c.panel("CF")                   # 현금흐름표 · 문자열만 바꾸면 끝`;

	async function copy() {
		await navigator.clipboard.writeText(snippet);
		copied = true;
		setTimeout(() => (copied = false), 2000);
	}
</script>

<section id="quickstart" class="py-24 px-6">
	<div class="mx-auto max-w-2xl">
		<div class="text-center mb-12">
			<span
				class="text-xs font-semibold uppercase tracking-widest text-dl-primary mb-3 block"
				>빠른 시작</span
			>
			<h2 class="text-3xl md:text-4xl font-bold text-dl-text mb-4">3줄이면 끝</h2>
			<p class="text-dl-text-muted text-lg">
				종목코드 하나면 회사 이름·공시 상태·전 분기 재무제표가 자동으로 딸려온다.
			</p>
		</div>

		<Card class="!p-0 overflow-hidden">
			<div
				class="flex items-center justify-between px-4 py-2.5 bg-dl-bg-darker/80 border-b border-dl-border"
			>
				<span class="text-xs font-mono text-dl-primary">python</span>
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
			<pre class="p-4 font-mono text-sm leading-7 text-dl-text overflow-x-auto"><code
					><span class="text-purple-400">import</span><span class="text-dl-text">
dartlab</span>

<span class="text-dl-text">c = dartlab.</span><span class="text-cyan-400">Company</span
					><span class="text-dl-text-muted">(</span><span class="text-emerald-400"
						>"005930"</span
					><span class="text-dl-text-muted">)</span><span class="text-dl-text-dim"
						>   # 삼성전자</span
					>
<span class="text-dl-text">c.</span><span class="text-cyan-400">show</span
					><span class="text-dl-text-muted">(</span><span class="text-emerald-400"
						>"IS"</span
					><span class="text-dl-text-muted">)</span><span class="text-dl-text-dim"
						>                    # 손익계산서 전 분기</span
					>
<span class="text-dl-text">c.</span><span class="text-cyan-400">show</span
					><span class="text-dl-text-muted">(</span><span class="text-emerald-400"
						>"CF"</span
					><span class="text-dl-text-muted">)</span><span class="text-dl-text-dim"
						>                    # 현금흐름표 · 문자열만 바꾸면 끝</span
					></code
				></pre>
		</Card>

		<div
			class="mt-10 rounded-xl border border-dl-border bg-dl-bg-card px-6 py-5 flex items-start justify-between gap-6"
		>
			<div>
				<div class="text-sm font-semibold text-dl-text mb-1">실습은 노트북 섹션에서</div>
				<p class="text-sm text-dl-text-muted leading-relaxed">
					Colab · Molab · 로컬 마리모 · 같은 코드를 세 경로로 바로 돌려볼 수 있다.
				</p>
			</div>
			<a
				href="#notebooks"
				class="shrink-0 inline-flex items-center gap-1.5 px-4 py-2 rounded-lg bg-dl-primary/15 hover:bg-dl-primary/25 border border-dl-primary/40 text-dl-primary text-sm font-semibold transition-colors"
			>
				노트북으로
				<ArrowDown class="w-4 h-4" />
			</a>
		</div>
	</div>
</section>
