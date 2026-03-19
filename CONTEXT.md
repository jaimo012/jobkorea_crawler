# CONTEXT.md — 잡코리아 자동 크롤러 프로젝트

> 이 문서는 AI 코딩 에이전트가 프로젝트의 전체 맥락을 빠르게 파악하기 위한 프로젝트 컨텍스트 파일입니다.
> **매 작업 시작 전 반드시 이 문서와 README.md의 [작업 로그]를 확인하세요.**

---

## 1. 프로젝트 개요

| 항목 | 내용 |
|------|------|
| **프로젝트명** | 잡코리아 후보자 자동화 파이프라인 |
| **목적** | 잡코리아 제안 수락 후보자 정보를 자동 수집하여 Google Sheets / Drive에 동기화 |
| **실행 환경** | Oracle Cloud VM (Ubuntu 20.04, Python 3.8, 1GB RAM + 2GB Swap) |
| **관리 환경** | Windows 로컬 PC → SSH로 서버 원격 관리 |
| **GitHub** | https://github.com/jaimo012/jobkorea_crawler |
| **브랜치** | `main` (운영), `claude/festive-shamir` (개발/작업 중) |

---

## 2. 핵심 아키텍처

```
[Windows 로컬 PC]
    ├── .bat 원클릭 스크립트 → SSH로 서버 관리
    └── git push → GitHub

[Oracle Cloud VM - Ubuntu 20.04]
    ├── systemd 서비스 (jobkorea-crawler)
    │     └── main.py (상시 실행 스케줄러)
    │           ├── 워킹타임: 08:00~18:00 KST
    │           ├── 크롤링 주기: 매 10분
    │           └── 브라우저 재시작: 매일 08:00
    │
    ├── driver.py → Chrome(headless) + ID/PW 로그인 + 2FA 자동
    ├── scraper.py → 잡코리아 페이지 파싱
    ├── pipeline.py → 데이터 가공 + Google Sheets 동기화
    ├── ocr.py → 연락처 이미지 OCR (Tesseract)
    └── google_services.py → Sheets/Drive API

[Google Apps Script (GAS)]
    └── 매 1분마다 Gmail에서 잡코리아 2FA 인증코드 수집
        → '2차인증' 시트에 자동 기록
        → 크롤러가 폴링하여 인증코드 획득
```

---

## 3. 파일 구조 및 역할

```
jobkorea_crawler/
├── main.py              # 상시 실행 스케줄러 (systemd 서비스 엔트리포인트)
├── config.py            # 환경변수 기반 설정 관리 (dotenv)
├── driver.py            # Chrome WebDriver + ID/PW 로그인 + 2FA 자동 처리
├── scraper.py           # 잡코리아 크롤링 핵심 로직 (목록 수집, 이력서, 제안, PDF)
├── pipeline.py          # 데이터 가공 + Google Sheets 동기화
├── google_services.py   # Google Sheets / Drive API 연동
├── ocr.py               # Tesseract OCR (연락처 이미지 해독)
├── utils_debug.py       # 디버그 스크린샷/HTML 저장
│
├── deploy/
│   ├── jobkorea-crawler.service  # systemd 서비스 파일
│   ├── setup_service.sh          # 서비스 등록 스크립트 (최초 1회)
│   ├── 크롤러_관리.bat            # Windows 원클릭 관리 메뉴
│   ├── 크롤러_시작.bat            # Windows 원클릭 시작
│   └── 크롤러_상태확인.bat        # Windows 원클릭 상태 확인
│
├── .env.example         # 환경변수 예시
├── .gitignore           # .env, credentials, pkl, temp_files 등 제외
├── requirements.txt     # Python 패키지 목록
├── CONTEXT.md           # 이 파일 (AI 에이전트용 프로젝트 컨텍스트)
└── README.md            # 사용자용 문서 + 작업 로그
```

---

## 4. 2FA 자동 인증 흐름 (핵심)

잡코리아는 기업회원 로그인 시 2단계 인증(이메일 인증코드)을 요구합니다.

### 흐름도
```
1. ID/PW 로그인 → 잡코리아 기업회원 로그인
2. 보호 페이지 접근 → 2FA 리다이렉트 감지 (URL에 "twofactorauth" 포함)
3. 이름/이메일 입력:
   - input#UserName → "이재모"
   - input#UserEmail → "alpha" (아이디 부분만, 도메인은 hidden input#corpDomain="kmong.com")
   - input/change 이벤트 dispatch (폼 유효성 통과용)
4. 인증코드 발송 → button#btnSendCertCorpDomain 클릭
5. alert("인증번호가 전송됐습니다.") → 자동 수락
6. GAS가 Gmail에서 인증코드 수집 → '2차인증' 시트에 기록 (매 1분)
7. 크롤러가 시트 폴링 (10초 간격, 최대 300초)
   - login_time(-30초 보정) 이후의 마지막 인증코드 사용
8. 인증코드 입력 → input#certNumCorpDomain
9. 인증 버튼 클릭 → button#btnCorpDomainCheckCert
10. alert 수락 → 인증 완료
```

