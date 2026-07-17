import type {
	UniverseKnowledgeDomainId,
	UniverseKnowledgeEdge,
	UniverseKnowledgeNode,
	UniverseKnowledgeNodeKind,
	UniverseKnowledgeRelation,
	UniverseLane
} from '@dartlab/ui-contracts';

const HF_REPOSITORY_ID = 'eddmpython/dartlab-data';
const REPOSITORY_NODE_ID = `repository:hf:${HF_REPOSITORY_ID}`;

const FAMILY_LABELS: Readonly<Record<string, string>> = Object.freeze({
	'dart/panel': 'DART 공시 재무 패널',
	'dart/finance': 'DART 재무 관측',
	'dart/report': 'DART 정기 보고서',
	'dart/docs': 'DART 문서 인덱스',
	'dart/sections': 'DART 공시 섹션',
	'dart/allFilings': 'DART 전체 공시',
	'edgar/panel': 'EDGAR 공시 재무 패널',
	'edgar/finance': 'EDGAR 재무 관측',
	'edgar/financeStmt': 'EDGAR 재무제표',
	'edgar/docs': 'EDGAR 문서 인덱스',
	'edgar/allFilings': 'EDGAR 전체 공시',
	'edgar/allFilingsContent': 'EDGAR 공시 원문',
	'edgar/tickers': 'SEC 발행인 식별자',
	'edgar/prices': '미국 시장 가격',
	'gov/prices': '한국 시장 가격',
	'landing/map': '산업 관계 지도',
	'news/public': '공개 뉴스 인텔리전스'
});

interface SemanticSubject {
	nodeId: string;
	label: string;
	secondaryLabel: string;
	kind: 'entity' | 'security';
	domainId: 'entities' | 'securities';
	registryRef: string;
}

export interface UniverseKnowledgeSemanticInput {
	path: string;
	revision: string;
	domainId: UniverseKnowledgeDomainId;
	sourceRef: string;
}

export interface UniverseKnowledgeSemanticGraph {
	nodes: readonly UniverseKnowledgeNode[];
	edges: readonly UniverseKnowledgeEdge[];
}

function normalizedPath(path: string): string {
	return path.replace(/^\/+|\/+$/g, '');
}

function encodedPath(path: string): string {
	return normalizedPath(path).split('/').map(encodeURIComponent).join('/');
}

function repositoryRef(): string {
	return `https://huggingface.co/datasets/${HF_REPOSITORY_ID}`;
}

function treeRef(revision: string, path: string): string {
	return `${repositoryRef()}/tree/${encodeURIComponent(revision)}/${encodedPath(path)}`;
}

function blobRef(revision: string, path: string): string {
	return `${repositoryRef()}/blob/${encodeURIComponent(revision)}/${encodedPath(path)}`;
}

function semanticNode(input: {
	nodeId: string;
	label: string;
	secondaryLabel: string;
	kind: UniverseKnowledgeNodeKind;
	domainId: UniverseKnowledgeDomainId;
	lane: UniverseLane;
	weight: number;
	expandable?: boolean;
	sourceRef: string;
	evidenceRefs: readonly string[];
	attributes: UniverseKnowledgeNode['attributes'];
}): UniverseKnowledgeNode {
	return Object.freeze({
		...input,
		x: 0,
		y: 0,
		expandable: input.expandable ?? false,
		evidenceRefs: Object.freeze([...input.evidenceRefs]),
		attributes: Object.freeze({ ...input.attributes })
	});
}

function semanticEdge(input: {
	sourceId: string;
	targetId: string;
	relation: UniverseKnowledgeRelation;
	lane: UniverseLane;
	sourceRef: string;
	evidenceRefs: readonly string[];
	ruleId: string;
}): UniverseKnowledgeEdge {
	return Object.freeze({
		...input,
		edgeId: `edge:${input.ruleId}:${input.sourceId}:${input.targetId}`,
		evidenceRefs: Object.freeze([...input.evidenceRefs])
	});
}

function subjectForPath(path: string, revision: string): SemanticSubject | null {
	const dartMatch = /^(?:dart\/(?:panel|finance|report|docs)|dart\/sections)\/([0-9]{6})(?:[/.]|$)/i.exec(path);
	if (dartMatch?.[1]) {
		const code = dartMatch[1];
		return {
			nodeId: `security:dart:${code}`,
			label: code,
			secondaryLabel: 'DART 종목 식별자',
			kind: 'security',
			domainId: 'securities',
			registryRef: blobRef(revision, 'metadata/dartList.parquet')
		};
	}
	const cikMatch = /^edgar\/finance\/([0-9]{10})\.(?:parquet|arrow)$/i.exec(path);
	if (cikMatch?.[1]) {
		const cik = cikMatch[1];
		return {
			nodeId: `entity:sec:cik:${cik}`,
			label: `CIK ${cik}`,
			secondaryLabel: 'SEC 발행인 식별자',
			kind: 'entity',
			domainId: 'entities',
			registryRef: blobRef(revision, 'edgar/tickers/tickers.parquet')
		};
	}
	const tickerMatch = /^edgar\/(?:panel|docs|financeStmt|prices)\/([^/.]+)\.(?:parquet|arrow)$/i.exec(path);
	if (tickerMatch?.[1]) {
		const ticker = tickerMatch[1].toLocaleUpperCase();
		return {
			nodeId: `security:sec:ticker:${ticker}`,
			label: ticker,
			secondaryLabel: 'SEC 티커 식별자',
			kind: 'security',
			domainId: 'securities',
			registryRef: blobRef(revision, 'edgar/tickers/tickers.parquet')
		};
	}
	return null;
}

