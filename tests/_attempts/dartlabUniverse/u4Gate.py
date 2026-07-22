"""Current U3 artifact 위에서 Universe U4 G3와 G4E live gate를 판정한다."""

from __future__ import annotations

import argparse
import os
import sys
import time
from dataclasses import asdict
from pathlib import Path

from .canonical import canonicalDigest, canonicalJson
from .catalog.recoveryStore import defaultRecoveryRoot
from .graph.query import GraphStore
from .identity.ledger import buildIdentityLedger
from .query.adapters import LexicalAdapterContext
from .query.blogAst import BlogAstIndex
from .query.capabilityCanary import capabilityCanarySummary, runCapabilityCanary
from .query.contentSearch import DartContentSearchAdapter
from .query.engine import UniverseQueryEngine
from .query.golden import evaluateGoldenQueries, loadGoldenQueries
from .queryTestSupport import buildQueryRuntimeFixture
from .u3C2 import defaultCheckpointPath
from .u3Gate import buildLiveU3Artifacts, defaultControlRoot


def defaultGoldenPath() -> Path:
    return Path(__file__).parent / "fixtures" / "universeGoldenQueries.json"


def defaultU4ControlRoot() -> Path:
    root = Path(os.getenv("LOCALAPPDATA") or (Path.home() / ".dartlab"))
    return root / "DartLab" / "universe" / "control" / "u4"


def _runFixtureGolden(goldenPath: Path):
    runtime = buildQueryRuntimeFixture()
    cases = loadGoldenQueries(goldenPath, scope="FIXTURE")
    with UniverseQueryEngine(
        runtime.catalog,
        runtime.snapshot,
        runtime.graph,
        identityLedger=runtime.ledger,
    ) as engine:
        return evaluateGoldenQueries(
            cases,
            engine=engine,
            catalog=runtime.catalog,
            snapshot=runtime.snapshot,
            graph=runtime.graph,
        )


