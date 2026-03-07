<script lang="ts">
	import { base } from '$app/paths';
	import { brand } from '$lib/brand';
</script>

<section class="relative pt-32 pb-20 px-6 overflow-hidden">
	<div
		class="absolute inset-0 bg-[radial-gradient(ellipse_at_top,_rgba(245,158,11,0.08)_0%,_transparent_60%)]"
	></div>
	<div
		class="absolute -top-1/2 -left-1/2 w-[200%] h-[200%] pointer-events-none"
		style="background: radial-gradient(ellipse at 30% 50%, rgba(245,158,11,0.04) 0%, transparent 50%), radial-gradient(ellipse at 70% 50%, rgba(59,130,246,0.03) 0%, transparent 50%);"
	></div>

	<div class="relative mx-auto max-w-4xl text-center">
		<div
			class="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-dl-bg-card border border-dl-border text-xs text-dl-text-muted mb-8"
		>
			<span class="w-1.5 h-1.5 rounded-full bg-dl-success animate-pulse"></span>
			v{brand.version} — 14개 분석 모듈 출시
		</div>

		<h1 class="text-5xl md:text-7xl font-extrabold tracking-tight leading-[1.1] mb-6">
			<span class="text-dl-text">공시의 숫자</span><br />
			<span
				class="bg-gradient-to-r from-dl-primary via-dl-primary-light to-dl-primary bg-clip-text text-transparent"
				>너머를 읽다</span
			>
		</h1>

		<p class="text-lg md:text-xl text-dl-text-muted max-w-2xl mx-auto mb-10 leading-relaxed">
			DART 공시 문서를 완벽하게 분석하는 Python 라이브러리.<br />
			<span class="text-dl-text font-medium">숫자는 결과이고, 텍스트는 원인이다.</span> DartLab은 둘
			다 읽는다.
		</p>

		<div class="flex flex-wrap items-center justify-center gap-4 mb-16">
			<a
				href="#install"
				class="px-6 py-3 rounded-xl bg-gradient-to-r from-dl-primary to-dl-primary-dark text-dl-bg-dark font-semibold text-sm shadow-lg shadow-dl-primary/20 hover:shadow-dl-primary/40 hover:-translate-y-0.5 transition-all"
			>
				시작하기
			</a>
			<a
				href="{base}/docs/"
				class="px-6 py-3 rounded-xl bg-dl-bg-card border border-dl-border text-dl-text-muted font-medium text-sm hover:text-dl-text hover:border-dl-text-dim hover:-translate-y-0.5 transition-all"
			>
				문서 보기 →
			</a>
			<a
				href={brand.repo}
				target="_blank"
				rel="noopener"
				class="px-6 py-3 rounded-xl bg-dl-bg-card border border-dl-border text-dl-text-muted font-medium text-sm hover:text-dl-text hover:border-dl-text-dim hover:-translate-y-0.5 transition-all"
			>
				GitHub →
			</a>
		</div>

		<div class="grid grid-cols-2 md:grid-cols-4 gap-4 max-w-3xl mx-auto">
			{#each [
				{ value: '14', unit: '개', label: '분석 모듈' },
				{ value: '260', unit: '+', label: '상장사 데이터' },
				{ value: '95', unit: '%+', label: '매칭 커버리지' },
				{ value: 'MIT', unit: '', label: '라이선스' }
			] as stat}
				<div
					class="px-4 py-4 rounded-xl bg-dl-bg-card/50 border border-dl-border/50 hover:border-dl-primary/30 transition-all"
				>
					<div
						class="text-2xl font-extrabold bg-gradient-to-r from-dl-primary to-dl-accent bg-clip-text text-transparent"
					>
						{stat.value}<span class="text-sm">{stat.unit}</span>
					</div>
					<div class="text-xs text-dl-text-dim mt-1">{stat.label}</div>
				</div>
			{/each}
		</div>
	</div>
</section>
