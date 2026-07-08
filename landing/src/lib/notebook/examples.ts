// 예제 노트북 SSOT. 허브 갤러리 + (추후) 블로그 임베드가 이 한 레지스트리를 공유한다.
// v1 은 범용 커널(numpy/pandas/matplotlib)에서 즉시 도는 일반 파이썬 예제.
// dartlab 실데이터 예제는 wheel 로드 검증 후 추가(후속).
import type { Cell } from './stores/notebookStore';

export interface NotebookExample {
	id: string;
	title: string;
	description: string;
	tags: string[];
	cells: Cell[];
}

function mk(exampleId: string, defs: [Cell['type'], string][]): Cell[] {
	return defs.map(([type, content], i) => ({ id: `${exampleId}-${i}`, type, content }));
}

export const EXAMPLES: NotebookExample[] = [
	{
		id: 'pandas-basics',
		title: 'pandas 시작하기',
		description: 'DataFrame 만들고 정렬·집계·요약하기. 표 출력이 그대로 렌더됩니다.',
		tags: ['pandas', '기초'],
		cells: mk('pandas-basics', [
			['markdown', '# pandas 시작하기\n\nDataFrame 을 만들고 정렬·집계·요약해 봅니다. 마지막 표현식이 표로 렌더됩니다.'],
			[
				'code',
				'import pandas as pd\n\ndf = pd.DataFrame(\n    {\n        "city": ["Seoul", "Busan", "Incheon", "Daegu", "Daejeon"],\n        "pop_k": [9411, 3324, 2954, 2380, 1454],\n        "area_km2": [605, 770, 1063, 884, 539],\n    }\n)\ndf'
			],
			['code', '# 인구밀도 파생 + 내림차순 정렬\ndf["density"] = (df["pop_k"] * 1000 / df["area_km2"]).round(0)\ndf.sort_values("density", ascending=False)'],
			['code', '# 요약 통계\ndf[["pop_k", "area_km2", "density"]].describe()']
		])
	},
	{
		id: 'matplotlib-gallery',
		title: 'matplotlib 시각화',
		description: '선 그래프와 막대 그래프. 그림이 셀 안에 이미지로 렌더됩니다.',
		tags: ['matplotlib', '시각화'],
		cells: mk('matplotlib-gallery', [
			['markdown', '# matplotlib 시각화\n\n선 그래프와 막대 그래프를 그립니다. 브라우저 안에서 실행되고 그림이 바로 뜹니다.'],
			[
				'code',
				'import numpy as np\nimport matplotlib.pyplot as plt\n\nx = np.linspace(0, 4 * np.pi, 300)\nplt.figure(figsize=(6, 3.2))\nplt.plot(x, np.sin(x), label="sin")\nplt.plot(x, np.cos(x), label="cos")\nplt.legend()\nplt.title("sin & cos")\nplt.grid(True, alpha=0.3)'
			],
			[
				'code',
				'labels = ["A", "B", "C", "D", "E"]\nvalues = [23, 45, 56, 12, 39]\nplt.figure(figsize=(6, 3.2))\nplt.bar(labels, values)\nplt.title("bar chart")'
			]
		])
	},
	{
		id: 'numpy-arrays',
		title: 'numpy 배열과 통계',
		description: '배열 생성·형태 변환·축별 집계. 순수 파이썬 계산.',
		tags: ['numpy', '기초'],
		cells: mk('numpy-arrays', [
			['markdown', '# numpy 배열과 통계\n\n배열을 만들고 형태를 바꾸고 축별로 집계합니다.'],
			['code', 'import numpy as np\n\na = np.arange(12).reshape(3, 4)\na'],
			['code', '# 축별 평균\n{"col_mean": a.mean(axis=0).tolist(), "row_mean": a.mean(axis=1).tolist()}'],
			['code', '# 난수 + 기술통계\nrng = np.random.default_rng(0)\nx = rng.normal(loc=10, scale=2, size=1000)\n{"mean": round(float(x.mean()), 3), "std": round(float(x.std()), 3), "min": round(float(x.min()), 3), "max": round(float(x.max()), 3)}']
		])
	}
];

export function getExample(id: string): NotebookExample | undefined {
	return EXAMPLES.find((e) => e.id === id);
}
