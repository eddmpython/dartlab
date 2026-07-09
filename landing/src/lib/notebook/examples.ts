// dartlab 노트북 예제 SSOT. 허브 갤러리(+추후 블로그 임베드)가 이 레지스트리를 공유한다.
// 커널은 범용 파이썬이지만 예제는 dartlab 엔진을 세밀하게 쪼갠 granular 데모다.
// 각 예제 = [설명 markdown] + [공유 SETUP 부트스트랩] + [엔진 호출 셀들(셀당 한 호출)].
import type { Cell } from './stores/notebookStore';

export interface NotebookExample {
	id: string;
	title: string;
	description: string;
	tags: string[];
	cells: Cell[];
}

// 공유 부트스트랩: import dartlab 만 하면 노트북이 최초 1회 자동 설치(워커가 micropip 로 처리). 그다음은
// 데스크톱과 완전히 동일하게 Company 를 쓴다. 설치·C 확장·데이터경로·lazy fetch 등 복잡성은 라이브러리가
// 통째로 흡수하므로 prefetch 나 await, loadPackage 가 필요 없다. 데이터는 메서드 첫 접근 시 자동 다운로드.
const SETUP = `# dartlab 은 import 하면 노트북이 알아서 설치한다 (최초 1회 약 20초).
import dartlab
c = dartlab.Company("005930")   # 데스크톱과 동일. 데이터는 첫 접근 시 자동 다운로드`;

function cells(exampleId: string, defs: [Cell['type'], string][]): Cell[] {
	return defs.map(([type, content], i) => ({ id: `${exampleId}-${i}`, type, content }));
}

