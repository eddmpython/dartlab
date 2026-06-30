<script lang="ts">
	import { base } from '$app/paths';
	import Header from '$lib/components/sections/Header.svelte';
	import Footer from '$lib/components/sections/Footer.svelte';
	import { brand } from '$lib/brand';
	import { buildAbsoluteUrl, buildBreadcrumbJsonLd, buildWebsiteJsonLd } from '$lib/seo';
	import { displayTier, tierLabel, type MarketSkill } from '$lib/skills/marketCatalog';
	import { hasSkillPage } from '$lib/skills/catalog';
	import { ArrowLeft, ExternalLink, ShieldAlert } from 'lucide-svelte';

	let { data } = $props<{ data: { skill: MarketSkill } }>();
	const skill = $derived(data.skill);

	const pageTitle = $derived(`${skill.title} · DartLab Skill Market`);
	const pageDesc = $derived(skill.summary ?? skill.intent ?? 'DartLab community Skill Market entry');
	const pageUrl = $derived(buildAbsoluteUrl(`skills/market/${skill.id}`));
	const jsonLd = $derived(
		JSON.stringify([
			buildWebsiteJsonLd(),
			buildBreadcrumbJsonLd([
				{ name: 'DartLab', url: brand.url },
				{ name: 'Skill Catalog', url: buildAbsoluteUrl('skills') },
				{ name: 'Skill Market', url: buildAbsoluteUrl('skills/market') },
				{ name: skill.title, url: pageUrl }
			])
		])
	);

	function join(values: string[] | undefined): string {
		return values?.length ? values.join(', ') : '미정';
	}
</script>

<svelte:head>
	<title>{pageTitle}</title>
	<meta name="description" content={pageDesc} />
	<link rel="canonical" href={pageUrl} />
	{@html `<script type="application/ld+json">${jsonLd}</script>`}
</svelte:head>

<Header context="skills" />

