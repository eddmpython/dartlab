"""Driver sheet structures + topological deterministic executor (L2.5 born-clean core).

The L3 simulate engine builds a driver DAG whose only owned math is the macro→fundamentals
edge transfer (see `simulate/transfer.py`); every other node is a thin call into an L2 leaf.
This module holds the structural foundation per
`mainPlan/scenario-simulator/01-engine-architecture.md` §5/§6:

- `NodeValue` / `DriverNode` / `DriverSheet` — the node contract (§6.1).
- `computeInputsHash` — the memoization-key SSOT (§6.1).
- `buildOrder` — deterministic Kahn topological sort (§6.2).
- `evaluateSheet` — the deterministic executor that resolves deps in topo order and fills each
  node's `det` (§6.2 `_evalDet` analogue).

Determinism by construction: pure functions, no global state, sorted-tie topo order, and an
`inputsHash` over normalized frozen inputs. There is NO lens / AI symbol in this module —
invariant-1 ("deterministic without AI") is proven by the *physical absence* of an AI entry
point, not a runtime branch. The lens path is a later phase.

Naming follows §5: DriverNode / DriverSheet (NOT *Graph / *Loop / *Kernel / *Dag).

Layer: L3. Imports nothing above L0; this file is pure stdlib (no dartlab import).
"""

from __future__ import annotations

import hashlib
import json
import math
from collections.abc import Callable
from dataclasses import dataclass, field

# ──────────────────────────────────────────────────────────────────────
# §6.1 data structures
# ──────────────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class NodeValue:
    """One driver node's computed output (§6.1) — frozen, hashable evidence record.

    value      : representative scalar (typically last element of a time vector).
                 None = data absent (a block; missing != 0 invariant).
    vector     : per-period tuple, element-wise None allowed (missing != 0 invariant).
    provenance : human-auditable formula tag, e.g.
                 "transfer:rev×(1+βgdp...)" | "preset:baseline" | "proforma:cashplug".
    refs       : grounding ref addresses (deterministic = leaf ref; lens = cited ref).
    inputsHash : blake2b-256 over parents' inputsHash + fn key + typed canonical frozen inputs.
    asOf       : data vintage used to compute this value.
    latestAsOf : latest available vintage (for downstream staleness judgement).
    """

    value: float | None
    vector: tuple[float | None, ...] | None
    provenance: str
    refs: tuple[str, ...]
    inputsHash: str
    asOf: str
    latestAsOf: str


@dataclass(frozen=True)
class DriverNode:
    """A single driver node (§6.1). The 3-coordinate key is the SSOT addressing scheme.

    nodeId = f"{driverId}@{scenarioId}#{periodKey}" — driver × scenario × period coordinates.
    The horizon collapses into `NodeValue.vector` (§5: one node per scenario, not per year), so
    there is no dimension explosion and each leaf is called once per node.

    det : the deterministic L2-leaf output. Always filled by the executor (lens-independent).
    ai  : a lens opinion. Default None — only populated on fork/gap nodes under a lens (a later
          phase). The deterministic core never touches it.
    deps: upstream nodeIds this node consumes.
    fn  : dispatch key into the sheet's function registry.
    """

    nodeId: str
    driverId: str
    scenarioId: str
    periodKey: str
    deps: tuple[str, ...]
    fn: str
    det: NodeValue | None = None
    ai: NodeValue | None = None


@dataclass
class DriverSheet:
    """A set of driver nodes plus a frozen input snapshot (§6.1).

    nodes    : nodeId -> DriverNode (each node's `det` is filled in-place by `evaluateSheet`).
    registry : fn key -> callable(node, sheet, depValues) ->
               (value, vector, provenance, refs, frozenInputs, asOf, latestAsOf).
               The registry holds the ONLY place that touches an L2 leaf (§2: leaf 0 lines, the
               edge transfer is the sole owned math; everything else is an L2 SSOT call).
    snapshot : frozen inputs (asOf-locked). Read-only during evaluation (§13b-5: snapshot, no
               reload) so that a re-run is byte-identical.
    """

    nodes: dict[str, DriverNode] = field(default_factory=dict)
    registry: dict[str, Callable] = field(default_factory=dict)
    snapshot: dict = field(default_factory=dict)

    def add(self, node: DriverNode) -> None:
        """Register a node under its nodeId; reject duplicate keys.

        Args:
            node: the DriverNode to add. Its nodeId must be unique within the sheet.

        Returns:
            None. Mutates `self.nodes` in place.

        Raises:
            ValueError: if a node with the same nodeId is already registered.

        Example:
            >>> s = DriverSheet()
            >>> s.add(DriverNode("a@base#all", "a", "base", "all", (), "fA"))
            >>> "a@base#all" in s.nodes
            True

        Requires:
            The node's `fn` should have a matching entry in `self.registry` before evaluation.
        """
        if node.nodeId in self.nodes:
            raise ValueError(f"duplicate nodeId: {node.nodeId}")
        self.nodes[node.nodeId] = node


