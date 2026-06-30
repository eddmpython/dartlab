<section class="py-24 px-6">
	<div class="mx-auto max-w-4xl">
		<div class="text-center mb-12">
			<span class="text-xs font-semibold uppercase tracking-widest text-dl-primary mb-3 block"
				>AI 분석</span
			>
			<h2 class="text-3xl md:text-4xl font-bold text-dl-text mb-4">
				코드 불필요. 그냥 물어본다.
			</h2>
			<p class="text-dl-text-muted text-lg max-w-2xl mx-auto">
				DartLab 이 데이터를 구조화해 LLM 에 먹인다. 자연어로 질문 &mdash;
				터미널에서도, Python 에서도.
			</p>
		</div>

		<div class="grid md:grid-cols-2 gap-5">
			<!-- Terminal -->
			<div
				class="rounded-lg overflow-hidden bg-[#0d1117] border border-dl-border shadow-lg shadow-black/20"
			>
				<div
					class="flex items-center gap-2 px-4 py-2.5 bg-white/[0.03] border-b border-dl-border"
				>
					<div class="flex gap-1.5">
						<span class="w-2.5 h-2.5 rounded-full bg-[#ff5f57]"></span>
						<span class="w-2.5 h-2.5 rounded-full bg-[#febc2e]"></span>
						<span class="w-2.5 h-2.5 rounded-full bg-[#28c840]"></span>
					</div>
					<span class="text-xs text-dl-text-dim font-mono ml-2">터미널</span>
				</div>
				<div class="p-4 font-mono text-xs leading-relaxed">
					<div class="text-dl-text-muted">
						<span class="text-dl-accent">$</span> dartlab ask "삼성전자 재무건전성 분석해줘"
					</div>
					<br />
					<div class="text-dl-text-dim">삼성전자 (005930) 분석 중...</div>
					<div class="text-dl-text-dim mb-2">재무·비율·인사이트 로드 중...</div>
					<br />
					<div class="text-dl-text">
						삼성전자는 <span class="text-dl-primary">재무건전성이 견고</span>:
					</div>
					<div class="text-dl-text-muted mt-1">
						&bull; 부채비율 31.8% (섹터 평균 45.2%)
					</div>
					<div class="text-dl-text-muted">
						&bull; 유동비율 258.6% &mdash; 안전선 한참 위
					</div>
					<div class="text-dl-text-muted">
						&bull; ROE 회복: 4 분기 동안 1.6% &rarr; 10.2%
					</div>
					<div class="text-dl-text-muted">&bull; 이자보상배율 22.1배</div>
				</div>
			</div>

			<!-- Python -->
			<div
				class="rounded-lg overflow-hidden bg-[#0d1117] border border-dl-border shadow-lg shadow-black/20"
			>
				<div
					class="flex items-center gap-2 px-4 py-2.5 bg-white/[0.03] border-b border-dl-border"
				>
					<div class="flex gap-1.5">
						<span class="w-2.5 h-2.5 rounded-full bg-[#ff5f57]"></span>
						<span class="w-2.5 h-2.5 rounded-full bg-[#febc2e]"></span>
						<span class="w-2.5 h-2.5 rounded-full bg-[#28c840]"></span>
					</div>
					<span class="text-xs text-dl-text-dim font-mono ml-2">Python</span>
				</div>
				<div class="p-4 font-mono text-xs leading-relaxed">
					<div>
						<span class="text-purple-400">import</span>
						<span class="text-dl-text">dartlab</span>
					</div>
					<br />
					<div class="text-dl-text-dim"># 한 줄 &mdash; stdout 으로 스트리밍</div>
					<div>
						<span class="text-dl-text">dartlab</span><span class="text-dl-text-muted"
							>.</span
						><span class="text-cyan-400">ask</span><span class="text-dl-text-muted"
							>(</span
						><span class="text-emerald-400">"AAPL 위험 분석"</span><span
							class="text-dl-text-muted">)</span
						>
					</div>
					<br />
					<div class="text-dl-text-dim"># 옵션 지정</div>
					<div>
						<span class="text-dl-text">dartlab</span><span class="text-dl-text-muted"
							>.</span
						><span class="text-cyan-400">ask</span><span class="text-dl-text-muted"
							>(</span
						>
					</div>
					<div class="pl-4">
						<span class="text-emerald-400">"삼성전자 배당 분석"</span><span
							class="text-dl-text-muted">,</span
						>
					</div>
					<div class="pl-4">
						<span class="text-dl-text">provider</span><span class="text-dl-text-muted"
							>=</span
						><span class="text-emerald-400">"openai"</span><span class="text-dl-text-muted"
							>,</span
						>
					</div>
					<div class="pl-4">
						<span class="text-dl-text">include</span><span class="text-dl-text-muted"
							>=[</span
						><span class="text-emerald-400">"dividend"</span><span
							class="text-dl-text-muted">,</span
						>
						<span class="text-emerald-400">"IS"</span><span class="text-dl-text-muted"
							>]</span
						>
					</div>
					<div><span class="text-dl-text-muted">)</span></div>
					<br />
					<div class="text-dl-text-dim"># 5 개 provider: ollama · openai ·</div>
					<div class="text-dl-text-dim"># oauth-codex · codex · custom</div>
				</div>
			</div>
		</div>

		<!-- AI 는 적극적 분석가 · 대화 중에 엔진 가정을 직접 바꾼다 -->
		<div class="mt-6 rounded-lg overflow-hidden bg-[#0d1117] border border-dl-border shadow-lg shadow-black/20">
			<div class="flex items-center gap-2 px-4 py-2.5 bg-white/[0.03] border-b border-dl-border">
				<span class="w-2 h-2 rounded-full bg-dl-primary"></span>
				<span class="text-xs text-dl-text-dim font-mono ml-1">AI 는 read-only 가 아니다 &mdash; 엔진 가정을 바꿀 수 있다</span>
			</div>
			<div class="p-4 font-mono text-xs leading-relaxed space-y-2">
				<div>
					<span class="text-dl-accent">you</span>
					<span class="text-dl-text-dim">›</span>
					<span class="text-dl-text">삼성전자 DCF 계산해봐</span>
				</div>
				<div>
					<span class="text-dl-primary">ai</span>
					<span class="text-dl-text-dim">›</span>
					<span class="text-dl-text-muted">c.analysis("valuation")</span>
					<span class="text-dl-text-dim">&rarr;</span>
					<span class="text-dl-warning">implied WACC 18.2% · 이 프로파일에는 높아 보임</span>
				</div>
				<div>
					<span class="text-dl-accent">you</span>
					<span class="text-dl-text-dim">›</span>
					<span class="text-dl-text">WACC 9%로 재계산</span>
				</div>
				<div>
					<span class="text-dl-primary">ai</span>
					<span class="text-dl-text-dim">›</span>
					<span class="text-dl-text-muted">c.analysis(</span><span class="text-emerald-400">"valuation"</span><span class="text-dl-text-muted">, overrides=&#123;</span><span class="text-emerald-400">"wacc"</span><span class="text-dl-text-muted">:</span>
					<span class="text-dl-accent">0.09</span><span class="text-dl-text-muted">&#125;)</span>
				</div>
				<div class="pl-6 text-dl-text">
					<span class="text-dl-text-dim">&rarr;</span> 수정된 적정가치 밴드: <span class="text-dl-success">91,200 ~ 115,400 원 / 주</span>
				</div>
			</div>
			<div class="px-4 py-3 border-t border-dl-border text-[11px] text-dl-text-dim leading-relaxed">
				AI 는 read-only 요약자가 아니다. <span class="text-dl-text">엔진 가정을 override</span>
				&mdash; WACC · 성장률 · 비교군 · 할인 기간 &mdash; 같은 세션 안에서 재계산한다. 운전대는 사용자가 잡는다.
			</div>
		</div>

		<div class="text-center mt-8">
			<p class="text-dl-text-dim text-xs">
				2 단 아키텍처가 구조화된 회사 데이터를 어떤 LLM 에든 먹인다. 기본 분석은 모든 provider 에서 동작.
				Tool-calling provider 는 더 깊이 들어간다.
			</p>
		</div>
	</div>
</section>
