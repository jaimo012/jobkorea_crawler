# 잡코리아 후보자 자동화 파이프라인

잡코리아 제안 수락 후보자 정보를 자동 수집하여 Google Sheets / Drive에 동기화하고,
후보자에게 이메일·SMS·Slack 안내를 자동 발송하는 통합 자동화 시스템입니다.

---

## 전체 시스템 구성

```
[Python 크롤러 (Oracle Cloud VM)]
    └── 잡코리아 제안 수락 목록 자동 수집 → Google Sheets (RAW 시트) 적재
    └── 이력서 상세 정보 (OCR, PDF, 제안정보) 업데이트

[Google Apps Script (GAS)]
    ├── [제안수락 자동화] RAW 시트 감지 → 이메일 + SMS + Slack 자동 발송
    │                                  → 회원기준정보 DB 시트 동기화
    └── [2차인증 수집기] Gmail에서 잡코리아 인증코드 자동 수집 → '2차인증' 시트 기록
```

---

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
├── notify.py            # Slack 웹훅 알림 모듈
├── utils_debug.py       # 디버그 스크린샷/HTML 저장
│
├── GAS/
│   ├── _Config.gs           # 상수, 시트 ID, API URL, 컬럼명 매핑
│   ├── Main.gs              # 메인 오케스트레이션 (processNewAcceptances)
│   ├── SheetService.gs      # 시트 읽기/쓰기, 범례 매칭, 행→객체 변환
│   ├── EmailService.gs      # Gmail 발송 (HTML + Plain Text 템플릿)
│   ├── SmsService.gs        # NHN Cloud SMS v3.0 API 호출
│   ├── SlackService.gs      # Slack Incoming Webhook 발송
│   ├── MemberSyncService.gs # 회원기준정보 DB 시트 Upsert 동기화
│   ├── Utilities.gs         # 회신기한 계산, 경력 파싱 등 공통 유틸리티
│   ├── _DevLog.gs           # 개발 히스토리
│   └── 2단계 인증번호 수집기.gs  # Gmail → '2차인증' 시트 자동 수집
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

---

## Part 1. Python 크롤러

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

### OTP 자동 수집 (GAS - 2단계 인증번호 수집기.gs)
- Google Apps Script가 매 1분마다 지메일에서 잡코리아 인증코드를 수집
- '2차인증' 시트에 자동 기록 (컬럼: 수신일시 | 메시지ID | 인증코드)
- OTP 시트 URL: config.py의 `OTP_SHEET_URL` 참조

### 저메모리 VM 대응
- Chrome 메모리 절약 옵션: 이미지 비활성화, 확장 프로그램 비활성화, JS 힙 256MB 제한
- 2GB swap 파일 추가 (`/swapfile`)
- page_load_timeout 120초 설정
- 모든 driver.get() 호출에 타임아웃 예외 처리

---

## Part 2. GAS 제안수락 자동화

### 개요
잡코리아에서 제안을 수락한 후보자 정보가 RAW 시트에 적재되면, GAS가 이를 감지하여 이메일·SMS·Slack 안내를 자동 발송하고 회원기준정보 DB 시트에 동기화합니다.

### 실행 순서
```
미처리 행 탐색 (휴대전화번호 있고 발송 미완료인 행)
    → ① 이메일 발송 (Gmail, HTML + Plain Text)
    → ② SMS 발송 (NHN Cloud SMS v3.0)
    → ③ Slack 알림 (Incoming Webhook, 담당자 멘션)
    → ④ 회원기준정보 DB 시트 동기화 (Upsert)
    → ⑤ RAW 시트 상태 컬럼 업데이트
```

### 주요 기능

**이메일 발송 (EmailService.gs)**
- 발신: `alpha@kmong.com` (GAS 실행 계정)
- 참조: 담당 매니저 이메일 자동 추가
- 내용: 포지션명, 요청사항, 회신기한, 담당자 연락처 포함
- 회신기한 자동 계산: 다음 영업일 오전 11시

**SMS 발송 (SmsService.gs)**
- NHN Cloud SMS v3.0 API 사용
- 담당자별 APP_KEY / SECRET_KEY 스크립트 속성으로 관리
- 발신번호: 범례 시트의 매니저 연락처 사용 (NHN Cloud 등록 필수)

**Slack 알림 (SlackService.gs)**
- 담당 매니저 슬랙 ID 멘션
- 후보자 이름, 포지션, 연락처, 이력서 링크, 이메일/SMS 발송 결과 포함

**회원기준정보 DB 동기화 (MemberSyncService.gs)**
- 전화번호 기준 기존 회원 탐색 → 히스토리 로그 Upsert
- 신규 회원은 6849행 이후 빈칸에 삽입
- 비공개 전화번호인 경우 DB 동기화 제외 (`미입력` 처리)

### 스프레드시트 구성

| 시트명 | 역할 |
|--------|------|
| RAW | 크롤러가 적재하는 원본 데이터. GAS 처리 대상 |
| TEST | 개발/테스트용 시트 (`_Config.gs`의 `TARGET_SHEET_NAME`으로 전환) |
| 범례 | 매니저 정보 (이름, 이메일, 슬랙ID, SMS 활성화 여부 등) |
| 2차인증 | GAS가 Gmail에서 수집한 잡코리아 2FA 인증코드 |

### 상태 마커 (컬럼 업데이트 기준)

| 값 | 의미 |
|----|------|
| `발송완료` | 정상 발송 |
| `비공개` | 연락처 비공개로 발송 생략 |
| `입력완료` | DB 시트 동기화 완료 |
| `미입력` | 비공개 등 사유로 DB 입력 생략 |
| `발송제외` | 범례 설정상 해당 채널 비활성 |
| `오류: ...` | 처리 중 예외 발생 |

