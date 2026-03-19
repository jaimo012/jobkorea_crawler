"""
driver.py
Chrome WebDriver 세팅 · ID/PW 로그인 · 2FA 자동 처리를 담당합니다.
(Python 3.8 호환성을 위해 __future__ import 추가)

2FA 흐름:
    1. ID/PW 로그인 후 2FA 페이지 감지
    2. 이름/이메일 입력 → 인증코드 발송 요청
    3. GAS가 지메일에서 자동 수집한 인증코드를 '2차인증' 시트에서 폴링
       (컬럼: 수신일시 | 메시지ID | 인증코드)
    4. 로그인 시점 이후에 수신된 마지막 인증코드를 사용
    5. 인증코드를 자동 입력하여 로그인 완료
"""
from __future__ import annotations

import datetime
import random
import time

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

from config import Config


# ──────────────────────────────────────────────
# 브라우저 초기화
# ──────────────────────────────────────────────

def setup_chrome_driver(headless: bool = True) -> webdriver.Chrome:
    print("[드라이버] 크롬 브라우저를 초기화합니다...")
    options = Options()

    if headless:
        options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-extensions")
        options.add_argument("--blink-settings=imagesEnabled=false")
        options.add_argument("--disable-software-rasterizer")
        options.add_argument("--disable-background-networking")
        options.add_argument("--disable-default-apps")
        options.add_argument("--disable-translate")
        options.add_argument("--js-flags=--max-old-space-size=256")

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
    driver.set_page_load_timeout(120)

    print("[드라이버] 크롬 브라우저 준비 완료")
    return driver


# ──────────────────────────────────────────────
# 로그인 상태 확인
# ──────────────────────────────────────────────

def is_logged_in(driver: webdriver.Chrome) -> bool:
    """실제 권한이 필요한 페이지로 이동하여 로그인 상태를 확인합니다."""
    try:
        test_url = Config.ACCEPT_URL.replace("PAGE_NUM", "1")
        try:
            driver.get(test_url)
        except Exception:
            pass  # 타임아웃이 발생해도 URL은 확인 가능
        time.sleep(3)
        url = driver.current_url.lower()
        return "login" not in url and "twofactorauth" not in url
    except Exception:
        return False


# ──────────────────────────────────────────────
# 통합 로그인 (ID/PW + 2FA 자동 인증)
# ──────────────────────────────────────────────

def ensure_login(driver: webdriver.Chrome) -> webdriver.Chrome:
    """
    로그인을 보장합니다. 순서:
        1. 이미 로그인 상태면 패스
        2. ID/PW + 2FA 자동 인증
    성공 시 driver 반환, 실패 시 예외를 발생시킵니다.
    """
    # 1) 이미 로그인 상태 확인
    if is_logged_in(driver):
        print("[로그인] 기존 세션 유효 — 로그인 생략")
        return driver

    # 2) ID/PW 로그인 + 2FA
    print("[로그인] ID/PW 로그인을 시도합니다...")
    if _login_with_credentials(driver):
        print("[로그인] ✅ 로그인 성공!")
        return driver

    raise RuntimeError("[로그인] 로그인에 실패했습니다.")


# ──────────────────────────────────────────────
# ID/PW 로그인 + 2FA 자동 처리
# ──────────────────────────────────────────────

