import type { UniverseKnowledgeDomainId, UniverseKnowledgeNodeKind } from '@dartlab/ui-contracts';

const HF_REPOSITORY_ID = 'eddmpython/dartlab-data';

export function normalizeKnowledgePath(path: string): string {
	return path.replace(/^\/+|\/+$/g, '');
}

export function classifyKnowledgePath(inputPath: string): UniverseKnowledgeDomainId {
	const path = normalizeKnowledgePath(inputPath).toLocaleLowerCase();
	if (path.startsWith('assets/')) return 'timeMedia';
	if (path.startsWith('news/') || path.startsWith('research/')) return 'intelligence';
	if (path.startsWith('macro/') || path.startsWith('gov/indices') || path.startsWith('krx/indices')) return 'macro';
	if (path.startsWith('gov/prices') || path.startsWith('krx/prices') || path.startsWith('edgar/prices') || path.startsWith('expectations/')) return 'marketData';
	if (path.startsWith('landing/map') || path.startsWith('dart/scan') || path.startsWith('edgar/scan') || path.includes('/industry')) return 'industry';
	if (path.startsWith('dart/finance') || path.startsWith('edgar/finance')) return 'observations';
	if (path.startsWith('dart/panel') || path.startsWith('dart/report') || path.startsWith('dart/docs') || path.startsWith('dart/sections') || path.startsWith('dart/ipo')
		|| path.startsWith('dart/allfilings') || path.startsWith('dart/search') || path.startsWith('dart/contentindex')
		|| path.startsWith('edgar/panel') || path.startsWith('edgar/docs') || path.startsWith('edgar/allfilings') || path.startsWith('edgar/meta')) return 'filings';
	if (path.startsWith('edgar/tickers') || path.startsWith('metadata/corplist') || path.startsWith('metadata/dartlist')
		|| path.includes('corpcode') || path.includes('companyprofile') || path.includes('/profile')) return 'entities';
	if (path.startsWith('pyodide/')) return 'capabilities';
	if (path.startsWith('landing/') && /\.(png|webp|jpe?g|gif|svg|mp4|webm|m4a)$/i.test(path)) return 'timeMedia';
	if (path.startsWith('gov/') || path.startsWith('krx/') || path.includes('security')) return 'securities';
	return 'sources';
}

export function knowledgeSkillDomain(category: string): UniverseKnowledgeDomainId {
	return category === 'engines' ? 'capabilities' : 'skills';
}

export function knowledgeLifecycleForPath(path: string): string {
	const lower = path.toLocaleLowerCase();
	if (lower.includes('/_staging/') || lower.includes('/staging/')) return 'staging';
	if (lower.includes('/compat') || lower.includes('/legacy')) return 'compatibility';
	return 'active';
}

export function knowledgeNodeKindForPath(path: string, domainId: UniverseKnowledgeDomainId): UniverseKnowledgeNodeKind {
	if (/\.(png|webp|jpe?g|gif|svg|mp4|webm|m4a|mp3|wav)$/i.test(path)) return 'media';
	if (domainId === 'entities') return 'entity';
	if (domainId === 'observations' || domainId === 'marketData' || domainId === 'macro') return 'observation';
	if (domainId === 'filings' || /\.(md|txt|xml|html|pdf)$/i.test(path)) return 'document';
	return 'file';
}

export function knowledgeSourceUrl(revision: string, path: string): string {
	const encoded = normalizeKnowledgePath(path).split('/').map(encodeURIComponent).join('/');
	return `https://huggingface.co/datasets/${HF_REPOSITORY_ID}/blob/${revision}/${encoded}`;
}

export function scoreKnowledgeText(query: string, text: string, exactText: string): number {
	const terms = query.toLocaleLowerCase().split(/\s+/).filter(Boolean);
	const haystack = text.toLocaleLowerCase();
	if (!terms.every((term) => haystack.includes(term))) return 0;
	const exact = exactText.toLocaleLowerCase();
	if (exact === query.toLocaleLowerCase()) return 120;
	if (exact.startsWith(query.toLocaleLowerCase())) return 92;
	return 58 + terms.length * 7 - Math.min(18, haystack.length / 160);
}