### GAS 운영 설정

**스크립트 속성 (Script Properties)에 등록 필요한 값:**
- `TERRY_APP_KEY`, `TERRY_SECRET_KEY`
- `JESS_APP_KEY`, `JESS_SECRET_KEY`
- `KUN_APP_KEY`, `KUN_SECRET_KEY`
- `ANITA_APP_KEY`, `ANITA_SECRET_KEY`
- `ALPHA_APP_KEY`, `ALPHA_SECRET_KEY`

**트리거 설정 필요:**
- `processNewAcceptances` — 시간 기반, 5분 간격 권장
- `collectJobKoreaAuthCodes` — 시간 기반, 1분 간격 필수

### 운영 전환 체크리스트
- [ ] `_Config.gs`의 `TARGET_SHEET_NAME`을 `'TEST'` → `'RAW'`로 변경
- [ ] `RESUME_TEMPLATE_URL`을 실제 개인이력카드 양식 URL로 교체
- [ ] 각 매니저의 SMS 발신번호가 NHN Cloud에 등록되어 있는지 확인
- [ ] 시간 기반 트리거 설정 (processNewAcceptances: 5분 / collectJobKoreaAuthCodes: 1분)
- [ ] Slack Webhook URL 유효성 확인

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

## 작업 로그

### 2026-03-23 (v1.1.0): GAS 회원기준정보 DB 동기화 기능 추가
- `MemberSyncService.gs` 신규 추가: 회원기준정보 시트에 데이터 Upsert 연동
- `Utilities.gs`에 `parseExperience` 함수 추가 (총경력 문자열 파싱, 년차·시작일 역산)
- `Main.gs`에 Slack 발송 이후 DB 동기화(`processDbSync`) 로직 추가
- 중복 발송 차단 강화: 미처리 행 조건 변경 (시트입력 미완료 건 포함)
- 전화번호 정규식 치환 (`replace(/\D/g, '')`) 추가
- 변경 파일: `MemberSyncService.gs` (신규), `Main.gs`, `Utilities.gs`, `README.md`

### 2026-03-20 (v1.0.0): GAS 제안수락 자동화 초기 버전
- 기본 흐름 구현: RAW/TEST 시트 → 이메일 → SMS → Slack → 시트 업데이트
- 담당자 ↔ 범례 매니저 매칭 (매니저_이름 기준)
- NHN Cloud SMS v3.0 연동 (담당자별 APP_KEY/SECRET_KEY)
- Slack Incoming Webhook 연동
- 회신기한 자동 계산 (다음 영업일 오전 11시)
- 비공개 처리 (전화번호/이메일 = "비공개" → 해당 채널 발송 skip)
- 헤더 기반 컬럼 매핑 (TEST/RAW 시트 컬럼 순서 차이 자동 대응)
- 신규 파일: `_Config.gs`, `Main.gs`, `SheetService.gs`, `EmailService.gs`, `SmsService.gs`, `SlackService.gs`, `Utilities.gs`, `_DevLog.gs`

### 2026-03-20 (크롤러): Slack 웹훅 알림 기능 추가
- `notify.py` 신규 생성: 크롤러 시작/종료, 사이클 완료/오류, 2FA 시작/성공/실패, 브라우저 재시작/크래시 알림
- 모든 오류/주의 알림에 `<@alpha>` 멘션 포함
- main.py, driver.py, pipeline.py에 알림 연동
- config.py에 `SLACK_WEBHOOK_URL` 설정 추가
- 변경 파일: `notify.py` (신규), `config.py`, `main.py`, `driver.py`, `pipeline.py`, `README.md`
- **다음 작업 예정**:
  - `claude/festive-shamir` 브랜치를 `main`에 머지
  - OCR 디버그 이미지 자동 정리 (디스크 용량 관리)

### 2026-03-20 (크롤러): OCR 오류 수정 + 전체 파이프라인 정상 작동 확인
- **근본 원인**: 서버 `.env`에 Windows Tesseract 경로 설정 → Linux 서버에서 OCR 전체 실패
- **수정**: 서버 `.env`의 `TESSERACT_CMD=/usr/bin/tesseract`로 변경
- OCR 품질 개선: 3배 업스케일, 그레이스케일 변환, 샤프닝, PSM 7, 문자 whitelist 적용
- `google_services.py`: `Tuple`, `Optional` import 누락 수정
- 전체 파이프라인 정상 작동 확인: 로그인 → 목록 수집 → 시트 적재 → OCR → PDF → 제안정보
- 변경 파일: `ocr.py`, `scraper.py`, `google_services.py`, `README.md`

### 2026-03-19 (크롤러): CONTEXT.md 작성 + 작업 임시 중단
- `CONTEXT.md` 생성: AI 에이전트용 프로젝트 컨텍스트 파일 작성
- 변경 파일: `CONTEXT.md` (신규), `README.md`

### 2026-03-19 (크롤러): 2FA 자동 인증 완성 + 서버 배포 성공
- 2FA 자동 인증 end-to-end 성공
- 잡코리아 2FA 페이지 구조 정확히 분석: UserEmail에 아이디만 입력
- alert 팝업 자동 수락, login_time -30초 보정 적용
- Chrome 메모리 절약 옵션 + 2GB swap 추가

### 2026-03-18 (크롤러): 2FA 자동 인증 + 상시 스케줄러 구현
- 쿠키 기반 로그인 방식 완전 제거
- ID/PW 로그인 + 2FA 자동 인증 구현 (Google Sheets OTP 폴링)
- main.py를 1회성 Cron에서 상시 실행 스케줄러로 전환 (워킹타임 8~18시, 10분 간격)
- systemd 서비스 파일 + Windows 원클릭 배포/관리 .bat 스크립트 추가
