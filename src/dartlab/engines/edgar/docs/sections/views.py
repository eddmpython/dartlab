from __future__ import annotations

import re

import polars as pl

_TOPIC_RE = re.compile(r"^(10-K|10-Q|20-F)::")


def sortPeriods(periods: list[str]) -> list[str]:
    def key(period: str) -> tuple[int, int]:
        if "Q" not in period:
            return int(period), 4
        return int(period[:4]), int(period[-1])

    return sorted(periods, key=key, reverse=True)


def sortTopics(topics: list[str], topicOrder: dict[str, int]) -> list[str]:
    def key(topic: str) -> tuple[int, str, str]:
        match = _TOPIC_RE.match(topic)
        formType = match.group(1) if match else ""
        return topicOrder.get(topic, 999999), formType, topic

    return sorted(topics, key=key)


def buildMarkdownWide(df: pl.DataFrame | None) -> str:
    if df is None or df.is_empty():
        return ""
    periods = [col for col in df.columns if col != "topic"]
    header = "| topic | " + " | ".join(periods) + " |"
    sep = "| --- | " + " | ".join(["---"] * len(periods)) + " |"
    lines = [header, sep]
    for row in df.iter_rows(named=True):
        values = [str(row.get(period) or "") for period in periods]
        values = [value.replace("|", "｜").replace("\n", "<br>") for value in values]
        lines.append("| " + str(row["topic"]) + " | " + " | ".join(values) + " |")
    return "\n".join(lines)
