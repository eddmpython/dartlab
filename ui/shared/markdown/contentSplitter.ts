/**
 * 스트리밍 콘텐츠 분리 -- 완료된 부분과 진행 중인 부분을 나눈다.
 * 테이블이나 코드 펜스가 아직 닫히지 않았으면 draft로 분류해서
 * 깨진 마크다운 렌더링을 방지한다.
 */

const TABLE_LINE_RE = /^\s*\|.+\|\s*$/;
const CODE_FENCE_RE = /^```[\w-]*$/;

type DraftType = "none" | "text" | "table" | "code";

export interface SplitResult {
  committed: string;
  draft: string;
  draftType: DraftType;
}

function computeSplit(text: string) {
  const lines = text.split("\n");
  let safeIndex = lines.length;

  if (!text.endsWith("\n")) safeIndex = Math.min(safeIndex, lines.length - 1);

  let codeFenceCount = 0;
  let lastFenceLine = -1;
  for (let i = 0; i < lines.length; i++) {
    if (CODE_FENCE_RE.test(lines[i].trim())) {
      codeFenceCount += 1;
      lastFenceLine = i;
    }
  }
  if (codeFenceCount % 2 === 1 && lastFenceLine >= 0) {
    safeIndex = Math.min(safeIndex, lastFenceLine);
  }

  let trailingTableStart = -1;
  for (let i = lines.length - 1; i >= 0; i--) {
    const line = lines[i];
    if (!line.trim()) break;
    if (TABLE_LINE_RE.test(line)) trailingTableStart = i;
    else {
      trailingTableStart = -1;
      break;
    }
  }
  if (trailingTableStart >= 0) {
    safeIndex = Math.min(safeIndex, trailingTableStart);
  }

  let draftType: DraftType = "text";
  if (trailingTableStart >= 0 && trailingTableStart <= safeIndex) draftType = "table";
  else if (codeFenceCount % 2 === 1) draftType = "code";

  return { lines, safeIndex, draftType };
}

export function splitStreamingContent(text: string, loading: boolean): SplitResult {
  if (!text) return { committed: "", draft: "", draftType: "none" };
  if (!loading) return { committed: text, draft: "", draftType: "none" };

  const { lines, safeIndex, draftType } = computeSplit(text);

  if (safeIndex <= 0) {
    return { committed: "", draft: text, draftType };
  }

  const committed = lines.slice(0, safeIndex).join("\n");
  const draft = lines.slice(safeIndex).join("\n");
  return { committed, draft, draftType: draft ? draftType : "none" };
}

export interface StreamSplitter {
  split(text: string, loading: boolean): SplitResult;
  reset(): void;
}

/**
 * Monotonic 스트림 분리기 -- committed 영역이 줄어드는 것을 방지.
 */
export function createStreamSplitter(): StreamSplitter {
  let maxSafeIndex = 0;
  let prevLineCount = 0;
  let fenceCount = 0;
  let lastFenceLine = -1;
  let prevLastLineFence = false;

  return {
    split(text: string, loading: boolean): SplitResult {
      if (!text) return { committed: "", draft: "", draftType: "none" };
      if (!loading) {
        this.reset();
        return { committed: text, draft: "", draftType: "none" };
      }

      const lines = text.split("\n");
      let safeIndex = lines.length;
      if (!text.endsWith("\n")) safeIndex = Math.min(safeIndex, lines.length - 1);

      const scanStart = Math.max(0, prevLineCount - 1);
      if (prevLastLineFence && scanStart < lines.length && scanStart === prevLineCount - 1) {
        fenceCount -= 1;
        if (lastFenceLine === scanStart) lastFenceLine = -1;
      }
      let lastLineFence = false;
      for (let i = scanStart; i < lines.length; i++) {
        if (CODE_FENCE_RE.test(lines[i].trim())) {
          fenceCount += 1;
          lastFenceLine = i;
          if (i === lines.length - 1) lastLineFence = true;
        }
      }
      prevLineCount = lines.length;
      prevLastLineFence = lastLineFence;

      if (fenceCount % 2 === 1 && lastFenceLine >= 0) {
        safeIndex = Math.min(safeIndex, lastFenceLine);
      }

      let trailingTableStart = -1;
      for (let i = lines.length - 1; i >= 0; i--) {
        const line = lines[i];
        if (!line.trim()) break;
        if (TABLE_LINE_RE.test(line)) trailingTableStart = i;
        else {
          trailingTableStart = -1;
          break;
        }
      }
      if (trailingTableStart >= 0) {
        safeIndex = Math.min(safeIndex, trailingTableStart);
      }

      let draftType: DraftType = "text";
      if (trailingTableStart >= 0 && trailingTableStart <= safeIndex) draftType = "table";
      else if (fenceCount % 2 === 1) draftType = "code";

      const effectiveIndex = Math.max(safeIndex, maxSafeIndex);
      const clamped = Math.min(effectiveIndex, lines.length);
      maxSafeIndex = clamped;

      if (clamped <= 0) {
        return { committed: "", draft: text, draftType };
      }

      const committed = lines.slice(0, clamped).join("\n");
      const draft = lines.slice(clamped).join("\n");
      return { committed, draft, draftType: draft ? draftType : "none" };
    },
    reset() {
      maxSafeIndex = 0;
      prevLineCount = 0;
      fenceCount = 0;
      lastFenceLine = -1;
      prevLastLineFence = false;
    },
  };
}
