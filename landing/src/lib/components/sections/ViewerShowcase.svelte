<script lang="ts">
	import { base } from '$app/paths';
	import { Button } from '$lib/components/ui/button';
</script>

<section class="viewer-showcase" aria-labelledby="viewer-showcase-title">
	<div class="inner">
		<div class="kicker">공시 뷰어 · 무설치</div>
		<h2 id="viewer-showcase-title">그 수평 맵을, 브라우저에서 직접</h2>
		<p class="lead">
			panel 은 제각각인 공시를 항목 × 기간 한 격자로 수평화한다 · 비교의 좌표축이다.
			공시 뷰어는 그 격자를 설치도 코드도 없이 브라우저에서 만지게 한다.
			셀을 누르면 공시 원문 근거로, 비교 모드를 켜면 여러 회사가 같은 행에 나란히 선다.
		</p>

		<div class="ctas">
			<Button href="{base}/viewer">공시 뷰어 열기 →</Button>
			<Button variant="secondary" href="{base}/compare">비교 모드 보기</Button>
		</div>
	</div>
</section>

<style>
	.viewer-showcase {
		padding: 80px 24px;
		background: #050811;
		color: #f1f5f9;
	}
	.inner {
		max-width: 880px;
		margin: 0 auto;
		text-align: center;
	}
	.kicker {
		font-size: 11px;
		color: var(--dl-accent);
		text-transform: uppercase;
		letter-spacing: 0.12em;
		font-weight: 700;
		margin-bottom: 12px;
	}
	h2 {
		font-size: 36px;
		line-height: 1.22;
		margin: 0 0 18px;
		font-weight: 800;
	}
	.lead {
		margin: 0 auto 24px;
		max-width: 680px;
		color: #cbd5e1;
		font-size: 15px;
		line-height: 1.72;
	}
	.ctas {
		display: flex;
		gap: 10px;
		justify-content: center;
		flex-wrap: wrap;
	}
	@media (max-width: 720px) {
		h2 {
			font-size: 28px;
		}
	}
</style>