### 2FA 관련 설정 (config.py)
```python
AUTH_NAME   = '이재모'
AUTH_EMAIL  = 'alpha@kmong.com'
OTP_SHEET_URL = 'https://docs.google.com/spreadsheets/d/1orsOtn-9czDxCcs6CbVJ0tjPfYDMUsg3iDyu2XBvDGU'
OTP_SHEET_NAME = '2차인증'    # 컬럼: 수신일시 | 메시지ID | 인증코드
OTP_POLL_INTERVAL = 10        # 폴링 간격 (초)
OTP_TIMEOUT = 300             # 타임아웃 (5분)
```

### GAS 코드 (Gmail → 시트 자동 수집)
- 스프레드시트: `1orsOtn-9czDxCcs6CbVJ0tjPfYDMUsg3iDyu2XBvDGU`
- 시트명: `2차인증`
- Gmail 검색: `from:(helpdesk@jobkorea.co.kr) subject:([잡코리아] 요청하신 2단계 인증번호)`
- 인증코드 추출: 메일 본문에서 "인증번호" 뒤 6자리 숫자 정규식 매칭
- **트리거**: 시간 기반 → 매 1분마다 `collectJobKoreaAuthCodes` 실행 필요

---

## 5. 서버 환경 상세

| 항목 | 값 |
|------|-----|
| **IP** | 158.179.162.168 |
| **OS** | Ubuntu 20.04 |
| **Python** | 3.8 |
| **RAM** | 1GB + 2GB Swap (`/swapfile`) |
| **타임존** | Asia/Seoul |
| **프로젝트 경로** | `/home/ubuntu/jobkorea_crawler` |
| **서비스명** | `jobkorea-crawler` (systemd) |
| **SSH 키** | `C:\Users\jaimo\OneDrive\Desktop\개발자원\오라클\ssh-key-2026-03-17.key` |

### 저메모리 VM 대응
- Chrome 메모리 절약: 이미지 비활성화, JS 힙 256MB 제한
- page_load_timeout 120초
- 모든 `driver.get()`에 타임아웃 예외 처리

---

## 6. 코딩 규칙

### Python 호환성 (3.8)
- **필수**: `from __future__ import annotations` (모든 파일 상단)
- **필수**: `Optional`, `Tuple`, `List`, `Dict` → `typing` 모듈에서 import
- **금지**: `str | None`, `list[str]` 등 3.10+ 문법 (런타임에서 사용 시)
- 타입 힌트에서 `tuple[X, Y]`는 annotations import 덕분에 문법 오류 없음 (문자열 평가)

### 에러 처리
- 모든 `driver.get()` 호출은 `try/except`로 타임아웃 방어
- 크롤링 실패 시 다음 사이클에서 자동 재시도 (브라우저 재시작 유도)
- `save_debug_snapshot()` 으로 오류 현장 스크린샷/HTML 저장

### Git 워크플로우
- 로컬 수정 → commit → push → 서버에서 `git pull` + `systemctl restart`
- `.env`, `*.json`, `*.pkl` 등 시크릿은 절대 commit 금지

---

## 7. 주요 의존성

```
selenium, webdriver-manager    # 브라우저 자동화
beautifulsoup4                 # HTML 파싱
pandas                         # 데이터 가공
gspread, google-auth           # Google Sheets API
google-api-python-client       # Google Drive API
pytesseract, Pillow            # OCR
python-dotenv                  # 환경변수
```

---

## 8. 알려진 이슈 및 주의사항

### 해결된 이슈
- SSH 키 파일명: `ssh-key-2026-03-17.key` (bat 파일에 정확히 반영 필요)
- Python 출력 버퍼링: systemd에서 `PYTHONUNBUFFERED=1` 필수
- 서버 타임존: `sudo timedatectl set-timezone Asia/Seoul` 적용 완료
- 2FA UserEmail: 아이디 부분만 입력 (도메인은 hidden 필드)
- 발송 버튼 비활성화: JS로 강제 활성화 + input/change 이벤트 dispatch
- alert 팝업: `driver.switch_to.alert.accept()` 로 자동 수락

### 미해결 / 개선 필요
- **OCR 정확도**: Tesseract 기반 연락처 인식 — 정확도 검증 및 개선 필요
- **GAS 트리거**: 매 1분 실행 트리거가 GAS 에디터에서 설정되어 있는지 확인 필요
- **2FA 재인증 빈도**: 서버 IP 기준으로 2FA가 얼마나 자주 트리거되는지 모니터링 필요
- **google_services.py 타입힌트**: `Tuple`, `Optional` import 누락 (런타임 오류 가능성)

---

## 9. 필독 규칙 (매 작업 시작 전 반드시 확인)

1. **이 문서와 README.md의 [작업 로그]를 반드시 확인**한다
2. 전체 개발 방향과 현재 진행 상태를 파악한 후 작업을 시작한다
3. 작업 완료 후 반드시 **README.md의 [작업 로그] 섹션을 업데이트**한다
4. GitHub에 반드시 push까지 완료한다
5. 업데이트 내용: 완료한 작업, 변경된 파일 목록, 다음 작업 예정 내용
