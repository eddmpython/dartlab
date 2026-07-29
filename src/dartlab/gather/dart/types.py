"""gather/dart 데이터 타입."""

from __future__ import annotations

from dataclasses import dataclass


class DartDocError(Exception):
    """gather/dart viewer 도구의 기본 예외."""


class InvalidRceptNoError(DartDocError):
    """rcept_no 형식이 잘못된 경우 (14자리 숫자 아님)."""


class ViewerPageParseError(DartDocError):
    """viewer index 또는 section HTML 구조가 손상된 경우."""


class DocumentNotFoundError(DartDocError):
    """rcept_no 가 존재하지만 viewer 가 sub-doc 을 반환하지 않은 경우.

    비공개 공시 (정정 전 원본) 또는 잘못된 번호가 원인.
    """


@dataclass(frozen=True)
class DartDocMeta:
    """공시 문서 메타데이터.

    Attributes
    ----------
    rceptNo : str
        접수번호 (14자리).
    indexUrl : str
        공시 인덱스 페이지 URL (dsaf001/main.do).
    sectionCount : int
        하위 섹션 수.
    """

    rceptNo: str
    indexUrl: str
    sectionCount: int
