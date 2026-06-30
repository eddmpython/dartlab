<script lang="ts">
	interface Props {
		// ecosystem.json 노드 (심층 비재무 필드: 지배구조·인력·CF·감사·이익질·유동성·주주환원·업종위치)
		node: any;
		// companies/{code}.json (creditMetrics 등 · 없으면 null)
		detail: any | null;
		// 산업 분위(상위 %) · 부모 $derived 전달(node.industryRank/PeerCount 파생)
		peerPct: number | null;
	}
	let { node, detail, peerPct }: Props = $props();
</script>

	<div class="deep-tab">
		<!-- 지배구조 -->
		{#if node.govGrade}
			<details class="accordion">
				<summary>지배구조 <span class="acc-badge">등급 {node.govGrade}</span></summary>
				<div class="acc-body">
					{#if node.holderPct != null}
						<div class="acc-row"><span>최대주주 지분</span><span>{node.holderPct.toFixed(1)}%</span></div>
					{/if}
					{#if node.holderChange != null}
						<div class="acc-row"><span>지분 변동</span><span style:color={node.holderChange > 0 ? '#10b981' : node.holderChange < 0 ? '#ef4444' : '#94a3b8'}>{node.holderChange > 0 ? '+' : ''}{node.holderChange.toFixed(1)}%p</span></div>
					{/if}
					{#if node.stability}
						<div class="acc-row"><span>지분 안정성</span><span>{node.stability}</span></div>
					{/if}
				</div>
			</details>
		{/if}

		<!-- 인력/급여 -->
		{#if node.empCount}
			<details class="accordion">
				<summary>인력 <span class="acc-badge">{node.empCount.toLocaleString()}명</span></summary>
				<div class="acc-body">
					<div class="acc-row"><span>직원수</span><span>{node.empCount.toLocaleString()}명</span></div>
				</div>
			</details>
		{/if}

		<!-- 현금흐름 -->
		{#if node.cfPattern}
			<details class="accordion">
				<summary>현금흐름 <span class="acc-badge">{node.cfPattern}</span></summary>
				<div class="acc-body">
					<div class="acc-row"><span>CF 패턴</span><span>{node.cfPattern}</span></div>
					<p class="acc-note">영업/투자/재무 현금흐름의 부호 조합으로 분류한 8가지 유형</p>
				</div>
			</details>
		{/if}

		<!-- 감사 리스크 -->
		{#if node.auditRisk}
			<details class="accordion">
				<summary>감사 리스크 <span class="acc-badge" style:color={node.auditRisk === '안전' ? '#10b981' : node.auditRisk === '주의' || node.auditRisk === '고위험' ? '#ef4444' : '#fbbf24'}>{node.auditRisk}</span></summary>
				<div class="acc-body">
					<div class="acc-row"><span>감사 위험 등급</span><span>{node.auditRisk}</span></div>
				</div>
			</details>
		{/if}

		<!-- 이익의 질 -->
		{#if node.qualGrade}
			<details class="accordion">
				<summary>이익의 질 <span class="acc-badge">{node.qualGrade}</span></summary>
				<div class="acc-body">
					<div class="acc-row"><span>품질 등급</span><span>{node.qualGrade}</span></div>
					<p class="acc-note">발생액 비율(Accrual)과 Beneish M-Score 기반 판정</p>
				</div>
			</details>
		{/if}

		<!-- 유동성 -->
		{#if node.liqGrade}
			<details class="accordion">
				<summary>유동성 <span class="acc-badge">{node.liqGrade}</span></summary>
				<div class="acc-body">
					<div class="acc-row"><span>유동성 등급</span><span>{node.liqGrade}</span></div>
				</div>
			</details>
		{/if}

		<!-- 주주환원 -->
		{#if node.capClass}
			<details class="accordion">
				<summary>주주환원 <span class="acc-badge">{node.capClass}</span></summary>
				<div class="acc-body">
					<div class="acc-row"><span>환원 분류</span><span>{node.capClass}</span></div>
					<p class="acc-note">배당성향·자사주·증자감자 종합 분류</p>
				</div>
			</details>
		{/if}

		<!-- 신용등급 -->
		{#if detail?.creditMetrics}
			<details class="accordion">
				<summary>신용등급 <span class="acc-badge">{detail.creditMetrics.grade || detail.creditMetrics.creditGrade || '-'}</span></summary>
				<div class="acc-body">
					{#if detail.creditMetrics.totalScore != null}
						<div class="acc-row"><span>종합 점수</span><span>{detail.creditMetrics.totalScore.toFixed(1)}점</span></div>
					{/if}
					{#if detail.creditMetrics.grade}
						<div class="acc-row"><span>등급</span><span>{detail.creditMetrics.grade}</span></div>
					{/if}
				</div>
			</details>
		{/if}

		<!-- 업종 내 위치 -->
		{#if node.industryRank}
			<details class="accordion" open>
				<summary>업종 내 위치 <span class="acc-badge">{node.industryName}</span></summary>
				<div class="acc-body">
					<div class="acc-row"><span>매출 순위</span><span>{node.industryRank}위 / {node.industryPeerCount}사</span></div>
					{#if node.marketShare}
						<div class="acc-row"><span>상장사매출비중</span><span>{node.marketShare.toFixed(1)}%</span></div>
					{/if}
					{#if peerPct !== null}
						<div class="acc-row"><span>산업 분위</span><span>상위 {(100 - peerPct)}%</span></div>
					{/if}
				</div>
			</details>
		{/if}

		{#if !node.govGrade && !node.cfPattern && !node.qualGrade && !node.liqGrade && !node.capClass && !node.empCount && !detail?.creditMetrics}
			<div class="deep-empty">
				<p>심층 데이터가 아직 없습니다.</p>
				<p class="acc-note">빌드 파이프라인이 scan digest를 주입하면 여기에 표시됩니다.</p>
			</div>
		{/if}
	</div>

<style>
	/* 심층 탭 */
	.deep-tab {
		padding-top: 8px;
	}
	.accordion {
		border-bottom: 1px solid rgba(30, 36, 51, 0.5);
	}
	.accordion summary {
		padding: 10px 0;
		font-size: 13px;
		font-weight: 600;
		color: var(--color-dl-text);
		cursor: pointer;
		display: flex;
		justify-content: space-between;
		align-items: center;
		list-style: none;
	}
	.accordion summary::-webkit-details-marker {
		display: none;
	}
	.accordion summary::before {
		content: '▸';
		margin-right: 6px;
		color: var(--color-dl-text-dim);
		transition: transform 0.15s;
	}
	.accordion[open] summary::before {
		transform: rotate(90deg);
	}
	.acc-badge {
		font-size: 11px;
		font-weight: 500;
		color: var(--color-dl-text-muted);
		background: rgba(148, 163, 184, 0.08);
		padding: 1px 8px;
		border-radius: 4px;
		margin-left: auto;
	}
	.acc-body {
		padding: 0 0 12px 16px;
	}
	.acc-row {
		display: flex;
		justify-content: space-between;
		padding: 3px 0;
		font-size: 12px;
		color: var(--color-dl-text-muted);
	}
	.acc-note {
		font-size: 10px;
		color: var(--color-dl-text-dim);
		margin: 4px 0 0;
		line-height: 1.5;
	}
	.deep-empty {
		text-align: center;
		padding: 24px 0;
		color: var(--color-dl-text-dim);
		font-size: 13px;
	}
</style>
