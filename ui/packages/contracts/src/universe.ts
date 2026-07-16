// DartLab Universe 공개 장면 계약.
// Truth와 renderer 사이의 직렬화 경계만 소유하며 데이터 로드나 엔진 로직은 두지 않는다.

export const UNIVERSE_SCHEMA_VERSION = 'boundedScene.v1' as const;
export const UNIVERSE_PROJECTION_SCHEMA_VERSION = 'projectionSpec.v1' as const;
export const UNIVERSE_FLIGHT_SCHEMA_VERSION = 'universeFlightPlan.v1' as const;
export const UNIVERSE_VISUAL_GRAMMAR_VERSION = 'universeVisualGrammar.v1' as const;
export const UNIVERSE_PREDICATES = [
	'suppliesTo',
	'sellsTo',
	'ownsStakeIn',
	'affiliatedWith',
	'classifiedIn',
	'filed',
	'aggregateFlow'
] as const;

export type UniverseLane = 'fact' | 'candidate' | 'derived' | 'scenario';
export type UniverseAssertionStatus = 'observed' | 'corroborated' | 'disputed' | 'retracted';
export type UniverseVisualStatus =
	| 'fact'
	| 'candidate'
	| 'derived'
	| 'disputed'
	| 'retracted'
	| 'scenario'
	| 'unknown';
export type UniverseDirection = 'subjectToObject' | 'objectToSubject' | 'undirected';
export type UniverseStage = 'upstream' | 'midstream' | 'downstream' | 'unknown';
export type UniverseEntityKind = 'industry' | 'company' | 'filing' | 'metric' | 'aggregate' | 'unknown';
export type UniverseTransition = 'replace' | 'diff' | 'overlay';
export type UniverseBeatIntent = 'orient' | 'focus' | 'compare' | 'evidence' | 'falsify' | 'conclude';
export type UniverseObjective = 'investigate' | 'compare' | 'falsify' | 'explain';
export type UniverseReleaseState = 'localReview' | 'publicBeta' | 'ga' | 'disabled';
export type UniverseGapKind = 'unavailable' | 'notPublic' | 'notApplicable' | 'unresolved' | 'stale' | 'omitted';
export type UniverseEvidenceStatus = 'supported' | 'contradicted' | 'missing' | 'scenario';
export type UniverseLocatorKind = 'text' | 'table';
export type UniverseRedistributionClass = 'public' | 'metadataOnly' | 'localOnly' | 'blocked' | 'unknown';
export type UniverseChangeMode = 'currentDemo' | 'exactReplay';
export type UniverseChangeKind = 'created' | 'corrected' | 'retracted' | 'newlyKnown' | 'stale';
export type UniverseLensRefKind = 'valueRef' | 'tableRef' | 'dateRef' | 'executionRef';
export type UniverseWorkflowId = 'growthSustainability' | 'creditFragility' | 'disclosureChange';
export type UniverseClaimLane = 'fact' | 'derived' | 'gap' | 'scenario';
export type UniversePredicate = (typeof UNIVERSE_PREDICATES)[number];

export interface UniverseTextLocator {
	charStart: number;
	charEnd: number;
	snippetHash: string;
}

export interface UniverseTableLocator {
	rowIndex: number;
	headerHash: string;
	rowHash: string;
}

export interface EvidencePointer {
	evidenceId: string;
	documentId: string;
	sectionPath: string;
	sectionOrder: number;
	sourceRef: string;
	sourcePath: string;
	sourceVersion: string;
	subjectId: string;
	predicate: UniversePredicate;
	objectId: string;
	direction: UniverseDirection;
	sourcePublishedAt: string;
	availableAt: string;
	contentHash: string;
	locatorKind: UniverseLocatorKind;
	textLocator: UniverseTextLocator | null;
	tableLocator: UniverseTableLocator | null;
}

