<script lang="ts">
	import { onMount } from 'svelte';
	import type {
		UniverseKnowledgeContent,
		UniverseKnowledgeEdge,
		UniverseKnowledgeNode,
		UniverseKnowledgeScene
	} from '@dartlab/ui-contracts';
	import { parseKnowledgeArticle } from '../knowledgeArticle';

	interface RelatedKnowledge {
		edge: UniverseKnowledgeEdge;
		node: UniverseKnowledgeNode;
	}

	interface Props {
		node: UniverseKnowledgeNode;
		scene: UniverseKnowledgeScene;
		content: UniverseKnowledgeContent | null;
		contentLoading: boolean;
		contentError: string | null;
		domainLabel: string;
		onClose: () => void;
		onNavigate: (nodeId: string) => void;
	}

	let { node, scene, content, contentLoading, contentError, domainLabel, onClose, onNavigate }: Props = $props();
	let dialog: HTMLElement;
	const longFormKeys = new Set(['bodyPreview', 'procedure', 'expectedOutputs', 'failureModes', 'forbidden', 'examples', 'runtimeCompatibility']);
	let related = $derived(scene.edges.flatMap((edge): RelatedKnowledge[] => {
		if (edge.sourceId !== node.nodeId && edge.targetId !== node.nodeId) return [];
		const otherId = edge.sourceId === node.nodeId ? edge.targetId : edge.sourceId;
		const other = scene.nodes.find((candidate) => candidate.nodeId === otherId);
		return other ? [{ edge, node: other }] : [];
	}));
	let facts = $derived(Object.entries(node.attributes)
		.filter(([key, value]) => !longFormKeys.has(key) && value !== '' && value !== null)
		.slice(0, 16));
	let contractGroups = $derived(['procedure', 'expectedOutputs', 'failureModes', 'forbidden', 'examples']
		.flatMap((key) => {
			const value = node.attributes[key];
			return typeof value === 'string' && value ? [{ key, items: value.split('\n').filter(Boolean) }] : [];
		}));
	let runtimeCompatibility = $derived(typeof node.attributes.runtimeCompatibility === 'string' ? node.attributes.runtimeCompatibility : '');
	let articleText = $derived(typeof node.attributes.bodyPreview === 'string' && node.attributes.bodyPreview
		? node.attributes.bodyPreview
		: content?.kind === 'text' ? content.text : '');
	let blocks = $derived(parseKnowledgeArticle(articleText));

	function formatBytes(value: number | null): string {
		if (value === null) return '기록 없음';
		if (value >= 1e9) return `${(value / 1e9).toLocaleString('ko-KR', { maximumFractionDigits: 1 })} GB`;
		if (value >= 1e6) return `${(value / 1e6).toLocaleString('ko-KR', { maximumFractionDigits: 1 })} MB`;
		if (value >= 1e3) return `${(value / 1e3).toLocaleString('ko-KR', { maximumFractionDigits: 1 })} KB`;
		return `${value.toLocaleString()} B`;
	}

	function keydown(event: KeyboardEvent): void {
		if (event.key === 'Escape') {
			event.preventDefault();
			onClose();
			return;
		}
		if (event.key !== 'Tab') return;
		const focusable = [...dialog.querySelectorAll<HTMLElement>(
			'a[href], button:not([disabled]), audio[controls], video[controls], [tabindex]:not([tabindex="-1"])'
		)].filter((element) => element.getClientRects().length > 0);
		if (focusable.length === 0) {
			event.preventDefault();
			dialog.focus();
			return;
		}
		const first = focusable[0];
		const last = focusable.at(-1);
		if (event.shiftKey && (document.activeElement === first || document.activeElement === dialog)) {
			event.preventDefault();
			last?.focus();
		} else if (!event.shiftKey && document.activeElement === last) {
			event.preventDefault();
			first?.focus();
		}
	}

	onMount(() => {
		const previousFocus = document.activeElement instanceof HTMLElement ? document.activeElement : null;
		const previousOverflow = document.documentElement.style.overflow;
		document.documentElement.style.overflow = 'hidden';
		dialog?.focus();
		return () => {
			document.documentElement.style.overflow = previousOverflow;
			previousFocus?.focus();
		};
	});
</script>

