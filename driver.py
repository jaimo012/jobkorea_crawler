"""
driver.py
Chrome WebDriver 세팅 및 쿠키 기반 로그인을 담당합니다.
(Python 3.8 호환성을 위해 __future__ import 추가)
"""
from __future__ import annotations # <- 마법의 주문 추가!
import os
import pickle
import time
from typing import Optional # 구버전 호환용 도구

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

from config import Config

def setup_chrome_driver(headless: bool = True) -> webdriver.Chrome:
    print("[드라이버] 크롬 브라우저를 초기화합니다...")
    options = Options()

    if headless:
        options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")

    options.add_experimental_option(
        "excludeSwitches", ["ignore-certificate-errors", "ignore-ssl-errors"]
    )
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

def login_with_cookie(driver: webdriver.Chrome) -> Optional[webdriver.Chrome]:
    cookie_path = Config.COOKIE_FILE

    if not os.path.exists(cookie_path):
        print(f"[로그인] ❌ 쿠키 파일({cookie_path})이 없습니다.")
        return None

    print("[로그인] 쿠키 파일을 불러옵니다...")
    driver.get("https://www.jobkorea.co.kr")
    time.sleep(2)

    cookies = pickle.load(open(cookie_path, "rb"))
    for cookie in cookies:
        try:
            driver.add_cookie(cookie)
        except Exception:
            pass

    # 2. [강화된 검증] 단순히 새로고침만 하지 않고, 실제 권한이 필요한 주소로 바로 이동해봅니다.
    test_url = Config.ACCEPT_URL.replace("PAGE_NUM", "1")
    print(f"[로그인] 권한 검증을 위해 대상 페이지로 이동합니다...")
    driver.get(test_url)
    time.sleep(3)

    # 3. 만약 이동했는데도 다시 로그인 주소로 튕겨있다면 실패로 처리
    if "login" in driver.current_url.lower():
        print(f"[로그인] ❌ 쿠키가 거절되었습니다. 다시 구워야 합니다.")
        return None

    print("[로그인] ✅ 최종 권한 획득 성공!")
    return driver