export interface UniverseNodePresentation {
	entityKind: UniverseEntityKind;
	stage: UniverseStage;
	validOrder: number | null;
	metricValue: number | null;
	comparisonValue: number | null;
	memberCount: number | null;
	colorToken: string;
	attributes: Readonly<Record<string, unknown>>;
}

export interface UniverseNode {
	nodeId: string;
	label: string;
	lane: UniverseLane;
	priority: number;
	sourceKind: string;
	sourceRef: string;
	presentation?: UniverseNodePresentation;
}

export interface UniverseRelation {
	edgeId: string;
	sourceId: string;
	targetId: string;
	predicate: UniversePredicate;
	lane: UniverseLane;
	priority: number;
	sourceRef: string;
	assertionId: string;
	evidenceRefs: readonly string[];
	derivationRefs: readonly string[];
	scenarioReceiptId: string;
}

export interface UniverseAssertion {
	relationId: string;
	assertionId: string;
	subjectId: string;
	predicate: UniversePredicate;
	objectId: string;
	direction: UniverseDirection;
	status: UniverseAssertionStatus;
	sourceSnapshotSetId: string;
	sourcePublishedAt: string;
	availableAt: string;
	validFrom: string;
	validTo: string;
	eventAt: string;
	supersedesAssertionId: string;
	evidenceRefs: readonly EvidencePointer[];
	evidenceBindingHash: string;
}

export interface SnapshotSource {
	sourceId: string;
	origin: string;
	path: string;
	versionOrEtag: string | null;
	payloadHash: string | null;
	dataAsOf: string | null;
	redistributionReceiptId: string | null;
	replayStatus: 'replayable' | 'unreplayable';
	unreplayableReason: string | null;
	contentLength: number | null;
}

export interface SourceSnapshotSet {
	schemaVersion: string;
	snapshotSetId: string;
	createdAt: string;
	sources: readonly SnapshotSource[];
	mapBuildId: string | null;
	capabilityCatalogVersion: string | null;
	recipeCatalogVersion: string | null;
	exactReplayReady: boolean;
	unreplayableSourceIds: readonly string[];
	missingDataAsOfSourceIds: readonly string[];
	missingRedistributionReceiptSourceIds: readonly string[];
}

export interface ProjectionSpec {
	projectionId: string;
	query: string;
	seedIds: readonly string[];
	sourceSnapshotSetId: string;
	maxDepth: number;
	maxNodes: number;
	maxEdges: number;
	validAt?: string | null;
	knownAt?: string | null;
	predicates?: readonly string[];
	statuses?: readonly UniverseAssertionStatus[];
}

export interface OmissionReceipt {
	omittedNodeCount: number;
	omittedEdgeCount: number;
	nodeReasonCounts: readonly (readonly [string, number])[];
	edgeReasonCounts: readonly (readonly [string, number])[];
	omittedNodeLaneCounts: readonly (readonly [UniverseLane, number])[];
	omittedEdgeLaneCounts: readonly (readonly [UniverseLane, number])[];
}

export interface SceneReceipt {
	specHash: string;
	sourceSnapshotSetId: string;
	inputNodeCount: number;
	inputEdgeCount: number;
	outputNodeCount: number;
	outputEdgeCount: number;
	seedCount: number;
	retainedSeedCount: number;
	maxDepthObserved: number;
	omission: OmissionReceipt;
}

export interface UniverseScene {
	schemaVersion: typeof UNIVERSE_SCHEMA_VERSION;
	sceneId: string;
	nodes: readonly UniverseNode[];
	edges: readonly UniverseRelation[];
	assertions: readonly UniverseAssertion[];
	receipt: SceneReceipt;
	sceneHash: string;
}

export interface EvidenceReceipt {
	receiptId: string;
	claimId: string;
	evidenceRefs: readonly string[];
	derivationRefs: readonly string[];
	falsifierRefs: readonly string[];
	sourceSnapshotIds: readonly string[];
	status: UniverseEvidenceStatus;
	validAt: string | null;
	knownAt: string | null;
	generatedAt: string;
}

