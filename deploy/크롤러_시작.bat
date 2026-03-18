@echo off
chcp 65001 >nul 2>&1

set SSH_KEY=C:\Users\jaimo\OneDrive\Desktop\개발자원\오라클\ssh-key.key
set SERVER_USER=ubuntu
set SERVER_IP=여기에_공인IP_입력

echo 크롤러를 시작합니다...
ssh -i "%SSH_KEY%" %SERVER_USER%@%SERVER_IP% "sudo systemctl start jobkorea-crawler && sudo systemctl status jobkorea-crawler --no-pager"
echo.
pause
