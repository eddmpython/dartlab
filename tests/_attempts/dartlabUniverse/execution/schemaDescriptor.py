"""실존 callable보다 넓어지지 않는 Universe-local schema descriptor."""

from __future__ import annotations

import hashlib
import inspect
import re
import types
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any, get_args, get_origin

from ..canonical import canonicalDigest
from ..contracts import ValidationIssue, ValidationReport

_NONE_TYPE = type(None)
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


@dataclass(frozen=True, slots=True)
class SchemaDescriptor:
    descriptorId: str
    apiRef: str
    axis: str | None
    sourceRevision: str
    sourceDigest: str
    extractionEvidenceRefs: tuple[str, ...]
    argsSchema: dict[str, Any]
    outputSchema: dict[str, Any]
    validationCorpusRef: str
    validationReportRef: str
    reviewer: str
    version: str
    status: str


@dataclass(frozen=True, slots=True)
class SchemaValidationCorpus:
    corpusRef: str
    sourceDigest: str
    validArgs: tuple[dict[str, Any], ...]
    invalidArgs: tuple[dict[str, Any], ...]
    outputs: tuple[Any, ...]


def _report(issues: list[ValidationIssue]) -> ValidationReport:
    ordered = tuple(sorted(issues, key=lambda item: (item.code, item.path, item.detail)))
    return ValidationReport(valid=not ordered, issues=ordered, digest=canonicalDigest(ordered))


def _annotationText(annotation: Any) -> str:
    if annotation is inspect.Parameter.empty or annotation is inspect.Signature.empty:
        return ""
    return str(annotation).replace("typing.", "")


def _primitiveSchema(annotation: Any, default: Any) -> dict[str, Any] | None:
    """Signature annotation을 보수적인 JSON schema subset으로 바꾼다."""
    text = _annotationText(annotation).lower()
    origin = get_origin(annotation)
    args = get_args(annotation)
    if origin in {types.UnionType} or args:
        variants = []
        for item in args:
            if item is _NONE_TYPE:
                variants.append({"type": "null"})
            else:
                variant = _primitiveSchema(item, inspect.Parameter.empty)
                if variant is not None:
                    variants.append(variant)
        if variants:
            return variants[0] if len(variants) == 1 else {"anyOf": variants}
    variants = []
    for token, schemaType in (
        ("str", "string"),
        ("bool", "boolean"),
        ("int", "integer"),
        ("float", "number"),
        ("dict", "object"),
        ("mapping", "object"),
        ("list", "array"),
        ("tuple", "array"),
    ):
        if re.search(rf"(^|[^a-z]){token}([^a-z]|$)", text):
            candidate: dict[str, Any] = {"type": schemaType}
            if schemaType == "object":
                candidate["additionalProperties"] = True
            variants.append(candidate)
    if "none" in text or default is None:
        variants.append({"type": "null"})
    unique = []
    for variant in variants:
        if variant not in unique:
            unique.append(variant)
    if not unique:
        if default is inspect.Parameter.empty:
            return None
        if isinstance(default, bool):
            return {"type": "boolean"}
        if isinstance(default, int):
            return {"type": "integer"}
        if isinstance(default, float):
            return {"type": "number"}
        if isinstance(default, str):
            return {"type": "string"}
        return None
    return unique[0] if len(unique) == 1 else {"anyOf": unique}


def _outputSchema(signature: inspect.Signature) -> dict[str, Any] | None:
    text = _annotationText(signature.return_annotation).lower()
    variants = []
    if "dataframe" in text or "lazyframe" in text:
        variants.append({"type": "tabular"})
    if "dict" in text or "mapping" in text:
        variants.append({"type": "object", "additionalProperties": True})
    if "list" in text or "tuple" in text:
        variants.append({"type": "array"})
    if "str" in text:
        variants.append({"type": "string"})
    if "bool" in text:
        variants.append({"type": "boolean"})
    if "int" in text:
        variants.append({"type": "integer"})
    if "float" in text:
        variants.append({"type": "number"})
    if "none" in text:
        variants.append({"type": "null"})
    unique = []
    for variant in variants:
        if variant not in unique:
            unique.append(variant)
    if not unique:
        return None
    return unique[0] if len(unique) == 1 else {"anyOf": unique}


