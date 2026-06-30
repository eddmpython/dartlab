<script lang="ts">
	// 감사 리스크 스트립 · 연도 가로 세그먼트: 감사인(교체 경계 색 전환) + 의견 뱃지 + 특기사항 도트.
	// 데이터 규칙은 ReportPort.auditTrail 구현이 보장 (사업보고서 당기 행 · 사업연도 = 접수연도−1).
	import type { AuditYear } from '@dartlab/ui-contracts';

	interface Props {
		trail: AuditYear[]; // 연도 오름차순
	}
	let { trail }: Props = $props();

	// 같은 감사인 연속 구간(run) 으로 묶는다 · 교체 경계에서 색 전환
	const runs = $derived.by(() => {
		const out: { auditor: string; items: AuditYear[] }[] = [];
		for (const a of trail) {
			const last = out[out.length - 1];
			if (last && last.auditor === a.auditor) last.items.push(a);
			else out.push({ auditor: a.auditor, items: [a] });
		}
		return out;
	});
	const RUN_COLORS = ['#5b9bf0', '#a78bfa', '#22d3ee', '#fbbf24', '#34d399', '#fb923c'];
	const runColor = (ri: number) => RUN_COLORS[ri % RUN_COLORS.length];
	const isBad = (a: AuditYear) => a.opinion != null && a.opinion !== '적정';
	const opLabel = (a: AuditYear) => a.opinion ?? '·';
	const segTitle = (a: AuditYear) =>
		`FY${a.year} · ${a.auditor} · ${a.opinion ?? '의견 미기재'}${a.special ? '\n특기사항: ' + a.special.slice(0, 200) : ''}`;
	const changeCount = $derived(Math.max(0, runs.length - 1));
	const badCount = $derived(trail.filter(isBad).length);
</script>

<div class="audStrip" role="group" aria-label="감사 이력">
	<div class="audStripHead">
		<span class="audStripTitle">감사 이력</span>
		<span class="audStripMeta mono">
			{trail.length}년
			{#if changeCount > 0}<i> · 감사인 교체 {changeCount}회</i>{/if}
			{#if badCount > 0}<b class="audWarn"> · 비적정 {badCount}건</b>{/if}
		</span>
	</div>
	<div class="audRuns">
		{#each runs as run, ri (ri)}
			<div class="audRun" style={`--runC:${runColor(ri)}`}>
				<span class="audRunName" title={run.auditor}>{run.auditor}</span>
				<div class="audSegs">
					{#each run.items as a (a.year)}
						<div class={'audSeg' + (isBad(a) ? ' bad' : '')} title={segTitle(a)}>
							<span class="audYear mono">{String(a.year).slice(2)}</span>
							<span class={'audOp' + (isBad(a) ? ' bad' : '')}>{opLabel(a)}</span>
							{#if a.special}<i class="audDot" title={a.special.slice(0, 200)}></i>{/if}
						</div>
					{/each}
				</div>
			</div>
		{/each}
	</div>
</div>
