@echo off
chcp 65001 >nul 2>&1

set SSH_KEY=C:\Users\jaimo\OneDrive\Desktop\개발자원\오라클\ssh-key.key
set SERVER_USER=ubuntu
set SERVER_IP=여기에_공인IP_입력

echo 크롤러 상태를 확인합니다...
echo.
ssh -i "%SSH_KEY%" %SERVER_USER%@%SERVER_IP% "sudo systemctl status jobkorea-crawler --no-pager; echo ''; echo '=== 최근 로그 ==='; tail -20 /home/ubuntu/jobkorea_crawler/crawler.log 2>/dev/null || echo '로그 없음'"
echo.
pause
