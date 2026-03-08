"""주주총회 등에 관한 사항 분석 모듈."""

from dartlab.engines.docsParser.finance.shareholderMeeting.pipeline import shareholderMeeting
from dartlab.engines.docsParser.finance.shareholderMeeting.types import ShareholderMeetingResult

__all__ = ["shareholderMeeting", "ShareholderMeetingResult"]
