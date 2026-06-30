<script lang="ts">
	import { base } from '$app/paths';
	import { Card } from '$lib/components/ui/card';
</script>

<section class="py-24 px-6">
	<div class="mx-auto max-w-4xl">
		<div class="text-center mb-16">
			<h2 class="text-3xl md:text-4xl font-bold text-dl-text mb-4">기업의 모든 진실은 이미 공시에 있다</h2>
			<p class="text-dl-text-muted text-lg max-w-2xl mx-auto">단지 읽기 어려울 뿐. 사업보고서는 200쪽이 넘고, 분기보고서는 쌓여가고, 필요한 데이터는 문서·포맷·연도에 흩어져 묻혀 있다.</p>
		</div>

		<div class="grid md:grid-cols-2 gap-5">
			<Card hover={false}>
				<div class="text-[11px] font-mono text-dl-text-dim mb-4 uppercase tracking-wider">현실</div>
				<div class="space-y-2.5 font-mono text-sm">
					<div class="flex items-center gap-3 text-dl-text-dim">
						<span class="text-dl-warning">✗</span> 200쪽 PDF 를 스크롤해서 한 섹션 찾기
					</div>
					<div class="flex items-center gap-3 text-dl-text-dim">
						<span class="text-dl-warning">✗</span> 재무 숫자는 한 도구, 텍스트는 다른 도구
					</div>
					<div class="flex items-center gap-3 text-dl-text-dim">
						<span class="text-dl-warning">✗</span> 작년 위험요소 비교? 수동 복붙
					</div>
					<div class="h-px bg-dl-border my-2"></div>
					<div class="flex items-center gap-3 text-dl-text-dim">
						<span class="text-dl-warning">✗</span> DART 도구는 EDGAR 에서 안 됨 (반대도)
					</div>
					<div class="flex items-center gap-3 text-dl-text-dim">
						<span class="text-dl-warning">✗</span> 공시를 AI 에 먹이기? 프롬프트 엔지니어링 몇 시간
					</div>
					<div class="flex items-center gap-3 text-dl-text-dim">
						<span class="text-dl-warning">✗</span> 2,700 개 종목 스크리닝? 직접 만들기
					</div>
				</div>
			</Card>

			<Card hover={false} class="border-dl-primary/20 bg-dl-bg-card">
				<div class="flex items-center gap-2 mb-4">
					<picture>
						<source srcset="{base}/avatar-analyze.webp" type="image/webp" />
						<img src="{base}/avatar-analyze.png" alt="" width="20" height="20" loading="lazy" decoding="async" class="rounded-full" />
					</picture>
					<span class="text-[11px] font-mono text-dl-primary uppercase tracking-wider">DartLab 으로</span>
				</div>
				<div class="space-y-2.5 font-mono text-sm">
					<div class="flex items-center gap-3 text-dl-text">
						<span class="text-dl-primary">✓</span> 모든 공시 topic, panel 로 구조화 완료
					</div>
					<div class="flex items-center gap-3 text-dl-text">
						<span class="text-dl-primary">✓</span> 텍스트 + 숫자 + 보고서, 하나의 Company 객체
					</div>
					<div class="flex items-center gap-3 text-dl-text">
						<span class="text-dl-primary">✓</span> 5년치 나란히 · `diff()` 한 줄
					</div>
					<div class="h-px bg-dl-border my-2"></div>
					<div class="flex items-center gap-3 text-dl-text">
						<span class="text-dl-primary">✓</span> DART · EDGAR 동일한 `Company` 인터페이스
					</div>
					<div class="flex items-center gap-3 text-dl-text">
						<span class="text-dl-primary">✓</span> 구조화된 panel topic 이 바로 LLM 컨텍스트로
					</div>
					<div class="flex items-center gap-3 text-dl-text">
						<span class="text-dl-accent">✓</span> 전 상장사 횡단 스캔
					</div>
				</div>
			</Card>
		</div>

		<!-- 코드 비교 -->
		<div class="grid md:grid-cols-2 gap-4 mt-8">
			<div class="rounded-lg overflow-hidden border border-dl-border bg-dl-bg-card/50">
				<div class="px-4 py-2 bg-white/[0.03] border-b border-dl-border">
					<span class="text-[10px] font-mono text-dl-warning uppercase tracking-wider">DartLab 없이</span>
				</div>
				<pre class="p-4 font-mono text-xs text-dl-text-dim leading-relaxed overflow-x-auto"><code><span class="text-dl-text-dim"># 1. DART 에서 PDF 다운로드</span>
pdf = download_report("005930", "2024")
<span class="text-dl-text-dim"># 2. PDF 에서 표 추출</span>
tables = parse_pdf_tables(pdf)
<span class="text-dl-text-dim"># 3. 수동 계정 매핑</span>
mapped = manual_map(tables, my_schema)
<span class="text-dl-text-dim"># 4. 분기마다 반복...</span>
<span class="text-dl-text-dim"># 5. 종목마다 반복...</span>
<span class="text-dl-text-dim"># 6. 포맷 일치를 기도</span></code></pre>
			</div>

			<div class="rounded-lg overflow-hidden border border-dl-primary/30 bg-dl-bg-card">
				<div class="px-4 py-2 bg-dl-primary/5 border-b border-dl-primary/20">
					<span class="text-[10px] font-mono text-dl-primary uppercase tracking-wider">DartLab 으로</span>
				</div>
				<pre class="p-4 font-mono text-xs text-dl-text leading-relaxed overflow-x-auto"><code><span class="text-cyan-400">import</span> dartlab

c = dartlab.Company(<span class="text-dl-primary">"005930"</span>)
c.show("BS")       <span class="text-dl-text-dim"># 표준화된 재무상태표</span>
c.show("ratios")   <span class="text-dl-text-dim"># 47 개 재무비율</span>
c.diff()   <span class="text-dl-text-dim"># 5년치 변화</span></code></pre>
			</div>
		</div>
	</div>
</section>
