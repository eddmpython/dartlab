import type {
	EvidenceReceipt,
	GapReceipt,
	UniverseClaimLane,
	UniverseClaimReceipt,
	UniverseWorkflowCompilation,
	UniverseWorkflowId,
	UniverseWorkflowRecipe
} from '@dartlab/ui-contracts';
import { canonicalSha256, stripSha256 } from './canonical';
import { compileFlightPlan, compileFlightReceipt } from './flight';

export const UNIVERSE_WORKFLOWS: readonly UniverseWorkflowRecipe[] = [
	{
		workflowId: 'growthSustainability',
		version: '1.0.0',
		label: '성장 지속성',
		objective: 'falsify',
		procedure: ['orient', 'evidence', 'compare', 'falsify', 'conclude'],
		claims: [
			{ claimId: 'growth:revenue', label: '매출 성장의 반복성', requiredEvidence: ['financialSeries', 'filingExplanation'], falsifier: '성장이 일회성 거래 또는 연결범위 변경에서 발생했는가', defaultLane: 'fact' },
			{ claimId: 'growth:margin', label: '성장과 수익성의 동행', requiredEvidence: ['marginSeries'], falsifier: '성장 구간에서 마진이 구조적으로 악화되는가', defaultLane: 'derived' },
			{ claimId: 'growth:scenario', label: '다음 기간 지속 시나리오', requiredEvidence: ['scenarioAssumptions'], falsifier: '핵심 가정 하나가 깨지면 결론이 뒤집히는가', defaultLane: 'scenario' }
		]
	},
	{
		workflowId: 'creditFragility',
		version: '1.0.0',
		label: '신용 취약',
		objective: 'falsify',
		procedure: ['orient', 'evidence', 'compare', 'falsify', 'conclude'],
		claims: [
			{ claimId: 'credit:debt', label: '차입 부담의 증가', requiredEvidence: ['debtSeries', 'maturityTable'], falsifier: '상환 일정과 유동성이 부담 증가를 상쇄하는가', defaultLane: 'fact' },
			{ claimId: 'credit:coverage', label: '이자 상환 여력', requiredEvidence: ['interestCoverage'], falsifier: '현금흐름 기준 상환 여력이 회계이익과 다른가', defaultLane: 'derived' },
			{ claimId: 'credit:scenario', label: '금리 충격 시나리오', requiredEvidence: ['scenarioAssumptions'], falsifier: '고정금리 비중이 충격을 제한하는가', defaultLane: 'scenario' }
		]
	},
	{
		workflowId: 'disclosureChange',
		version: '1.0.0',
		label: '공시 변화',
		objective: 'investigate',
		procedure: ['orient', 'evidence', 'compare', 'falsify', 'conclude'],
		claims: [
			{ claimId: 'disclosure:text', label: '원문 변경', requiredEvidence: ['beforeLocator', 'afterLocator'], falsifier: '서식 또는 표준 문구 변화에 불과한가', defaultLane: 'fact' },
			{ claimId: 'disclosure:meaning', label: '의미 변화', requiredEvidence: ['semanticDiff', 'sectionContext'], falsifier: '주변 문맥을 포함하면 의미가 유지되는가', defaultLane: 'derived' },
			{ claimId: 'disclosure:impact', label: '영향 시나리오', requiredEvidence: ['scenarioAssumptions'], falsifier: '변경이 실제 수치 또는 계약에 연결되지 않는가', defaultLane: 'scenario' }
		]
	}
];

function recipeById(workflowId: UniverseWorkflowId): UniverseWorkflowRecipe {
	const recipe = UNIVERSE_WORKFLOWS.find((item) => item.workflowId === workflowId);
	if (!recipe) throw new Error(`Universe workflow is closed: ${workflowId}`);
	return recipe;
}

async function identity(prefix: string, payload: unknown): Promise<string> {
	return `${prefix}:${stripSha256(await canonicalSha256(payload))}`;
}

