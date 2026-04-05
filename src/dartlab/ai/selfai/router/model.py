"""로컬 소형 모델 추론 — ExLlamaV2 또는 llama-cpp-python 기반.

Phase 3에서 Qwen3-1.7B를 도구 라우터로 사용.
모델이 없으면 ImportError → engine.py에서 rule fallback.

지원 백엔드 (우선순위):
1. ExLlamaV2 — 최고 속도 (Ollama 대비 30~52% 빠름)
2. llama-cpp-python — 범용 (GGUF 지원)
3. Ollama API — 이미 설치된 경우 fallback
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

log = logging.getLogger(__name__)

_MODEL_DIR = Path.home() / ".dartlab" / "models"
_ROUTER_MODEL = _MODEL_DIR / "router"  # router/ 디렉토리에 모델 파일

# 싱글톤 — 모델 1회 로드
_engine: _InferenceEngine | None = None


class _InferenceEngine:
    """추론 엔진 추상화."""

    def generate(self, prompt: str, max_tokens: int = 256) -> str:
        raise NotImplementedError


class _ExLlamaEngine(_InferenceEngine):
    """ExLlamaV2 기반 추론."""

    def __init__(self, model_dir: Path):
        from exllamav2 import ExLlamaV2, ExLlamaV2Cache, ExLlamaV2Config, ExLlamaV2Tokenizer
        from exllamav2.generator import ExLlamaV2DynamicGenerator

        config = ExLlamaV2Config(str(model_dir))
        config.prepare()

        self._model = ExLlamaV2(config)
        self._model.load()

        self._cache = ExLlamaV2Cache(self._model, max_seq_len=4096)
        self._tokenizer = ExLlamaV2Tokenizer(config)
        self._generator = ExLlamaV2DynamicGenerator(
            model=self._model,
            cache=self._cache,
            tokenizer=self._tokenizer,
        )
        log.info("ExLlamaV2 라우터 모델 로드 완료: %s", model_dir)

    def generate(self, prompt: str, max_tokens: int = 256) -> str:
        return self._generator.generate(
            prompt=prompt,
            max_new_tokens=max_tokens,
            temperature=0.1,
            top_p=0.9,
        )


class _LlamaCppEngine(_InferenceEngine):
    """llama-cpp-python 기반 추론."""

    def __init__(self, model_path: Path):
        from llama_cpp import Llama

        self._llm = Llama(
            model_path=str(model_path),
            n_ctx=4096,
            n_gpu_layers=-1,  # 모든 레이어 GPU
            verbose=False,
        )
        log.info("llama.cpp 라우터 모델 로드 완료: %s", model_path)

    def generate(self, prompt: str, max_tokens: int = 256) -> str:
        result = self._llm(prompt, max_tokens=max_tokens, temperature=0.1, stop=["}"])
        text = result["choices"][0]["text"]
        return text + "}"  # stop token 복원


class _OllamaEngine(_InferenceEngine):
    """Ollama API fallback."""

    def __init__(self, model: str = "qwen3:1.7b"):
        self._model = model
        log.info("Ollama 라우터 모델: %s", model)

    def generate(self, prompt: str, max_tokens: int = 256) -> str:
        import urllib.request

        # chat API + think:false (qwen3 thinking mode 비활성화)
        payload = json.dumps(
            {
                "model": self._model,
                "messages": [
                    {"role": "system", "content": "JSON으로만 응답하라. 설명 없이 JSON만."},
                    {"role": "user", "content": prompt},
                ],
                "stream": False,
                "think": False,
                "options": {"temperature": 0.1, "num_predict": max_tokens},
            }
        ).encode()

        req = urllib.request.Request(
            "http://localhost:11434/api/chat",
            data=payload,
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read())
            return data.get("message", {}).get("content", "")


class _TransformersEngine(_InferenceEngine):
    """HuggingFace Transformers 기반 추론 — 학습된 safetensors 직접 로드."""

    def __init__(self, model_dir: Path):
        from transformers import AutoModelForCausalLM, AutoTokenizer

        self._tokenizer = AutoTokenizer.from_pretrained(str(model_dir))
        self._model = AutoModelForCausalLM.from_pretrained(
            str(model_dir),
            torch_dtype="auto",
            device_map="auto",
        )
        self._model.eval()
        log.info("Transformers 라우터 모델 로드 완료: %s", model_dir)

    def generate(self, prompt: str, max_tokens: int = 256) -> str:
        import torch

        inputs = self._tokenizer(prompt, return_tensors="pt").to(self._model.device)
        with torch.no_grad():
            outputs = self._model.generate(
                **inputs,
                max_new_tokens=max_tokens,
                temperature=0.1,
                do_sample=True,
                pad_token_id=self._tokenizer.pad_token_id or self._tokenizer.eos_token_id,
            )
        new_tokens = outputs[0][inputs["input_ids"].shape[1] :]
        return self._tokenizer.decode(new_tokens, skip_special_tokens=True)


def _loadEngine() -> _InferenceEngine:
    """최적의 추론 엔진을 자동 감지하여 로드."""
    global _engine
    if _engine is not None:
        return _engine

    # 0. Transformers — 학습된 safetensors 모델 있으면 (Phase 3)
    if _ROUTER_MODEL.exists() and (_ROUTER_MODEL / "config.json").exists() and (_ROUTER_MODEL / "model.safetensors").exists():
        try:
            _engine = _TransformersEngine(_ROUTER_MODEL)
            return _engine
        except ImportError:
            log.debug("transformers 미설치")
        except (OSError, RuntimeError) as e:
            log.warning("Transformers 로드 실패: %s", e)

    # 1. ExLlamaV2 — EXL2 모델 있으면
    exl_dir = _ROUTER_MODEL
    if exl_dir.exists() and (exl_dir / "config.json").exists():
        try:
            _engine = _ExLlamaEngine(exl_dir)
            return _engine
        except ImportError:
            log.debug("exllamav2 미설치")
        except (OSError, RuntimeError) as e:
            log.warning("ExLlamaV2 로드 실패: %s", e)

    # 2. llama-cpp-python — GGUF 파일 있으면
    gguf_files = list(_ROUTER_MODEL.glob("*.gguf")) if _ROUTER_MODEL.exists() else []
    if gguf_files:
        try:
            _engine = _LlamaCppEngine(gguf_files[0])
            return _engine
        except ImportError:
            log.debug("llama-cpp-python 미설치")
        except (OSError, RuntimeError) as e:
            log.warning("llama.cpp 로드 실패: %s", e)

    # 3. Ollama fallback — 서버 실행 중이면
    try:
        import urllib.request

        urllib.request.urlopen("http://localhost:11434/api/tags", timeout=2)
        _engine = _OllamaEngine("qwen3:1.7b")
        return _engine
    except (OSError, ImportError):
        pass

    raise ImportError("로컬 라우터 모델 없음. ~/.dartlab/models/router/에 모델을 설치하거나 Ollama를 실행하세요.")


def infer_route(question: str, stock_code: str | None = None) -> "RouteResult | None":
    """로컬 모델로 라우팅 추론."""
    from dartlab.ai.selfai.router.engine import RouteResult
    from dartlab.ai.selfai.router.prompt import ROUTER_EXAMPLES, ROUTER_SYSTEM_PROMPT

    engine = _loadEngine()

    # Few-shot 프롬프트 구성
    parts = [ROUTER_SYSTEM_PROMPT, "\n\n## 예시\n"]
    for ex in ROUTER_EXAMPLES[:3]:
        parts.append(f"Q: {ex['q']}\nA: {ex['a']}\n\n")
    parts.append(f"Q: {question}\nA: ")

    prompt = "".join(parts)
    raw = engine.generate(prompt, max_tokens=256)

    # JSON 파싱 — 응답에서 첫 번째 유효한 JSON 객체 추출
    import re as _re

    data = None
    # 모든 {...} 후보를 찾아서 파싱 시도
    for m in _re.finditer(r"\{[^{}]*\}", raw):
        try:
            candidate = json.loads(m.group())
            if "tool" in candidate:
                data = candidate
                break
        except json.JSONDecodeError:
            continue

    if data is None:
        # 중첩 JSON 시도
        try:
            start = raw.index("{")
            depth = 0
            for i, ch in enumerate(raw[start:], start):
                if ch == "{":
                    depth += 1
                elif ch == "}":
                    depth -= 1
                    if depth == 0:
                        candidate = json.loads(raw[start : i + 1])
                        if "tool" in candidate:
                            data = candidate
                        break
        except (ValueError, json.JSONDecodeError):
            pass

    if data is None:
        log.warning("라우터 JSON 파싱 실패: %s", raw[:200])
        return None

    tool = data.get("tool", "")
    if not tool:
        return None

    return RouteResult(
        tool=tool,
        group=data.get("group"),
        axis=data.get("axis"),
        code=data.get("code", ""),
        needs_company=data.get("needs_company", True),
        confidence=0.85,  # 로컬 모델 기본 신뢰도
        source="local",
    )
