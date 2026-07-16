import type { GapReceipt, UniverseLensCard, UniverseLensRef, UniverseLensTray } from '@dartlab/ui-contracts';
import { canonicalSha256, stripSha256 } from './canonical';

const REF_KINDS = new Set<UniverseLensRef['kind']>(['valueRef', 'tableRef', 'dateRef', 'executionRef']);

async function identity(prefix: string, payload: unknown): Promise<string> {
	return `${prefix}:${stripSha256(await canonicalSha256(payload))}`;
}

async function lensGap(ref: UniverseLensRef, reasonCode: string): Promise<GapReceipt> {
	return {
		gapId: await identity('gap', { refId: ref.refId, reasonCode }),
		kind: ref.status === 'failed' ? 'unavailable' : 'unresolved',
		ownerSource: `${ref.engine}.${ref.axis}`,
		requestedField: ref.label,
		reasonCode,
		retryPolicy: ref.status === 'failed' ? 'retryExecution' : 'supplySourceValue'
	};
}

function validateRef(ref: UniverseLensRef): void {
	if (!ref.refId || !REF_KINDS.has(ref.kind) || !ref.engine || !ref.axis || !ref.label) {
		throw new Error('Universe lens requires a standard Ref identity');
	}
	if (ref.kind === 'tableRef' && ref.columns.length === 0) throw new Error('Universe tableRef requires columns');
	if (ref.rows.some((row) => row.length !== ref.columns.length)) throw new Error('Universe tableRef row width is invalid');
	if (ref.status === 'available' && !ref.sourceRef) throw new Error('Universe available lens requires sourceRef');
}

async function card(ref: UniverseLensRef, role: UniverseLensCard['role']): Promise<UniverseLensCard> {
	validateRef(ref);
	const gaps: GapReceipt[] = [];
	if (ref.status !== 'available') gaps.push(await lensGap(ref, ref.status === 'failed' ? 'executionFailed' : 'valueMissing'));
	if (ref.status === 'available' && ref.value === null && ref.rows.length === 0) gaps.push(await lensGap(ref, 'emptyRef'));
	return { lensId: await identity('lens', { role, ref }), role, ref, gaps };
}

export async function compileLensTray(primary: UniverseLensRef, comparison: UniverseLensRef | null = null): Promise<UniverseLensTray> {
	const primaryCard = await card(primary, 'primary');
	const comparisonCard = comparison ? await card(comparison, 'comparison') : null;
	return {
		primary: primaryCard,
		comparison: comparisonCard,
		receiptHash: await canonicalSha256({ primary: primaryCard, comparison: comparisonCard })
	};
}

function fixture(engine: string, kind: UniverseLensRef['kind']): UniverseLensRef {
	const table = kind === 'tableRef';
	return {
		refId: `fixture:${engine}`,
		kind,
		engine,
		axis: 'contractFixture',
		label: `${engine} generic Ref`,
		sourceRef: `fixture:${engine}:source`,
		dataAsOf: 'fixture',
		unit: kind === 'valueRef' ? 'fixtureUnit' : null,
		value: table ? null : 'fixtureValue',
		columns: table ? ['field', 'value'] : [],
		rows: table ? [['fixture', 'value']] : [],
		executedAt: kind === 'executionRef' ? 'fixture' : null,
		status: 'available',
		limitation: '계약 적합성 검사용 fixture이며 시장 사실이 아닙니다.'
	};
}

export const UNIVERSE_LENS_CONTRACT_FIXTURES: readonly UniverseLensRef[] = [
	fixture('industry', 'tableRef'),
	fixture('financial', 'valueRef'),
	fixture('credit', 'valueRef'),
	fixture('macro', 'dateRef'),
	fixture('quant', 'executionRef'),
	fixture('scan', 'tableRef')
];