export const EXAMPLES: NotebookExample[] = [
	{
		id: 'dartlab-panel-statements',
		title: `panel: 공시 수평화 보드에서 IS·BS·CF 꺼내기`,
		description: `c.panel 로 회사 공시 보드를 잡고 손익계산서·재무상태표·현금흐름표를 꺼냅니다.`,
		tags: ['company', 'panel'],
		cells: cells('dartlab-panel-statements', [
			['markdown', `# panel: 공시 수평화 보드

\`c.panel\` 은 한 회사의 공시(재무제표·주석·서술)를 '항목 × 기간' 하나의 큰 wide 표로 세워 둔 보드입니다. 잡는 순간 그대로 polars DataFrame 이고, 이름을 주면(예: \`c.panel("IS")\`) 그 표를 강한 정규화 소스(finance)로 꺼내 줍니다.

배우는 것: 보드의 모양 보기, 손익계산서(IS)·재무상태표(BS)·현금흐름표(CF) 호출.

먼저 아래 setup 셀을 실행하세요. 약 20초 걸리며 dartlab 을 브라우저에 올립니다.`],
			['code', SETUP],
			['code', `# 공시 수평화 보드: 행 = 공시 항목, 열 = 기간. 잡는 순간 하나의 큰 wide 표
c.panel.shape`],
			['code', `# 손익계산서 (분기 연결 기본). 강한 소스(finance)가 자동 주입된다
c.panel("IS")`],
			['code', `# 재무상태표
c.panel("BS")`],
			['code', `# 현금흐름표
c.panel("CF")`],
		])
	},
	{
		id: 'dartlab-select-accounts',
		title: `select: 특정 계정 시계열만 콕 집어 뽑기`,
		description: `c.select 로 IS·BS 에서 원하는 계정만 골라 분기·연간·별도 시계열로 뽑습니다.`,
		tags: ['company', 'select'],
		cells: cells('dartlab-select-accounts', [
			['markdown', `# select: 계정 시계열 뽑기

\`c.select(topic, 계정목록)\` 은 재무제표 전체 대신 필요한 행(계정)만 골라 SelectResult 로 돌려줍니다. \`freq\` 로 분기·연간을, \`scope\` 로 연결·별도를 토글합니다.

배우는 것: 계정 1개 뽑기, 여러 계정 동시, 연간 합산(freq), 별도재무제표(scope).

아래 setup 셀을 먼저 실행하세요 (약 20초).`],
			['code', SETUP],
			['code', `# IS 에서 매출액 한 줄만. 분기 컬럼 전체가 딸려온다 (SelectResult 로 렌더)
c.select("IS", ["매출액"])`],
			['code', `# 여러 계정 동시 추출
c.select("IS", ["매출액", "영업이익", "당기순이익"])`],
			['code', `# freq="Y" 로 연간 합산 매출
c.select("IS", ["매출액"], freq="Y")`],
			['code', `# scope="separate" 로 별도재무제표의 자본총계
c.select("BS", ["자본총계"], scope="separate")`],
		])
	},
	{
		id: 'dartlab-analysis-axes',
		title: `analysis: 재무 22축 심층 분석 (수익성·성장성·안정성)`,
		description: `c.analysis 로 22축 카탈로그를 보고 수익성·성장성·안정성 축을 분석합니다.`,
		tags: ['analysis'],
		cells: cells('dartlab-analysis-axes', [
			['markdown', `# analysis: 재무 22축 심층 분석

\`c.analysis()\` 를 인자 없이 부르면 무엇을 분석할 수 있는지 22축 카탈로그를 표로 돌려줍니다. \`c.analysis(그룹, 축)\` 로 개별 축을 지정하면 시계열·전환점·데이터 기준시점이 담긴 dict 를 돌려줍니다.

배우는 것: 축 카탈로그 보기, financial 그룹의 수익성·성장성·안정성 분석.

참고: 축 결과는 표가 아니라 dict(텍스트)로 출력됩니다. 아래 setup 셀을 먼저 실행하세요 (약 20초).`],
			['code', SETUP],
			['code', `# 인자 없이 호출하면 22축 카탈로그(무엇을 부를 수 있나)를 표로 돌려준다
c.analysis()`],
			['code', `# financial 그룹의 수익성 축. history / turningPoints / dataAsOf 등이 담긴 dict
c.analysis("financial", "수익성")`],
			['code', `# 성장성 축
c.analysis("financial", "성장성")`],
			['code', `# 안정성 축
c.analysis("financial", "안정성")`],
		])
	},
	{
		id: 'dartlab-credit-dcr',
		title: `credit: dartlab 독립 신용등급 dCR 과 7축`,
		description: `c.credit 로 dartlab 독립 신용등급(dCR)과 7축 위험 점수를 계산합니다.`,
		tags: ['credit'],
		cells: cells('dartlab-credit-dcr', [
			['markdown', `# credit: 독립 신용등급 dCR

\`c.credit()\` 은 dartlab 자체 신용평가 엔진이 산출하는 dCR 등급(AAA~D)과 종합 점수를 돌려줍니다. 7축(채무상환·자본구조·유동성·현금흐름·사업안정성·재무신뢰성·공시리스크)을 개별로 부르거나 \`detail=True\` 로 시계열까지 한 번에 볼 수 있습니다.

배우는 것: 종합 등급, 채무상환·유동성 축, 7축 상세.

참고: 결과는 dict(텍스트)로 출력됩니다. 아래 setup 셀을 먼저 실행하세요 (약 20초).`],
			['code', SETUP],
			['code', `# 종합 신용등급(dCR). grade / score / healthScore / axes / outlook
c.credit()`],
			['code', `# 채무상환 축만
c.credit("채무상환")`],
			['code', `# 유동성 축만
c.credit("유동성")`],
			['code', `# detail=True 로 7축 상세 + 지표 시계열
c.credit(detail=True)`],
		])
	},
	{
		id: 'dartlab-story-section',
		title: `story: 재무 서사를 6막 인과 블록으로`,
		description: `c.story 로 재무 한 섹션을 6막 인과 서사 블록으로 조립합니다.`,
		tags: ['story'],
		cells: cells('dartlab-story-section', [
			['markdown', `# story: 재무 서사 블록

\`c.story(섹션)\` 은 여러 분석 엔진의 결과를 사람이 읽는 서사 블록으로 조립한 보고서(Story)를 돌려줍니다. Story 객체는 표·문장이 섞인 형태로 렌더되고, \`.toMarkdown()\` 으로 원문을 꺼낼 수 있습니다.

배우는 것: 수익성 섹션 렌더, 같은 결과의 마크다운 원문.

참고: 이 예제는 조립 과정 때문에 수십 초 걸릴 수 있습니다. 아래 setup 셀을 먼저 실행하세요 (약 20초).`],
			['code', SETUP],
			['code', `# 수익성 섹션의 서사 블록. 조립에 수십 초 걸릴 수 있다
st = c.story("수익성")
st`],
			['code', `# 같은 결과를 마크다운 원문으로 (앞 1200자). Story.toMarkdown() 사용
print(st.toMarkdown()[:1200])`],
		])
	},
];

export function getExample(id: string): NotebookExample | undefined {
	return EXAMPLES.find((e) => e.id === id);
}
