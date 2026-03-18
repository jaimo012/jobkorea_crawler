import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # ── 잡코리아 계정 ──────────────────────────────
    USER_ID   = os.getenv('JOBKOREA_ID')
    USER_PW   = os.getenv('JOBKOREA_PW')
    LOGIN_URL = 'https://www.jobkorea.co.kr/Login'
    ACCEPT_URL = (
        'https://www.jobkorea.co.kr/corp/person/position'
        '?rPageCode=PO&Period=1&Page=PAGE_NUM'
    )

    # ── Google API ────────────────────────────────
    JSON_FILE_NAME  = os.getenv('GOOGLE_JSON_FILE', 'google_credentials.json')
    TARGET_URL      = os.getenv('GOOGLE_SHEET_URL')
    SHEET_NAME      = os.getenv('GOOGLE_SHEET_NAME', 'RAW')
    DRIVE_FOLDER_ID = os.getenv('GOOGLE_DRIVE_FOLDER_ID')

    # ── 쿠키 파일 경로 ────────────────────────────
    COOKIE_FILE = os.getenv('COOKIE_FILE', 'jobkorea_cookies.pkl')

    # ── Tesseract 경로 ────────────────────────────
    # Windows: C:\Program Files\Tesseract-OCR\tesseract.exe
    # Linux  : /usr/bin/tesseract
    TESSERACT_CMD = os.getenv('TESSERACT_CMD', '/usr/bin/tesseract')

    # ── 임시 파일 저장 경로 ───────────────────────
    TEMP_DIR = 'temp_files'

    # ── 2FA 본인인증 정보 ─────────────────────────
    AUTH_NAME   = os.getenv('AUTH_NAME', '이재모')
    AUTH_EMAIL  = os.getenv('AUTH_EMAIL', 'alpha@kmong.com')

    # ── OTP 인증 (Google Sheets 경유) ────────────
    # GAS가 지메일에서 인증코드를 자동 수집하는 시트
    OTP_SHEET_URL       = os.getenv(
        'OTP_SHEET_URL',
        'https://docs.google.com/spreadsheets/d/1orsOtn-9czDxCcs6CbVJ0tjPfYDMUsg3iDyu2XBvDGU'
    )
    OTP_SHEET_NAME      = os.getenv('OTP_SHEET_NAME', '2차인증')
    # 컬럼: 수신일시 | 메시지ID | 인증코드
    OTP_POLL_INTERVAL   = int(os.getenv('OTP_POLL_INTERVAL', '10'))      # 초
    OTP_TIMEOUT         = int(os.getenv('OTP_TIMEOUT', '300'))           # 5분

    # ── 스케줄러 설정 ───────────────────────────────
    CRAWL_INTERVAL_MIN  = int(os.getenv('CRAWL_INTERVAL_MIN', '10'))     # 분
    WORK_START_HOUR     = int(os.getenv('WORK_START_HOUR', '8'))         # 오전 8시
    WORK_END_HOUR       = int(os.getenv('WORK_END_HOUR', '18'))          # 오후 6시
    BROWSER_RESTART_HOUR = int(os.getenv('BROWSER_RESTART_HOUR', '8'))   # 매일 재시작 시각
