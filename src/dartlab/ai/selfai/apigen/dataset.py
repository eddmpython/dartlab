"""SFT 데이터셋 구축기 — 검증된 트리플을 학습용 형식으로 변환.

verified.jsonl → SFT 데이터셋 (messages 형식).
Unsloth/TRL/Axolotl에서 바로 사용할 수 있는 형식.
"""

from __future__ import annotations

import json
from pathlib import Path

from dartlab.ai.selfai.router.prompt import ROUTER_SYSTEM_PROMPT


def buildSftDataset(
    verified_path: Path | str,
    output_path: Path | str,
    *,
    system_prompt: str | None = None,
) -> int:
    """검증된 트리플을 SFT 형식으로 변환.

    Args:
        verified_path: verified.jsonl 경로
        output_path: SFT 데이터셋 출력 경로 (train.jsonl)
        system_prompt: 시스템 프롬프트 (None이면 라우터 프롬프트 사용)

    Returns:
        생성된 예시 수
    """
    verified_path = Path(verified_path)
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    sys_prompt = system_prompt or ROUTER_SYSTEM_PROMPT
    count = 0

    with open(verified_path, encoding="utf-8") as vf, \
         open(output_path, "w", encoding="utf-8") as of:

        for line in vf:
            try:
                item = json.loads(line)
            except json.JSONDecodeError:
                continue

            if not item.get("verified"):
                continue

            question = item.get("question", "")
            code = item.get("code", "")
            output = item.get("output", "")
            tool = item.get("tool", "")
            group = item.get("group", "")
            axis = item.get("axis", "")

            # 라우터 학습용: 질문 → JSON 응답
            route_json = json.dumps(
                {
                    "tool": tool,
                    "group": group or None,
                    "axis": axis or None,
                    "code": code,
                    "needs_company": item.get("stock_code") is not None,
                },
                ensure_ascii=False,
            )

            sft_record = {
                "messages": [
                    {"role": "system", "content": sys_prompt},
                    {"role": "user", "content": question},
                    {"role": "assistant", "content": route_json},
                ],
                "metadata": {
                    "tool": tool,
                    "group": group,
                    "axis": axis,
                    "stock_code": item.get("stock_code"),
                    "verified": True,
                },
            }

            of.write(json.dumps(sft_record, ensure_ascii=False) + "\n")
            count += 1

    return count


def splitDataset(
    dataset_path: Path | str,
    output_dir: Path | str,
    *,
    val_ratio: float = 0.1,
    test_ratio: float = 0.1,
    seed: int = 42,
) -> dict[str, int]:
    """데이터셋을 train/val/test로 분리.

    Returns:
        {"train": N, "val": M, "test": K}
    """
    import random

    dataset_path = Path(dataset_path)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    with open(dataset_path, encoding="utf-8") as f:
        lines = f.readlines()

    rng = random.Random(seed)
    rng.shuffle(lines)

    n = len(lines)
    n_test = int(n * test_ratio)
    n_val = int(n * val_ratio)

    test_lines = lines[:n_test]
    val_lines = lines[n_test : n_test + n_val]
    train_lines = lines[n_test + n_val :]

    for name, data in [("train", train_lines), ("val", val_lines), ("test", test_lines)]:
        with open(output_dir / f"{name}.jsonl", "w", encoding="utf-8") as f:
            f.writelines(data)

    return {"train": len(train_lines), "val": len(val_lines), "test": len(test_lines)}
