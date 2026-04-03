import { mount } from "svelte";
import App from "./App.svelte";

// VSCode webview 환경 감지 → CSS 테마 매핑 활성화
if (window.__vscode || typeof window.acquireVsCodeApi === "function") {
	document.body.setAttribute("data-vscode", "");
}

const app = mount(App, { target: document.getElementById("app") });

export default app;
