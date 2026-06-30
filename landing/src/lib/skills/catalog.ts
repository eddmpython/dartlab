import skillIndex from '$skills/catalog.json';

// operation 카테고리는 landing 검색에서 제외 (skills 필터 참조) · 메뉴/순서에서도 노출 X.
export const skillCategoryOrder = ['start', 'runtime', 'engines', 'recipes'] as const;

export const skillCategoryTitle: Record<string, string> = {
	start: 'Start',
	runtime: 'Runtime',
	engines: 'Engines',
	recipes: 'Recipes'
};

export const canonicalEngineSubGroups = [
	'company',
	'gather',
	'scan',
	'analysis',
	'credit',
	'macro',
	'quant',
	'industry'
] as const;

export const canonicalEngineSubGroupSet = new Set<string>(canonicalEngineSubGroups);

export interface RuntimeEntry {
	status?: string;
	notes?: string[];
	limitations?: string[];
	dataSources?: string[];
}

export interface RecipeStep {
	skillId: string;
	note?: string;
}

export interface SkillDoc {
	id: string;
	title: string;
	category: string;
	categoryTitle?: string;
	kind?: string;
	status: string;
	purpose: string;
	whenToUse?: string[];
	inputs?: string[];
	requiredInputs?: string[];
	outputs?: string[];
	apiRefs?: string[];
	toolRefs?: string[];
	datasetRefs?: string[];
	knowledgeRefs?: string[];
	linkedSkills?: string[];
	sourceRefs?: string[];
	procedure?: string[];
	recipeSteps?: RecipeStep[];
	requiredEvidence?: string[];
	expectedOutputs?: string[];
	visualGuidance?: string[];
	failureModes?: string[];
	forbidden?: string[];
	examples?: string[];
	runtimeCompatibility?: Record<string, RuntimeEntry>;
	// 트랙 8 · 새 frontmatter 필드 (graph + 사람용 도입)
	humanIntro?: string;
	predecessors?: string[];
	successors?: string[];
	audiences?: Record<string, string>;
	isLeafNode?: boolean;
	entryHint?: boolean;
	graphTier?: string | null;
	cluster?: string | null;
	visualRefs?: string[];
	bodyHuman?: string;
}

export interface SkillIndexMeta {
	entrySkillId?: string;
	canonicalSurface?: string;
	skillCount?: number;
	categories?: Array<{ id: string; title: string; description?: string; count: number }>;
	sourcePolicy?: string;
}

type SkillModule = {
	default: ConstructorOfATypedSvelteComponent;
	metadata?: Record<string, unknown>;
};

const components = import.meta.glob('$skills/specs/**/*.md', { eager: true }) as Record<string, SkillModule>;
const rawSources = import.meta.glob('$skills/specs/**/*.md', { eager: true, query: '?raw', import: 'default' }) as Record<string, string>;

function extractFrontmatterId(raw: string): string | undefined {
	// BOM 제거 후 frontmatter 경계 식별. 들여쓰기·따옴표 변형 모두 허용.
	const stripped = raw.replace(/^﻿/, '');
	if (!stripped.startsWith('---')) return undefined;
	const end = stripped.indexOf('\n---', 3);
	if (end < 0) return undefined;
	const block = stripped.slice(3, end);
	const match = block.match(/^\s*id:\s*(.+?)\s*$/m);
	if (!match) return undefined;
	return match[1].trim().replace(/^["']|["']$/g, '');
}

const componentsById = new Map<string, ConstructorOfATypedSvelteComponent>();
const rawById = new Map<string, string>();
const sourcePathById = new Map<string, string>();
const skippedPaths: string[] = [];

for (const [path, raw] of Object.entries(rawSources)) {
	const id = extractFrontmatterId(raw);
	if (!id) {
		skippedPaths.push(path);
		continue;
	}
	rawById.set(id, raw);
	sourcePathById.set(id, path);
	const mod = components[path];
	if (mod?.default) componentsById.set(id, mod.default);
}

if (skippedPaths.length > 0 && typeof console !== 'undefined') {
	console.warn(
		`[skills/catalog] frontmatter id 추출 실패 (${skippedPaths.length}건):\n  - ` +
			skippedPaths.join('\n  - ')
	);
}

export const skillsMeta: SkillIndexMeta = (skillIndex as { meta?: SkillIndexMeta }).meta ?? {};
// operation/ 은 운영자·기여자 내부 SSOT (philosophy·code·testing·architecture).
// landing 방문자가 검색할 컨텐츠가 아님 · 빌드 JSON 은 운영자 권한이라 UI 단에서 제외.
export const skills: SkillDoc[] = ((skillIndex as { skills?: SkillDoc[] }).skills ?? [])
	.filter((skill) => skill.category !== 'capability' && skill.category !== 'operation')
	.filter((skill) => componentsById.has(skill.id))
	.map(normalizeSkillCategory);

const skillById = new Map<string, SkillDoc>(skills.map((skill) => [skill.id, skill]));

// operation/capability 도 prerender 대상 (Stability.svelte 등이 직접 링크).
// UI 검색·메뉴는 위 skills (operation 제외) 사용, 페이지 라우트만 전체 catalog.
const allSkillById = new Map<string, SkillDoc>(
	((skillIndex as { skills?: SkillDoc[] }).skills ?? [])
		.map(normalizeSkillCategory)
		.map((skill) => [skill.id, skill])
);

export function normalizeSkillCategory(skill: SkillDoc): SkillDoc {
	if (!skill.id.startsWith('recipes.')) return skill;
	return {
		...skill,
		category: 'recipes',
		categoryTitle: skillCategoryTitle.recipes
	};
}

export function getSkillSubGroup(skill: Pick<SkillDoc, 'id' | 'category'>): string | null {
	if (skill.category !== 'engines' && skill.category !== 'recipes') return null;
	const parts = skill.id.split('.');
	return parts.length >= 2 ? parts[1] : null;
}

export function getSkillMeta(id: string): SkillDoc | undefined {
	return allSkillById.get(id);
}

export function getSkillComponent(id: string): ConstructorOfATypedSvelteComponent | undefined {
	return componentsById.get(id);
}

export function getSkillRaw(id: string): string | undefined {
	return rawById.get(id);
}

export function getSkillSourcePath(id: string): string | undefined {
	return sourcePathById.get(id);
}

export function allSkillIds(): string[] {
	return Array.from(allSkillById.keys()).filter((id) => componentsById.has(id));
}

export function findRelatedSkills(id: string, limit = 6): SkillDoc[] {
	const current = skillById.get(id);
	if (!current) return [];
	return skills
		.filter((skill) => skill.id !== id && skill.category === current.category)
		.slice(0, limit);
}

export function isCatalogSkillId(value: string): boolean {
	return skillById.has(value);
}

// prerender-가능 페이지 존재 여부 (allSkillById + componentsById 둘 다 만족).
// market 페이지 등이 mappedBuiltinSkills 를 link 할 때 미존재 spec ID 차단용.
export function hasSkillPage(id: string): boolean {
	return allSkillById.has(id) && componentsById.has(id);
}
