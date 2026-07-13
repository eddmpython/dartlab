"""Kill tests for PIT-frozen joint moving-block paths."""

from __future__ import annotations

from dataclasses import replace

import polars as pl
import pytest

from dartlab.simulate.empiricalPaths import (
    EmpiricalPathError,
    PathVariable,
    buildJointBlockPaths,
    issuePathMeasureCertificate,
)

VARIABLES = (
    PathVariable("oilShock", "oil", "simpleReturn"),
    PathVariable("rateShock", "rate", "percentagePointChange"),
)


def _panel(n: int = 20) -> pl.DataFrame:
    return pl.DataFrame(
        {
            "eventTime": [f"202001{i + 1:02d}" for i in range(n)],
            "availableAt": [f"202001{i + 1:02d}" for i in range(n)],
            "oil": [float(i) for i in range(n)],
            "rate": [1000.0 + float(i) for i in range(n)],
        }
    )


def _build(panel: pl.DataFrame, **overrides):
    args = {
        "knowledgeAsOf": "20201231",
        "frequency": "week",
        "horizon": 6,
        "pathCount": 4,
        "blockLength": 3,
        "seed": 7,
        "minObservations": 8,
    }
    args.update(overrides)
    return buildJointBlockPaths(panel, VARIABLES, **args)


def test_future_rows_and_future_amendments_do_not_change_origin_paths() -> None:
    base = _panel()
    future = pl.concat(
        [
            base,
            pl.DataFrame(
                {
                    "eventTime": ["20200103", "20220101"],
                    "availableAt": ["20210101", "20220101"],
                    "oil": [999.0, 999.0],
                    "rate": [999.0, 999.0],
                }
            ),
        ]
    )
    first = _build(base)
    second = _build(future)
    assert first.audit.inputHash == second.audit.inputHash
    assert first.audit.pathSetHash == second.audit.pathSetHash
    assert [path.steps for path in first.paths] == [path.steps for path in second.paths]


def test_joint_rows_and_within_block_adjacency_are_preserved() -> None:
    result = _build(_panel())
    support = {(float(i), 1000.0 + float(i)) for i in range(20)}
    for path in result.paths:
        for step in path.steps:
            assert (step["oilShock"], step["rateShock"]) in support
        for offset in range(0, 6, 3):
            chunk = path.steps[offset : offset + 3]
            assert all(chunk[i + 1]["oilShock"] - chunk[i]["oilShock"] == 1.0 for i in range(len(chunk) - 1))


def test_seed_row_order_and_path_count_have_stable_common_prefix() -> None:
    panel = _panel()
    first = _build(panel)
    reordered = _build(panel.reverse())
    expanded = _build(panel, pathCount=8)
    changedSeed = _build(panel, seed=8)
    assert first.audit.pathSetHash == reordered.audit.pathSetHash
    assert [path.steps for path in first.paths] == [path.steps for path in expanded.paths[:4]]
    assert [path.pathId for path in first.paths] == [path.pathId for path in expanded.paths[:4]]
    assert [path.steps for path in first.paths] != [path.steps for path in changedSeed.paths]


def test_resamples_are_retrospective_measure_not_probability() -> None:
    result = _build(_panel())
    assert result.audit.weightLabel == "empiricalResamplingMeasure"
    assert result.audit.validationStatus == "retrospectiveOnly"
    assert {path.weightKind for path in result.paths} == {"resampled"}
    assert {path.validationStatus for path in result.paths} == {"retrospectiveOnly"}
    assert all(path.certificateId == "" for path in result.paths)


def test_insufficient_joint_support_abstains_without_global_fallback() -> None:
    with pytest.raises(EmpiricalPathError, match="insufficient joint support"):
        _build(_panel(6), minObservations=8)