export interface UniverseEvidenceQuery {
	claimId: string;
	text: string;
	subjectId: string;
	predicate: UniversePredicate;
	objectId: string;
	direction: UniverseDirection;
	validAt: string | null;
	knownAt: string | null;
	pointer?: EvidencePointer | null;
}

export interface UniverseEvidenceCandidate {
	documentId: string;
	title: string;
	entityId: string;
	publishedAt: string;
	sourceRef: string;
	snippet: string;
	score: number;
}

export interface UniverseEvidenceResolution {
	query: UniverseEvidenceQuery;
	pointer: EvidencePointer | null;
	receipt: EvidenceReceipt;
	candidates: readonly UniverseEvidenceCandidate[];
	gaps: readonly GapReceipt[];
	indexBuiltAt: string | null;
}

export interface GapReceipt {
	gapId: string;
	kind: UniverseGapKind;
	ownerSource: string;
	requestedField: string;
	reasonCode: string;
	retryPolicy: string;
}

export interface UniverseChangeEvidence {
	before: EvidenceReceipt;
	after: EvidenceReceipt;
	gaps: readonly GapReceipt[];
}

export interface UniverseChangeMark {
	changeId: string;
	entityId: string;
	entityLabel: string;
	industryId: string;
	kind: UniverseChangeKind;
	metricId: string;
	beforeValue: number | null;
	afterValue: number | null;
	unit: string | null;
	eventAt: string;
	knownAt: string;
	sourceRef: string;
	summary: string;
	evidence: UniverseChangeEvidence;
}

export interface UniverseChangeAggregate {
	industryId: string;
	industryLabel: string;
	memberCount: number;
	coveredCount: number;
	unknownCount: number;
	omittedCount: number;
	coverage: number;
	changeCount: number;
}

export interface UniverseChangeSet {
	mode: UniverseChangeMode;
	fromSnapshotSetId: string | null;
	toSnapshotSetId: string;
	fromPeriod: string | null;
	toPeriod: string;
	marks: readonly UniverseChangeMark[];
	aggregates: readonly UniverseChangeAggregate[];
	gaps: readonly GapReceipt[];
	diffHash: string;
	generatedAt: string;
}

export interface SceneBeat {
	beatId: string;
	intent: UniverseBeatIntent;
	projectionSpec: ProjectionSpec;
	selectedIds: readonly string[];
	expectedEvidenceRefs: readonly string[];
	transition: UniverseTransition;
	narration: string;
}

export interface UniverseFlightPlan {
	schemaVersion: typeof UNIVERSE_FLIGHT_SCHEMA_VERSION;
	flightId: string;
	questionRef: string | null;
	objective: UniverseObjective;
	snapshotSetId: string;
	beats: readonly SceneBeat[];
}

export interface UniverseFlightReceipt {
	schemaVersion: 'universeFlightReceipt.v1';
	flightId: string;
	beatEvidence: Readonly<Record<string, readonly EvidenceReceipt[]>>;
	beatGaps: Readonly<Record<string, readonly GapReceipt[]>>;
	outputHash: string;
	generatedAt: string;
}

export interface UniverseLensRef {
	refId: string;
	kind: UniverseLensRefKind;
	engine: string;
	axis: string;
	label: string;
	sourceRef: string;
	dataAsOf: string | null;
	unit: string | null;
	value: number | string | boolean | null;
	columns: readonly string[];
	rows: readonly (readonly (number | string | boolean | null)[])[];
	executedAt: string | null;
	status: 'available' | 'missing' | 'failed';
	limitation: string;
}

export interface UniverseLensCard {
	lensId: string;
	role: 'primary' | 'comparison';
	ref: UniverseLensRef;
	gaps: readonly GapReceipt[];
}

export interface UniverseLensTray {
	primary: UniverseLensCard;
	comparison: UniverseLensCard | null;
	receiptHash: string;
}

