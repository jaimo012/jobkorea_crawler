# 잡코리아 후보자 자동화 파이프라인

잡코리아 제안 수락 후보자 정보를 자동 수집하여 Google Sheets / Drive에 동기화하는 크롤러입니다.

## 프로젝트 구조

```
jobkorea_crawler/
├── main.py              # 상시 실행 스케줄러 (systemd 서비스)
├── config.py            # 환경변수 기반 설정 관리
├── driver.py            # Chrome WebDriver 초기화 + ID/PW 로그인 + 2FA 자동 처리
├── scraper.py           # 잡코리아 크롤링 핵심 로직
├── pipeline.py          # 데이터 가공 + Google Sheets 동기화
├── google_services.py   # Google Sheets / Drive API 연동
├── ocr.py               # Tesseract OCR 유틸리티
├── utils_debug.py       # 디버그 스크린샷/HTML 저장
│
├── deploy/
│   ├── jobkorea-crawler.service  # systemd 서비스 파일
│   ├── setup_service.sh          # 서비스 등록 스크립트
│   ├── 크롤러_관리.bat            # Windows 원클릭 관리 메뉴
│   ├── 크롤러_시작.bat            # Windows 원클릭 시작
│   └── 크롤러_상태확인.bat        # Windows 원클릭 상태 확인
│
├── .env.example         # 환경변수 예시 파일
├── .gitignore
├── requirements.txt
└── README.md
```

## 동작 방식

### 스케줄러 (main.py)
- **워킹타임**: 매일 오전 8시 ~ 오후 6시 (KST)
- **크롤링 주기**: 10분마다 자동 실행
- **브라우저 관리**: 워킹타임 동안 브라우저 세션 유지, 매일 1회 재시작
- **비워킹타임**: 브라우저 종료 후 대기, 다음 워킹타임 시작 시 자동 재개

### 로그인 + 2FA 자동 인증 (driver.py)
1. ID/PW로 잡코리아 기업회원 로그인
2. 보호된 페이지 접근 시 2FA 리다이렉트 감지
3. 2FA 자동 처리:
   - 이름/이메일 아이디 입력 (`input#UserName`, `input#UserEmail` — 아이디만, 도메인은 hidden 필드)
   - input/change 이벤트 dispatch로 폼 유효성 통과
   - 인증코드 발송 (`button#btnSendCertCorpDomain`) + alert 팝업 자동 수락
   - GAS가 지메일에서 자동 수집한 인증코드를 '2차인증' 시트에서 폴링
   - 인증코드 입력 (`input#certNumCorpDomain`) + 인증 (`button#btnCorpDomainCheckCert`) + alert 처리

### OTP 자동 수집 (GAS)
- Google Apps Script가 매 1분마다 지메일에서 잡코리아 인증코드를 수집
- '2차인증' 시트에 자동 기록 (컬럼: 수신일시 | 메시지ID | 인증코드)
- OTP 시트 URL: config.py의 `OTP_SHEET_URL` 참조

### 저메모리 VM 대응
- Chrome 메모리 절약 옵션: 이미지 비활성화, 확장 프로그램 비활성화, JS 힙 256MB 제한
- 2GB swap 파일 추가 (`/swapfile`)
- page_load_timeout 120초 설정
- 모든 driver.get() 호출에 타임아웃 예외 처리

---

## 서버 환경

- **서버**: Oracle Cloud VM (Ubuntu 20.04, Python 3.8, 1GB RAM + 2GB Swap)
- **IP**: 158.179.162.168
- **프로젝트 경로**: `/home/ubuntu/jobkorea_crawler`
- **서비스명**: `jobkorea-crawler` (systemd)
- **타임존**: Asia/Seoul

---

## 세팅 가이드

### 1. 저장소 클론 + 패키지 설치
```bash
git clone https://github.com/jaimo012/jobkorea_crawler.git
cd jobkorea_crawler
pip install -r requirements.txt
```

### 2. 환경변수 설정
```bash
cp .env.example .env
# .env 파일을 열어 실제 값 입력
```

### 3. 필수 파일 준비 (GitHub에 없음)
- `google_credentials.json` — Google Service Account 키 파일
- `.env` — 환경변수 (잡코리아 계정, Google API 등)

### 4. 서버 서비스 등록 (최초 1회)
```bash
sudo bash deploy/setup_service.sh
```

---

## 서버 관리

### Windows에서 원클릭 관리
- `deploy/크롤러_관리.bat` — 시작/중지/재시작/상태확인/로그/배포 메뉴
- `deploy/크롤러_시작.bat` — 원클릭 시작
- `deploy/크롤러_상태확인.bat` — 원클릭 상태 확인

### SSH로 직접 관리
```bash
# 서비스 상태 확인
sudo systemctl status jobkorea-crawler

# 로그 확인
tail -50 /home/ubuntu/jobkorea_crawler/crawler.log

# 재시작
sudo systemctl restart jobkorea-crawler

# 코드 업데이트 + 재시작
cd /home/ubuntu/jobkorea_crawler && git pull && sudo systemctl restart jobkorea-crawler
```

---

## 코드 업데이트 워크플로우

```bash
# 로컬에서 코드 수정 후
git add .
git commit -m "수정 내용"
git push

# 서버 배포 (크롤러_관리.bat의 6번 메뉴 또는 수동)
ssh -i "키파일" ubuntu@158.179.162.168 "cd /home/ubuntu/jobkorea_crawler && git pull && sudo systemctl restart jobkorea-crawler"
```

---

## 보안 주의사항

`.env`, `*.json`, `*.pkl` 파일은 절대 GitHub에 올리지 마세요.
`.gitignore`에 등록되어 있으나 실수로 `git add .` 했다면:

```bash
git rm --cached .env
git rm --cached google_credentials.json
```

---

## 작업 이력

### 2026-03-19: 2FA 자동 인증 완성 + 서버 배포 성공
- 2FA 자동 인증 end-to-end 성공 (이메일 발송 → GAS 수집 → OTP 입력 → 인증 완료)
- 잡코리아 2FA 페이지 구조 정확히 분석: UserEmail에 아이디만 입력 (도메인은 corpDomain hidden 필드)
- alert 팝업 ("인증번호가 전송됐습니다.") 자동 수락 처리
- login_time -30초 보정으로 메일 수신시각 오차 흡수
- Chrome 메모리 절약 옵션 추가 (1GB VM 대응)
- 2GB swap 파일 추가 (/swapfile)
- page_load_timeout 120초 + 모든 driver.get()에 타임아웃 예외 처리
- input/change 이벤트 dispatch로 폼 유효성 검증 통과

### 2026-03-18: 2FA 자동 인증 + 상시 스케줄러 구현
- 쿠키 기반 로그인 방식 완전 제거 (save_cookies.py 삭제)
- ID/PW 로그인 + 2FA 자동 인증 구현 (Google Sheets OTP 폴링)
- 잡코리아 2FA 페이지 실제 셀렉터 적용 (UserName, UserEmail, certNumCorpDomain 등)
- main.py를 1회성 Cron에서 상시 실행 스케줄러로 전환 (워킹타임 8~18시, 10분 간격)
- systemd 서비스 파일 + Windows 원클릭 배포/관리 .bat 스크립트 추가
- 서버 타임존 Asia/Seoul 설정, PYTHONUNBUFFERED=1 적용
