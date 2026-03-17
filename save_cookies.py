"""
save_cookies.py
【로컬 PC 전용】 잡코리아 2단계 인증을 직접 처리하고 쿠키를 저장합니다.

사용 방법:
    1. 로컬 PC에서 실행: python save_cookies.py
    2. 뜨는 브라우저에서 2단계 인증 직접 완료
    3. 터미널에서 Enter 입력
    4. 생성된 .pkl 파일을 서버로 전송:
       scp -i ssh-key.pem jobkorea_cookies.pkl ubuntu@[서버IP]:~/crawler/
"""

import pickle
import time
import random

import pyperclip
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager

from config import Config

load_dotenv()


def save_cookies() -> None:
    # ── 브라우저 실행 (화면 표시 필수) ───────────
    options = Options()
    options.add_argument("--start-maximized")
    options.add_experimental_option(
        "excludeSwitches", ["ignore-certificate-errors", "ignore-ssl-errors"]
    )

    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options,
    )
    driver.implicitly_wait(10)

    # ── 로그인 페이지 접속 ───────────────────────
    driver.get(Config.LOGIN_URL)
    time.sleep(random.uniform(0.5, 0.8))

    # 기업회원 탭 클릭
    try:
        corp_tab = driver.find_element(By.CSS_SELECTOR, 'a[data-m-type="Co"]')
        corp_tab.click()
        time.sleep(random.uniform(0.5, 0.8))
    except Exception:
        pass

    # 아이디 입력
    tag_id = driver.find_element(By.NAME, "M_ID")
    tag_id.click()
    pyperclip.copy(Config.USER_ID)
    tag_id.send_keys(Keys.CONTROL, "v")
    time.sleep(random.uniform(0.4, 0.6))

    # 비밀번호 입력
    tag_pw = driver.find_element(By.NAME, "M_PWD")
    tag_pw.click()
    pyperclip.copy(Config.USER_PW)
    tag_pw.send_keys(Keys.CONTROL, "v")
    time.sleep(random.uniform(0.4, 0.6))

    # 로그인 버튼 클릭
    login_btn = driver.find_element(By.CLASS_NAME, "login-button")
    login_btn.click()

    # ── 2단계 인증 대기 ──────────────────────────
    print("\n" + "=" * 55)
    print("  브라우저에서 2단계 인증을 직접 완료해주세요!")
    print("  완료 후 이 터미널에서 Enter 를 눌러주세요...")
    print("=" * 55)
    input()

    # ── 로그인 상태 확인 ─────────────────────────
    current_url = driver.current_url
    print(f"\n현재 URL: {current_url}")

    if "login" in current_url.lower():
        print("❌ 로그인이 완료되지 않은 것 같습니다. 다시 시도해주세요.")
        driver.quit()
        return

    # ── 쿠키 저장 ────────────────────────────────
    cookies   = driver.get_cookies()
    save_path = Config.COOKIE_FILE
    pickle.dump(cookies, open(save_path, "wb"))

    print(f"\n✅ 쿠키 {len(cookies)}개 저장 완료! → {save_path}")
    print("\n다음 명령어로 서버에 전송하세요:")
    print(f"  scp -i ssh-key.pem {save_path} ubuntu@[서버IP]:~/crawler/\n")

    driver.quit()


if __name__ == "__main__":
    save_cookies()