export interface UniverseWorkflowClaimSpec {
	claimId: string;
	label: string;
	requiredEvidence: readonly string[];
	falsifier: string;
	defaultLane: UniverseClaimLane;
}

export interface UniverseWorkflowRecipe {
	workflowId: UniverseWorkflowId;
	version: string;
	label: string;
	objective: UniverseObjective;
	procedure: readonly UniverseBeatIntent[];
	claims: readonly UniverseWorkflowClaimSpec[];
}

export interface UniverseClaimReceipt {
	claimId: string;
	label: string;
	lane: UniverseClaimLane;
	evidence: EvidenceReceipt;
	gaps: readonly GapReceipt[];
	falsifier: string;
	conclusionReady: boolean;
}

export interface UniverseWorkflowCompilation {
	recipe: UniverseWorkflowRecipe;
	flightPlan: UniverseFlightPlan;
	flightReceipt: UniverseFlightReceipt;
	claims: readonly UniverseClaimReceipt[];
	conclusionReady: boolean;
	compileHash: string;
}

export interface UniverseLegalEntityIdentity {
	market: 'KR' | 'US';
	legalEntityId: string;
	securityId: string;
	ticker: string;
	validFrom: string;
	validTo: string | null;
	sourceRef: string;
}

export interface UniverseConformanceObservation {
	entity: UniverseLegalEntityIdentity;
	metricId: string;
	value: number | null;
	unit: string | null;
	dataAsOf: string | null;
	sourceRef: string;
}

export interface UniversePairedQuestion {
	questionId: string;
	label: string;
	metricId: string;
}

export interface UniversePairedResult {
	question: UniversePairedQuestion;
	status: 'ready' | 'blocked';
	kr: UniverseConformanceObservation | null;
	us: UniverseConformanceObservation | null;
	gaps: readonly GapReceipt[];
}

export interface UniverseVisualToken {
	stroke: string;
	pattern: string;
	glyph: string;
	label: string;
	color: string;
	evidenceAction: string;
	ariaStatus: string;
}

export interface UniverseUrlState {
	version: 1;
	snapshotSetId: string | null;
	buildId: string | null;
	workflowId: string;
	beatIndex: number;
	flightId: string | null;
	seedIds: readonly string[];
	validAt: string | null;
	knownAt: string | null;
	predicates: readonly string[];
	statuses: readonly UniverseAssertionStatus[];
	lens: string | null;
	grouping: 'industry' | 'stage' | 'market';
	colorBy: string | null;
	sizeBy: string | null;
	selectedId: string | null;
}

export interface UniverseObservationPoint {
	entityId: string;
	metricId: string;
	period: string;
	value: number | null;
	unit: string | null;
	availableAt: string | null;
	sourceRef: string;
}

export interface UniverseObservationRange {
	from?: string | null;
	to?: string | null;
}

export interface UniverseRouteMeta {
	schemaVersion: number;
	buildId: string;
	buildTime: string;
	commitSha: string;
	dataAsOf: Readonly<Record<string, string | null>>;
	sizes: Readonly<Record<string, number>>;
	counts: Readonly<Record<string, number>>;
}

export interface UniverseAtlasIndustry {
	id: string;
	name: string;
	revenue: number;
	nodeCount: number;
	stagedCount: number;
	stageMix: Readonly<Record<string, number>>;
	stages: readonly {
		key: string;
		name: string;
		role: string;
		stream: UniverseStage | string;
	}[];
}

export interface UniverseAtlasFlow {
	fromIndustry: string;
	toIndustry: string;
	edgeCount: number;
	amount: number;
}

export interface UniverseAtlas {
	version: string;
	industries: readonly UniverseAtlasIndustry[];
	flows: readonly UniverseAtlasFlow[];
}

export interface UniverseRouteSeed {
	meta: UniverseRouteMeta;
	atlas: UniverseAtlas;
	snapshot: SourceSnapshotSet;
	scene: UniverseScene;
	releaseState: UniverseReleaseState;
}
