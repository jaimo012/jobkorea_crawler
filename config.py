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
