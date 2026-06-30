// xlsx 작업면 공개 표면 · zero-dep .xlsx 작성기 (table-export Phase 2a CORE).
// 격자기 + 정합 정규화 + STORE ZIP + OOXML emit + 워크북 빌더. UI 배선은 별도 패스(ViewerStudio/ExportDrawer).

export { tableGrid, type GridCell } from './tableGrid';
export { coerceCell, detectUnit } from './tableExtract';
export { crc32, ZipStore } from './zipStore';
export {
	emitOoxmlParts,
	cellRef,
	colLetter,
	xmlEsc,
	STYLE,
	type SheetCell,
	type SheetPart,
	type OoxmlParts
} from './workbook';
export { buildWorkbook, objectsToWorkbook, sheetName, type SheetInput, type ObjectSheet } from './buildWorkbook';
