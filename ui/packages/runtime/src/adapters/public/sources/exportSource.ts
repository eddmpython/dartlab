// public ExportPort · 브라우저 zero-dep .xlsx 생성 + localStorage 양식 CRUD + 동봉 PRESETS (03 §3).
// 패리티: generate 는 surfaces 의 buildWorkbook 을 wrap 한다. 단 surfaces 는 runtime 을 의존하므로(역방향 금지)
// runtime 이 surfaces 를 import 하면 순환 · 셸(landing)이 buildWorkbookBytes(선택→격자 파생+buildWorkbook)를
// 주입한다(reportFacts·changes 와 동일 shared 주입 패턴). 미주입이면 generate 가 정직히 에러(silent fallback 금지).

import type {
	ExcelTemplate,
	ExportArtifact,
	ExportableTable,
	ExportBundleLike,
	ExportInput,
	ExportPort,
	StoragePort
} from '@dartlab/ui-contracts';
import { listExportableTables } from '../../export/exportShared';

const XLSX_MIME = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet';

// 동봉 PRESETS · 서버 0 공개 표면은 ~/.dartlab/templates 를 못 쓰므로 정적 양식만(엔진 모듈 시트 = 로컬 전용).
// 공시 표 selection 은 사용자가 격자에서 즉석 구성 → 양식 저장은 localStorage. PRESETS 는 빈 셸(공개는 모듈
// 시트 미지원)이라 현재 0개 · 구조만 둔다(미래 공개 가능한 공시 표 묶음 양식용).
const PRESETS: ExcelTemplate[] = [];

const TEMPLATE_STORE_KEY = 'viewer.exportTemplates' as const;

/** 공개 generate 가 셸로부터 주입받는 워크북 빌더 · 선택→격자 파생 + buildWorkbook(surfaces, bundle-bound). */
export interface PublicExportShared {
	/** ExportInput → 진짜 .xlsx 바이트(null = 내보낼 데이터 없음). 셸이 surfaces loadPanelBundle+deriveWorkbookInput+buildWorkbook
	 *  로 구현(LRU 캐시라 재다운로드 0). bundle 비동기 로드 위해 Promise. */
	buildWorkbookBytes(input: ExportInput): Promise<Uint8Array | null>;
	/** 파일명용 표시 회사명(없으면 code). bundle 미로드 가능성에 sync 폴백 허용. */
	corpName(code: string): string;
}

function notWiredYet(): never {
	throw new Error(
		'[public export] generate 는 셸이 buildWorkbookBytes 를 주입해야 한다 · 미주입 호출은 배선 순서 위반이다.'
	);
}

function safeFilename(name: string): string {
	return (name || 'export').replace(/[\\/:*?"<>|]/g, '_');
}

/**
 * public ExportPort 생성 · shared 주입(셸)이 있으면 generate 가 brower .xlsx, 없으면 generate 만 throw 게이트.
 *
 * @param storage 양식 영속용 StoragePort(localStorage 백엔드).
 * @param shared 셸 주입 워크북 빌더(미주입이면 generate 트립와이어).
 * @returns ExportPort.
 *
 * @example
 * const port = publicExportPort(storage, { buildWorkbookBytes, corpName });
 */
export function publicExportPort(storage: StoragePort, shared?: PublicExportShared): ExportPort {
	return {
		listExportableTables(bundle: ExportBundleLike): ExportableTable[] {
			return listExportableTables(bundle);
		},

		async listTemplates(): Promise<ExcelTemplate[]> {
			const saved = (await storage.get<ExcelTemplate[]>(TEMPLATE_STORE_KEY)) ?? [];
			return [...PRESETS, ...saved];
		},

		async saveTemplate(template: ExcelTemplate): Promise<string> {
			const id = template.templateId || `t_${Date.now()}`;
			const withId: ExcelTemplate = { ...template, templateId: id, updatedAt: Date.now() };
			const saved = (await storage.get<ExcelTemplate[]>(TEMPLATE_STORE_KEY)) ?? [];
			const next = saved.filter((t) => t.templateId !== id);
			next.push(withId);
			await storage.set(TEMPLATE_STORE_KEY, next);
			return id;
		},

		async deleteTemplate(id: string): Promise<boolean> {
			// PRESET 은 삭제 불가(정적) · 정직히 false.
			if (PRESETS.some((t) => t.templateId === id)) return false;
			const saved = (await storage.get<ExcelTemplate[]>(TEMPLATE_STORE_KEY)) ?? [];
			const next = saved.filter((t) => t.templateId !== id);
			if (next.length === saved.length) return false;
			await storage.set(TEMPLATE_STORE_KEY, next);
			return true;
		},

		async generate(input: ExportInput): Promise<ExportArtifact> {
			if (!shared) notWiredYet();
			const bytes = await shared.buildWorkbookBytes(input);
			if (!bytes || bytes.length === 0) {
				throw new Error('선택한 표에서 내보낼 데이터를 찾지 못했습니다.');
			}
			// lib.dom BlobPart 는 ArrayBufferView<ArrayBuffer> 요구 · slice() 로 정확한 ArrayBuffer 사본(dataExport.downloadBlob 동일).
			const copy = bytes.slice();
			const corp = shared.corpName(input.code);
			return {
				filename: `${safeFilename(corp)}_공시표.xlsx`,
				mime: XLSX_MIME,
				blob: new Blob([copy.buffer as ArrayBuffer], { type: XLSX_MIME })
			};
		}
	};
}
