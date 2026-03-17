# 🚀 잡코리아 후보자 자동화 파이프라인

잡코리아 제안 수락 후보자 정보를 자동 수집하여 Google Sheets / Drive에 동기화하는 크롤러입니다.

## 📁 프로젝트 구조

```
jobkorea_crawler/
├── main.py              # 서버 실행 진입점 (Cron 등록 대상)
├── save_cookies.py      # 【로컬 전용】 2단계 인증 처리 + 쿠키 저장
│
├── config.py            # 환경변수 기반 설정 관리
├── driver.py            # Chrome WebDriver 초기화 + 쿠키 로그인
├── scraper.py           # 잡코리아 크롤링 핵심 로직
├── pipeline.py          # 데이터 가공 + Google Sheets 동기화
├── google_services.py   # Google Sheets / Drive API 연동
├── ocr.py               # Tesseract OCR 유틸리티
│
├── .env.example         # 환경변수 예시 파일
├── .gitignore           # GitHub 업로드 제외 파일 목록
├── requirements.txt     # Python 패키지 목록
└── README.md
```

## ⚙️ 처음 세팅하기

### 1. 저장소 클론
```bash
git clone https://github.com/내아이디/저장소이름.git
cd jobkorea_crawler
```

### 2. 패키지 설치
```bash
pip install -r requirements.txt
```

### 3. 환경변수 설정
```bash
cp .env.example .env
# .env 파일을 열어 실제 값 입력
```

### 4. 민감 파일 준비 (GitHub에 없으므로 별도 전달)
- `google_credentials.json` — Google Service Account 키 파일
- `jobkorea_cookies.pkl`    — 로컬에서 save_cookies.py 실행 후 생성

---

## 💻 로컬 PC — 쿠키 저장 (최초 1회 + 만료 시 갱신)

```bash
# Windows 기준
python save_cookies.py
```

1. 브라우저가 자동으로 열립니다
2. 2단계 인증을 직접 완료합니다
3. 터미널에서 Enter를 누릅니다
4. `jobkorea_cookies.pkl` 파일이 생성됩니다
5. 파일을 서버로 전송합니다:

```bash
scp -i ssh-key.pem jobkorea_cookies.pkl ubuntu@[서버IP]:~/crawler/
```

---

## 🖥️ Oracle Cloud 서버 — 실행

### 수동 실행
```bash
cd ~/crawler
python3 main.py
```

### Cron 자동 실행 (매일 오전 9시)
```bash
crontab -e
```
```
0 9 * * * cd /home/ubuntu/crawler && git pull && python3 main.py >> /home/ubuntu/logs/crawler.log 2>&1
```

---

## 🔄 코드 업데이트 워크플로우

```bash
# 로컬에서 코드 수정 후
git add .
git commit -m "수정 내용"
git push

# 서버에서
cd ~/crawler
git pull
```

---

## 🔐 보안 주의사항

`.env`, `*.json`, `*.pkl` 파일은 절대 GitHub에 올리지 마세요.  
`.gitignore`에 등록되어 있으나 실수로 `git add .` 했다면:

```bash
git rm --cached .env
git rm --cached google_credentials.json
git rm --cached jobkorea_cookies.pkl
```

# 🛠️ 서버 환경 최적화 및 패키지 업데이트 내역

본 프로젝트는 로컬(Windows) 환경에서 개발되었으나, 오라클 클라우드(Ubuntu 20.04, Python 3.8) 서버에서 안정적으로 가동하기 위해 다음과 같은 기술적 수정 과정을 거쳤습니다.

## 1. 파이썬 버전 호환성 확보 (Python 3.8 대응)
서버의 기본 파이썬 버전(3.8)이 최신 문법을 지원하지 않아 발생하는 `TypeError`를 해결하였습니다.
* **마법의 주문 추가**: 모든 실행 파일(`driver.py`, `scraper.py`, `google_services.py` 등) 최상단에 `from __future__ import annotations`를 추가하여 최신 타입 힌트 문법을 허용하였습니다.
* **타입 힌트 수정**: Python 3.10+의 `|` 문법(Union) 대신 구버전 호환용 `typing.Optional`, `typing.Tuple`, `typing.List` 등을 사용하여 코드의 안정성을 높였습니다.

## 2. 원격 디버깅 시스템 구축 (Headless 환경 대응)
서버는 화면이 없는(Headless) 환경이므로, 에러 발생 시 상황 파악이 어렵다는 점을 개선하였습니다.
* **디버깅 유틸 신설**: `utils_debug.py`를 추가하여 에러 발생 시 현재 브라우저의 스크린샷(`.png`)과 HTML 소스(`.html`)를 자동으로 저장하는 기능을 구현하였습니다.
* **에러 추적 강화**: 크롤러가 페이지 번호를 찾지 못하는 등 예상치 못한 상황 발생 시 즉시 `save_debug_snapshot`을 호출하여 `temp_files` 폴더에 현장 증거를 남기도록 설계하였습니다.

## 3. 로그인 인증 및 권한 검증 고도화
단순히 쿠키를 주입하는 것에서 나아가, 실제 서비스 페이지에 접근 가능한지 확인하는 로직을 강화하였습니다.
* **권한 검증 로직**: `driver.py`의 `login_with_cookie` 함수를 수정하여 쿠키 주입 후 즉시 후보자 목록 페이지(`ACCEPT_URL`)로 이동해보고, 로그인 창으로 튕기는지 여부를 체크하여 최종 권한 획득 성공을 판단하도록 개선하였습니다.
* **대기 시간 최적화**: 서버의 네트워크 속도와 렌더링 시간을 고려하여 `time.sleep` 대기 시간을 넉넉하게 조정(3~5초)하였습니다.

## 4. 서버 시스템 종속성 해결 (Linux 특화)
서버 인프라 구축 시 발생한 환경적 이슈들을 해결하였습니다.
* **OpenSSL 라이브러리 충돌**: Ubuntu 20.04의 구형 보안 패키지와 최신 파이썬 라이브러리 충돌 건을 `sudo apt-get remove python3-openssl` 및 `pyOpenSSL` 강제 업데이트를 통해 해결하였습니다.
* **Tesseract 경로 설정**: `config.py`를 통해 윈도우와 리눅스 환경의 Tesseract 실행 경로를 환경 변수로 분리 관리하도록 세팅하였습니다.

## 5. 쿠키 저장 방식 개선 (수동 안전 모드)
잡코리아의 강력한 보안(2단계 인증 등)을 우회하기 위해 로컬 PC 전용 `save_cookies.py`를 수동 모드로 전환하여, 사람이 직접 인증을 완료한 후의 완벽한 세션 쿠키를 획득할 수 있도록 변경하였습니다.