def runLiveU4(
    *,
    checkpointPath: Path,
    recoveryRoot: Path,
    u3ControlRoot: Path,
    u4ControlRoot: Path,
    goldenPath: Path,
) -> tuple[bool, dict[str, object]]:
    """Live full catalog, local content index, blog AST와 fixture truth를 함께 평가한다."""
    started = time.perf_counter()
    artifacts = buildLiveU3Artifacts(
        checkpointPath=checkpointPath,
        recoveryRoot=recoveryRoot,
        controlRoot=u3ControlRoot,
    )
    catalog = artifacts.catalog
    snapshot = artifacts.snapshot
    graph = GraphStore((), artifacts.relations)
    ledger = buildIdentityLedger(artifacts.liveG1.identityRecords)
    blog = BlogAstIndex(artifacts.repoRoot, catalog)
    replayBlog = BlogAstIndex(artifacts.repoRoot, catalog)
    capabilityCanary, _capabilityAdapter = runCapabilityCanary(
        repoRoot=artifacts.repoRoot,
        controlRoot=u4ControlRoot / "executions",
        dataRoot=u4ControlRoot / "source-cache" / snapshot.snapshotId.rsplit(":", 1)[-1],
        token=artifacts.token,
        catalog=catalog,
        snapshot=snapshot,
        graph=graph,
        registry=artifacts.liveG1.capabilityRegistry,
    )
    content = DartContentSearchAdapter(catalog)
    replayContent = DartContentSearchAdapter(catalog)
    contentPreparation = content.prepare()
    replayContentPreparation = replayContent.prepare()
    liveCases = loadGoldenQueries(goldenPath, scope="LIVE")
    with UniverseQueryEngine(
        catalog,
        snapshot,
        graph,
        identityLedger=ledger,
        exactAdapters=(content,),
        lexicalAdapters=(blog, content),
    ) as engine:

        def prepareReplay(query) -> None:
            view = engine.prepare(frozenset(query.allowedVisibility))
            context = LexicalAdapterContext(
                allowedVisibility=view.allowedVisibility,
                objectById=view.objectById,
                resourceByVersion=view.resourceByVersion,
            )
            replayContent.searchExact(query, context)
            replayContent.search(query, context)

        liveReport = evaluateGoldenQueries(
            liveCases,
            engine=engine,
            catalog=catalog,
            snapshot=snapshot,
            graph=graph,
            virtualRetrievedVerifiers=(replayBlog.verifyRetrieved, replayContent.verifyRetrieved),
            prepareVirtualReplay=prepareReplay,
        )
    fixtureReport = _runFixtureGolden(goldenPath)
    failureCodes = []
    if not artifacts.report.passed or not artifacts.slo.passed:
        failureCodes.append("UPSTREAM_U3_FAILED")
    if not fixtureReport.passed:
        failureCodes.append("FIXTURE_G3_FAILED")
    if not liveReport.passed:
        failureCodes.append("LIVE_G3_G4E_FAILED")
    if not capabilityCanary.passed:
        failureCodes.append("LIVE_CAPABILITY_CANARY_FAILED")
    if blog.report.parseErrors or blog.report.staleResourceCount:
        failureCodes.append("BLOG_AST_INCOMPLETE")
    if content.binding is None or len(content.binding.resourceVersionIds) < 2:
        failureCodes.append("CONTENT_INDEX_BINDING_INCOMPLETE")
    metrics = {
        "schemaVersion": "du-u4-gate-live-v1",
        "passed": not failureCodes,
        "durationSeconds": round(time.perf_counter() - started, 6),
        "snapshotId": snapshot.snapshotId,
        "catalogDigest": catalog.digest,
        "u3Digest": artifacts.report.digest,
        "u3Passed": artifacts.report.passed and artifacts.slo.passed,
        "goldenCorpusDigest": canonicalDigest(loadGoldenQueries(goldenPath)),
        "fixture": asdict(fixtureReport),
        "live": asdict(liveReport),
        "blogAst": asdict(blog.report),
        "contentIndexBinding": {
            "manifestDigest": content.binding.manifestDigest if content.binding else "",
            "artifactSetDigest": content.binding.artifactSetDigest if content.binding else "",
            "artifactCount": len(content.binding.resourceVersionIds) if content.binding else 0,
            "metaResourceVersionId": content.binding.metaResourceVersionId if content.binding else "",
            "preparation": asdict(contentPreparation),
            "replayPreparation": asdict(replayContentPreparation),
        },
        "capabilityCanary": capabilityCanarySummary(capabilityCanary),
        "answerDraftCount": 0,
        "failureCodes": tuple(sorted(failureCodes)),
    }
    return not failureCodes, metrics


def buildArgumentParser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="DartLab Universe U4 live query and evidence gate")
    parser.add_argument("--checkpoint", type=Path, default=defaultCheckpointPath())
    parser.add_argument("--recovery-root", type=Path, default=defaultRecoveryRoot())
    parser.add_argument("--u3-control-root", type=Path, default=defaultControlRoot())
    parser.add_argument("--u4-control-root", type=Path, default=defaultU4ControlRoot())
    parser.add_argument("--report", type=Path)
    parser.add_argument("--golden", type=Path, default=defaultGoldenPath())
    parser.add_argument("--strict", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = buildArgumentParser().parse_args(argv)
    passed, metrics = runLiveU4(
        checkpointPath=args.checkpoint,
        recoveryRoot=args.recovery_root,
        u3ControlRoot=args.u3_control_root,
        u4ControlRoot=args.u4_control_root,
        goldenPath=args.golden,
    )
    payload = canonicalJson(metrics) + b"\n"
    if args.report is not None:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        temporary = args.report.with_suffix(args.report.suffix + ".tmp")
        temporary.write_bytes(payload)
        temporary.replace(args.report)
    sys.stdout.buffer.write(payload)
    return 2 if args.strict and not passed else 0


if __name__ == "__main__":
    raise SystemExit(main())
