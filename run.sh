#!/bin/bash
# 매일 오전 10시 자동 실행 스크립트
# cron에 등록: crontab -e  →  0 10 * * * /path/to/RFP/run.sh

set -e

# 이 스크립트가 있는 디렉토리로 이동
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# .env 파일 로드 (있으면)
if [ -f .env ]; then
  export $(grep -v '^#' .env | grep -v '^$' | xargs)
fi

# Python 실행 (venv가 있으면 사용, 없으면 시스템 python3)
if [ -f .venv/bin/python ]; then
  PYTHON=".venv/bin/python"
else
  PYTHON="python3"
fi

echo "=== RFP 크롤링 시작: $(date '+%Y-%m-%d %H:%M:%S') ==="
$PYTHON main.py --min-score 1
echo "=== 완료: $(date '+%Y-%m-%d %H:%M:%S') ==="
