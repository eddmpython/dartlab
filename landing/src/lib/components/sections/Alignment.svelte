<section class="py-24 px-6 bg-dl-bg-darker/50">
	<div class="mx-auto max-w-4xl">
		<div class="text-center mb-16">
			<h2 class="text-3xl md:text-4xl font-bold text-dl-text mb-4">공시 수평 정렬</h2>
			<p class="text-dl-text-muted text-lg">잘려 있는 공시를 하나의 시계열로 연결한다</p>
		</div>

		<div class="grid md:grid-cols-2 gap-6">
			<div class="p-6 rounded-2xl bg-dl-bg-card border border-dl-border">
				<div class="text-xs font-mono text-dl-text-dim mb-5 uppercase tracking-wider">
					보고서별 커버리지
				</div>

				<div class="space-y-3">
					<div class="grid grid-cols-[5rem_1fr] items-center gap-3">
						<span class="text-dl-text-muted text-xs text-right font-mono">1분기</span>
						<div class="h-8 rounded-lg bg-dl-bg-darker overflow-hidden relative">
							<div
								class="h-full w-1/4 bg-gradient-to-r from-dl-primary/50 to-dl-primary/20 rounded-lg flex items-center justify-center"
							>
								<span class="text-[10px] text-dl-primary-light font-semibold">Q1</span>
							</div>
						</div>
					</div>
					<div class="grid grid-cols-[5rem_1fr] items-center gap-3">
						<span class="text-dl-text-muted text-xs text-right font-mono">반기</span>
						<div class="h-8 rounded-lg bg-dl-bg-darker overflow-hidden">
							<div
								class="h-full w-1/2 bg-gradient-to-r from-dl-primary/50 to-dl-primary/20 rounded-lg flex items-center justify-center"
							>
								<span class="text-[10px] text-dl-primary-light font-semibold">Q1 + Q2</span>
							</div>
						</div>
					</div>
					<div class="grid grid-cols-[5rem_1fr] items-center gap-3">
						<span class="text-dl-text-muted text-xs text-right font-mono">3분기</span>
						<div class="h-8 rounded-lg bg-dl-bg-darker overflow-hidden">
							<div
								class="h-full w-3/4 bg-gradient-to-r from-dl-primary/50 to-dl-primary/20 rounded-lg flex items-center justify-center"
							>
								<span class="text-[10px] text-dl-primary-light font-semibold"
									>Q1 + Q2 + Q3</span
								>
							</div>
						</div>
					</div>
					<div class="grid grid-cols-[5rem_1fr] items-center gap-3">
						<span class="text-dl-text-muted text-xs text-right font-mono">사업</span>
						<div class="h-8 rounded-lg bg-dl-bg-darker overflow-hidden">
							<div
								class="h-full w-full bg-gradient-to-r from-dl-accent/50 to-dl-accent/20 rounded-lg flex items-center justify-center"
							>
								<span class="text-[10px] text-dl-accent-light font-semibold"
									>Q1 + Q2 + Q3 + Q4</span
								>
							</div>
						</div>
					</div>
				</div>

				<div class="flex items-center gap-2 mt-6 pt-4 border-t border-dl-border">
					<svg
						class="w-4 h-4 text-dl-primary shrink-0"
						fill="none"
						viewBox="0 0 24 24"
						stroke="currentColor"
						stroke-width="2"
						><path
							stroke-linecap="round"
							stroke-linejoin="round"
							d="M13 7l5 5m0 0l-5 5m5-5H6"
						/></svg
					>
					<span class="text-dl-text text-xs"
						>누적 구조에서 <span class="text-dl-primary font-semibold">개별 분기 실적</span>을
						역산한다</span
					>
				</div>
			</div>

			<div class="p-6 rounded-2xl bg-dl-bg-card border border-dl-border">
				<div class="text-xs font-mono text-dl-text-dim mb-5 uppercase tracking-wider">
					Bridge Matching
				</div>

				<div class="space-y-4 font-mono text-sm">
					<div class="grid grid-cols-3 gap-3 text-center">
						<div class="text-xs text-dl-text-dim">2022</div>
						<div class="text-xs text-dl-text-dim">2023</div>
						<div class="text-xs text-dl-text-dim">2024</div>
					</div>

					{#each [
						{ a: '매출액', b: '매출액', c: '수익(매출액)', changed: true },
						{ a: '영업이익', b: '영업이익', c: '영업이익', changed: false },
						{ a: '당기순이익', b: '당기순이익', c: '당기순이익(손실)', changed: true }
					] as row}
						<div class="grid grid-cols-3 gap-3 items-center">
							<div
								class="px-2 py-2 rounded-lg bg-dl-bg-darker text-xs text-dl-text text-center truncate"
							>
								{row.a}
							</div>
							<div
								class="px-2 py-2 rounded-lg bg-dl-bg-darker text-xs text-dl-text text-center truncate"
							>
								{row.b}
							</div>
							<div
								class="px-2 py-2 rounded-lg text-xs text-center truncate {row.changed
									? 'bg-dl-primary/10 text-dl-primary border border-dl-primary/30'
									: 'bg-dl-bg-darker text-dl-text'}"
							>
								{row.c}
							</div>
						</div>
						{#if row.changed}
							<div class="grid grid-cols-3 gap-3 -mt-2">
								<div></div>
								<div class="flex justify-center">
									<span class="text-[10px] text-dl-primary">──→</span>
								</div>
								<div class="flex justify-center">
									<span class="text-[9px] text-dl-primary font-medium">명칭 변경</span>
								</div>
							</div>
						{/if}
					{/each}
				</div>

				<div class="flex items-center gap-2 mt-6 pt-4 border-t border-dl-border">
					<svg
						class="w-4 h-4 text-dl-primary shrink-0"
						fill="none"
						viewBox="0 0 24 24"
						stroke="currentColor"
						stroke-width="2"
						><path
							stroke-linecap="round"
							stroke-linejoin="round"
							d="M13 7l5 5m0 0l-5 5m5-5H6"
						/></svg
					>
					<span class="text-dl-text text-xs"
						>금액 + 명칭 유사도로 <span class="text-dl-primary font-semibold">동일 계정</span
						>을 자동 연결한다</span
					>
				</div>
			</div>
		</div>
	</div>
</section>
