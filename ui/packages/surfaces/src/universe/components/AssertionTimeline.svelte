<script lang="ts">
	import type { UniverseAssertion, UniverseChangeMark } from '@dartlab/ui-contracts';

	interface Props {
		assertions?: readonly UniverseAssertion[];
		change?: UniverseChangeMark | null;
	}

	let { assertions = [], change = null }: Props = $props();
	let ordered = $derived([...assertions].sort((left, right) => left.availableAt.localeCompare(right.availableAt)));
</script>

<section class="timeline" aria-label="Assertion 시간선">
	<h4>ASSERTION TIMELINE</h4>
	{#if ordered.length}
		<ol>
			{#each ordered as assertion (assertion.assertionId)}
				<li class:retracted={assertion.status === 'retracted'}>
					<i aria-hidden="true"></i><div><strong>{assertion.status}</strong><span>유효 {assertion.validFrom || '미상'}</span><span>인지 {assertion.availableAt || '미상'}</span></div>
				</li>
			{/each}
		</ol>
	{:else if change}
		<ol><li><i aria-hidden="true"></i><div><strong>{change.kind}</strong><span>사건 {change.eventAt}</span><span>인지 {change.knownAt}</span></div></li></ol>
	{:else}
		<p>정확 assertion 이력이 아직 결속되지 않았습니다.</p>
	{/if}
</section>

<style>
	.timeline h4 { margin: 0 0 10px; color: #5d6e85; font: 600 8px/1 ui-monospace, monospace; letter-spacing: .1em; }
	.timeline ol { margin: 0; padding: 0; list-style: none; }
	.timeline li { position: relative; display: grid; grid-template-columns: 12px 1fr; gap: 7px; padding-bottom: 12px; }
	.timeline li::before { content: ''; position: absolute; left: 4px; top: 8px; bottom: -2px; border-left: 1px solid #26354a; }
	.timeline li:last-child::before { display: none; }
	.timeline i { position: relative; z-index: 1; width: 9px; height: 9px; border: 2px solid #64a8ff; border-radius: 50%; background: #0a0f17; }
	.timeline .retracted i { border-color: #e46b6b; }
	.timeline strong { display: block; color: #bac7d7; font-size: 10px; }
	.timeline span { display: inline-block; margin: 4px 8px 0 0; color: #64758c; font-size: 9px; }
	.timeline p { margin: 0; color: #69798f; font-size: 10px; line-height: 1.5; }
</style>
