// landing 공개 셸의 runtime 컴포지션 루트 · createPublicRuntime 인스턴스는 여기 1곳에서만 만든다.
// 공유 엔진(duckdb-wasm) 의존 메서드(reportFacts·changes)는 landing 잔류 모듈을 주입해 의존 방향을
// 보존한다 (packages → landing 역참조 금지). 컴포넌트는 setDartLabRuntime/useDartLabRuntime 컨텍스트로,
// 라우트 load·scan 글루 같은 비컴포넌트 셸 코드만 getPublicRuntime() 을 직접 부른다.
import { base } from '$app/paths';
import type { DartLabRuntime, ExportInput, ViewerPort } from '@dartlab/ui-contracts';
import { createPublicRuntime, type PublicExportShared } from '@dartlab/ui-runtime';
import { loadLiveCompanyReportFacts, loadLiveCompanyChanges } from '$lib/browser/companyLive';
import { loadPanelBundle, exportInputToWorkbookBytes } from '@dartlab/ui-surfaces/viewer';

// 공개 셸의 뷰어 = 임베드 컴포넌트 (터미널 오버레이가 ViewerStudio 를 lazy 마운트).
// urlForCompany = null → 오버레이가 iframe 대신 컴포넌트 임베드를 선택한다 (옛 localAdapter 의미 보존).
function publicViewerPort(): ViewerPort {
	const companyUrl = (code: string, vs?: string[]): string => {
		const qs = vs?.length ? `?vs=${encodeURIComponent(vs.join(','))}` : '';
		return `${base}/viewer/company/${encodeURIComponent(code)}${qs}`;
	};
	return {
		mode: 'component',
		urlForCompany: () => null,
		async openCompany(code, options) {
			location.assign(companyUrl(code, options?.vs));
		},
		async openFiling(filing) {
			window.open(filing.url, '_blank', 'noopener');
		}
	};
}

// table-export · public ExportPort.generate 가 wrap 할 브라우저 워크북 빌더. ViewerStudio 직접 경로와 *동일*
// loadPanelBundle(LRU 캐시 · 재다운로드 0) + exportInputToWorkbookBytes(deriveWorkbookInput+buildWorkbook) 라 산출 동형.
const exportShared: PublicExportShared = {
	async buildWorkbookBytes(input: ExportInput) {
		const bundle = await loadPanelBundle(input.code);
		return exportInputToWorkbookBytes(input, bundle);
	},
	corpName(code: string) {
		return code; // 회사명은 bundle 에 있으나 파일명 폴백은 code 로 충분(generate 가 safeFilename 처리).
	}
};

let instance: DartLabRuntime | null = null;

export function getPublicRuntime(): DartLabRuntime {
	instance ??= createPublicRuntime({
		env: {
			basePath: base,
			locale: 'ko',
			marketDefault: 'KR',
			buildVersion: __DARTLAB_VERSION__,
			readonly: true
		},
		shared: {
			reportFacts: loadLiveCompanyReportFacts,
			changes: loadLiveCompanyChanges
		},
		viewer: publicViewerPort(),
		exportShared
	});
	return instance;
}
