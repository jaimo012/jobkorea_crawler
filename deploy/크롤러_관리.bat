@echo off
chcp 65001 >nul 2>&1
title 잡코리아 크롤러 관리

REM ──────────────────────────────────────────────
REM  설정: 아래 값을 본인 환경에 맞게 수정하세요
REM ──────────────────────────────────────────────
set SSH_KEY=C:\Users\jaimo\OneDrive\Desktop\개발자원\오라클\ssh-key.key
set SERVER_USER=ubuntu
set SERVER_IP=여기에_공인IP_입력
set PROJECT_DIR=/home/ubuntu/jobkorea_crawler
set SERVICE_NAME=jobkorea-crawler

:MENU
echo.
echo ╔══════════════════════════════════════════╗
echo ║     잡코리아 크롤러 관리 메뉴           ║
echo ╠══════════════════════════════════════════╣
echo ║  1. 크롤러 시작                         ║
echo ║  2. 크롤러 중지                         ║
echo ║  3. 크롤러 재시작                       ║
echo ║  4. 상태 확인                           ║
echo ║  5. 실시간 로그 보기 (Ctrl+C로 종료)    ║
echo ║  6. 최신 코드 배포 + 재시작             ║
echo ║  7. 서비스 최초 등록 (1회만)            ║
echo ║  0. 종료                                ║
echo ╚══════════════════════════════════════════╝
echo.

set /p choice=선택:

if "%choice%"=="1" goto START
if "%choice%"=="2" goto STOP
if "%choice%"=="3" goto RESTART
if "%choice%"=="4" goto STATUS
if "%choice%"=="5" goto LOGS
if "%choice%"=="6" goto DEPLOY
if "%choice%"=="7" goto SETUP
if "%choice%"=="0" goto EXIT
echo 잘못된 선택입니다.
goto MENU

:START
echo.
echo [크롤러 시작 중...]
ssh -i "%SSH_KEY%" %SERVER_USER%@%SERVER_IP% "sudo systemctl start %SERVICE_NAME% && echo '크롤러가 시작되었습니다!'"
pause
goto MENU

:STOP
echo.
echo [크롤러 중지 중...]
ssh -i "%SSH_KEY%" %SERVER_USER%@%SERVER_IP% "sudo systemctl stop %SERVICE_NAME% && echo '크롤러가 중지되었습니다.'"
pause
goto MENU

:RESTART
echo.
echo [크롤러 재시작 중...]
ssh -i "%SSH_KEY%" %SERVER_USER%@%SERVER_IP% "sudo systemctl restart %SERVICE_NAME% && echo '크롤러가 재시작되었습니다!'"
pause
goto MENU

:STATUS
echo.
ssh -i "%SSH_KEY%" %SERVER_USER%@%SERVER_IP% "sudo systemctl status %SERVICE_NAME% --no-pager; echo ''; echo '=== 최근 로그 10줄 ==='; tail -10 %PROJECT_DIR%/crawler.log 2>/dev/null || echo '로그 파일이 아직 없습니다.'"
pause
goto MENU

:LOGS
echo.
echo [실시간 로그 - Ctrl+C로 종료]
echo.
ssh -i "%SSH_KEY%" %SERVER_USER%@%SERVER_IP% "tail -f %PROJECT_DIR%/crawler.log"
goto MENU

:DEPLOY
echo.
echo [최신 코드 배포 + 재시작]
ssh -i "%SSH_KEY%" %SERVER_USER%@%SERVER_IP% "cd %PROJECT_DIR% && git pull origin main && pip3 install -r requirements.txt --quiet && sudo systemctl restart %SERVICE_NAME% && echo '' && echo '배포 완료! 크롤러가 재시작되었습니다.'"
pause
goto MENU

:SETUP
echo.
echo [서비스 최초 등록 (1회만 실행)]
ssh -i "%SSH_KEY%" %SERVER_USER%@%SERVER_IP% "cd %PROJECT_DIR% && bash deploy/setup_service.sh"
pause
goto MENU

:EXIT
echo 종료합니다.
exit /b 0