# ──────────────────────────────────────────────────────────────────────
# inputsHash — memoization key SSOT (§6.1)
# ──────────────────────────────────────────────────────────────────────


def _normalize(obj: object) -> object:
    """타입과 컨테이너 경계를 보존하는 canonical hash payload를 만든다."""
    if obj is None:
        return {"type": "none"}
    if isinstance(obj, bool):
        return {"type": "bool", "value": obj}
    if isinstance(obj, int):
        return {"type": "int", "value": str(obj)}
    if isinstance(obj, float):
        if not math.isfinite(obj):
            raise ValueError("inputsHash cannot encode a non-finite float")
        return {"type": "float", "value": f"{round(obj, 9):.9f}"}
    if isinstance(obj, str):
        return {"type": "str", "value": obj}
    if isinstance(obj, bytes):
        return {"type": "bytes", "value": obj.hex()}
    if isinstance(obj, list):
        return {"type": "list", "items": [_normalize(value) for value in obj]}
    if isinstance(obj, tuple):
        return {"type": "tuple", "items": [_normalize(value) for value in obj]}
    if isinstance(obj, dict):
        pairs = [(_normalize(key), _normalize(value)) for key, value in obj.items()]
        pairs.sort(key=lambda pair: json.dumps(pair[0], sort_keys=True, separators=(",", ":")))
        return {"type": "dict", "items": pairs}
    raise TypeError(f"inputsHash cannot encode {type(obj).__module__}.{type(obj).__qualname__}")


