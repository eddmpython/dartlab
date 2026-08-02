// 근거 계약 — AG-UI TOOL_CALL_RESULT.refDetails 실형태 승격 (census B). Ask 답변과 원천 데이터를 분리 표시.
import type { SourceType } from './source';

export interface EvidenceRef {
	id: string;
	kind: string; // tableRef | valueRef | webRef | artifactRef | visualRef ...
	title: string;
	source: string;
	sourceType: SourceType | string;
	payload?: unknown;
	hasMore?: boolean;
	/** 로컬 북극성 receipt. 모델·provider·대화 본문과 무관한 opaque ID다. */
	outcomeId?: string;
}

/** 뷰어 선택(문단/표/기간)을 Ask 에 전달하는 컨텍스트. */
export interface EvidenceSelection {
	code: string;
	period?: string;
	sectionKey?: string;
	text?: string;
}
