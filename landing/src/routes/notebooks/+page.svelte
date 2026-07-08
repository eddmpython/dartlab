<script lang="ts">
	import { base } from '$app/paths';
	import NotebookEditor from '$lib/notebook/NotebookEditor.svelte';
	import type { Notebook } from '$lib/notebook/stores/notebookStore';

	// 정적 seed (SSR 안전한 고정 id). 범용 파이썬 예시 셀.
	const seed: Notebook = {
		id: 'notebook-seed',
		title: 'Notebook',
		cells: [
			{ id: 'nb-c1', type: 'code', content: 'print("Hello, notebook")\n21 * 2' },
			{
				id: 'nb-c2',
				type: 'code',
				content: 'import pandas as pd\n\npd.DataFrame({"n": [1, 2, 3, 4], "square": [1, 4, 9, 16]})'
			},
			{
				id: 'nb-c3',
				type: 'code',
				content:
					'import numpy as np\nimport matplotlib.pyplot as plt\n\nx = np.linspace(0, 2 * np.pi, 200)\nplt.plot(x, np.sin(x))\nplt.title("sin(x)")'
			}
		],
		metadata: {
			createdAt: '2026-07-08T00:00:00.000Z',
			updatedAt: '2026-07-08T00:00:00.000Z'
		}
	};
</script>

<svelte:head>
	<title>Notebook · dartlab</title>
	<meta
		name="description"
		content="브라우저에서 바로 실행하는 범용 파이썬 노트북. 설치 없이 numpy·pandas·matplotlib 을 쓰고 표와 그래프를 셀에서 확인하세요."
	/>
</svelte:head>

<NotebookEditor showHome homeHref="{base}/" initialNotebook={seed} />
