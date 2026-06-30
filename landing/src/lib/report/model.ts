// 리포트 모델 · 계약 SSOT 로 이주(@dartlab/ui-contracts/reportModel). Python story.buildReportModel 과
// 동일 계약. 본 파일은 re-export shim + 랜딩 전용 소형 보조타입·헬퍼. 모든 import 경로 무변경.
import type {
	Num,
	OverviewModel,
	ReportBlock,
	ReportModel,
	ReportResult,
	ReportSection,
	ReportSkipped,
	ReportSourceEngine,
	Thesis,
	ThesisPillar,
} from '@dartlab/ui-contracts';
import { isSkipped } from '@dartlab/ui-contracts';

export type {
	OverviewModel,
	ReportBlock,
	ReportModel,
	ReportResult,
	ReportSection,
	ReportSkipped,
	ReportSourceEngine,
	Thesis,
	ThesisPillar,
};
export { isSkipped };

// ── 랜딩 전용 보조타입 (계약 ReportModel 필드와 구조 동치 · 내부 빌더 가독용) ──
export interface ReportKpi {
	label: string;
	value: string;
}
export interface ReportFinding {
	key: string;
	finding: string;
	sourceEngine: ReportSourceEngine;
}
export interface ReportClosing {
	label: string;
	engine: ReportSourceEngine;
	line: string;
}
export interface ReportProvenance {
	engines: Record<string, { label: string; sections: number; blocks: number }>;
	note: string;
}
export interface OverviewTake {
	key: string;
	label: string;
	line: string;
	engine: ReportSourceEngine;
}

// 행 헬퍼 · Num[] 에서 마지막 유효값
export function lastNonNull(values: Num[]): Num {
	for (let i = values.length - 1; i >= 0; i--) {
		const v = values[i];
		if (v != null && Number.isFinite(v)) return v;
	}
	return null;
}