<div class="articleBackdrop" role="presentation" onclick={(event) => { if (event.target === event.currentTarget) onClose(); }}>
	<div class="knowledgeArticle" role="dialog" aria-modal="true" aria-labelledby="knowledge-article-title" tabindex="-1" bind:this={dialog} onkeydown={keydown}>
		<header class="articleTopbar">
			<div><i></i><b>DARTLAB KNOWLEDGE</b><span>{scene.receipt.sourceRevision.slice(0, 9)}</span></div>
			<button type="button" onclick={onClose} aria-label="지식 문서 닫기">닫기 <kbd>ESC</kbd></button>
		</header>

		<div class="articleLayout">
			<nav class="articleToc" aria-label="지식 문서 목차">
				<span>CONTENTS</span>
				<a href="#article-overview">개요</a>
				{#if facts.length > 0}<a href="#article-facts">핵심 정보</a>{/if}
				{#if content || contentLoading || contentError}<a href="#article-source">원문 구조</a>{/if}
				{#if contractGroups.length > 0 || runtimeCompatibility}<a href="#article-contract">운영 계약</a>{/if}
				<a href="#article-evidence">근거와 계보</a>
				{#if related.length > 0}<a href="#article-related">연결 지식</a>{/if}
			</nav>

			<article class="articleBody">
				<header class="articleHero" id="article-overview">
					<div class="articleEyebrow"><span>{domainLabel}</span><b class:derived={node.lane === 'derived'}>{node.lane}</b><em>{node.kind}</em></div>
					<h1 id="knowledge-article-title">{node.label}</h1>
					<p>{node.secondaryLabel}</p>
					<div class="heroReceipt">
						<div><span>RELATIONS</span><b>{related.length.toLocaleString()}</b></div>
						<div><span>EVIDENCE</span><b>{node.evidenceRefs.length.toLocaleString()}</b></div>
						<div><span>REVISION</span><b>{scene.receipt.sourceRevision.slice(0, 9)}</b></div>
						<div><span>LANE</span><b>{node.lane.toLocaleUpperCase()}</b></div>
					</div>
				</header>

				{#if facts.length > 0}
					<section class="articleSection" id="article-facts">
						<header><span>01</span><div><b>핵심 정보</b><p>현재 장면과 원천에서 확인된 구조화 속성입니다.</p></div></header>
						<dl class="factGrid">{#each facts as [key, value] (key)}<div><dt>{key}</dt><dd>{typeof value === 'number' ? value.toLocaleString() : String(value)}</dd></div>{/each}</dl>
					</section>
				{/if}

				{#if blocks.length > 0}
					<section class="articleSection proseSection" id="article-source">
						<header><span>02</span><div><b>본문</b><p>Skill OS 또는 원본 텍스트를 안전한 문서 블록으로 구성했습니다.</p></div></header>
						<div class="articleProse">
							{#each blocks as block, index (index)}
								{#if block.kind === 'heading'}<svelte:element this={block.level === 2 ? 'h2' : 'h3'}>{block.text}</svelte:element>
								{:else if block.kind === 'paragraph'}<p>{block.text}</p>
								{:else if block.kind === 'list'}<ul>{#each block.items as item (item)}<li>{item}</li>{/each}</ul>
								{:else}<div class="codeBlock"><span>{block.language || 'TEXT'}</span><pre>{block.text}</pre></div>{/if}
							{/each}
						</div>
					</section>
				{:else if content || contentLoading || contentError}
					<section class="articleSection" id="article-source">
						<header><span>02</span><div><b>원문 구조</b><p>revision에 고정된 실제 원문을 형식에 맞춰 읽습니다.</p></div></header>
						{#if contentLoading}<div class="articleState"><i></i>원문을 읽는 중입니다.</div>
						{:else if contentError}<div class="articleError">{contentError}</div>
						{:else if content?.kind === 'image'}<img class="articleMedia" src={content.contentRef} alt={content.title} />
						{:else if content?.kind === 'video'}<!-- svelte-ignore a11y_media_has_caption --><video class="articleMedia" src={content.contentRef} controls preload="metadata"></video>
						{:else if content?.kind === 'audio'}<audio class="articleAudio" src={content.contentRef} controls preload="metadata"></audio>
						{:else if content?.kind === 'json'}
							<div class="treeDocument">{#each content.tree.slice(0, 72) as item (item.nodeId)}<div style:--depth={item.depth}><i>{item.valueKind === 'object' ? '{}' : item.valueKind === 'array' ? '[]' : '·'}</i><b>{item.key}</b>{#if item.childCount > 0}<span>{item.childCount}</span>{:else}<code>{item.value}</code>{/if}</div>{/each}</div>
						{:else if content?.kind === 'table'}
							<div class="sourceMetrics"><div><span>ROWS</span><b>{content.tableMeta.totalRows?.toLocaleString() ?? content.rows.length}</b></div><div><span>COLUMNS</span><b>{content.columns.length}</b></div><div><span>FILE</span><b>{formatBytes(content.tableMeta.fileSizeBytes)}</b></div><div><span>TRANSFER</span><b>{formatBytes(content.tableMeta.transferredBytes)}</b></div></div>
							<div class="articleTable"><table><thead><tr>{#each content.columns as column (column)}<th>{column}</th>{/each}</tr></thead><tbody>{#each content.rows.slice(0, 8) as row, index (index)}<tr>{#each content.columns as column (column)}<td>{row[column]}</td>{/each}</tr>{/each}</tbody></table></div>
							{#if content.schema.length > 0}<div class="dataDictionary"><h3>데이터 사전</h3>{#each content.schema as column (column.name)}<div><b>{column.name}</b><span>{column.logicalType || column.physicalType}</span><code>{column.physicalType}</code></div>{/each}</div>{/if}
						{:else if content}<div class="binaryArticle"><b>{content.mimeType}</b><p>이 형식은 원본 주소와 파일 계보를 중심으로 제공합니다.</p><a href={content.contentRef} target="_blank" rel="noreferrer">원본 열기</a></div>{/if}
					</section>
				{/if}

				{#if contractGroups.length > 0 || runtimeCompatibility}
					<section class="articleSection" id="article-contract">
						<header><span>03</span><div><b>운영 계약</b><p>절차, 기대 출력, 실패 조건과 금지 규칙을 분리해 읽습니다.</p></div></header>
						<div class="contractGrid">
							{#each contractGroups as group (group.key)}<section><h3>{group.key}</h3><ol>{#each group.items as item (item)}<li>{item}</li>{/each}</ol></section>{/each}
							{#if runtimeCompatibility}<section><h3>runtimeCompatibility</h3><pre>{runtimeCompatibility}</pre></section>{/if}
						</div>
					</section>
				{/if}

				<section class="articleSection" id="article-evidence">
					<header><span>{contractGroups.length > 0 || runtimeCompatibility ? '04' : '03'}</span><div><b>근거와 계보</b><p>주장 레인과 원본 주소를 분리해 검산할 수 있습니다.</p></div></header>
					<div class="evidenceLedger">
						<div><span>PRIMARY SOURCE</span>{#if node.sourceRef.startsWith('https://')}<a href={node.sourceRef} target="_blank" rel="noreferrer">{node.sourceRef}</a>{:else}<code>{node.sourceRef}</code>{/if}</div>
						{#each node.evidenceRefs as evidenceRef (evidenceRef)}<div><span>EVIDENCE</span><code>{evidenceRef}</code></div>{/each}
						{#if content}<div><span>FILE HISTORY</span><a href={content.fileMeta.historyRef} target="_blank" rel="noreferrer">수정 이력 열기</a></div><div><span>FILE COMMIT</span><code>{content.fileMeta.lastCommitId ?? '기록 없음'}</code></div><div><span>BLOB</span><code>{content.fileMeta.blobId || '기록 없음'}</code></div>{/if}
					</div>
				</section>
			</article>

			<aside class="articleContext" id="article-related">
				<header><span>CONTEXT</span><b>{related.length}</b></header>
				<p>현재 지식과 직접 연결된 개체입니다. 선택하면 같은 문서 안에서 문맥을 이동합니다.</p>
				<div>{#each related as item (item.edge.edgeId)}<button type="button" onclick={() => onNavigate(item.node.nodeId)}><i class:derived={item.edge.lane === 'derived'}></i><span><b>{item.node.label}</b><small>{item.edge.relation} · {item.edge.lane}</small></span></button>{/each}</div>
			</aside>
		</div>
	</div>
</div>

<style>
	.articleBackdrop { position: fixed; z-index: 80; inset: 0; padding: 18px; background: rgba(2, 5, 9, .76); backdrop-filter: blur(16px); }
	.knowledgeArticle { width: min(1480px, 100%); height: 100%; margin: 0 auto; overflow: hidden; border: 1px solid rgba(112, 137, 170, .24); border-radius: 18px; outline: none; color: #dce5f2; background: radial-gradient(circle at 48% 0, rgba(48, 79, 120, .12), transparent 32%), #080d14; box-shadow: 0 36px 120px rgba(0, 0, 0, .62); }
	.knowledgeArticle button:focus-visible, .knowledgeArticle a:focus-visible, .knowledgeArticle audio:focus-visible, .knowledgeArticle video:focus-visible { outline: 1px solid #79afea; outline-offset: 2px; }
	.articleTopbar { height: 52px; display: flex; align-items: center; justify-content: space-between; padding: 0 18px; border-bottom: 1px solid rgba(98, 122, 155, .15); background: rgba(8, 13, 21, .92); }
	.articleTopbar div { display: flex; align-items: center; gap: 9px; }
	.articleTopbar i { width: 7px; height: 7px; border-radius: 50%; background: #75b8ff; box-shadow: 0 0 14px rgba(117, 184, 255, .68); }
	.articleTopbar b, .articleTopbar span { color: #8396ae; font: 650 8px/1 ui-monospace, monospace; letter-spacing: .11em; }
	.articleTopbar span { color: #465a73; }
	.articleTopbar button { border: 1px solid rgba(109, 133, 164, .2); border-radius: 8px; padding: 7px 9px; color: #9baec4; background: rgba(25, 35, 50, .5); font-size: 9px; cursor: pointer; }
	.articleTopbar kbd { margin-left: 5px; color: #60738b; font: 600 7px/1 ui-monospace, monospace; }
	.articleLayout { height: calc(100% - 52px); display: grid; grid-template-columns: 158px minmax(0, 1fr) 260px; overflow: hidden; }
	.articleToc { padding: 28px 18px; border-right: 1px solid rgba(98, 122, 155, .12); }
	.articleToc span { display: block; margin-bottom: 16px; color: #465a73; font: 650 7px/1 ui-monospace, monospace; letter-spacing: .14em; }
	.articleToc a { display: block; border-left: 1px solid #26374c; padding: 8px 0 8px 12px; color: #7589a2; font-size: 9px; text-decoration: none; }
	.articleToc a:hover { border-color: #72abed; color: #d8e3ef; }
	.articleBody { min-width: 0; overflow-y: auto; scroll-behavior: smooth; padding: 0 clamp(24px, 4vw, 68px) 80px; }
	.articleHero { padding: 56px 0 38px; border-bottom: 1px solid rgba(103, 126, 157, .15); }
	.articleEyebrow { display: flex; align-items: center; gap: 8px; }
	.articleEyebrow span, .articleEyebrow b, .articleEyebrow em { border: 1px solid rgba(102, 129, 164, .2); border-radius: 999px; padding: 5px 7px; color: #7890ad; font: 650 7px/1 ui-monospace, monospace; font-style: normal; text-transform: uppercase; }
	.articleEyebrow b { border-color: rgba(86, 190, 145, .28); color: #70bd9b; }
	.articleEyebrow b.derived { border-color: rgba(214, 158, 79, .3); color: #d1a05d; }
	.articleHero h1 { max-width: 900px; margin: 20px 0 8px; color: #f0f4f9; font-size: clamp(34px, 5vw, 66px); line-height: .98; letter-spacing: -.055em; font-weight: 560; overflow-wrap: anywhere; }
	.articleHero > p { max-width: 760px; margin: 0; color: #74879f; font-size: 12px; line-height: 1.65; overflow-wrap: anywhere; }
	.heroReceipt { margin-top: 34px; display: grid; grid-template-columns: repeat(4, 1fr); gap: 7px; }
	.heroReceipt div, .sourceMetrics div { padding: 11px; border: 1px solid rgba(99, 123, 155, .13); border-radius: 9px; background: rgba(15, 23, 34, .5); }
	.heroReceipt span, .sourceMetrics span { display: block; color: #4b6079; font: 600 7px/1 ui-monospace, monospace; }
	.heroReceipt b, .sourceMetrics b { display: block; margin-top: 8px; color: #a9b9cc; font: 650 11px/1 ui-monospace, monospace; }
	.articleSection { padding: 42px 0 8px; scroll-margin-top: 12px; }
	.articleSection > header { display: grid; grid-template-columns: 30px minmax(0, 1fr); gap: 12px; align-items: start; margin-bottom: 22px; }
	.articleSection > header > span { color: #4b6685; font: 600 8px/1 ui-monospace, monospace; }
	.articleSection > header b { display: block; color: #d8e2ee; font-size: 19px; font-weight: 560; }
	.articleSection > header p { margin: 6px 0 0; color: #60748d; font-size: 9px; line-height: 1.5; }
	.factGrid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 1px; margin: 0; border: 1px solid rgba(95, 120, 152, .14); border-radius: 11px; overflow: hidden; background: rgba(99, 123, 154, .12); }
	.factGrid div { min-width: 0; padding: 13px 14px; background: #0a1018; }
	.factGrid dt { color: #52667e; font: 600 7px/1 ui-monospace, monospace; }
	.factGrid dd { margin: 8px 0 0; color: #9cacc0; font-size: 10px; line-height: 1.5; white-space: pre-wrap; overflow-wrap: anywhere; }
	.articleProse { max-width: 820px; }
	.articleProse h2, .articleProse h3 { margin: 34px 0 12px; color: #e2e9f2; font-size: 22px; letter-spacing: -.025em; font-weight: 580; }
	.articleProse h3 { font-size: 17px; }
	.articleProse p, .articleProse li { color: #a3b0c1; font-size: 12px; line-height: 1.82; }
	.articleProse ul { margin: 12px 0 22px; padding-left: 20px; }
	.articleProse li { margin: 7px 0; }
	.codeBlock { margin: 20px 0; overflow: hidden; border: 1px solid rgba(95, 121, 154, .2); border-radius: 11px; background: #060a10; }
	.codeBlock span { display: block; padding: 9px 12px; border-bottom: 1px solid rgba(95, 121, 154, .15); color: #55708f; font: 650 7px/1 ui-monospace, monospace; }
	.codeBlock pre { margin: 0; overflow-x: auto; padding: 16px; color: #b5c8de; font: 500 10px/1.75 ui-monospace, monospace; }
	.sourceMetrics { display: grid; grid-template-columns: repeat(4, 1fr); gap: 7px; margin-bottom: 14px; }
	.articleTable { overflow: auto; border: 1px solid rgba(99, 124, 156, .16); border-radius: 10px; }
	.articleTable table { width: 100%; border-collapse: collapse; font-size: 8px; white-space: nowrap; }
	.articleTable th, .articleTable td { max-width: 240px; padding: 9px 10px; overflow: hidden; border-bottom: 1px solid rgba(89, 112, 143, .11); color: #8498b1; text-align: left; text-overflow: ellipsis; }
	.articleTable th { position: sticky; top: 0; color: #b4c3d5; background: #111925; }
	.dataDictionary { margin-top: 22px; }
	.dataDictionary h3 { color: #cbd6e3; font-size: 14px; }
	.dataDictionary > div { display: grid; grid-template-columns: minmax(140px, 1fr) .7fr .7fr; gap: 12px; padding: 9px 0; border-bottom: 1px solid rgba(90, 114, 145, .1); font-size: 8px; }
	.dataDictionary b { color: #9eb0c6; } .dataDictionary span, .dataDictionary code { color: #60758f; }
	.contractGrid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 10px; }
	.contractGrid section { min-width: 0; border: 1px solid rgba(95, 121, 154, .14); border-radius: 10px; padding: 16px; background: rgba(10, 16, 24, .7); }
	.contractGrid h3 { margin: 0 0 12px; color: #8199b7; font: 650 8px/1 ui-monospace, monospace; text-transform: uppercase; }
	.contractGrid ol { margin: 0; padding-left: 18px; }
	.contractGrid li { margin: 7px 0; color: #9aaabd; font-size: 10px; line-height: 1.55; }
	.contractGrid pre { margin: 0; overflow: auto; color: #7890ac; font: 500 8px/1.6 ui-monospace, monospace; white-space: pre-wrap; }
	.treeDocument { overflow: hidden; border: 1px solid rgba(94, 119, 151, .16); border-radius: 10px; }
	.treeDocument > div { --depth: 0; display: grid; grid-template-columns: 22px minmax(100px, .6fr) auto minmax(0, 1fr); align-items: center; gap: 8px; padding: 8px 10px 8px calc(10px + var(--depth) * 14px); border-bottom: 1px solid rgba(84, 109, 140, .08); font-size: 8px; }
	.treeDocument i { color: #557394; font-style: normal; } .treeDocument b { color: #a8b7c9; } .treeDocument span, .treeDocument code { overflow: hidden; color: #697d95; text-overflow: ellipsis; white-space: nowrap; }
	.articleMedia { display: block; max-width: 100%; max-height: 620px; border-radius: 12px; background: #05080d; }
	.articleAudio { width: 100%; }
	.articleState, .articleError, .binaryArticle { border: 1px solid rgba(102, 128, 161, .16); border-radius: 10px; padding: 22px; color: #71869f; background: rgba(14, 22, 33, .5); font-size: 10px; }
	.articleState i { display: inline-block; width: 10px; height: 10px; margin-right: 8px; border: 1px solid #426489; border-top-color: #a2c7f2; border-radius: 50%; animation: spin .8s linear infinite; }
	.articleError { color: #c6848c; }
	.binaryArticle a { color: #7eafe8; }
	.evidenceLedger { border-top: 1px solid rgba(98, 122, 154, .16); }
	.evidenceLedger > div { display: grid; grid-template-columns: 120px minmax(0, 1fr); gap: 16px; padding: 12px 0; border-bottom: 1px solid rgba(98, 122, 154, .1); }
	.evidenceLedger span { color: #50647d; font: 650 7px/1.4 ui-monospace, monospace; }
	.evidenceLedger code, .evidenceLedger a { overflow: hidden; color: #7692b3; font: 500 8px/1.45 ui-monospace, monospace; text-overflow: ellipsis; white-space: nowrap; text-decoration: none; }
	.articleContext { overflow-y: auto; padding: 28px 18px; border-left: 1px solid rgba(98, 122, 155, .12); background: rgba(7, 11, 18, .46); }
	.articleContext > header { display: flex; justify-content: space-between; color: #50657f; font: 650 7px/1 ui-monospace, monospace; letter-spacing: .13em; }
	.articleContext > p { margin: 18px 0; color: #61758d; font-size: 9px; line-height: 1.55; }
	.articleContext button { width: 100%; display: grid; grid-template-columns: 8px minmax(0, 1fr); gap: 9px; border: 0; border-bottom: 1px solid rgba(91, 115, 146, .1); padding: 11px 0; color: inherit; background: transparent; text-align: left; cursor: pointer; }
	.articleContext button > i { width: 6px; height: 6px; margin-top: 4px; border-radius: 50%; background: #65bd99; box-shadow: 0 0 0 3px rgba(101, 189, 153, .08); }
	.articleContext button > i.derived { background: #d3a05b; box-shadow: 0 0 0 3px rgba(211, 160, 91, .08); }
	.articleContext button b { display: block; overflow: hidden; color: #a8b7ca; font-size: 9px; text-overflow: ellipsis; white-space: nowrap; }
	.articleContext button small { display: block; margin-top: 5px; color: #52677f; font: 600 7px/1 ui-monospace, monospace; text-transform: uppercase; }
	@keyframes spin { to { transform: rotate(360deg); } }
	@media (max-width: 980px) { .articleBackdrop { padding: 0; } .knowledgeArticle { border-radius: 0; } .articleLayout { grid-template-columns: minmax(0, 1fr); } .articleToc, .articleContext { display: none; } .articleBody { padding-inline: 20px; } }
	@media (max-width: 560px) { .articleHero { padding-top: 36px; } .articleHero h1 { font-size: 38px; } .heroReceipt, .sourceMetrics { grid-template-columns: repeat(2, 1fr); } .factGrid, .contractGrid { grid-template-columns: 1fr; } .evidenceLedger > div { grid-template-columns: 1fr; gap: 7px; } }
	@media (prefers-reduced-motion: reduce) { .articleState i { animation: none; } }
</style>
