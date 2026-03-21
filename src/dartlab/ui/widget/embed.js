/**
 * DartLab Embed — 엔트리포인트.
 *
 * 사용:
 *   <script src="https://host/embed.js"
 *     data-code="005930"
 *     data-type="snapshot"
 *     data-theme="auto"
 *     data-token="readonly_token">
 *   </script>
 */

import Snapshot from "./Snapshot.svelte";
import { WIDGET_CSS } from "./theme.js";

/** 위젯 타입 → Svelte 컴포넌트 매핑 */
const WIDGET_TYPES = {
  snapshot: Snapshot,
};

/**
 * script 태그 하나를 위젯으로 마운트한다.
 */
function mount(scriptEl) {
  if (scriptEl.__dartlab_mounted) return;
  scriptEl.__dartlab_mounted = true;

  const code = scriptEl.dataset.code;
  if (!code) return;

  const type = scriptEl.dataset.type || "snapshot";
  const theme = scriptEl.dataset.theme || "auto";
  const token = scriptEl.dataset.token || "";
  const baseUrl = new URL(scriptEl.src).origin;

  const Component = WIDGET_TYPES[type];
  if (!Component) {
    console.warn(`[DartLab] 알 수 없는 위젯 타입: ${type}`);
    return;
  }

  // Shadow DOM 컨테이너 생성
  const container = document.createElement("div");
  container.className = "dartlab-embed";
  scriptEl.after(container);

  const shadow = container.attachShadow({ mode: "open" });

  // 테마 속성 전파 (CSS :host 선택자용)
  if (theme !== "auto") {
    container.setAttribute("data-theme", theme);
    // Shadow host에도 설정
    shadow.host.setAttribute("data-theme", theme);
  }

  // 스타일 주입
  const style = document.createElement("style");
  style.textContent = WIDGET_CSS;
  shadow.appendChild(style);

  // Svelte 컴포넌트 마운트
  const target = document.createElement("div");
  shadow.appendChild(target);

  new Component({
    target,
    props: { baseUrl, code, token, theme },
  });
}

/**
 * 페이지의 모든 dartlab embed script 태그를 처리한다.
 */
function processAllTags() {
  const scripts = document.querySelectorAll(
    'script[src*="embed.js"][data-code]'
  );
  scripts.forEach(mount);
}

// --- 초기화 ---

// 중복 로드 방지
if (!window.__DARTLAB_EMBED_LOADED) {
  window.__DARTLAB_EMBED_LOADED = true;

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", processAllTags);
  } else {
    processAllTags();
  }
} else {
  // 이미 로드됨 — 새로 추가된 태그만 처리
  processAllTags();
}
