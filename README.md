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
