"""
driver.py
Chrome WebDriver 세팅 및 쿠키 기반 로그인을 담당합니다.
"""

import os
import pickle
import time
import platform

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

from config import Config


def setup_chrome_driver(headless: bool = True) -> webdriver.Chrome:
    """
    Chrome WebDriver를 초기화합니다.
    - 서버(Oracle Cloud 등) 환경: headless=True  (기본값)
    - 로컬 쿠키 저장용            : headless=False
    """
    print("[드라이버] 크롬 브라우저를 초기화합니다...")

    options = Options()

    if headless:
        options.add_argument("--headless=new")   # 화면 없이 백그라운드 실행
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")

    # SSL 오류 무시
    options.add_experimental_option(
        "excludeSwitches", ["ignore-certificate-errors", "ignore-ssl-errors"]
    )

    # CDP(printToPDF)를 위한 로깅 활성화
    options.set_capability("goog:loggingPrefs", {"browser": "ALL"})

    options.add_argument("--window-size=1920,1080")
    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )

    service = Service(ChromeDriverManager().install())
    driver  = webdriver.Chrome(service=service, options=options)
    driver.implicitly_wait(10)

    print("[드라이버] ✅ 크롬 브라우저 준비 완료")
    return driver


def login_with_cookie(driver: webdriver.Chrome) -> webdriver.Chrome | None:
    """
    저장된 쿠키 파일로 잡코리아에 로그인합니다.
    쿠키 만료 / 파일 없음 시 None을 반환합니다.
    """
    cookie_path = Config.COOKIE_FILE

    if not os.path.exists(cookie_path):
        print(
            f"[로그인] ❌ 쿠키 파일({cookie_path})이 없습니다.\n"
            "  → 로컬 PC에서 save_cookies.py를 먼저 실행하세요."
        )
        return None

    print("[로그인] 쿠키 파일을 불러옵니다...")

    # 잡코리아 도메인 접속 후 쿠키 주입 (순서 중요)
    driver.get("https://www.jobkorea.co.kr")
    time.sleep(2)

    cookies: list = pickle.load(open(cookie_path, "rb"))
    for cookie in cookies:
        try:
            driver.add_cookie(cookie)
        except Exception:
            pass  # 일부 쿠키 주입 실패는 무시

    driver.refresh()
    time.sleep(2)

    # 로그인 성공 여부 검증
    if "login" in driver.current_url.lower():
        print(
            "[로그인] ❌ 쿠키가 만료되었습니다.\n"
            "  → 로컬 PC에서 save_cookies.py를 다시 실행하여 쿠키를 갱신하세요."
        )
        return None

    print("[로그인] ✅ 쿠키 로그인 성공!")
    return driver