def test_certificate_uses_last_fully_valid_step_and_binds_time_and_units() -> None:
    rows = []
    for factor in ("oilShock", "rateShock"):
        rows.extend(
            [
                {"factor": factor, "h": 1, "cov90": 0.90, "crps": 0.8, "crpsCarry": 1.0, "n": 30},
                {"factor": factor, "h": 2, "cov90": 0.85, "crps": 0.9, "crpsCarry": 1.0, "n": 30},
                {"factor": factor, "h": 3, "cov90": 0.90, "crps": 1.1, "crpsCarry": 1.0, "n": 30},
            ]
        )
    rows = [{**row, "availableAt": "20201231", "historyStatus": "asKnown"} for row in rows]
    certificate = issuePathMeasureCertificate(
        pl.DataFrame(rows),
        VARIABLES,
        knowledgeAsOf="20201231",
        frequency="week",
        historyStatus="asKnown",
    )
    assert certificate.status == "admitted"
    assert certificate.maxAdmittedStep == 2
    eligible = _build(_panel(), horizon=2, certificate=certificate, historyStatus="asKnown")
    assert eligible.audit.validationStatus == "retrospectiveOnly"
    assert {path.maxAdmittedStep for path in eligible.paths} == {2}
    assert "pathAdmissionReceipt:required" in eligible.audit.warnings
    with pytest.raises(EmpiricalPathError, match="maxAdmittedStep"):
        _build(_panel(), horizon=3, certificate=certificate, historyStatus="asKnown")
    with pytest.raises(EmpiricalPathError, match="step contract mismatch"):
        _build(_panel(), horizon=2, frequency="day", certificate=certificate, historyStatus="asKnown")


def test_revised_history_cannot_issue_an_admission_certificate() -> None:
    curves = pl.DataFrame(
        [
            {"factor": factor, "h": 1, "cov90": 0.90, "crps": 0.5, "crpsCarry": 1.0, "n": 30}
            for factor in ("oilShock", "rateShock")
        ]
    ).with_columns(
        pl.lit("20201231").alias("availableAt"),
        pl.lit("revisedHistory").alias("historyStatus"),
    )
    certificate = issuePathMeasureCertificate(
        curves,
        VARIABLES,
        knowledgeAsOf="20201231",
        frequency="week",
        historyStatus="revisedHistory",
    )
    assert certificate.status == "rejected"
    with pytest.raises(EmpiricalPathError, match="not admitted"):
        _build(_panel(), horizon=1, certificate=certificate)


def test_certificate_digest_and_knowledge_cutoff_are_recomputed() -> None:
    curves = pl.DataFrame(
        [
            {
                "factor": factor,
                "h": 1,
                "cov90": 0.90,
                "crps": 0.5,
                "crpsCarry": 1.0,
                "n": 30,
                "availableAt": "20201231",
                "historyStatus": "asKnown",
            }
            for factor in ("oilShock", "rateShock")
        ]
    )
    certificate = issuePathMeasureCertificate(
        curves,
        VARIABLES,
        knowledgeAsOf="20201231",
        frequency="week",
        historyStatus="asKnown",
    )
    with pytest.raises(EmpiricalPathError, match="digest mismatch"):
        _build(_panel(), horizon=1, certificate=replace(certificate, maxAdmittedStep=99), historyStatus="asKnown")
    with pytest.raises(EmpiricalPathError, match="knowledge cutoff mismatch"):
        _build(
            _panel(),
            horizon=1,
            certificate=certificate,
            historyStatus="asKnown",
            knowledgeAsOf="20210101",
        )


def test_certificate_evidence_must_be_available_and_match_history_status() -> None:
    base = pl.DataFrame(
        [
            {
                "factor": factor,
                "h": 1,
                "cov90": 0.90,
                "crps": 0.5,
                "crpsCarry": 1.0,
                "n": 30,
                "availableAt": "20210101",
                "historyStatus": "asKnown",
            }
            for factor in ("oilShock", "rateShock")
        ]
    )
    with pytest.raises(EmpiricalPathError, match="newer than cutoff"):
        issuePathMeasureCertificate(
            base,
            VARIABLES,
            knowledgeAsOf="20201231",
            frequency="week",
            historyStatus="asKnown",
        )
    revised = base.with_columns(
        pl.lit("20201231").alias("availableAt"),
        pl.lit("revisedHistory").alias("historyStatus"),
    )
    with pytest.raises(EmpiricalPathError, match="history status mismatch"):
        issuePathMeasureCertificate(
            revised,
            VARIABLES,
            knowledgeAsOf="20201231",
            frequency="week",
            historyStatus="asKnown",
        )