def callableSourceDigest(callableObject: Any, authorityDigest: str) -> tuple[str, tuple[str, ...]]:
    """Callable source byte와 live authority digest를 하나의 source digest로 묶는다."""
    sourcePath = inspect.getsourcefile(callableObject)
    evidence = [f"authority:sha256:{authorityDigest}"]
    payload = authorityDigest.encode("ascii")
    if sourcePath:
        path = Path(sourcePath).resolve()
        if path.is_file():
            sourceHash = hashlib.sha256(path.read_bytes()).hexdigest()
            evidence.append(f"source:{path.as_posix()}#sha256={sourceHash}")
            payload += b"\0" + sourceHash.encode("ascii")
    return hashlib.sha256(payload).hexdigest(), tuple(evidence)


def extractSchemaDescriptor(capability: Any, authorities: dict[str, Any]) -> SchemaDescriptor:
    """실제 dispatcher signature로 닫힌 descriptor 후보를 추출한다.

    ``**kwargs``와 ``Any``는 추측하지 않는다. axis는 CapabilityRef에 고정되므로 args에서
    제거하며, object instance를 받는 ``company``도 JSON admission surface에서 제외한다.
    """
    callableObject = authorities.get("callable")
    if not callable(callableObject):
        return SchemaDescriptor(
            descriptorId="",
            apiRef=capability.apiRef,
            axis=capability.axis,
            sourceRevision=authorities.get("sourceRevision", ""),
            sourceDigest=authorities.get("sourceDigest", ""),
            extractionEvidenceRefs=tuple(authorities.get("evidenceRefs", ())),
            argsSchema={},
            outputSchema={},
            validationCorpusRef="",
            validationReportRef="",
            reviewer="machine:signature-closure-v1",
            version="1",
            status="REJECTED",
        )
    signature = inspect.signature(callableObject)
    properties = {}
    required = []
    for name, parameter in signature.parameters.items():
        if name in {"self", "axis", "company"}:
            continue
        if parameter.kind in {inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD}:
            continue
        schema = _primitiveSchema(parameter.annotation, parameter.default)
        if schema is None:
            continue
        properties[name] = schema
        if parameter.default is inspect.Parameter.empty:
            required.append(name)
    argsSchema = {
        "type": "object",
        "properties": dict(sorted(properties.items())),
        "required": sorted(required),
        "additionalProperties": False,
    }
    outputSchema = _outputSchema(signature)
    sourceDigest = str(authorities.get("sourceDigest", ""))
    status = "CANDIDATE" if _SHA256_RE.fullmatch(sourceDigest) and outputSchema is not None else "REJECTED"
    descriptorInputs = {
        "apiRef": capability.apiRef,
        "axis": capability.axis,
        "sourceDigest": sourceDigest,
        "argsSchema": argsSchema,
        "outputSchema": outputSchema or {},
        "version": "1",
    }
    descriptorId = f"du:v1:schema:{canonicalDigest(descriptorInputs)}"
    return SchemaDescriptor(
        descriptorId=descriptorId,
        apiRef=capability.apiRef,
        axis=capability.axis,
        sourceRevision=str(authorities.get("sourceRevision", "")),
        sourceDigest=sourceDigest,
        extractionEvidenceRefs=tuple(authorities.get("evidenceRefs", ())),
        argsSchema=argsSchema,
        outputSchema=outputSchema or {},
        validationCorpusRef="",
        validationReportRef="",
        reviewer="machine:signature-closure-v1",
        version="1",
        status=status,
    )


def _matchesSchema(value: Any, schema: dict[str, Any], path: str = "$") -> list[ValidationIssue]:
    issues = []
    if "anyOf" in schema:
        if any(not _matchesSchema(value, variant, path) for variant in schema["anyOf"]):
            return []
        return [ValidationIssue("SCHEMA_TYPE", path, "anyOf와 일치하지 않음")]
    expected = schema.get("type")
    if expected == "null":
        matched = value is None
    elif expected == "boolean":
        matched = isinstance(value, bool)
    elif expected == "integer":
        matched = isinstance(value, int) and not isinstance(value, bool)
    elif expected == "number":
        matched = isinstance(value, (int, float)) and not isinstance(value, bool)
    elif expected == "string":
        matched = isinstance(value, str)
    elif expected == "array":
        matched = isinstance(value, (list, tuple))
    elif expected == "object":
        matched = isinstance(value, dict)
    elif expected == "tabular":
        matched = value.__class__.__name__ in {"DataFrame", "LazyFrame", "Table"}
    else:
        return [ValidationIssue("SCHEMA_TYPE_UNKNOWN", path, str(expected))]
    if not matched:
        return [ValidationIssue("SCHEMA_TYPE", path, f"expected={expected}, actual={type(value).__name__}")]
    if expected == "object" and isinstance(value, dict):
        properties = schema.get("properties", {})
        for name in schema.get("required", []):
            if name not in value:
                issues.append(ValidationIssue("SCHEMA_REQUIRED", f"{path}.{name}", "누락"))
        if schema.get("additionalProperties") is False:
            for name in sorted(set(value) - set(properties)):
                issues.append(ValidationIssue("SCHEMA_ADDITIONAL", f"{path}.{name}", "허용되지 않음"))
        for name, item in value.items():
            if name in properties:
                issues.extend(_matchesSchema(item, properties[name], f"{path}.{name}"))
    return issues


