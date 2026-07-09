// dartlab 노트북 예제 SSOT. 허브 갤러리(+추후 블로그 임베드)가 이 레지스트리를 공유한다.
// 커널은 범용 파이썬이지만 예제는 dartlab 을 처음부터 익히는 단계별 커리큘럼이다.
//
// 순서가 곧 커리큘럼이다: 기초(회사 잡기 → 재무제표 → 계정 뽑기) → 중급(무엇을 더 볼 수 있나 →
// 22축 분석) → 심화(직접 계산 → 전종목 횡단 → 신용등급 → 서사). 각 예제는 [설명 markdown] +
// [공유 SETUP 부트스트랩] + [셀당 한 호출] 로 이루어진다.
//
// ⚠ 여기 실린 호출은 전부 브라우저(pyodide)에서 실제로 실행해 확인한 것만 쓴다. 브라우저에서
// 못 도는 호출(네트워크 수집·전종목 screen 등)은 예제로 넣지 않고, 대신 경계를 설명한다.
import type { Cell } from './stores/notebookStore';

/** 커리큘럼 단계. 허브 갤러리가 이 순서로 묶어 보여 준다. */
export type ExampleLevel = '기초' | '중급' | '심화';

export interface NotebookExample {
	id: string;
	title: string;
	description: string;
	level: ExampleLevel;
	tags: string[];
	cells: Cell[];
}

// 공유 부트스트랩: import dartlab 만 하면 노트북이 최초 1회 자동 설치(워커가 micropip 로 처리). 그다음은
// 데스크톱과 완전히 동일하게 Company 를 쓴다. 설치·C 확장·데이터경로·lazy fetch 등 복잡성은 라이브러리가
// 통째로 흡수하므로 prefetch 나 await, loadPackage 가 필요 없다. 데이터는 메서드 첫 접근 시 자동 다운로드.
const SETUP = `# dartlab 은 import 하면 노트북이 알아서 설치한다 (최초 1회 약 20초).
import dartlab
c = dartlab.Company("005930")   # 데스크톱과 동일. 데이터는 첫 접근 시 자동 다운로드`;

/** 브라우저와 로컬의 차이를 설명하는 공용 안내 (예제 markdown 말미에 덧댄다). */
const BROWSER_NOTE = `---

**브라우저에서 도는 중입니다.** 공시·재무 데이터는 HuggingFace 에서 바로 받아 브라우저 안에서 계산합니다.
설치한 파이썬이 없어도 되고, 결과가 서버로 나가지도 않습니다. 반대로 실시간 시세·수급·뉴스처럼
바깥으로 나가야 하는 수집은 브라우저 보안 정책에 막혀 로컬 설치본에서만 됩니다.`;

function cells(exampleId: string, defs: [Cell['type'], string][]): Cell[] {
	return defs.map(([type, content], i) => ({ id: `${exampleId}-${i}`, type, content }));
}

