// 로컬 ipo 포트 · 발굴 목록은 공개 라이브 워커 소스를 공통배선 재사용(백엔드 0, price·finance 와 동일
// "깃헙페이지 자산 공유" 결). 단건 6카테고리 리포트만 로컬 /api 런타임 파싱(무거운 본문 파싱 = 로컬
// 상위집합, 터미널 HF-SSOT/로컬-compute 정합). 리포트는 rcept 단위 불변이라 LocalCaches 로 재파싱 방지.
import type { IpoPort, IpoReport } from '@dartlab/ui-contracts';
import type { LocalApi } from '../api/localApi';
import type { LocalCaches } from '../localTypes';
import { loadIpoFilings } from '../../public/sources/ipoFilingsSource';
import type { DataCore } from '../../../data/fetch/request';

export function localIpoPort(api: LocalApi, caches: LocalCaches, core: DataCore): IpoPort {
	return {
		// 공통배선 · 공개 라이브 워커(/ipo-filings) 그대로. 로컬 :8400 불요.
		recent: () => loadIpoFilings(core),

		report({ rceptNo, corpName, confirmationRceptNo }) {
			const key = `${rceptNo}:${confirmationRceptNo ?? ''}`;
			let p = caches.ipoReport.get(key);
			if (!p) {
				const qs = new URLSearchParams({ rcept: rceptNo });
				if (corpName) qs.set('corp', corpName);
				if (confirmationRceptNo) qs.set('confirmationRcept', confirmationRceptNo);
				p = api.getJson<IpoReport>(`/api/dart/ipo/report?${qs.toString()}`);
				caches.ipoReport.set(key, p);
			}
			return p;
		}
	};
}
