"""도구 라우터 학습 파이프라인 — APIGen → 검증 → SFT → GGUF.

사용법:
    # 전체 파이프라인
    uv run python -X utf8 scripts/trainRouter.py

    # 개별 단계
    uv run python -X utf8 scripts/trainRouter.py --step generate   # 질문+코드 생성
    uv run python -X utf8 scripts/trainRouter.py --step verify     # sandbox 검증
    uv run python -X utf8 scripts/trainRouter.py --step dataset    # SFT 데이터셋
    uv run python -X utf8 scripts/trainRouter.py --step train      # QLoRA 학습
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

# 데이터 디렉토리
DATA_DIR = Path.home() / ".dartlab" / "selfai" / "training_data"
MODEL_DIR = Path.home() / ".dartlab" / "models" / "router"


def step_generate():
    """Step 1+2: 질문 생성 + 코드 생성."""
    from dartlab.ai.selfai.apigen.code_gen import generateBatch
    from dartlab.ai.selfai.apigen.question_gen import generateQuestions

    log.info("=== Step 1: 질문 생성 ===")
    questions = generateQuestions(count=500)
    log.info("생성된 질문: %d개", len(questions))

    log.info("=== Step 2: 코드 생성 ===")
    coded = generateBatch(questions, output_path=DATA_DIR / "coded.jsonl")
    log.info("코드 생성 완료: %d/%d", len(coded), len(questions))

    return coded


def step_verify():
    """Step 3: sandbox 검증."""
    from dartlab.ai.selfai.apigen.verifier import verifyBatch

    coded_path = DATA_DIR / "coded.jsonl"
    if not coded_path.exists():
        log.error("coded.jsonl 없음. --step generate 먼저 실행")
        return None

    items = []
    with open(coded_path, encoding="utf-8") as f:
        for line in f:
            items.append(json.loads(line))

    log.info("=== Step 3: sandbox 검증 (%d개) ===", len(items))
    # ⚠ 메모리 주의: 종목별로 순차 실행
    result = verifyBatch(
        items,
        DATA_DIR / "verified",
        timeout=30,
        max_items=None,
    )
    log.info(
        "검증 완료: verified=%d, failed=%d (통과율 %.0f%%)",
        result["verified"],
        result["failed"],
        result["verified"] / max(result["total"], 1) * 100,
    )
    return result


def step_dataset():
    """Step 4: SFT 데이터셋 구축."""
    from dartlab.ai.selfai.apigen.dataset import buildSftDataset, splitDataset

    verified_path = DATA_DIR / "verified" / "verified.jsonl"
    if not verified_path.exists():
        log.error("verified.jsonl 없음. --step verify 먼저 실행")
        return None

    log.info("=== Step 4: SFT 데이터셋 구축 ===")
    count = buildSftDataset(verified_path, DATA_DIR / "sft" / "all.jsonl")
    log.info("SFT 변환 완료: %d개", count)

    splits = splitDataset(DATA_DIR / "sft" / "all.jsonl", DATA_DIR / "sft")
    log.info("분리: train=%d, val=%d, test=%d", splits["train"], splits["val"], splits["test"])

    return splits


def step_train():
    """Step 5: Unsloth QLoRA 학습 + GGUF 변환."""
    train_path = DATA_DIR / "sft" / "train.jsonl"
    if not train_path.exists():
        log.error("train.jsonl 없음. --step dataset 먼저 실행")
        return

    try:
        import torch

        if not torch.cuda.is_available():
            log.error("CUDA 사용 불가. GPU torch를 설치하세요:")
            log.error("  pip install torch --index-url https://download.pytorch.org/whl/cu126")
            return
        log.info("GPU: %s (%dMB)", torch.cuda.get_device_name(0), torch.cuda.get_device_properties(0).total_memory // 1024**2)
    except ImportError:
        log.error("torch 미설치")
        return

    try:
        from unsloth import FastLanguageModel
    except ImportError:
        log.error("unsloth 미설치. pip install unsloth")
        return

    log.info("=== Step 5: QLoRA 학습 ===")

    # 학습 데이터 로드
    from datasets import load_dataset

    dataset = load_dataset("json", data_files=str(train_path), split="train")
    log.info("학습 데이터: %d개", len(dataset))

    # 모델 로드
    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name="unsloth/Qwen3-1.7B",
        max_seq_length=1024,
        load_in_4bit=True,
    )

    # LoRA 설정
    model = FastLanguageModel.get_peft_model(
        model,
        r=32,
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
        lora_alpha=64,
        lora_dropout=0,
        use_gradient_checkpointing="unsloth",
    )

    # 학습 데이터 포맷팅
    def _format(example):
        messages = example["messages"]
        text = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=False)
        return {"text": text}

    dataset = dataset.map(_format)

    # Trainer
    from trl import SFTTrainer
    from transformers import TrainingArguments

    trainer = SFTTrainer(
        model=model,
        tokenizer=tokenizer,
        train_dataset=dataset,
        dataset_text_field="text",
        max_seq_length=1024,
        args=TrainingArguments(
            output_dir=str(DATA_DIR / "checkpoints"),
            per_device_train_batch_size=1,
            gradient_accumulation_steps=8,
            num_train_epochs=5,
            learning_rate=2e-4,
            warmup_steps=5,
            bf16=True,
            logging_steps=5,
            save_strategy="no",
            report_to="none",
        ),
    )

    log.info("학습 시작...")
    trainer.train()
    log.info("학습 완료!")

    # LoRA 어댑터만 저장 (GGUF 변환 없이)
    LORA_DIR = MODEL_DIR / "lora"
    LORA_DIR.mkdir(parents=True, exist_ok=True)
    model.save_pretrained(str(LORA_DIR))
    tokenizer.save_pretrained(str(LORA_DIR))
    log.info("LoRA 어댑터 저장 완료: %s", LORA_DIR)

    # 머지된 16bit 모델도 저장 (나중에 GGUF 변환 가능)
    MERGED_DIR = MODEL_DIR / "merged"
    MERGED_DIR.mkdir(parents=True, exist_ok=True)
    model.save_pretrained_merged(str(MERGED_DIR), tokenizer)
    log.info("머지 모델 저장 완료: %s", MERGED_DIR)
    log.info("GGUF 변환은 별도로: python -m llama_cpp.convert %s --outtype q4_k_m", MERGED_DIR)


def main():
    parser = argparse.ArgumentParser(description="dartlab 도구 라우터 학습 파이프라인")
    parser.add_argument("--step", choices=["generate", "verify", "dataset", "train", "all"], default="all")
    args = parser.parse_args()

    if args.step in ("generate", "all"):
        step_generate()

    if args.step in ("verify", "all"):
        step_verify()

    if args.step in ("dataset", "all"):
        step_dataset()

    if args.step in ("train", "all"):
        step_train()


if __name__ == "__main__":
    main()