function conceptKind(path: string, domainId: UniverseKnowledgeDomainId): 'document' | 'section' | 'observation' | null {
	if (/^dart\/sections\//i.test(path)) return 'section';
	if (domainId === 'filings') return 'document';
	if (domainId === 'observations' || domainId === 'marketData' || domainId === 'macro') return 'observation';
	return null;
}

function conceptRelation(kind: 'document' | 'section' | 'observation'): UniverseKnowledgeRelation {
	return kind === 'observation' ? 'observed' : 'available';
}

export function compileKnowledgeFileSemantics(input: UniverseKnowledgeSemanticInput): UniverseKnowledgeSemanticGraph {
	const path = normalizedPath(input.path);
	const parts = path.split('/');
	const familyPath = parts.slice(0, Math.min(2, parts.length)).join('/');
	const familyLabel = FAMILY_LABELS[familyPath] ?? familyPath;
	const fileNodeId = `hf:${path}`;
	const datasetNodeId = `dataset:hf:${familyPath}`;
	const nodes: UniverseKnowledgeNode[] = [];
	const edges: UniverseKnowledgeEdge[] = [];
	const exactEvidence = Object.freeze([input.sourceRef]);

	nodes.push(semanticNode({
		nodeId: REPOSITORY_NODE_ID,
		label: 'DartLab Data',
		secondaryLabel: `HF revision ${input.revision.slice(0, 9)}`,
		kind: 'repository',
		domainId: 'sources',
		lane: 'fact',
		weight: 18,
		expandable: true,
		sourceRef: repositoryRef(),
		evidenceRefs: exactEvidence,
		attributes: { repositoryId: HF_REPOSITORY_ID, revision: input.revision }
	}));
	nodes.push(semanticNode({
		nodeId: datasetNodeId,
		label: familyLabel,
		secondaryLabel: familyPath,
		kind: 'dataset',
		domainId: input.domainId,
		lane: 'fact',
		weight: 16,
		expandable: true,
		sourceRef: treeRef(input.revision, familyPath),
		evidenceRefs: exactEvidence,
		attributes: { path: familyPath, revision: input.revision }
	}));
	edges.push(semanticEdge({
		sourceId: REPOSITORY_NODE_ID,
		targetId: datasetNodeId,
		relation: 'contains',
		lane: 'fact',
		sourceRef: input.sourceRef,
		evidenceRefs: exactEvidence,
		ruleId: 'knowledge.repositoryFamily.v1'
	}));
	edges.push(semanticEdge({
		sourceId: datasetNodeId,
		targetId: fileNodeId,
		relation: 'contains',
		lane: 'fact',
		sourceRef: input.sourceRef,
		evidenceRefs: exactEvidence,
		ruleId: 'knowledge.familyFile.v1'
	}));

	const subject = subjectForPath(path, input.revision);
	const kind = conceptKind(path, input.domainId);
	if (subject) {
		const subjectEvidence = Object.freeze([input.sourceRef, subject.registryRef]);
		nodes.push(semanticNode({
			nodeId: subject.nodeId,
			label: subject.label,
			secondaryLabel: subject.secondaryLabel,
			kind: subject.kind,
			domainId: subject.domainId,
			lane: 'derived',
			weight: 17,
			sourceRef: subject.registryRef,
			evidenceRefs: subjectEvidence,
			attributes: { identityFromPath: path, registryRef: subject.registryRef }
		}));
		if (kind) {
			const conceptNodeId = `${kind}:file:${path}`;
			const conceptLabel = kind === 'observation' ? `${subject.label} 관측 집합` : kind === 'section' ? `${subject.label} 공시 섹션` : `${subject.label} 공시 문서`;
			nodes.push(semanticNode({
				nodeId: conceptNodeId,
				label: conceptLabel,
				secondaryLabel: familyLabel,
				kind,
				domainId: input.domainId,
				lane: 'derived',
				weight: 15,
				sourceRef: input.sourceRef,
				evidenceRefs: exactEvidence,
				attributes: { path, semanticRule: 'knowledge.pathSubject.v1' }
			}));
			edges.push(semanticEdge({
				sourceId: subject.nodeId,
				targetId: conceptNodeId,
				relation: conceptRelation(kind),
				lane: 'derived',
				sourceRef: input.sourceRef,
				evidenceRefs: subjectEvidence,
				ruleId: 'knowledge.pathSubject.v1'
			}));
			edges.push(semanticEdge({
				sourceId: conceptNodeId,
				targetId: fileNodeId,
				relation: 'supported',
				lane: 'derived',
				sourceRef: input.sourceRef,
				evidenceRefs: exactEvidence,
				ruleId: 'knowledge.semanticEvidence.v1'
			}));
		} else {
			edges.push(semanticEdge({
				sourceId: subject.nodeId,
				targetId: fileNodeId,
				relation: 'describes',
				lane: 'derived',
				sourceRef: input.sourceRef,
				evidenceRefs: subjectEvidence,
				ruleId: 'knowledge.pathSubject.v1'
			}));
		}
	}

	return Object.freeze({ nodes: Object.freeze(nodes), edges: Object.freeze(edges) });
}