def _login_with_credentials(driver: webdriver.Chrome) -> bool:
    """
    ID/PW로 로그인 후, 2FA가 나타나면 Google Sheets를 통해 자동 인증합니다.
    """
    try:
        driver.get(Config.LOGIN_URL)
    except Exception:
        pass  # 타임아웃이 발생해도 페이지는 로드됨
    time.sleep(random.uniform(2.0, 3.0))

    # 기업회원 탭 클릭
    try:
        corp_tab = driver.find_element(By.CSS_SELECTOR, 'a[data-m-type="Co"]')
        corp_tab.click()
        time.sleep(random.uniform(0.5, 0.8))
    except Exception:
        pass

    # 아이디 입력
    tag_id = driver.find_element(By.NAME, "M_ID")
    tag_id.clear()
    tag_id.send_keys(Config.USER_ID)
    time.sleep(random.uniform(0.3, 0.5))

    # 비밀번호 입력
    tag_pw = driver.find_element(By.NAME, "M_PWD")
    tag_pw.clear()
    tag_pw.send_keys(Config.USER_PW)
    time.sleep(random.uniform(0.3, 0.5))

    # 로그인 버튼 클릭 (JavaScript로 실행하여 타임아웃 방지)
    login_btn = driver.find_element(By.CLASS_NAME, "login-button")
    driver.execute_script("arguments[0].click();", login_btn)
    time.sleep(5)

    # 로그인 직후 URL 확인
    url = driver.current_url.lower()
    if "login" in url:
        print("[로그인] ❌ ID/PW 로그인 실패 — 아이디/비밀번호를 확인하세요.")
        return False

    # ── 로그인 직후 2FA 감지 ──────────────────────
    if _is_2fa_page(driver):
        print("[2FA] 2단계 인증이 필요합니다. Google Sheets에서 인증코드를 가져옵니다...")
        return _handle_2fa(driver)

    # ── 보호된 페이지로 이동하여 2FA 추가 감지 ─────
    # (잡코리아는 로그인 직후가 아닌 보호된 페이지 접근 시 2FA를 요구하는 경우가 있음)
    print("[로그인] ID/PW 로그인 성공 — 보호 페이지 접근 테스트...")
    test_url = Config.ACCEPT_URL.replace("PAGE_NUM", "1")
    try:
        driver.get(test_url)
    except Exception:
        pass
    time.sleep(3)

    url = driver.current_url.lower()
    if _is_2fa_page(driver) or "twofactorauth" in url:
        print("[2FA] 보호 페이지 접근 시 2단계 인증 감지! Google Sheets에서 인증코드를 가져옵니다...")
        return _handle_2fa(driver)

    if "login" not in url and "twofactorauth" not in url:
        return True

    print("[로그인] ❌ 로그인 후에도 접근 불가 — 알 수 없는 상태입니다.")
    return False


def _is_2fa_page(driver: webdriver.Chrome) -> bool:
    """
    현재 페이지가 2FA 인증 페이지인지 판별합니다.
    ※ 잡코리아 2FA 페이지의 실제 구조에 맞게 아래 조건을 조정하세요.
    """
    url = driver.current_url.lower()

    # URL 기반 판별
    if any(kw in url for kw in ("twofactorauth", "auth", "verify", "cert", "2fa", "otp")):
        return True

    # 페이지 내 인증코드 입력란 존재 여부
    for selector in ['input[name="certNo"]', 'input[name="authNo"]']:
        try:
            driver.find_element(By.CSS_SELECTOR, selector)
            return True
        except Exception:
            pass

    # 페이지 텍스트에 인증 관련 키워드 포함 여부
    try:
        page_text = driver.find_element(By.TAG_NAME, "body").text
        if any(kw in page_text for kw in ("인증번호", "인증코드", "본인인증")):
            return True
    except Exception:
        pass

    return False


# ──────────────────────────────────────────────
# 2FA 처리: Google Sheets OTP 폴링
# ──────────────────────────────────────────────

