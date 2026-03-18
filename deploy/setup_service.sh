#!/bin/bash
# ──────────────────────────────────────────────
# Oracle VM에서 1회만 실행하면 되는 서비스 등록 스크립트
# 사용법: bash deploy/setup_service.sh
# ──────────────────────────────────────────────

set -e

SERVICE_NAME="jobkorea-crawler"
SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"
PROJECT_DIR="/home/ubuntu/jobkorea_crawler"

echo "=== 잡코리아 크롤러 서비스 등록 ==="

# 1. 서비스 파일 복사
echo "[1/4] 서비스 파일 복사..."
sudo cp "${PROJECT_DIR}/deploy/${SERVICE_NAME}.service" "${SERVICE_FILE}"

# 2. systemd 리로드
echo "[2/4] systemd 리로드..."
sudo systemctl daemon-reload

# 3. 부팅 시 자동 시작 등록
echo "[3/4] 부팅 자동 시작 등록..."
sudo systemctl enable "${SERVICE_NAME}"

# 4. 서비스 시작
echo "[4/4] 서비스 시작..."
sudo systemctl start "${SERVICE_NAME}"

echo ""
echo "=== 등록 완료! ==="
echo "상태 확인: sudo systemctl status ${SERVICE_NAME}"
echo "로그 확인: tail -f ${PROJECT_DIR}/crawler.log"
echo "중지:      sudo systemctl stop ${SERVICE_NAME}"
echo "재시작:    sudo systemctl restart ${SERVICE_NAME}"
