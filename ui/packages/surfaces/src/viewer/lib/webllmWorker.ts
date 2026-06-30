// WebLLM 워커 엔트리 · 모델 추론을 메인스레드 밖에서(UI 비차단). webllm.ts 가 CreateWebWorkerMLCEngine 으로 연결.
import { WebWorkerMLCEngineHandler } from '@mlc-ai/web-llm';

const handler = new WebWorkerMLCEngineHandler();
self.onmessage = (msg: MessageEvent) => {
	handler.onmessage(msg);
};
