<script lang="ts">
	import { base } from '$app/paths';
	import { Button } from '$lib/components/ui/button';
</script>

<section class="dl-map-cta" aria-labelledby="map-cta-title">
	<div class="inner">
		<div class="left">
			<div class="kicker">시장 관계 분석</div>
			<h2 id="map-cta-title">산업 구조와 변화 근거를<br />한 화면에서</h2>
			<p class="lead">
				34개 산업의 구조와 파생 집계 흐름, 재무 변화 신호를 하나의 결정론적 장면에서 탐색합니다.
				후보와 사실을 섞지 않고, 근거가 비면 결론을 닫지 않는 Thesis Kill-Chain으로 가설을 검증합니다.
				<strong>모든 연결은 근거 상태를 함께 표시합니다.</strong>
			</p>
			<div class="ctas">
				<Button href="{base}/universe">Universe 열기 →</Button>
				<Button variant="secondary" href="{base}/map">산업지도 열기</Button>
			</div>
			<p class="disclaimer">
				dartlab 은 공시·재무 데이터를 시각화한다. 투자 자문 아님.
				DART 원본 공시·애널리스트 리포트와 함께 검증할 것.
			</p>
		</div>
		<div class="right">
			<div class="preview">
				<div class="preview-head">
					<span class="dot r"></span>
					<span class="dot y"></span>
					<span class="dot g"></span>
				</div>
				<div class="preview-body">
					<div class="preview-row">
						<span class="bubble" style="width:54px;height:54px;background:#0ea5e9;left:12%;top:8%"></span>
						<span class="bubble" style="width:72px;height:72px;background:#f97316;left:34%;top:22%"></span>
						<span class="bubble" style="width:48px;height:48px;background:#10b981;left:58%;top:10%"></span>
						<span class="bubble" style="width:60px;height:60px;background:#8b5cf6;left:70%;top:48%"></span>
						<span class="bubble" style="width:40px;height:40px;background:var(--dl-accent);left:20%;top:60%"></span>
						<span class="bubble" style="width:52px;height:52px;background:#fbbf24;left:46%;top:62%"></span>
						<span class="bubble small" style="width:20px;height:20px;background:#60a5fa;left:82%;top:22%"></span>
						<span class="bubble small" style="width:18px;height:18px;background:#34d399;left:8%;top:38%"></span>
						<svg class="flows" viewBox="0 0 400 240">
							<path d="M 60 40 Q 140 80 150 70" stroke="#fbbf24" stroke-width="2" fill="none" opacity="0.6" />
							<path d="M 170 70 Q 230 40 250 30" stroke="#fbbf24" stroke-width="3" fill="none" opacity="0.75" />
							<path d="M 265 35 Q 280 100 310 120" stroke="#fbbf24" stroke-width="2" fill="none" opacity="0.5" />
							<path d="M 150 70 Q 130 140 110 160" stroke="var(--dl-accent)" stroke-width="2" fill="none" opacity="0.4" />
						</svg>
					</div>
					<div class="preview-chips">
						<span class="chip g">● CURRENT DATA</span>
						<span class="chip n">파생 집계</span>
						<span class="chip w">근거 상태 표시</span>
					</div>
				</div>
			</div>
		</div>
	</div>
</section>

<style>
	.dl-map-cta {
		padding: 80px 24px;
		background: linear-gradient(180deg, #050811 0%, #0f1219 100%);
		color: #f1f5f9;
	}
	.inner {
		max-width: 1200px;
		margin: 0 auto;
		display: grid;
		grid-template-columns: 1fr 1fr;
		gap: 48px;
		align-items: center;
	}
	.kicker {
		font-size: 11px;
		color: var(--color-dl-primary);
		text-transform: uppercase;
		letter-spacing: 0.12em;
		font-weight: 600;
		margin-bottom: 12px;
	}
	h2 {
		font-size: 38px;
		font-weight: 700;
		line-height: 1.25;
		margin: 0 0 20px;
		letter-spacing: -0.02em;
	}
	.lead {
		font-size: 15px;
		line-height: 1.7;
		color: #cbd5e1;
		margin: 0 0 24px;
	}
	.lead strong {
		color: #fbbf24;
	}
	.ctas {
		display: flex;
		gap: 10px;
		flex-wrap: wrap;
	}
	.disclaimer {
		margin-top: 16px;
		font-size: 11px;
		color: #64748b;
		line-height: 1.6;
	}

	.preview {
		background: #0f1219;
		border: 1px solid #1e2433;
		border-radius: 12px;
		overflow: hidden;
		box-shadow: 0 24px 48px rgba(0, 0, 0, 0.4);
	}
	.preview-head {
		display: flex;
		align-items: center;
		gap: 6px;
		padding: 10px 14px;
		background: #050811;
		border-bottom: 1px solid #1e2433;
	}
	.preview-head .dot {
		width: 10px;
		height: 10px;
		border-radius: 50%;
	}
	.preview-head .dot.r {
		background: #f87171;
	}
	.preview-head .dot.y {
		background: #fbbf24;
	}
	.preview-head .dot.g {
		background: #34d399;
	}
	.preview-body {
		position: relative;
		height: 280px;
		background: radial-gradient(ellipse at center, rgba(30, 41, 59, 0.3) 0%, transparent 70%),
			#050811;
		overflow: hidden;
	}
	.bubble {
		position: absolute;
		border-radius: 50%;
		opacity: 0.85;
		filter: blur(0.3px);
	}
	.bubble.small {
		opacity: 0.6;
	}
	.flows {
		position: absolute;
		inset: 0;
		width: 100%;
		height: 100%;
		pointer-events: none;
	}
	.preview-chips {
		position: absolute;
		bottom: 12px;
		left: 12px;
		display: flex;
		gap: 6px;
		flex-wrap: wrap;
	}
	.chip {
		padding: 4px 10px;
		background: rgba(5, 8, 17, 0.85);
		border: 1px solid #1e2433;
		border-radius: 999px;
		font-size: 11px;
		color: #cbd5e1;
		backdrop-filter: blur(6px);
	}
	.chip.g {
		color: #34d399;
	}
	.chip.w {
		color: #fbbf24;
		border-color: rgba(251, 191, 36, 0.4);
	}

	@media (max-width: 900px) {
		.inner {
			grid-template-columns: 1fr;
		}
		h2 {
			font-size: 28px;
		}
	}
</style>
