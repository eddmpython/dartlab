// 로컬 scan 포트 · 회사 변경 피드는 로컬 미배선(해당 없음 []), 테이블 소스·프리셋은 단계-8(ScanSurface) throw.
import type { ScanPort } from '@dartlab/ui-contracts';
import { notWiredYet } from '../fetchJson';
import { listScanPresets, saveScanPreset } from '../../../data/scanPresets';

export function localScanPort(): ScanPort {
	return {
		// 로컬 changes 피드 미배선 · 해당 없음 = [].
		async changes() {
			return [];
		},
		listTableSources: () => notWiredYet('scan.listTableSources', '단계-8(scan 추출)'),
		async getPresets() {
			return listScanPresets();
		},
		async savePreset(preset) {
			saveScanPreset(preset);
		}
	};
}