<main class="market-detail">
	<nav class="breadcrumb" aria-label="breadcrumb">
		<a href="{base}/skills/market"><ArrowLeft size={14} /> Skill Market</a>
		<span>/</span>
		<span>{skill.id}</span>
	</nav>

	<header class="head">
		<div class="kicker-row">
			<span class="tier">{tierLabel(skill)}</span>
			<span class="state">{skill.state ?? displayTier(skill)}</span>
		</div>
		<h1>{skill.title}</h1>
		<p>{skill.summary ?? skill.intent}</p>
		<div class="id-row">
			<code>{skill.id}</code>
			{#if skill.sourceUrl}
				<a href={skill.sourceUrl} target="_blank" rel="noopener noreferrer">
					Discussion 원문 <ExternalLink size={12} />
				</a>
			{/if}
		</div>
	</header>

	<section class="notice">
		<ShieldAlert size={16} />
		<span>
			{#if skill.itemPath}
				이 항목은 커뮤니티 Skill Market accepted snapshot 이다. 공식 builtin Skill OS 로 포함된다는 뜻이 아니다.
			{:else}
				이 항목은 아직 최종 스킬 snapshot 이 없는 커뮤니티 초안이다. 랜딩과 AI의 실행 후보로 취급하지 않는다.
			{/if}
			{#if skill.revisionStatus === 'pendingReview'}
				후속 댓글 {skill.pendingCommentCount ?? 0}개는 검토 대기 중이며 현재 화면은 accepted item snapshot 기준 최종본이다.
			{/if}
		</span>
	</section>

	<div class="layout">
		<aside class="meta">
			<section>
				<h2>Credits</h2>
				<dl>
					<dt>Originator</dt>
					<dd>{join(skill.credits?.originator ?? (skill.author ? [skill.author] : []))}</dd>
					<dt>Co-author</dt>
					<dd>{join(skill.credits?.coAuthor)}</dd>
					<dt>Reviewer</dt>
					<dd>{join(skill.credits?.reviewer)}</dd>
					<dt>Curator</dt>
					<dd>{join(skill.credits?.curator)}</dd>
				</dl>
			</section>

			<section>
				<h2>Source</h2>
				<dl>
					<dt>Author</dt>
					<dd>@{skill.author ?? 'unknown'}</dd>
					<dt>Updated</dt>
					<dd>{skill.updatedAt ?? 'unknown'}</dd>
					<dt>Accepted</dt>
					<dd>{skill.acceptedAt ? `${skill.acceptedAt}${skill.version ? ` · v${skill.version}` : ''}` : 'snapshot 없음'}</dd>
					<dt>Canonical</dt>
					<dd>{skill.canonicalSource ?? 'githubDiscussion'} · {skill.itemPath ?? 'Discussion draft'}</dd>
					<dt>Revision</dt>
					<dd>{skill.revisionStatus ?? 'current'}{skill.pendingCommentCount ? ` · pending ${skill.pendingCommentCount}` : ''}</dd>
					<dt>Discussion</dt>
					<dd>{skill.discussionNumber ? `#${skill.discussionNumber}` : 'unknown'}</dd>
				</dl>
			</section>
		</aside>

		<article class="body">
			<section>
				<h2>Intent</h2>
				<p>{skill.intent ?? skill.summary}</p>
			</section>

			<section class="spec-grid">
				<div>
					<h2>Inputs</h2>
					<ul>{#each (skill.inputs ?? []) as item}<li>{item}</li>{/each}</ul>
				</div>
				<div>
					<h2>Data Sources</h2>
					{#if skill.dataSources?.length}
						<ul>{#each skill.dataSources as item}<li>{item}</li>{/each}</ul>
					{:else}
						<p class="muted">데이터 소스가 아직 부족하다.</p>
					{/if}
				</div>
			</section>

			<section>
				<h2>DartLab Execution Plan</h2>
				{#if skill.executionPlan?.length}
					<ol class="execution-plan">
						{#each skill.executionPlan as step}
							<li>
								<strong>{step.engine ?? '엔진 미정'}</strong>
								<span>{step.purpose ?? '목적 미정'}</span>
								{#if step.failureMode}
									<small>실패 조건: {step.failureMode}</small>
								{/if}
							</li>
						{/each}
					</ol>
				{:else}
					<p class="muted">실제 DartLab 엔진 호출 계획이 아직 없다.</p>
				{/if}
			</section>

			<section>
				<h2>Procedure</h2>
				{#if skill.procedure?.length}
					<ol>{#each skill.procedure as item}<li>{item}</li>{/each}</ol>
				{:else}
					<p class="muted">실행 절차가 아직 부족하다.</p>
				{/if}
			</section>

			<section class="spec-grid">
				<div>
					<h2>Outputs</h2>
					<ul>{#each (skill.outputs ?? []) as item}<li>{item}</li>{/each}</ul>
				</div>
				<div>
					<h2>Output Schema</h2>
					{#if skill.outputSchema?.length}
						<ul>{#each skill.outputSchema as item}<li>{item}</li>{/each}</ul>
					{:else}
						<p class="muted">출력 스키마가 아직 부족하다.</p>
					{/if}
				</div>
			</section>

			<section>
				<h2>Criteria</h2>
				{#if skill.criteria?.length}
					<ul>{#each skill.criteria as item}<li>{item}</li>{/each}</ul>
				{:else}
					<p class="muted">판단 기준이 아직 부족하다.</p>
				{/if}
			</section>

			{#if skill.forbidden?.length}
				<section>
					<h2>Forbidden</h2>
					<ul>{#each skill.forbidden as item}<li>{item}</li>{/each}</ul>
				</section>
			{/if}

			{#if skill.completionCriteria?.length}
				<section>
					<h2>Completion Criteria</h2>
					<ul>{#each skill.completionCriteria as item}<li>{item}</li>{/each}</ul>
				</section>
			{/if}

			<section>
				<h2>Mapped Builtin Skills</h2>
				{#if skill.mappedBuiltinSkills?.length}
					<div class="chips">
						{#each skill.mappedBuiltinSkills as item}
							{#if hasSkillPage(item)}
								<a href="{base}/skills/{item}">{item}</a>
							{:else}
								<span class="muted-chip">{item}</span>
							{/if}
						{/each}
					</div>
				{:else}
					<p class="muted">아직 연결된 builtin skill 이 없다.</p>
				{/if}
			</section>

			{#if skill.missingDetails?.length}
				<section>
					<h2>Missing Details</h2>
					<ul>{#each skill.missingDetails as item}<li>{item}</li>{/each}</ul>
				</section>
			{/if}

			{#if skill.revisionStatus === 'pendingReview'}
				<section>
					<h2>Pending Comments</h2>
					<p class="muted">
						후속 댓글은 자동으로 최종 스킬을 바꾸지 않는다. Maintainer가 revision draft를 검토하고 다시 상태를
						승격해야 accepted item snapshot과 market index가 갱신된다.
					</p>
					<ul>
						{#each (skill.pendingCommentUrls ?? []) as url}
							<li><a href={url} target="_blank" rel="noopener noreferrer">{url}</a></li>
						{/each}
					</ul>
				</section>
			{/if}

			{#if skill.examples?.length}
				<section>
					<h2>Examples</h2>
					<ul>{#each skill.examples as item}<li>{item}</li>{/each}</ul>
				</section>
			{/if}
		</article>
	</div>
</main>

<Footer />

<style>
	.market-detail {
		min-height: 100vh;
		max-width: 1180px;
		margin: 0 auto;
		padding: 6.5rem 1.25rem 4rem;
		color: var(--dl-ink);
	}

	.breadcrumb {
		display: flex;
		gap: 0.4rem;
		margin-bottom: 1.25rem;
		color: var(--dl-ink-dim);
		font-family: var(--dl-font-mono);
		font-size: 0.78rem;
	}

	.breadcrumb a,
	.id-row a {
		display: inline-flex;
		align-items: center;
		gap: 0.3rem;
		color: var(--dl-orange);
		text-decoration: none;
	}

	.head {
		margin-bottom: 1rem;
		padding-bottom: 1.25rem;
		border-bottom: 1px solid var(--dl-line);
	}

	.kicker-row {
		display: flex;
		gap: 0.5rem;
		margin-bottom: 0.5rem;
	}

	.tier,
	.state {
		padding: 0.12rem 0.45rem;
		border-radius: 5px;
		background: rgba(251, 146, 60, 0.12);
		color: var(--dl-orange);
		font-family: var(--dl-font-mono);
		font-size: 0.72rem;
	}

	.state {
		background: var(--dl-bg-raised);
		color: var(--dl-ink-dim);
	}

	h1 {
		margin: 0 0 0.65rem;
		color: var(--dl-ink-print);
		font-size: clamp(1.8rem, 3.4vw, 2.7rem);
		line-height: 1.15;
	}

	.head p {
		max-width: 62rem;
		margin: 0 0 0.75rem;
		color: var(--dl-ink-mute);
		line-height: 1.7;
	}

	.id-row {
		display: flex;
		gap: 0.85rem;
		align-items: center;
		flex-wrap: wrap;
	}

	.id-row code {
		padding: 0.18rem 0.5rem;
		border-radius: 4px;
		background: var(--dl-bg-raised);
		color: var(--dl-ink-dim);
	}

	.notice {
		display: flex;
		gap: 0.5rem;
		margin-bottom: 1rem;
		padding: 0.75rem 0.85rem;
		border: 1px solid rgba(251, 146, 60, 0.35);
		border-radius: 6px;
		background: rgba(251, 146, 60, 0.08);
		color: var(--dl-ink-mute);
		font-size: 0.86rem;
	}

	.layout {
		display: grid;
		grid-template-columns: minmax(240px, 0.75fr) minmax(0, 2fr);
		gap: 1rem;
		align-items: start;
	}

	.meta,
	.body {
		border: 1px solid var(--dl-line);
		border-radius: 8px;
		background: var(--dl-bg-raised);
	}

	.meta {
		position: sticky;
		top: 4.5rem;
		padding: 1rem;
	}

	.meta section + section,
	.body section + section {
		margin-top: 1rem;
		padding-top: 1rem;
		border-top: 1px solid var(--dl-line);
	}

	h2 {
		margin: 0 0 0.55rem;
		color: var(--dl-ink-print);
		font-size: 0.98rem;
	}

	dl {
		margin: 0;
	}

	dt {
		margin-top: 0.65rem;
		color: var(--dl-ink-dim);
		font-size: 0.72rem;
		text-transform: uppercase;
	}

	dd {
		margin: 0.18rem 0 0;
		color: var(--dl-ink-mute);
		font-size: 0.86rem;
	}

	.body {
		padding: 1.2rem;
	}

	.body p,
	.body li {
		color: var(--dl-ink-mute);
		line-height: 1.65;
	}

	.spec-grid {
		display: grid;
		grid-template-columns: repeat(2, minmax(0, 1fr));
		gap: 1rem;
	}

	.chips {
		display: flex;
		flex-wrap: wrap;
		gap: 0.4rem;
	}

	.chips a,
	.chips .muted-chip {
		padding: 0.2rem 0.5rem;
		border: 1px solid var(--dl-line);
		border-radius: 5px;
		color: var(--dl-orange);
		text-decoration: none;
		font-family: var(--dl-font-mono);
		font-size: 0.72rem;
	}

	.chips .muted-chip {
		color: var(--dl-text-dim);
		opacity: 0.6;
		cursor: default;
	}

	.execution-plan {
		display: grid;
		gap: 0.75rem;
		padding-left: 1.2rem;
	}

	.execution-plan li {
		padding: 0.75rem;
		border: 1px solid var(--dl-line);
		border-radius: 8px;
		background: rgba(255, 255, 255, 0.03);
	}

	.execution-plan strong,
	.execution-plan span,
	.execution-plan small {
		display: block;
	}

	.execution-plan strong {
		font-family: var(--dl-font-mono);
		font-size: 0.8rem;
		color: var(--dl-orange);
	}

	.muted {
		color: var(--dl-ink-dim);
	}

	@media (max-width: 860px) {
		.layout,
		.spec-grid {
			grid-template-columns: 1fr;
		}

		.meta {
			position: static;
		}
	}
</style>
