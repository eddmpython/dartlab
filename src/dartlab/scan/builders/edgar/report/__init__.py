"""Scan EDGAR report 도메인. 정기보고서 파생(주주환원·부채만기·임원보수·직원수). KR builders/kr/report 대칭."""

from dartlab.scan.builders.edgar.report.auditorBuild import buildEdgarAuditor, buildEdgarPanelReports
from dartlab.scan.builders.edgar.report.build import buildEdgarReport
from dartlab.scan.builders.edgar.report.employeeBuild import buildEdgarEmployee
from dartlab.scan.builders.edgar.report.ex21Build import buildEdgarSubsidiaries
from dartlab.scan.builders.edgar.report.proxyBuild import buildEdgarProxyReport
from dartlab.scan.builders.edgar.report.segmentsBuild import buildEdgarSegments

__all__ = [
    "buildEdgarAuditor",
    "buildEdgarEmployee",
    "buildEdgarPanelReports",
    "buildEdgarProxyReport",
    "buildEdgarReport",
    "buildEdgarSegments",
    "buildEdgarSubsidiaries",
]