export const EXAMPLES: NotebookExample[] = [
	// ── 기초 ──────────────────────────────────────────────────────────────
	{
		id: 'dartlab-panel-statements',
		title: `1. 회사를 잡고 재무제표 3종 꺼내기`,
		description: `Company 하나로 손익계산서·재무상태표·현금흐름표를 그대로 받습니다. 첫걸음.`,
		level: '기초',
		tags: ['company', 'panel'],
		cells: cells('dartlab-panel-statements', [
			['markdown', `# 1. 회사를 잡고 재무제표 3종 꺼내기

dartlab 에서 모든 것은 **회사 하나를 잡는 것**에서 시작합니다.

\`\`\`python
c = dartlab.Company("005930")   # 삼성전자
\`\`\`

그 회사의 공시(재무제표·주석·서술)는 '항목 x 기간' 하나의 큰 표로 세워져 있습니다. 이것을 \`panel\` 이라 부릅니다.
이름을 주면 그 표를 꺼내 줍니다. \`c.panel("IS")\` 는 손익계산서, \`"BS"\` 는 재무상태표, \`"CF"\` 는 현금흐름표입니다.

배우는 것: 회사 잡기, 보드의 모양 보기, 재무제표 3종 호출.

아래 setup 셀부터 순서대로 실행하세요. 최초 1회 dartlab 설치에 20초쯤 걸립니다.

${BROWSER_NOTE}`],
			['code', SETUP],
			['code', `# 공시 수평화 보드: 행 = 공시 항목, 열 = 기간. 잡는 순간 하나의 큰 표
c.panel.shape`],
			['code', `# 손익계산서 (분기 연결 기본). 처음 부를 때 보드를 내려받아 수 초 걸린다
c.panel("IS")`],
			['code', `# 재무상태표
c.panel("BS")`],
			['code', `# 현금흐름표
c.panel("CF")`],
			['code', `# 다른 회사도 똑같다. 코드만 바꾸면 된다 (000660 = SK하이닉스)
dartlab.Company("000660").panel("IS")`]
		])
	},
	{
		id: 'dartlab-select-accounts',
		title: `2. 필요한 계정만 콕 집어 뽑기`,
		description: `재무제표 전체 대신 매출액·영업이익 같은 필요한 행만 시계열로 받습니다.`,
		level: '기초',
		tags: ['company', 'select'],
		cells: cells('dartlab-select-accounts', [
			['markdown', `# 2. 필요한 계정만 콕 집어 뽑기

재무제표 전체를 보는 일은 드뭅니다. 보통은 **몇 개 계정의 시계열**이 필요하죠.

\`c.select(주제, 계정목록)\` 이 그 일을 합니다. \`freq\` 로 분기/연간을, \`scope\` 로 연결/별도를 바꿉니다.

배우는 것: 계정 1개 뽑기, 여러 계정 동시, 연간 합산, 별도재무제표.

${BROWSER_NOTE}`],
			['code', SETUP],
			['code', `# IS 에서 매출액 한 줄만. 분기 컬럼 전체가 딸려온다
c.select("IS", ["매출액"])`],
			['code', `# 여러 계정 동시
c.select("IS", ["매출액", "영업이익", "당기순이익"])`],
			['code', `# freq="Y" 로 연간
c.select("IS", ["매출액"], freq="Y")`],
			['code', `# scope="separate" 로 별도재무제표의 자본총계
c.select("BS", ["자본총계"], scope="separate")`]
		])
	},

	// ── 중급 ──────────────────────────────────────────────────────────────
	{
		id: 'dartlab-gather-catalog',
		title: `3. 이 회사에서 무엇을 더 가져올 수 있나`,
		description: `gather 카탈로그로 수집 가능한 축(시세·수급·뉴스·업종...)을 훑고, 브라우저와 로컬의 경계를 확인합니다.`,
		level: '중급',
		tags: ['gather', 'catalog'],
		cells: cells('dartlab-gather-catalog', [
			['markdown', `# 3. 이 회사에서 무엇을 더 가져올 수 있나

재무제표 말고도 회사에는 시세·수급·뉴스·업종 같은 데이터가 붙습니다. 그것을 모아 오는 일을 **gather** 라고 합니다.

인자 없이 \`c.gather()\` 를 부르면 **무엇을 가져올 수 있는지 목록(카탈로그)** 을 표로 돌려줍니다.
같은 방식으로 \`c.quant()\` 는 기술적 지표 축을, \`c.analysis()\` 는 분석 축을 훑게 해 줍니다.
dartlab 에서 "인자 없이 부르면 카탈로그" 는 어디서나 통하는 약속입니다.

**여기서 브라우저와 로컬이 갈립니다.** 카탈로그는 브라우저에서도 보이지만, 실제 시세·수급 수집은
바깥 사이트로 나가야 해서 브라우저 보안 정책에 막힙니다. 마지막 셀이 그 경계를 실제로 보여 줍니다.

${BROWSER_NOTE}`],
			['code', SETUP],
			['code', `# 수집 가능한 축 카탈로그 (axis / label / description / example / 인증)
c.gather()`],
			['code', `# 기술적 지표 축 카탈로그
c.quant()`],
			['code', `# 분석 축 카탈로그 (22축)
c.analysis()`],
			['code', `# 경계 확인: 시세 수집은 바깥 네트워크가 필요해 브라우저에서 막힌다.
# 로컬(pip install dartlab)에서는 그대로 동작한다.
try:
    c.gather("price")
except Exception as e:
    print(type(e).__name__, "->", e)
    print("\\n시세·수급·뉴스 수집은 로컬 설치본에서 쓰세요.")`]
		])
	},
	{
		id: 'dartlab-analysis-axes',
		title: `4. 22축 분석 (수익성·성장성·안정성)`,
		description: `c.analysis 로 축 카탈로그를 보고 수익성·성장성·안정성을 분석합니다.`,
		level: '중급',
		tags: ['analysis'],
		cells: cells('dartlab-analysis-axes', [
			['markdown', `# 4. 22축 분석

\`c.analysis()\` 를 인자 없이 부르면 22축 카탈로그가 나옵니다. \`c.analysis(그룹, 축)\` 로 축을 지정하면
시계열·전환점·데이터 기준시점이 담긴 dict 를 돌려줍니다.

배우는 것: financial 그룹의 수익성·성장성·안정성.

참고: 축 결과는 표가 아니라 dict(텍스트)로 출력됩니다.

${BROWSER_NOTE}`],
			['code', SETUP],
			['code', `# 인자 없이 호출하면 22축 카탈로그를 표로 돌려준다
c.analysis()`],
			['code', `# financial 그룹의 수익성 축. history / turningPoints / dataAsOf 등이 담긴 dict
c.analysis("financial", "수익성")`],
			['code', `# 성장성 축
c.analysis("financial", "성장성")`],
			['code', `# 안정성 축
c.analysis("financial", "안정성")`]
		])
	},

	// ── 심화 ──────────────────────────────────────────────────────────────
	{
		id: 'dartlab-is-margin',
		title: `5. 심화: 손익계산서로 마진 구조 직접 계산`,
		description: `select 로 뽑은 IS 를 polars 로 굴려 연도별 영업이익률을 손으로 계산합니다.`,
		level: '심화',
		tags: ['select', 'polars', 'IS'],
		cells: cells('dartlab-is-margin', [
			['markdown', `# 5. 심화: 손익계산서로 마진 구조 직접 계산

지금까지는 dartlab 이 준 결과를 그대로 봤습니다. 이제 그 결과를 **직접 굴려 봅니다.**

\`c.select(...)\` 가 돌려주는 \`SelectResult\` 는 \`.df\` 로 polars DataFrame 을 내줍니다.
행은 계정, 열은 기간인 넓은 표라서, 원하는 행을 골라 나눠 주면 비율이 나옵니다.

배우는 것: \`.df\` 로 내려가기, 연도 컬럼 고르기, 연도별 영업이익률 계산, 매출총이익률까지 확장.

${BROWSER_NOTE}`],
			['code', SETUP],
			['code', `import polars as pl

# 연간 매출액·영업이익. 행 = 계정, 열 = 연도인 넓은 표
res = c.select("IS", ["매출액", "영업이익"], freq="Y")
df = res.df
df`],
			['code', `# 연도 컬럼만 고른다 (2026Q1 같은 분기 컬럼과 snakeId/항목 을 제외)
years = [col for col in df.columns if col.isdigit()]
years`],
			['code', `# 영업이익률 = 영업이익 / 매출액 x 100
sales = df.filter(pl.col("snakeId") == "sales").select(years).row(0)
op = df.filter(pl.col("snakeId") == "operating_profit").select(years).row(0)

margin = {y: round(o / s * 100, 1) for y, s, o in zip(years, sales, op) if s and o is not None}
margin`],
			['code', `# 매출총이익률까지. 계정 이름만 바꾸면 같은 틀이 그대로 돈다
res2 = c.select("IS", ["매출액", "매출총이익"], freq="Y")
d2 = res2.df
ys = [col for col in d2.columns if col.isdigit()]
rev = d2.filter(pl.col("snakeId") == "sales").select(ys).row(0)
gp = d2.filter(pl.col("snakeId") == "gross_profit").select(ys).row(0)
{y: round(g / r * 100, 1) for y, r, g in zip(ys, rev, gp) if r and g is not None}`]
		])
	},
	{
		id: 'dartlab-scan-cross',
		title: `6. 심화: scan 으로 전종목 한 번에 비교`,
		description: `한 회사가 아니라 상장사 전체를 한 표로. ROE·성장성·수익성 횡단 스캔.`,
		level: '심화',
		tags: ['scan', 'cross-section'],
		cells: cells('dartlab-scan-cross', [
			['markdown', `# 6. 심화: scan 으로 전종목 한 번에 비교

\`Company\` 가 회사 **한 개**를 세로로 파고든다면, \`scan\` 은 상장사 **전체**를 가로로 자릅니다.
호출 형식은 \`dartlab.scan("축")\` 또는 \`dartlab.scan("축", "대상")\` 입니다.

첫 호출은 전종목 경량 재무 데이터(약 20MB)를 한 번 내려받습니다. 그다음부터는 빠릅니다.

배우는 것: ROE 랭킹, 성장성 스캔, 수익성 스캔, 계정 하나로 전종목 시계열 뽑기.

브라우저에서 도는 축: growth · profitability · liquidity · cashflow · ratio · account · debt.
(직원수 프리빌드나 KRX 목록이 필요한 workforce · screen 축은 로컬 설치본에서 쓰세요.)

${BROWSER_NOTE}`],
			['code', SETUP],
			['code', `# 전종목 ROE. 첫 호출은 경량 재무 데이터(약 20MB)를 내려받아 수 초 걸린다
roe = dartlab.scan("ratio", "roe")
roe.shape`],
			['code', `# 전종목 성장성 (매출/영업이익/순이익 CAGR + 성장 패턴)
growth = dartlab.scan("growth")
growth.head(10)`],
			['code', `# 전종목 수익성 (영업이익률·순이익률·ROE·ROA + 등급)
prof = dartlab.scan("profitability")
prof.head(10)`],
			['code', `import polars as pl

# 결과 컬럼은 한글이다. 영업이익률 상위 10 곳
prof.columns`],
			['code', `prof.filter(pl.col("영업이익률").is_not_null()).sort("영업이익률", descending=True).head(10)`],
			['code', `# 계정 하나로 전종목 시계열. 매출액 기준 상위를 본다
dartlab.scan("account", "매출액").head(10)`]
		])
	},
	{
		id: 'dartlab-credit-dcr',
		title: `7. 심화: 독립 신용등급 dCR 과 7축`,
		description: `c.credit 로 dartlab 자체 신용등급(dCR)과 7축 위험 점수를 계산합니다.`,
		level: '심화',
		tags: ['credit'],
		cells: cells('dartlab-credit-dcr', [
			['markdown', `# 7. 심화: 독립 신용등급 dCR

\`c.credit()\` 은 dartlab 자체 신용평가 엔진이 산출하는 dCR 등급(AAA~D)과 종합 점수를 돌려줍니다.
7축(채무상환·자본구조·유동성·현금흐름·사업안정성·재무신뢰성·공시리스크)을 개별로 부르거나
\`detail=True\` 로 시계열까지 한 번에 볼 수 있습니다.

배우는 것: 종합 등급, 채무상환·유동성 축, 7축 상세.

${BROWSER_NOTE}`],
			['code', SETUP],
			['code', `# 종합 신용등급(dCR). grade / score / healthScore / axes / outlook
c.credit()`],
			['code', `# 채무상환 축만
c.credit("채무상환")`],
			['code', `# 유동성 축만
c.credit("유동성")`],
			['code', `# detail=True 로 7축 상세 + 지표 시계열
c.credit(detail=True)`]
		])
	},
	{
		id: 'dartlab-story-section',
		title: `8. 심화: 재무 서사를 읽는 글로`,
		description: `c.story 로 여러 분석 결과를 사람이 읽는 서사 블록으로 조립합니다.`,
		level: '심화',
		tags: ['story'],
		cells: cells('dartlab-story-section', [
			['markdown', `# 8. 심화: 재무 서사 블록

\`c.story(섹션)\` 은 여러 분석 엔진의 결과를 사람이 읽는 서사 블록으로 조립한 보고서(Story)를 돌려줍니다.
Story 객체는 표와 문장이 섞인 형태로 렌더되고, \`.toMarkdown()\` 으로 원문을 꺼낼 수 있습니다.

배우는 것: 수익성 섹션 렌더, 같은 결과의 마크다운 원문.

참고: 조립 과정 때문에 수십 초 걸릴 수 있습니다.

${BROWSER_NOTE}`],
			['code', SETUP],
			['code', `# 수익성 섹션의 서사 블록. 조립에 수십 초 걸릴 수 있다
st = c.story("수익성")
st`],
			['code', `# 같은 결과를 마크다운 원문으로 (앞 1200자)
print(st.toMarkdown()[:1200])`]
		])
	}
];

/** 커리큘럼 표시 순서. 허브 갤러리 섹션 헤더가 이 순서를 따른다. */
export const EXAMPLE_LEVELS: ExampleLevel[] = ['기초', '중급', '심화'];

export function getExample(id: string): NotebookExample | undefined {
	return EXAMPLES.find((e) => e.id === id);
}

export function examplesByLevel(level: ExampleLevel): NotebookExample[] {
	return EXAMPLES.filter((e) => e.level === level);
}
