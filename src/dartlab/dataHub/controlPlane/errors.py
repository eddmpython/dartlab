"""DataHub control plane의 비밀 없는 오류 계약."""

from __future__ import annotations

ERROR_MESSAGES = {
    "DATA_HUB_INVALID": "DataHub 요청이 유효하지 않습니다",
    "DATA_HUB_NOT_FOUND": "DataHub job을 찾을 수 없습니다",
    "DATA_HUB_CONFLICT": "DataHub job 상태가 요청과 충돌합니다",
    "DATA_HUB_LEASE_LOST": "DataHub worker lease를 잃었습니다",
    "DATA_HUB_NOT_READY": "DataHub job 결과가 아직 준비되지 않았습니다",
    "DATA_HUB_CANCELLED": "DataHub job이 취소됐습니다",
    "DATA_HUB_ATTEMPTS_EXHAUSTED": "DataHub job의 재시도 한도를 소진했습니다",
    "DATA_HUB_WORKER_FAILED": "DataHub worker가 job 실행에 실패했습니다",
    "DATA_HUB_AUTH_REQUIRED": "DataHub 원격 인증이 필요합니다",
    "DATA_HUB_PAYLOAD_BUDGET": "DataHub payload 예산을 초과했습니다",
    "DATA_HUB_CORRUPT": "DataHub durable state 검증에 실패했습니다",
    "DATA_HUB_PLAN_MISSING": "DataHub job의 실행 계획 증거가 없습니다",
    "DATA_HUB_RESULT_UNBOUND": "DataHub 결과가 제출 query와 결박되지 않았습니다",
    "DATA_HUB_RESULT_INCOMPLETE": "DataHub 원격 결과가 단일 durable page로 완결되지 않았습니다",
}


class DataHubControlError(RuntimeError):
    """고정 code만 외부에 노출하는 control plane 오류."""

    def __init__(self, code: str):
        if code not in ERROR_MESSAGES:
            raise ValueError("등록되지 않은 DataHub 오류 code입니다")
        self.code = code
        super().__init__(ERROR_MESSAGES[code])