async function missingClaimGap(claimId: string, requestedField: string): Promise<GapReceipt> {
	return {
		gapId: await identity('gap', { claimId, requestedField, reasonCode: 'requiredEvidenceMissing' }),
		kind: 'unresolved',
		ownerSource: 'universeWorkflow',
		requestedField,
		reasonCode: 'requiredEvidenceMissing',
		retryPolicy: 'resolveRequiredEvidence'
	};
}

async function absentReceipt(claimId: string, snapshotSetId: string, validAt: string | null, knownAt: string | null, generatedAt: string): Promise<EvidenceReceipt> {
	return {
		receiptId: await identity('receipt', { claimId, snapshotSetId, status: 'missing', validAt, knownAt }),
		claimId,
		evidenceRefs: [],
		derivationRefs: [],
		falsifierRefs: [],
		sourceSnapshotIds: [snapshotSetId],
		status: 'missing',
		validAt,
		knownAt,
		generatedAt
	};
}

function admittedLane(defaultLane: UniverseClaimLane, evidence: EvidenceReceipt, requiredCount: number): UniverseClaimLane {
	if (defaultLane === 'scenario') return 'scenario';
	if (evidence.status !== 'supported') return 'gap';
	if (defaultLane === 'fact' && evidence.evidenceRefs.length >= requiredCount) return 'fact';
	if (defaultLane === 'derived' && evidence.derivationRefs.length > 0 && evidence.evidenceRefs.length > 0) return 'derived';
	return 'gap';
}

function requiredEvidenceReady(defaultLane: UniverseClaimLane, evidence: EvidenceReceipt, requiredCount: number): boolean {
	if (evidence.status === 'missing' || evidence.status === 'contradicted') return false;
	if (defaultLane === 'fact') return evidence.evidenceRefs.length >= requiredCount;
	if (defaultLane === 'derived') return evidence.evidenceRefs.length > 0 && evidence.derivationRefs.length > 0;
	return evidence.status === 'scenario' && evidence.derivationRefs.length > 0;
}

export interface CompileWorkflowInput {
	workflowId: UniverseWorkflowId;
	snapshotSetId: string;
	seedIds: readonly string[];
	validAt: string | null;
	knownAt: string | null;
	generatedAt: string;
	evidenceByClaim?: Readonly<Record<string, EvidenceReceipt>>;
}

export async function compileUniverseWorkflow(input: CompileWorkflowInput): Promise<UniverseWorkflowCompilation> {
	const recipe = recipeById(input.workflowId);
	const flightPlan = await compileFlightPlan({ recipe, snapshotSetId: input.snapshotSetId, seedIds: input.seedIds, validAt: input.validAt, knownAt: input.knownAt });
	const claims: UniverseClaimReceipt[] = [];
	for (const spec of recipe.claims) {
		const evidence = input.evidenceByClaim?.[spec.claimId]
			?? await absentReceipt(spec.claimId, input.snapshotSetId, input.validAt, input.knownAt, input.generatedAt);
		const lane = admittedLane(spec.defaultLane, evidence, spec.requiredEvidence.length);
		const gaps = !requiredEvidenceReady(spec.defaultLane, evidence, spec.requiredEvidence.length)
			? await Promise.all(spec.requiredEvidence.map((required) => missingClaimGap(spec.claimId, required)))
			: [];
		claims.push({
			claimId: spec.claimId,
			label: spec.label,
			lane,
			evidence,
			gaps,
			falsifier: spec.falsifier,
			conclusionReady: lane === 'fact' || lane === 'derived'
		});
	}
	const allGaps = claims.flatMap((claim) => claim.gaps);
	const flightReceipt = await compileFlightReceipt(flightPlan, claims.map((claim) => claim.evidence), allGaps, input.generatedAt);
	const conclusionReady = claims.every((claim) => claim.conclusionReady) && claims.every((claim) => Boolean(claim.falsifier));
	return {
		recipe,
		flightPlan,
		flightReceipt,
		claims,
		conclusionReady,
		compileHash: await canonicalSha256({ recipe, flightPlan, flightReceipt, claims, conclusionReady })
	};
}
