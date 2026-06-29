// 다운로드 변환 유틸 — surface 중립 배럴(컴포넌트·무거운 deps 0). 여러 surface(terminal·viewer·landing)가
// 공유하는 순수 작성기(xlsx OOXML·BOM CSV·Blob 다운로드)를 한 진입점으로. viewer/scan 무거운 배럴(klinecharts·
// codemirror·web-llm 등 끌어옴)을 우회해 다운로드만 쓰는 곳이 가벼운 번들을 받게 한다.
export { buildWorkbook, objectsToWorkbook, sheetName, ZipStore, type SheetInput, type GridCell, type ObjectSheet } from './viewer/lib/xlsx';
export { downloadBlob, downloadText } from './viewer/lib/dataExport';
export { toCsv, downloadCsv } from './scan/csvExport';