def validateValue(value: Any, schema: dict[str, Any]) -> ValidationReport:
    """Universe schema subset으로 단일 값을 검증한다."""
    return _report(_matchesSchema(value, schema))


def validateSchemaDescriptor(
    descriptor: SchemaDescriptor,
    corpus: SchemaValidationCorpus,
) -> ValidationReport:
    """Positive, negative, output corpus와 source digest freshness를 함께 검증한다."""
    issues = []
    if descriptor.status not in {"CANDIDATE", "VALIDATED"}:
        issues.append(ValidationIssue("DESCRIPTOR_NOT_CANDIDATE", "status", descriptor.status))
    if descriptor.sourceDigest != corpus.sourceDigest:
        issues.append(ValidationIssue("SOURCE_DIGEST_STALE", "sourceDigest", corpus.sourceDigest))
    for index, args in enumerate(corpus.validArgs):
        report = validateValue(args, descriptor.argsSchema)
        if not report.valid:
            issues.append(ValidationIssue("VALID_ARGS_REJECTED", f"validArgs[{index}]", report.digest))
    for index, args in enumerate(corpus.invalidArgs):
        if validateValue(args, descriptor.argsSchema).valid:
            issues.append(ValidationIssue("INVALID_ARGS_ACCEPTED", f"invalidArgs[{index}]", "mutation 생존"))
    for index, output in enumerate(corpus.outputs):
        report = validateValue(output, descriptor.outputSchema)
        if not report.valid:
            issues.append(ValidationIssue("OUTPUT_SCHEMA_MISMATCH", f"outputs[{index}]", report.digest))
    return _report(issues)


def closeSchemaDescriptor(
    descriptor: SchemaDescriptor,
    corpus: SchemaValidationCorpus,
    report: ValidationReport,
) -> SchemaDescriptor:
    """검증 evidence를 descriptor에 불변 successor 형태로 결합한다."""
    if descriptor.sourceDigest != corpus.sourceDigest:
        return replace(
            descriptor,
            validationCorpusRef=corpus.corpusRef,
            validationReportRef=report.digest,
            status="STALE",
        )
    return replace(
        descriptor,
        validationCorpusRef=corpus.corpusRef,
        validationReportRef=report.digest,
        status="VALIDATED" if report.valid else "REJECTED",
    )


def buildContractCorpus(descriptor: SchemaDescriptor) -> SchemaValidationCorpus:
    """Source contract 자체를 검산하는 최소 positive와 mutation corpus를 만든다."""
    valid = {}
    for name, schema in descriptor.argsSchema.get("properties", {}).items():
        if name not in descriptor.argsSchema.get("required", []):
            continue
        valid[name] = _exampleForSchema(schema)
    invalid = dict(valid)
    invalid["__inventedArgument"] = True
    output = _exampleForSchema(descriptor.outputSchema)
    corpusDigest = canonicalDigest(
        {
            "descriptorId": descriptor.descriptorId,
            "sourceDigest": descriptor.sourceDigest,
            "validArgs": (valid,),
            "invalidArgs": (invalid,),
            "outputKinds": (type(output).__name__,),
        }
    )
    return SchemaValidationCorpus(
        corpusRef=f"du:v1:schema-corpus:{corpusDigest}",
        sourceDigest=descriptor.sourceDigest,
        validArgs=(valid,),
        invalidArgs=(invalid,),
        outputs=(output,),
    )


class _TabularExample:
    pass


_TabularExample.__name__ = "DataFrame"


def _exampleForSchema(schema: dict[str, Any]) -> Any:
    if "anyOf" in schema:
        nonNull = [item for item in schema["anyOf"] if item.get("type") != "null"]
        return _exampleForSchema(nonNull[0] if nonNull else schema["anyOf"][0])
    return {
        "null": None,
        "boolean": False,
        "integer": 1,
        "number": 1.0,
        "string": "fixture",
        "array": [],
        "object": {},
        "tabular": _TabularExample(),
    }.get(schema.get("type"))
