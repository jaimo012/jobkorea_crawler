@echo off
chcp 65001 >nul 2>&1

set SSH_KEY=C:\Project\개발자원\오라클\ssh-key-2026-03-17.key
set SERVER_USER=ubuntu
set SERVER_IP=158.179.162.168

REM SSH 키 권한 자동 설정 (Windows 필수)
icacls "%SSH_KEY%" /inheritance:r /grant:r "%USERNAME%:(R)" >nul 2>&1

echo 크롤러 상태를 확인합니다...
echo.
ssh -i "%SSH_KEY%" -o StrictHostKeyChecking=no %SERVER_USER%@%SERVER_IP% "sudo systemctl status jobkorea-crawler --no-pager; echo ''; echo '=== 최근 로그 ==='; tail -20 /home/ubuntu/jobkorea_crawler/crawler.log 2>/dev/null || echo '로그 없음'"
echo.
pause
