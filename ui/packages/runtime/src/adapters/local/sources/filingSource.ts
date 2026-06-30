// 로컬 filing 포트 · 정기/비정기 공시 목록·워치 신선도는 공개 HF 소스를 공통배선 재사용(백엔드 0,
// price·finance 와 동일 "깃헙페이지 자산 공유"). panel 격자(공시뷰어)만 로컬 /api · 인-터미널 뷰어는
// 백엔드 보유 시 여는 로컬 전용 기능(공개 어댑터는 단계-6 까지 notWiredYet). 타입 정본 = contracts.
import type {
	FilingPort,
	PanelGridResponse,
	PanelInitResponse,
	PanelTocResponse
} from '@dartlab/ui-contracts';
import type { LocalApi } from '../api/localApi';
import type { ClientPanelGrid, ClientPanelInit, ClientPanelToc, LocalCaches } from '../localTypes';
import { loadCompanyRegularFilings } from '../../public/sources/regularFilingsSource';
import { loadCompanyNonRegularFilings, loadMarketFeed, loadRecentFilingsForCodes } from '../../public/sources/nonRegularFilingsSource';
import type { DataCore } from '../../../data/fetch/request';

// 로컬 panel toc 는 leafType/disclosureKey 메타 미탑재 · 미제공 = null 정직 표기 (위조 금지).
function tocToContract(toc: ClientPanelToc): PanelTocResponse {
	return {
		stockCode: toc.stockCode,
		corpName: toc.corpName,
		periods: toc.periods,
		chapters: toc.chapters.map((ch) => ({
			chapter: ch.chapter,
			sections: ch.sections.map((s) => ({
				sectionLeaf: s.sectionLeaf,
				sectionKey: s.sectionKey,
				blocks: s.blocks.map((b) => ({ blockLeaf: b.blockLeaf, leafType: null, disclosureKey: null }))
			}))
		}))
	};
}

// chapter/sectionLeaf 가 null 이면 sectionKey(`${chapter}␟${sectionLeaf}`)에서 파생 · 키가 SSOT.
function gridToContract(g: ClientPanelGrid): PanelGridResponse {
	const [keyChapter = '', keyLeaf = ''] = g.sectionKey.split('␟');
	const dartUrlByPeriod = g.dartUrlByPeriod
		? Object.fromEntries(
				Object.entries(g.dartUrlByPeriod).filter((e): e is [string, string] => e[1] != null)
			)
		: undefined;
	return {
		stockCode: g.stockCode,
		corpName: g.corpName,
		chapter: g.chapter ?? keyChapter,
		sectionLeaf: g.sectionLeaf ?? keyLeaf,
		sectionKey: g.sectionKey,
		periods: g.periods,
		rows: g.rows.map((r) => ({ ...r, leafType: null })),
		dartUrlByPeriod
	};
}

// init 필수 구성(grid·first 포인터) 결손 = 사용 가능한 패널 없음 → null 정직 표기.
function initToContract(init: ClientPanelInit | null): PanelInitResponse | null {
	if (!init || !init.grid || init.firstChapter == null || init.firstSectionKey == null) return null;
	return {
		stockCode: init.stockCode,
		corpName: init.corpName,
		toc: tocToContract(init.toc),
		firstChapter: init.firstChapter,
		firstSectionKey: init.firstSectionKey,
		grid: gridToContract(init.grid)
	};
}

function loadPanelInit(api: LocalApi, caches: LocalCaches, code: string): Promise<ClientPanelInit | null> {
	const c = code.trim();
	let p = caches.panelInit.get(c);
	if (!p) {
		p = api.getJson<ClientPanelInit>(`/api/company/${encodeURIComponent(c)}/panel/init`);
		caches.panelInit.set(c, p);
	}
	return p;
}

export function localFilingPort(api: LocalApi, caches: LocalCaches, core: DataCore): FilingPort {
	return {
		// 공통배선 · 공개 HF 소스 그대로(정기 = regularFilingsSource, 비정기 = allFilings). 로컬 :8400 불요.
		regular: (code, limit = 500) => loadCompanyRegularFilings(core, code, limit),
		nonRegular: (code) => loadCompanyNonRegularFilings(core, code),
		recentForCodes: (codes) => loadRecentFilingsForCodes(core, codes),
		marketFeed: () => loadMarketFeed(core), // 시장 공시 피드 · 공개와 동일 공통배선(HF 통파일)

		async panelToc(code) {
			const toc = await api.getJson<ClientPanelToc>(
				`/api/company/${encodeURIComponent(code.trim())}/panel/toc`
			);
			return toc ? tocToContract(toc) : null;
		},
		async panelInit(code) {
			return initToContract(await loadPanelInit(api, caches, code));
		},
		async panelGrid(code, sectionKey) {
			const qs = new URLSearchParams({ section: sectionKey });
			const grid = await api.getJson<ClientPanelGrid>(
				`/api/company/${encodeURIComponent(code.trim())}/panel?${qs.toString()}`
			);
			return grid ? gridToContract(grid) : null;
		}
	};
}
