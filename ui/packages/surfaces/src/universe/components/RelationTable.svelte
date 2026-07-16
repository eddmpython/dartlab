<script lang="ts">
	import type { UniverseScene } from '@dartlab/ui-contracts';

	interface Props {
		scene: UniverseScene;
		selectedId?: string | null;
		onSelect?: (nodeId: string) => void;
	}

	let { scene, selectedId = null, onSelect }: Props = $props();
	const predicateLabels: Readonly<Record<string, string>> = {
		suppliesTo: '공급', sellsTo: '판매', ownsStakeIn: '지분 보유', affiliatedWith: '계열',
		classifiedIn: '분류', filed: '공시', aggregateFlow: '산업 집계 흐름'
	};
	let nodeById = $derived(new Map(scene.nodes.map((node) => [node.nodeId, node])));
	let rows = $derived(scene.edges.filter((edge) => !selectedId || edge.sourceId === selectedId || edge.targetId === selectedId));
</script>

<div class="tableWrap">
	<table>
		<caption>{selectedId ? '선택 산업에 연결된 관계' : '현재 장면의 전체 관계'}</caption>
		<thead><tr><th>출발</th><th>관계</th><th>도착</th><th>상태</th><th>출처 위치</th></tr></thead>
		<tbody>
			{#each rows as edge (edge.edgeId)}
				<tr>
					<td><button onclick={() => onSelect?.(edge.sourceId)}>{nodeById.get(edge.sourceId)?.label ?? edge.sourceId}</button></td>
					<td>{predicateLabels[edge.predicate] ?? edge.predicate}</td>
					<td><button onclick={() => onSelect?.(edge.targetId)}>{nodeById.get(edge.targetId)?.label ?? edge.targetId}</button></td>
					<td><span class:derived={edge.lane === 'derived'} class:candidate={edge.lane === 'candidate'}>{edge.lane === 'derived' ? '파생' : '후보'}</span></td>
					<td><code>{edge.sourceRef}</code></td>
				</tr>
			{/each}
			{#if rows.length === 0}<tr><td colspan="5" class="empty">현재 조건에 표시할 관계가 없습니다.</td></tr>{/if}
		</tbody>
	</table>
</div>

<style>
	.tableWrap { overflow: auto; max-height: 560px; border: 1px solid #1b2535; border-radius: 16px; background: #0a0f18; }
	table { width: 100%; border-collapse: collapse; min-width: 760px; color: #b8c4d6; font-size: 12px; }
	caption { padding: 14px 16px; text-align: left; color: #7e8da3; font-size: 11px; }
	th { position: sticky; top: 0; z-index: 1; padding: 10px 14px; background: #0f1622; color: #68788f; text-align: left; font: 600 9px/1 ui-monospace, monospace; letter-spacing: .09em; }
	td { padding: 11px 14px; border-top: 1px solid #172131; }
	td button { border: 0; padding: 0; background: none; color: #dbe4f1; cursor: pointer; font: inherit; }
	td button:hover { color: #fff; text-decoration: underline; }
	code { color: #65758d; font-size: 10px; }
	td span { display: inline-flex; padding: 3px 7px; border-radius: 999px; font-size: 10px; }
	.derived { color: #80baff; background: rgba(100,168,255,.1); border: 1px solid rgba(100,168,255,.24); }
	.candidate { color: #f5c66b; background: rgba(245,184,75,.1); border: 1px dashed rgba(245,184,75,.34); }
	.empty { color: #64748b; text-align: center; padding: 40px; }
</style>