def computeInputsHash(parentHashes: tuple[str, ...], fn: str, frozenInputs: object) -> str:
    """Deterministic memoization key over typed canonical inputs.

    Capabilities:
        Produces the stable content hash that addresses a node's computed value. Two evaluations
        with the same parent hashes, fn key, and (float-normalized) frozen inputs yield the same
        64-hex digest, which is the basis of deterministic re-run and future memoization.

    Args:
        parentHashes: the inputsHash of every upstream dependency (order-independent — sorted
            internally).
        fn: the node's registry dispatch key.
        frozenInputs: the exact inputs the node's fn consumed, normalized via `_normalize`
            (floats rounded to 1e-9, dicts key-sorted) before hashing.

    Returns:
        str: a 64-character hex digest (blake2b-256).

    Raises:
        TypeError: if an unsupported object would require an unstable repr fallback.
        ValueError: if a non-finite float is present.

    Example:
        >>> h = computeInputsHash((), "macro.path", {"gdp": [1.5, 2.0, 2.2]})
        >>> len(h)
        64

    Guide:
        Float normalization is what makes the hash portable across runtimes and stable across
        re-runs; never hash raw repr of floats.

    SeeAlso:
        - ``evaluateSheet``: computes this hash for every node from its parents + frozen inputs.
        - ``NodeValue.inputsHash``: where the result is stored.

    Requires:
        Standard library only (`hashlib`).

    AIContext:
        The hash is an integrity/memoization key, not a value to surface to users.

    LLM Specifications:
        AntiPatterns:
            - Hashing un-normalized floats — breaks cross-runtime determinism.
            - Treating the digest as a value rather than an address.
        OutputSchema: ``str`` of length 64 (hex).
        Prerequisites: ``frozenInputs`` must be composed of str/float/int/list/tuple/dict.
        Freshness: pure function — no data vintage.
        Dataflow: parentHashes + fn + normalize(frozenInputs) -> blake2b-256 -> 64 hex.
        TargetMarkets: market-neutral (pure utility).
    """
    payload = json.dumps(
        {"parents": sorted(parentHashes), "fn": fn, "inputs": _normalize(frozenInputs)},
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.blake2b(payload.encode("utf-8"), digest_size=32).hexdigest()


# ──────────────────────────────────────────────────────────────────────
# §6.2 topological deterministic executor
# ──────────────────────────────────────────────────────────────────────


def buildOrder(sheet: DriverSheet) -> tuple[str, ...]:
    """Deterministic Kahn topological sort of a DriverSheet's nodes (§6.2).

    Capabilities:
        Returns the evaluation order in which every node appears after all of its deps. Ties
        among ready nodes are broken by sorted nodeId, so the order is stable across runs and
        platforms. A dependency cycle, or a dep on a missing node, raises.

    Args:
        sheet: the DriverSheet whose `nodes` (and their `deps`) define the DAG.

    Returns:
        tuple[str, ...]: nodeIds in a valid, deterministic topological order.

    Raises:
        ValueError: if a node depends on a nodeId not present in the sheet, or if the deps
            contain a cycle.

    Example:
        >>> s = DriverSheet()
        >>> s.add(DriverNode("a", "a", "x", "all", (), "fA"))
        >>> s.add(DriverNode("b", "b", "x", "all", ("a",), "fB"))
        >>> buildOrder(s)
        ('a', 'b')

    Guide:
        This is the order `evaluateSheet` walks; calling it directly is useful for previewing or
        validating a sheet before evaluation.

    When:
        Before evaluating, to validate wiring (cycle / missing dep) or to inspect the plan.

    How:
        Build an in-degree map, then run Kahn's algorithm popping the sorted ready set so ties
        resolve deterministically by nodeId.

    SeeAlso:
        - ``evaluateSheet``: consumes this order to resolve and fill each node.
        - ``DriverSheet.add``: builds the node set this sorts.

    Requires:
        Every nodeId referenced in any node's `deps` must exist in `sheet.nodes`.

    AIContext:
        A `ValueError` here means the sheet wiring is malformed — report the cycle/missing dep,
        do not silently reorder.

    LLM Specifications:
        AntiPatterns:
            - Relying on insertion order instead of this sort — non-deterministic ties.
            - Swallowing the cycle ValueError.
        OutputSchema: ``tuple[str, ...]`` of all nodeIds, each once.
        Prerequisites: a `DriverSheet` with consistent deps.
        Freshness: pure function — no data vintage.
        Dataflow: nodes/deps -> in-degree map -> Kahn loop (sorted ready set) -> order tuple.
        TargetMarkets: market-neutral (structural).
    """
    nodes = sheet.nodes
    indeg = {nid: 0 for nid in nodes}
    children: dict[str, list[str]] = {nid: [] for nid in nodes}
    for nid, node in nodes.items():
        for dep in node.deps:
            if dep not in nodes:
                raise ValueError(f"node {nid!r} depends on missing node {dep!r}")
            indeg[nid] += 1
            children[dep].append(nid)
    # deterministic: process ready nodes in sorted order
    ready = sorted(nid for nid, d in indeg.items() if d == 0)
    order: list[str] = []
    while ready:
        nid = ready.pop(0)
        order.append(nid)
        newly = []
        for child in children[nid]:
            indeg[child] -= 1
            if indeg[child] == 0:
                newly.append(child)
        if newly:
            ready = sorted(ready + newly)
    if len(order) != len(nodes):
        raise ValueError("cycle detected in DriverSheet deps")
    return tuple(order)


def evaluateSheet(sheet: DriverSheet) -> dict[str, NodeValue]:
    """Deterministic executor: resolve deps in topo order and fill each node's `det` (§6.2).

    Capabilities:
        Walks `buildOrder(sheet)`, calls each node's registry fn with its resolved dependency
        values, wraps the result in a `NodeValue` (computing `inputsHash` from the parents' hashes
        + the fn key + the node's normalized frozen inputs and data vintage), and writes the value back into the
        node's `det`. This is the lens=None (deterministic) path: there is NO lens / AI symbol
        referenced here, so invariant-1 ("deterministic without AI") holds by physical absence of
        an AI entry point, not a runtime branch.

    Args:
        sheet: a fully-wired DriverSheet. Every node's `fn` must be present in `sheet.registry`,
            and each registry fn must return a 7-tuple
            ``(value, vector, provenance, refs, frozenInputs, asOf, latestAsOf)``.

    Returns:
        dict[str, NodeValue]: nodeId -> computed NodeValue. As a side effect, every node in
        `sheet.nodes` is rebuilt as a frozen DriverNode with its `det` populated.

    Raises:
        ValueError: from `buildOrder` on a cycle / missing dep, or if a node's `fn` has no
            entry in `sheet.registry`.

    Example:
        >>> s = DriverSheet()
        >>> s.registry["fConst"] = lambda node, sht, deps: (
        ...     1.0, (1.0,), "const", (), {"k": 1.0}, "2024Q4", "2024Q4")
        >>> s.add(DriverNode("a@base#all", "a", "base", "all", (), "fConst"))
        >>> out = evaluateSheet(s)
        >>> out["a@base#all"].value
        1.0

    Guide:
        Re-running on a freshly-built equivalent sheet yields byte-identical det values (same
        value/vector/inputsHash/provenance/refs) because all fns are pure and `inputsHash`
        normalizes floats. See `conceptDemo`-style real DAGs for the macro→rev→proforma chain.

    When:
        To compute the deterministic answer for a wired DriverSheet (the lens=None path).

    How:
        Walk `buildOrder`; per node call its registry fn with resolved deps, hash parents + fn +
        frozen inputs + vintage into a NodeValue, and write it back into the node's `det`.

    SeeAlso:
        - ``buildOrder``: the deterministic order this walks.
        - ``computeInputsHash``: the per-node hashing rule.
        - ``simulate.transfer``: the only owned-math edge a registry fn calls.

    Requires:
        Each registry fn is pure and reads only its node, the sheet snapshot, and its dep values.

    AIContext:
        `det` is the grounded deterministic answer; surface `provenance` and `refs` for audit and
        never blend a (future) lens opinion into it.

    LLM Specifications:
        AntiPatterns:
            - Mutating `sheet.snapshot` inside a registry fn — breaks re-run determinism.
            - Calling a registry fn out of topo order.
        OutputSchema: ``dict[str, NodeValue]``.
        Prerequisites: a wired DriverSheet with a registry covering every node's fn key.
        Freshness: inherits each leaf's asOf via the registry fn's returned `asOf`/`latestAsOf`.
        Dataflow: buildOrder -> per node (resolve deps -> fn -> wrap NodeValue -> write det).
        TargetMarkets: market-neutral (the leaf calls carry market specificity).
    """
    order = buildOrder(sheet)
    out: dict[str, NodeValue] = {}
    for nid in order:
        node = sheet.nodes[nid]
        fn = sheet.registry.get(node.fn)
        if fn is None:
            raise ValueError(f"no registry fn for {node.fn!r} (node {nid})")
        depValues = {dep: out[dep] for dep in node.deps}
        value, vector, provenance, refs, frozenInputs, asOf, latestAsOf = fn(node, sheet, depValues)
        parentHashes = tuple(out[dep].inputsHash for dep in node.deps)
        hashInputs = {
            "frozenInputs": frozenInputs,
            "asOf": asOf,
            "latestAsOf": latestAsOf,
            "dataSnapshotId": sheet.snapshot.get("dataSnapshotId", ""),
            "dataContractHash": sheet.snapshot.get("dataContractHash", ""),
        }
        ih = computeInputsHash(parentHashes, node.fn, hashInputs)
        nv = NodeValue(
            value=value,
            vector=tuple(vector) if vector is not None else None,
            provenance=provenance,
            refs=tuple(refs),
            inputsHash=ih,
            asOf=asOf,
            latestAsOf=latestAsOf,
        )
        out[nid] = nv
        # write det back (frozen DriverNode -> rebuild)
        sheet.nodes[nid] = DriverNode(
            nodeId=node.nodeId,
            driverId=node.driverId,
            scenarioId=node.scenarioId,
            periodKey=node.periodKey,
            deps=node.deps,
            fn=node.fn,
            det=nv,
            ai=node.ai,
        )
    return out
