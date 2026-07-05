// 로컬 ipo 포트 · 발굴 목록은 공개 라이브 워커 소스를 공통배선 재사용(백엔드 0). 단건 리포트는
// 왓치가 구운 HF(dart/ipo/reports.parquet)를 퍼블릭과 동일하게 우선 직독(빠름). 미베이크(다음 cron 전)
// 발행사만 로컬 서버가 원문 라이브 파싱(/api). 로컬 상위집합 = HF 베이크 + 로컬 라이브 헤드룸.
// 리포트는 rcept 단위 사실상 불변이라 LocalCaches 로 재조회/재파싱 방지.
import type { IpoPort, IpoReport } from '@dartlab/ui-contracts';
import type { LocalApi } from '../api/localApi';
import type { LocalCaches } from '../localTypes';
import { loadIpoFilings } from '../../public/sources/ipoFilingsSource';
import { loadIpoReport } from '../../public/sources/ipoReportSource';
import type { DataCore } from '../../../data/fetch/request';

export function localIpoPort(api: LocalApi, caches: LocalCaches, core: DataCore): IpoPort {
	return {
		// 공통배선 · 공개 라이브 워커(/ipo-filings) 그대로. 로컬 :8400 불요.
		recent: () => loadIpoFilings(core),

		report({ rceptNo, corpName, confirmationRceptNo }) {
			const key = `${rceptNo}:${confirmationRceptNo ?? ''}`;
			let p = caches.ipoReport.get(key);
			if (!p) {
				p = (async () => {
					// 공통배선: 왓치가 구운 HF 리포트 우선(퍼블릭과 동일 경로, 빠름).
					const baked = await loadIpoReport(core, rceptNo);
					if (baked) return baked;
					// 로컬 상위집합 헤드룸: 미베이크(다음 cron 전) 발행사만 로컬 서버가 원문 라이브 파싱.
					const qs = new URLSearchParams({ rcept: rceptNo });
					if (corpName) qs.set('corp', corpName);
					if (confirmationRceptNo) qs.set('confirmationRcept', confirmationRceptNo);
					return api.getJson<IpoReport>(`/api/dart/ipo/report?${qs.toString()}`);
				})();
				caches.ipoReport.set(key, p);
			}
			return p;
		}
	};
}
