// dartlab notebook - 셀/출력 데이터 모델.
// 출력은 파이썬 실행기(_dl_format_result)가 발급한 구조화 payload 를 그대로 담는다.

export type NbOutput =
	| { type: 'none' }
	| {
			type: 'dataframe';
			columns: string[];
			dtypes: string[];
			rows: unknown[][];
			nrows: number;
			ncols: number;
			truncated: boolean;
	  }
	| { type: 'html'; data: string }
	| { type: 'repr'; data: string }
	| { type: 'error'; data: string };

export type CellRun = { ok: boolean; stdout: string; output: NbOutput };

export interface NotebookCell {
	id: string;
	code: string;
	running: boolean;
	stdout: string;
	output: NbOutput | null;
	ran: boolean;
}
