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

// 공유 부트스트랩: pyodide 에 dartlab wheel 설치 + 삼성전자 데이터 prefetch + Company 생성 (약 20초, 최초 1회).
const SETUP = `# dartlab 부트스트랩 (약 20초). 커널은 범용이라 예제가 스스로 dartlab 을 올린다.
import os, io
os.environ["DARTLAB_DATA_DIR"] = "/data"          # pyodide 로컬 데이터 경로를 /data 로 통일
os.environ["DARTLAB_NO_HF_DOWNLOAD"] = "1"         # 오프라인: 자동 HF 다운로드 차단
import pyodide_js, micropip, zipfile, site
from pyodide.http import pyfetch
await pyodide_js.loadPackage(["polars","pyarrow","micropip","beautifulsoup4","lxml","httpx","pydantic","rich","sqlite3","numpy"])
await micropip.install(["diff-match-patch","openpyxl"])
# dartlab wheel 을 HF 에서 받아 site-packages 에 푼다
_wheel = "https://huggingface.co/datasets/eddmpython/dartlab-data/resolve/main/pyodide/dartlab-0.10.7-py3-none-any.whl"
_resp = await pyfetch(_wheel)
zipfile.ZipFile(io.BytesIO(await _resp.bytes())).extractall(site.getsitepackages()[0])
import dartlab
await dartlab.prefetch("005930", categories=["panel","finance","report"])   # 삼성전자 데이터 미리 받기
c = dartlab.Company("005930")`;

function cells(exampleId: string, defs: [Cell['type'], string][]): Cell[] {
	return defs.map(([type, content], i) => ({ id: `${exampleId}-${i}`, type, content }));
}

export const EXAMPLES: NotebookExample[] = [
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
	{
		id: 'dartlab-audit-redflags',
		title: `audit: 감사의견·계속기업 red flag 점검`,
		description: `c.audit 로 감사의견·감사인 변경·계속기업 불확실성 red flag 를 점검합니다.`,
		tags: ['company', 'audit'],
		cells: cells('dartlab-audit-redflags', [
			['markdown', `# audit: 감사 red flag 점검

\`c.audit()\` 은 감사의견·감사인 변경·계속기업 불확실성 같은 회계 위험 신호(Anomaly)를 리스트로 돌려줍니다. 투자 판단의 안전장치로, 이상이 잡히면 목록에 담기고 없으면 빈 리스트입니다.

배우는 것: red flag 목록, 사람이 읽는 문장으로 변환.

참고: 삼성전자 같은 우량 기업은 목록이 비어 있을 수 있습니다(정상). 아래 setup 셀을 먼저 실행하세요 (약 20초).`],
			['code', SETUP],
			['code', `# 감사 red flag 목록 (list[Anomaly]): 감사의견 / 감사인 변경 / 계속기업 등
flags = c.audit()
flags`],
			['code', `# 사람이 읽을 문장으로. 비어 있으면 감사 이슈 없음(우량)
[str(f) for f in flags] or "감사 red flag 없음 (우량)"`],
		])
	},
];

export function getExample(id: string): NotebookExample | undefined {
	return EXAMPLES.find((e) => e.id === id);
}
