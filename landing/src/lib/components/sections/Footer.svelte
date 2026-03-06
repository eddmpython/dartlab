<script lang="ts">
	import { base } from '$app/paths';
</script>

<footer class="border-t border-dl-border bg-dl-bg-darker/50">
	<div class="mx-auto max-w-5xl px-6 py-12">
		<div class="grid md:grid-cols-4 gap-8 mb-8">
			<div>
				<div class="flex items-center gap-2.5 mb-3">
					<div class="w-7 h-7 rounded-lg bg-gradient-to-br from-dl-primary to-dl-accent flex items-center justify-center">
						<span class="text-xs font-bold text-dl-bg-dark">D</span>
					</div>
					<span class="text-sm font-bold text-dl-text">DartLab</span>
				</div>
				<p class="text-xs text-dl-text-dim leading-relaxed">
					DART 공시 문서를 완벽하게 분석하는 Python 라이브러리
				</p>
			</div>

			<div>
				<div class="text-xs font-semibold text-dl-text-muted mb-3 uppercase tracking-wider">프로젝트</div>
				<div class="space-y-2">
					<a href="https://github.com/eddmpython/dartlab" class="block text-sm text-dl-text-dim hover:text-dl-text transition-colors">GitHub</a>
					<a href="https://pypi.org/project/dartlab/" class="block text-sm text-dl-text-dim hover:text-dl-text transition-colors">PyPI</a>
					<a href="https://github.com/eddmpython/dartlab/releases/tag/data-v1" class="block text-sm text-dl-text-dim hover:text-dl-text transition-colors">데이터</a>
				</div>
			</div>

			<div>
				<div class="text-xs font-semibold text-dl-text-muted mb-3 uppercase tracking-wider">문서</div>
				<div class="space-y-2">
					<a href="https://eddmpython.github.io/dartlab/docs/" class="block text-sm text-dl-text-dim hover:text-dl-text transition-colors">시작하기</a>
					<a href="https://eddmpython.github.io/dartlab/docs/" class="block text-sm text-dl-text-dim hover:text-dl-text transition-colors">API 레퍼런스</a>
				</div>
			</div>

			<div>
				<div class="text-xs font-semibold text-dl-text-muted mb-3 uppercase tracking-wider">지원</div>
				<div class="space-y-3">
					<a href="https://github.com/eddmpython/dartlab/issues" class="block text-sm text-dl-text-dim hover:text-dl-text transition-colors">이슈 리포트</a>
					<a href="https://buymeacoffee.com/eddmpython" target="_blank" rel="noopener">
						<img src="https://cdn.buymeacoffee.com/buttons/v2/default-yellow.png" alt="Buy Me A Coffee" width="140" height="36" />
					</a>
				</div>
			</div>
		</div>

		<div class="pt-6 border-t border-dl-border flex flex-col md:flex-row items-center justify-between gap-3">
			<span class="text-xs text-dl-text-dim">MIT License</span>
			<span class="text-xs text-dl-text-dim">Made by <a href="https://github.com/eddmpython" class="text-dl-text-muted hover:text-dl-text transition-colors">eddmpython</a></span>
		</div>
	</div>
</footer>
