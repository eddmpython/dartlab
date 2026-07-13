"""simulate — L2.5 scenario driver engine (born-clean foundation).

The simulate engine assembles a deterministic driver DAG over scenario × period coordinates.
Every node is a thin call into an L2 leaf except the single owned macro→fundamentals edge
(`transfer`). This package currently exposes the deterministic foundation only:

- `sheet`: the node contract (`NodeValue` / `DriverNode` / `DriverSheet`) plus the topological
  deterministic executor (`buildOrder` / `evaluateSheet`) and the memoization-key hash
  (`computeInputsHash`).
- `transfer`: the macro→fundamentals edge (`transferMacroToFundamentals` and the horizon carry
  `transferRevenuePath`).
- `registry`: the deterministic driver node definitions (`buildSnapshot` / `buildScenarioSheet`)
  for the `macro.path -> rev.path -> proforma -> dcf` chain.
- `run`: the internal end-to-end driver (`runScenario`) and its result types
  (`SimulationResult` / `NodeAudit`).

Layer (operation.architecture SSOT): L2.5.
- import OK: dartlab.core (L0), dartlab.gather/providers (L1), dartlab.synth and the other L1.5
  siblings, and the L2 analysis/macro/quant/industry/credit leafs (forward, single-direction).
- not a peer of the L2 analysis engines — calling several L2 leafs from one node is legal.

`runScenario` is internal. A callable top-level / Company preview exists, but Skill OS and
apiContract registration, the lens path, Play, and DriverRegistry convergence are later phases.
"""

from __future__ import annotations

from dartlab.simulate.registry import (
    buildScenarioSheet,
    buildSnapshot,
)
from dartlab.simulate.run import (
    NodeAudit,
    SimulationResult,
    runScenario,
)
from dartlab.simulate.sheet import (
    DriverNode,
    DriverSheet,
    NodeValue,
    buildOrder,
    computeInputsHash,
    evaluateSheet,
)
from dartlab.simulate.transfer import (
    transferMacroToFundamentals,
    transferRevenuePath,
)

__all__ = [
    "NodeValue",
    "DriverNode",
    "DriverSheet",
    "computeInputsHash",
    "buildOrder",
    "evaluateSheet",
    "transferMacroToFundamentals",
    "transferRevenuePath",
    "buildSnapshot",
    "buildScenarioSheet",
    "runScenario",
    "SimulationResult",
    "NodeAudit",
]
