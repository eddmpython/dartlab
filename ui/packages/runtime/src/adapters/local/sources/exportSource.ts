// local ExportPort · 엔진 openpyxl 완전판 .xlsx(자동너비·음수 빨강·풍부 서식). /api/export/* 프록시(03 §3).
// generate: POST /api/export/excel {code, template} → FileResponse(.xlsx 바이너리) → object URL.
// 양식 CRUD: GET/POST/DELETE /api/export/templates (data.py 계약). listExportableTables 는 공유 순수 함수(동일).
// 모든 /api 호출은 로컬 게이트(api/localApi) 경유 · raw fetch·URL 합성을 이 source 가 직접 갖지 않는다(02 §5).
// blob·DELETE·상태코드별 정직 표기가 필요하므로 게이트의 fetchRaw 로 raw Response 를 받아 해석한다.
// silent fallback 금지(게이트 규약) · 실패는 throw/정직 표기, 다른 소스 우회 0.

import type {
	ExcelTemplate,
	ExportArtifact,
	ExportableTable,
	ExportBundleLike,
	ExportInput,
	ExportPort
} from '@dartlab/ui-contracts';
import { listExportableTables, selectionsToTemplate } from '../../export/exportShared';
import type { LocalApi } from '../api/localApi';

const XLSX_MIME = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet';

/** Content-Disposition filename 추출(서버 FileResponse 가 outPath.name 을 지정) · 없으면 폴백. */
function filenameFromResponse(res: Response, fallback: string): string {
	const cd = res.headers.get('content-disposition') ?? '';
	const star = /filename\*=(?:UTF-8'')?([^;]+)/i.exec(cd);
	if (star?.[1]) return decodeURIComponent(star[1].replace(/"/g, '').trim());
	const plain = /filename="?([^";]+)"?/i.exec(cd);
	if (plain?.[1]) return plain[1].trim();
	return fallback;
}

/**
 * local ExportPort 생성 · 엔진 /api/export/* 프록시(로컬 게이트 경유).
 *
 * @param api 로컬 provider 게이트(createLocalRuntime 이 1개 만들어 주입).
 * @returns ExportPort.
 *
 * @example
 * const port = localExportPort(createLocalApi(''));
 */
export function localExportPort(api: LocalApi): ExportPort {
	return {
		listExportableTables(bundle: ExportBundleLike): ExportableTable[] {
			return listExportableTables(bundle);
		},

		async listTemplates(): Promise<ExcelTemplate[]> {
			const res = await api.getJson<{ templates: ExcelTemplate[] }>('/api/export/templates');
			return res?.templates ?? [];
		},

		async saveTemplate(template: ExcelTemplate): Promise<string> {
			const r = await api.fetchRaw('/api/export/templates', {
				method: 'POST',
				headers: { 'content-type': 'application/json' },
				body: JSON.stringify(template)
			});
			if (!r.ok) throw new Error(`양식 저장 실패 (${r.status})`);
			const body = (await r.json()) as { ok: boolean; templateId: string };
			return body.templateId;
		},

		async deleteTemplate(id: string): Promise<boolean> {
			const r = await api.fetchRaw(`/api/export/templates/${encodeURIComponent(id)}`, {
				method: 'DELETE'
			});
			// 400 = 프리셋 삭제 불가(정직 false), 그 외 실패도 false.
			if (!r.ok) return false;
			const body = (await r.json()) as { ok: boolean };
			return body.ok === true;
		},

		async generate(input: ExportInput): Promise<ExportArtifact> {
			const template = selectionsToTemplate(input);
			const r = await api.fetchRaw('/api/export/excel', {
				method: 'POST',
				headers: { 'content-type': 'application/json' },
				body: JSON.stringify({ code: input.code, template })
			});
			if (!r.ok) {
				let detail = `내보내기 실패 (${r.status})`;
				try {
					const err = (await r.json()) as { detail?: string };
					if (err?.detail) detail = err.detail;
				} catch {
					/* 비 JSON 응답 무시 */
				}
				throw new Error(detail);
			}
			const blob = await r.blob();
			const filename = filenameFromResponse(r, `${input.code}_공시표.xlsx`);
			// FileResponse 바이너리 → object URL(surface 가 navigate/다운로드). mime 은 응답값 우선.
			const url = URL.createObjectURL(blob);
			return { filename, mime: blob.type || XLSX_MIME, url };
		}
	};
}
