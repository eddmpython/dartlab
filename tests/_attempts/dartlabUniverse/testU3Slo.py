"""Universe U3 runtime SLO를 실제 in-memory projection으로 검증한다."""

from tests._attempts.dartlabUniverse.catalog.compiler import compileCatalog
from tests._attempts.dartlabUniverse.catalog.snapshot import buildCatalogSnapshot
from tests._attempts.dartlabUniverse.graph.relations import compileCatalogRelations, defaultRelationTaxonomy
from tests._attempts.dartlabUniverse.testCoverage import _fakeResult
from tests._attempts.dartlabUniverse.validation.slo import benchmarkU3Runtime


def testU3RuntimeProjectionMeetsProductSloOnFixture():
    catalog = compileCatalog(_fakeResult())
    taxonomy = defaultRelationTaxonomy()
    snapshot = buildCatalogSnapshot(
        catalog,
        universeSnapshotId="du:v1:snapshot:" + "a" * 64,
        capabilityRegistryVersion="capability-v1",
        identityLedgerVersion="identity-v1",
        relationTaxonomyVersion=taxonomy.version,
    )
    relations = compileCatalogRelations(catalog, taxonomy=taxonomy)

    report = benchmarkU3Runtime(catalog, relations, snapshot, sampleCount=20)

    assert report.passed, report.failureCodes
    assert report.catalogDigest == catalog.digest
    assert report.snapshotId == snapshot.snapshotId
    assert report.sourceRevisionDigest
    assert report.thresholdDigest
    environment = dict(report.runtimeEnvironment)
    assert environment["python"]
    assert environment["logicalCpuCount"]
    assert environment["cacheProfile"] == "COLD_PROJECTION_WARM_LOOKUPS"
    assert environment["networkProfile"] == "NOT_APPLICABLE_RUNTIME_QUERY"
    assert report.processPeakRssBytes is None or report.processPeakRssBytes > 0
    assert report.resourceCount == len(catalog.resources)
    assert report.objectCount == len(catalog.objects)
    assert report.relationCount == len(relations)
    assert report.sampleCount == 20
    assert report.exactLookupP50Ms <= 30.0
    assert report.exactLookupP95Ms <= 100.0
    assert report.exactLookupP99Ms <= 300.0
    assert report.objectDetailP50Ms <= 80.0
    assert report.objectDetailP95Ms <= 300.0
    assert report.objectDetailP99Ms <= 1000.0
    assert report.graphTraversalP50Ms <= 100.0
    assert report.graphTraversalP95Ms <= 300.0
    assert report.graphTraversalP99Ms <= 1000.0
    assert report.snapshotReplayMs <= 5000.0