def _handle_2fa(driver: webdriver.Chrome) -> bool:
    """
    2FA 흐름:
        1. 이름/이메일 입력 → 인증코드 발송 요청
        2. GAS가 지메일에서 자동 수집한 '2차인증' 시트를 폴링
        3. 로그인 시점 이후에 수신된 마지막 인증코드를 가져옴
        4. 인증코드를 페이지에 입력하고 인증 완료
    """
    # ── Step 1. 이름/이메일 입력 + 인증코드 발송 요청 ──
    if not _fill_2fa_identity(driver):
        print("[2FA] ❌ 이름/이메일 입력 또는 인증코드 발송 요청 실패")
        return False

    # 인증코드 발송 시점 기록 (이메일 발송 직후)
    login_time = datetime.datetime.now()
    print(f"[2FA] 인증코드 발송 요청 완료 — 발송 시점: {login_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"[2FA] GAS가 지메일에서 인증코드를 수집할 때까지 대기합니다... (제한시간: {Config.OTP_TIMEOUT}초)")

    # ── Step 2. OTP 시트에서 인증코드 폴링 ──
    otp_ws = _get_otp_worksheet()
    if otp_ws is None:
        print("[2FA] ❌ OTP 시트를 열 수 없습니다.")
        return False

    otp_code = _poll_otp_from_sheet(otp_ws, login_time)

    if not otp_code:
        print("[2FA] ❌ 인증코드 수신 시간이 초과되었습니다.")
        return False

    print(f"[2FA] 인증코드 수신: {otp_code}")

    # ── Step 3. 인증코드 입력 ──
    if not _submit_otp(driver, otp_code):
        return False

    print("[2FA] ✅ 2단계 인증 완료!")
    return True


def _fill_2fa_identity(driver: webdriver.Chrome) -> bool:
    """
    잡코리아 2FA 페이지에서 이름과 이메일을 입력하고 인증코드 발송 버튼을 누릅니다.

    잡코리아 2FA 페이지 구조:
        - input#UserName  : 이름 입력
        - input#UserEmail : 이메일 전체 주소 입력 (예: alpha@kmong.com)
        - button#btnSendCertCorpDomain : 인증번호 발송 (이름/이메일 입력 후 enabled)
    """
    try:
        print(f"[2FA] 이름({Config.AUTH_NAME}) / 이메일({Config.AUTH_EMAIL}) 입력 중...")

        # 이름 입력
        name_input = driver.find_element(By.ID, "UserName")
        name_input.clear()
        name_input.send_keys(Config.AUTH_NAME)
        time.sleep(0.5)
        print("[2FA] 이름 입력 완료")

        # 이메일 입력 (아이디 부분만 — 도메인은 corpDomain hidden 필드에 자동 세팅)
        email_id = Config.AUTH_EMAIL.split("@")[0]  # alpha@kmong.com → alpha
        email_input = driver.find_element(By.ID, "UserEmail")
        email_input.clear()
        email_input.send_keys(email_id)
        time.sleep(0.5)
        print(f"[2FA] 이메일 아이디 입력 완료: {email_id}")

        # disabled 해제 대기 후 인증번호 발송 버튼 클릭
        time.sleep(1)
        send_btn = driver.find_element(By.ID, "btnSendCertCorpDomain")

        # disabled 속성 제거를 위해 JavaScript로 클릭
        if send_btn.get_attribute("disabled"):
            print("[2FA] 발송 버튼이 비활성화 상태 — JavaScript로 활성화 시도...")
            driver.execute_script(
                "arguments[0].disabled = false; arguments[0].classList.remove('disabled');",
                send_btn,
            )
            time.sleep(0.5)

        send_btn.click()
        print("[2FA] 인증번호 발송 버튼 클릭 완료")
        time.sleep(3)

        return True

    except Exception as e:
        print(f"[2FA] ❌ 이름/이메일 입력 오류: {e}")
        return False


def _get_otp_worksheet():
    """
    GAS가 인증코드를 자동 수집하는 '2차인증' 시트를 엽니다.
    시트 URL: Config.OTP_SHEET_URL / 탭명: Config.OTP_SHEET_NAME
    컬럼: 수신일시 | 메시지ID | 인증코드
    """
    try:
        import gspread
        from google.oauth2.service_account import Credentials

        creds = Credentials.from_service_account_file(
            Config.JSON_FILE_NAME,
            scopes=[
                "https://spreadsheets.google.com/feeds",
                "https://www.googleapis.com/auth/drive",
            ],
        )
        gc  = gspread.authorize(creds)
        doc = gc.open_by_url(Config.OTP_SHEET_URL)
        otp_ws = doc.worksheet(Config.OTP_SHEET_NAME)
        return otp_ws

    except Exception as e:
        print(f"[2FA] OTP 시트 접근 오류: {e}")
        return None


def _poll_otp_from_sheet(otp_ws, login_time: datetime.datetime) -> str:
    """
    '2차인증' 시트를 폴링하여 login_time 이후에 수신된 마지막 인증코드를 가져옵니다.

    시트 구조 (GAS가 자동 채움):
        A열: 수신일시 (예: "2026-03-18 09:23:45")
        B열: 메시지ID
        C열: 인증코드

    login_time 이후의 행 중 가장 마지막 행의 인증코드를 반환합니다.
    """
    elapsed = 0

    while elapsed < Config.OTP_TIMEOUT:
        time.sleep(Config.OTP_POLL_INTERVAL)
        elapsed += Config.OTP_POLL_INTERVAL

        try:
            all_rows = otp_ws.get_all_values()
            data_rows = all_rows[1:]  # 헤더 제외

            if elapsed <= Config.OTP_POLL_INTERVAL:
                # 첫 폴링 시 시트 상태 출력
                print(f"[2FA] 시트 행 수: {len(data_rows)} (login_time: {login_time.strftime('%Y-%m-%d %H:%M:%S')})")
                if data_rows:
                    last_row = data_rows[-1]
                    print(f"[2FA] 마지막 행: {last_row}")

            # 뒤에서부터 탐색 (최신 행 우선)
            for row in reversed(data_rows):
                if len(row) < 3:
                    continue

                recv_time_str = row[0].strip()
                otp_code      = row[2].strip()

                if not recv_time_str or not otp_code:
                    continue

                # 수신일시 파싱
                recv_time = None
                for fmt in ("%Y-%m-%d %H:%M:%S", "%Y/%m/%d %H:%M:%S"):
                    try:
                        recv_time = datetime.datetime.strptime(recv_time_str, fmt)
                        break
                    except ValueError:
                        continue

                if recv_time is None:
                    print(f"[2FA] 날짜 파싱 실패: '{recv_time_str}'")
                    continue

                # 로그인 시점 이후의 인증코드만 사용
                if recv_time >= login_time:
                    return otp_code

        except Exception as e:
            print(f"[2FA] 시트 폴링 오류 (재시도): {e}")

        remaining = Config.OTP_TIMEOUT - elapsed
        if remaining > 0 and elapsed % 30 < Config.OTP_POLL_INTERVAL:
            print(f"[2FA] 인증코드 대기 중... (남은 시간: {remaining}초)")

    return ""


def _submit_otp(driver: webdriver.Chrome, otp_code: str) -> bool:
    """
    잡코리아 2FA 페이지에서 인증코드를 입력하고 인증 버튼을 누릅니다.

    잡코리아 2FA 페이지 구조:
        - input#certNumCorpDomain : 인증번호 숫자 6자리 입력
        - button#btnCorpDomainCheckCert : 인증 버튼
    """
    try:
        otp_input = driver.find_element(By.ID, "certNumCorpDomain")
        otp_input.clear()
        otp_input.send_keys(otp_code)
        time.sleep(0.5)
        print(f"[2FA] 인증코드 입력 완료: {otp_code}")

        submit_btn = driver.find_element(By.ID, "btnCorpDomainCheckCert")
        submit_btn.click()
        print("[2FA] 인증 버튼 클릭 완료")
        time.sleep(3)

        url = driver.current_url.lower()
        if "login" not in url and "twofactorauth" not in url:
            return True

        print("[2FA] ❌ 인증코드 입력 후에도 인증 페이지에 남아있습니다.")
        return False

    except Exception as e:
        print(f"[2FA] ❌ 인증코드 제출 오류: {e}")
        return False


