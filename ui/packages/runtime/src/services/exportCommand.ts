// export.tablesToExcel · command palette(⌘K "엑셀로 내보내기") 진입점 (03 §5).
// 분업(03 §2): ServiceCommand 가 진입점, execute 는 ExportPort.generate 위임 후 ServiceCommandResult{kind:'toast'} 반환.
// args.input = ExportInput(현재 선택). 산출은 toast(blob/url 은 Port 가, 다운로드 트리거는 surface 가).

import type {
	ExportInput,
	ExportPort,
	ServiceCommandInput,
	ServiceCommandResult
} from '@dartlab/ui-contracts';
import type { ServiceRegistration } from './serviceRegistry';

const COMMAND_ID = 'export.tablesToExcel';
const SERVICE_ID = 'export';

/**
 * export 서비스 등록 · descriptor + command + execute(ExportPort.generate 위임).
 *
 * @param exportPort 런타임 export Port(public=브라우저 .xlsx / local=엔진 완전판).
 * @param onArtifact 산출물 처리 콜백(surface 다운로드 트리거 주입). 미주입이면 toast 만(다운로드는 호출측 책임).
 * @returns ServiceRegistration · createServiceRegistry 입력.
 *
 * @example
 * const reg = exportServiceRegistration(runtime.export);
 */
export function exportServiceRegistration(
	exportPort: ExportPort,
	onArtifact?: (artifact: { filename: string; mime: string; blob?: Blob; url?: string }) => void
): ServiceRegistration {
	return {
		descriptor: {
			id: SERVICE_ID,
			label: '표 내보내기',
			group: 'export',
			availability: 'available'
		},
		commands: [
			{
				id: COMMAND_ID,
				serviceId: SERVICE_ID,
				label: '엑셀로 내보내기',
				icon: 'file-spreadsheet',
				mode: 'both',
				requires: [{ kind: 'code' }]
			}
		],
		async execute(input: ServiceCommandInput): Promise<ServiceCommandResult> {
			const payload = input.args?.input as ExportInput | undefined;
			if (!payload || !payload.code || !payload.selections?.length) {
				return { kind: 'toast', ok: false, message: '내보낼 표를 선택하세요.' };
			}
			try {
				const artifact = await exportPort.generate(payload);
				onArtifact?.(artifact);
				return { kind: 'toast', ok: true, message: '다운로드 완료', payload: artifact };
			} catch (e) {
				return { kind: 'toast', ok: false, message: e instanceof Error ? e.message : String(e) };
			}
		}
	};
}
