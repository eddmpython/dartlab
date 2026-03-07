<script lang="ts">
	import { base } from '$app/paths';
</script>

<section class="py-24 px-6">
	<div class="mx-auto max-w-2xl text-center">
		<div
			class="p-8 md:p-12 rounded-2xl bg-gradient-to-b from-dl-bg-card to-dl-bg-darker border border-dl-border relative overflow-hidden"
		>
			<div
				class="absolute inset-0 bg-[radial-gradient(ellipse_at_center,_rgba(245,158,11,0.05)_0%,_transparent_70%)]"
			></div>
			<div class="relative">
				<h2 class="text-2xl md:text-3xl font-bold text-dl-text mb-4">공시 분석을 시작하세요</h2>
				<p class="text-dl-text-muted mb-8">숫자 너머의 이야기를 읽어보세요.</p>

				<div class="flex flex-wrap items-center justify-center gap-4">
					<a
						href="#install"
						class="px-6 py-3 rounded-xl bg-gradient-to-r from-dl-primary to-dl-primary-dark text-dl-bg-dark font-semibold text-sm shadow-lg shadow-dl-primary/20 hover:shadow-dl-primary/40 hover:-translate-y-0.5 transition-all"
					>
						설치하기
					</a>
					<a
						href="{base}/docs/"
						class="px-6 py-3 rounded-xl bg-dl-bg-card border border-dl-border text-dl-text-muted font-medium text-sm hover:text-dl-text hover:-translate-y-0.5 transition-all"
					>
						문서 보기 →
					</a>
				</div>
			</div>
		</div>
	</div>
</section>
