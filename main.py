"""
main.py
서버(Oracle Cloud)에서 Cron으로 실행되는 메인 진입점입니다.

실행 흐름:
    1. Chrome WebDriver 초기화 (헤드리스)
    2. 쿠키로 잡코리아 로그인
    3. 수락 후보자 목록 수집 → Google Sheets 초기 적재
    4. 연락처 미수집 후보자 → 상세 정보 수집 및 시트 업데이트
    5. 드라이버 종료
"""

import sys

from driver import setup_chrome_driver, login_with_cookie
from pipeline import process_and_upload_candidates, update_empty_resumes_in_sheet
from scraper import scrape_all_accepted_candidates


def main() -> None:
    driver = None

    try:
        # ── Step 1. 드라이버 초기화 ──────────────
        driver = setup_chrome_driver(headless=True)

        # ── Step 2. 쿠키 로그인 ──────────────────
        driver = login_with_cookie(driver)
        if driver is None:
            print("[메인] ❌ 로그인 실패로 종료합니다.")
            sys.exit(1)

        # ── Step 3. 후보자 목록 수집 + 시트 적재 ─
        driver, df_new = scrape_all_accepted_candidates(driver)
        process_and_upload_candidates(df_new)

        # ── Step 4. 상세 정보 업데이트 ───────────
        update_empty_resumes_in_sheet(driver)

    except Exception as e:
        print(f"[메인] ❌ 예상치 못한 오류 발생: {e}")
        raise

    finally:
        if driver:
            driver.quit()
            print("[메인] 브라우저 종료 완료")


if __name__ == "__main__":
    main()
