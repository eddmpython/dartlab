// terminal surface 공개 표면 (§8.1 · 작업면 한 폴더, index.ts 하나가 공개 API).
// 셸(landing route · ui/web 브리지)이 소비하는 마운트 표면 + 셸 글루(routeLoad)가 쓰는 데이터 형태만 공개.
// 내부 부품(panels·charts·ui·engine 헬퍼)은 비공개 · 트리 내부 상대 import 로만 접근.
export { default as TerminalSurface } from './TerminalSurface.svelte';
// 후원·기여 센터 · 자기완결(terminal.css 불필요) 라 landing 헤더 등 다른 셸에서도 재사용.
export { default as SupportDialog } from './panels/SupportDialog.svelte';
// 브랜드 색 테마 아이콘 · 자기완결(document 직접). 터미널 topbar·카드·랜딩 Header 가 *동일* 컨트롤 공유.
export { default as BrandSwitch } from './ui/BrandSwitch.svelte';
// SNS 아이콘 묶음 SSOT · GitHub·후원·YouTube·Threads·Instagram. landing(/cards·/report)·로컬 챗 셸 공유.
// 컴포넌트가 마크업·치수·색을 모두 소유한다(색만 --brandSocial-* 로 열림). `.dlTerm` 스코프 불필요.
export { default as BrandSocial } from './ui/BrandSocial.svelte';
// 브랜드 마크 SSOT · 아바타·DartLab·/·표면 태그. 터미널·카드·리포트·노트북 허브가 같은 마크업/치수/색을 쓴다.
export { default as BrandMark } from './ui/BrandMark.svelte';
// 재무 추이 미니차트 · finance.bundle 의 FinCard 를 경량 SVG 렌더(klinecharts·백테스트 0 의존).
// landing /cards 라이브 카드 캐러셀의 백본 슬라이드가 터미널과 동일한 재무 시각을 재현할 때 재사용.
// (heatmap/bars 등 백테스트 자본곡선 의존 차트는 백본 아님 → export 보류.)
export { default as MiniFinChart } from './charts/MiniFinChart.svelte';
export { CARD_GUIDE, type CardGuide } from './lib/cardGuide';
export { createEngine } from './lib/engine';
export type { Engine } from './lib/engine';
export type {
	TerminalHosts,
	TerminalBrandLinks,
	SupportPerson,
	SupportDonor,
	ViewerStudioHostProps,
	FinanceDialogHostProps
} from './lib/hosts';
// dartlab 브랜드·후원 SSOT · landing·local 셸 공통 주입 정본.
export { DARTLAB_BRAND_LINKS } from './lib/brandLinks';
export { LAST_SYM_KEY } from './lib/lastSymbol';
export { warmCompany } from './lib/warmup';
// GitHub 스타 라이브 배지 · landing 보고서 헤더 등 다른 셸이 터미널과 동일한 SNS 배지를 재현할 때 재사용.
export { fetchGithubStars, fmtStars } from './lib/githubStars';
// 데이터 형태 · landing 셸 글루(terminal-shell/routeLoad.ts)의 RawData 조립 + ui/web 브리지(localTerminalData) 소비.
export type {
	RawData,
	FinanceCompany,
	FinanceFile,
	MacroFile,
	MetaFile,
	PricesFile,
	PriceRow,
	IndexRow,
	EcosystemFile,
	QuartersFile,
	IndustryStatsFile
} from './lib/types';
