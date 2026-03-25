# HuggingFace Spaces — DartLab 데모
# CPU free tier (16GB RAM), port 7860

FROM python:3.12-slim

WORKDIR /app

# 시스템 의존성
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# dartlab 설치
RUN pip install --no-cache-dir dartlab

# 샘플 데이터 프리로드 스크립트
COPY scripts/hfPreload.py scripts/hfPreload.py
RUN python scripts/hfPreload.py

# HF Spaces 기본 포트
EXPOSE 7860

# 서버 실행
CMD ["python", "-m", "dartlab.server"]
