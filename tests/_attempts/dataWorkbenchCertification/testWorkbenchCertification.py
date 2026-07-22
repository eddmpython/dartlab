"""Data Workbench descriptor selector attempt tests."""

from __future__ import annotations

import time

from workbenchCertification import SelectorContract, executeWindow, planSelectors


def testSubjectSelectorDoesNotDependOnOwnerName():
    contract = SelectorContract("future.signal", "subject", True)

    plan = planSelectors(contract, subjects=("A", "B"))

    assert plan.selectors == ((("subject", "A"),), (("subject", "B"),))
    assert plan.gapCode is None


def testOptionalSubjectIsForwardedWhenPresent():
    contract = SelectorContract("macro.cycle", "subject", False)

    plan = planSelectors(contract, subjects=("KR",))

    assert plan.selectors == ((("subject", "KR"),),)


def testMeasureSelectorAndMissingSelectorAreExplicit():
    contract = SelectorContract("scan.ratio", "measure", True)

    selected = planSelectors(contract, measures=("roe",))
    missing = planSelectors(contract)

    assert selected.selectors == ((("measure", "roe"),),)
    assert missing.selectors == ()
    assert missing.gapCode == "MISSING_SELECTOR"


def testResourceLocatorNeedsNoPayloadSubject():
    contract = SelectorContract("resource.scan", "subject", True)

    plan = planSelectors(contract, locatorOnly=True)

    assert plan.selectors == ((),)
    assert plan.gapCode is None


def testExecutionWindowRunsConcurrentlyButKeepsRequestOrder():
    def task(value, delay):
        def execute():
            time.sleep(delay)
            return value

        return execute

    started = time.perf_counter()
    result = executeWindow(
        (
            ("slow", task(1, 0.08)),
            ("fast", task(2, 0.01)),
            ("middle", task(3, 0.04)),
        ),
        maxConcurrency=3,
    )

    assert result == (("slow", 1), ("fast", 2), ("middle", 3))
    assert time.perf_counter() - started < 0.14
