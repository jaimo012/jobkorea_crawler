"""
main.py
상시 실행 스케줄러 — 브라우저를 유지한 채로 워킹타임 내 주기적 크롤링을 수행합니다.

실행 흐름:
    1. Chrome WebDriver 초기화 (1회)
    2. 로그인 보장 (ID/PW + 2FA 자동)
    3. 워킹타임(08:00~18:00) 동안 매 10분마다 크롤링 사이클 실행
    4. 매일 BROWSER_RESTART_HOUR 에 브라우저 재시작
    5. 워킹타임 외에는 대기 (브라우저 세션은 유지)
"""
from __future__ import annotations

import datetime
import signal
import sys
import time
import traceback

from config import Config
from driver import setup_chrome_driver, ensure_login, is_logged_in
from notify import (
    notify_crawler_started, notify_crawler_stopped,
    notify_cycle_complete, notify_cycle_error,
    notify_browser_restart, notify_browser_crash,
)
from pipeline import process_and_upload_candidates, update_empty_resumes_in_sheet
from scraper import scrape_all_accepted_candidates


# ──────────────────────────────────────────────
# 전역 상태
# ──────────────────────────────────────────────
_driver = None
_last_browser_restart_date = None


def _now():
    return datetime.datetime.now()


# ──────────────────────────────────────────────
# 브라우저 관리
# ──────────────────────────────────────────────

def _init_browser(reason: str = "초기화") -> None:
    """브라우저를 (재)시작하고 로그인합니다."""
    global _driver, _last_browser_restart_date

    if _driver:
        try:
            _driver.quit()
        except Exception:
            pass

    _driver = setup_chrome_driver(headless=True)
    _driver = ensure_login(_driver)
    _last_browser_restart_date = _now().date()
    print(f"[스케줄러] 브라우저 초기화 완료 ({_now().strftime('%H:%M:%S')})")


def _should_restart_browser() -> bool:
    """하루에 한 번 BROWSER_RESTART_HOUR 에 브라우저를 재시작할지 판단합니다."""
    now = _now()
    if _last_browser_restart_date == now.date():
        return False
    return now.hour >= Config.BROWSER_RESTART_HOUR


def _ensure_browser_alive() -> None:
    """브라우저 세션이 유효한지 확인하고, 필요하면 재시작합니다."""
    global _driver

    # 일일 재시작
    if _should_restart_browser():
        print("[스케줄러] 일일 브라우저 재시작...")
        notify_browser_restart("일일 재시작")
        _init_browser(reason="일일 재시작")
        return

    # 세션 유효성 확인
    try:
        if not is_logged_in(_driver):
            print("[스케줄러] 로그인 세션 만료 — 재로그인 시도...")
            _driver = ensure_login(_driver)
    except Exception as e:
        print("[스케줄러] 브라우저 연결 끊김 — 재시작...")
        notify_browser_crash(e)
        _init_browser(reason="브라우저 크래시 복구")


# ──────────────────────────────────────────────
# 크롤링 사이클
# ──────────────────────────────────────────────

def _run_crawl_cycle() -> None:
    """한 번의 크롤링 사이클을 실행합니다."""
    global _driver

    cycle_start = _now()
    print(f"\n{'='*55}")
    print(f"  크롤링 사이클 시작: {cycle_start.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*55}")

    try:
        _ensure_browser_alive()

        # 후보자 목록 수집 + 시트 적재
        _driver, df_new = scrape_all_accepted_candidates(_driver)
        new_count = len(df_new) if not df_new.empty else 0
        process_and_upload_candidates(df_new)

        # 상세 정보 업데이트
        updated_count = update_empty_resumes_in_sheet(_driver)

        elapsed = (_now() - cycle_start).total_seconds()
        print(f"\n[스케줄러] 사이클 완료 (소요: {elapsed:.0f}초)")
        notify_cycle_complete(new_count, new_count, updated_count, elapsed)

    except Exception as e:
        print(f"[스케줄러] ❌ 사이클 중 오류: {e}")
        traceback.print_exc()
        notify_cycle_error(e)
        # 오류 발생 시 다음 사이클에서 브라우저 재시작을 유도
        try:
            if _driver:
                _driver.quit()
        except Exception:
            pass
        _driver = None


# ──────────────────────────────────────────────
# 워킹타임 체크
# ──────────────────────────────────────────────

def _is_working_time() -> bool:
    """현재 시각이 워킹타임(WORK_START_HOUR ~ WORK_END_HOUR) 내인지 확인합니다."""
    hour = _now().hour
    return Config.WORK_START_HOUR <= hour < Config.WORK_END_HOUR


def _seconds_until_next_work_start() -> int:
    """다음 워킹타임 시작까지 남은 초를 계산합니다."""
    now = _now()
    if now.hour < Config.WORK_START_HOUR:
        next_start = now.replace(
            hour=Config.WORK_START_HOUR, minute=0, second=0, microsecond=0
        )
    else:
        next_start = (now + datetime.timedelta(days=1)).replace(
            hour=Config.WORK_START_HOUR, minute=0, second=0, microsecond=0
        )
    return int((next_start - now).total_seconds())


# ──────────────────────────────────────────────
# 메인 스케줄러 루프
# ──────────────────────────────────────────────

def _graceful_shutdown(signum, frame):
    """Ctrl+C / SIGTERM 시 브라우저를 정리하고 종료합니다."""
    global _driver
    print("\n[스케줄러] 종료 신호 수신 — 정리 중...")
    notify_crawler_stopped("종료 신호 수신 (SIGTERM/SIGINT)")
    if _driver:
        try:
            _driver.quit()
        except Exception:
            pass
    print("[스케줄러] 종료 완료")
    sys.exit(0)


def main() -> None:
    global _driver

    signal.signal(signal.SIGINT, _graceful_shutdown)
    signal.signal(signal.SIGTERM, _graceful_shutdown)

    print(f"[스케줄러] 잡코리아 크롤러 시작")
    print(f"  - 크롤링 간격 : {Config.CRAWL_INTERVAL_MIN}분")
    print(f"  - 워킹타임    : {Config.WORK_START_HOUR:02d}:00 ~ {Config.WORK_END_HOUR:02d}:00")
    print(f"  - 브라우저 재시작: 매일 {Config.BROWSER_RESTART_HOUR:02d}:00")
    print(f"  - Slack 알림  : {'활성' if Config.SLACK_WEBHOOK_URL else '비활성'}\n")
    notify_crawler_started()

    while True:
        # ── 워킹타임 외: 대기 ─────────────────────
        if not _is_working_time():
            wait_sec = _seconds_until_next_work_start()
            wait_min = wait_sec // 60
            print(
                f"[스케줄러] 워킹타임 외 — "
                f"다음 시작까지 {wait_min}분 대기 "
                f"({_now().strftime('%H:%M')})"
            )

            # 대기 중 브라우저 종료 (리소스 절약)
            if _driver:
                try:
                    _driver.quit()
                except Exception:
                    pass
                _driver = None
                print("[스케줄러] 대기 모드 — 브라우저 종료")

            # 1분 단위로 체크하며 대기
            while not _is_working_time():
                time.sleep(60)

            print(f"[스케줄러] 워킹타임 시작! ({_now().strftime('%H:%M')})")

        # ── 브라우저 초기화 (필요 시) ─────────────
        if _driver is None:
            try:
                _init_browser(reason="워킹타임 시작")
            except Exception as e:
                print(f"[스케줄러] ❌ 브라우저 초기화 실패: {e}")
                traceback.print_exc()
                notify_browser_crash(e)
                print("[스케줄러] 60초 후 재시도...")
                time.sleep(60)
                continue

        # ── 크롤링 실행 ──────────────────────────
        _run_crawl_cycle()

        # ── 다음 사이클까지 대기 ──────────────────
        if _is_working_time():
            print(
                f"[스케줄러] 다음 크롤링: {Config.CRAWL_INTERVAL_MIN}분 후 "
                f"({(_now() + datetime.timedelta(minutes=Config.CRAWL_INTERVAL_MIN)).strftime('%H:%M')})"
            )
            waited = 0
            interval_sec = Config.CRAWL_INTERVAL_MIN * 60
            while waited < interval_sec:
                time.sleep(min(60, interval_sec - waited))
                waited += 60
                if not _is_working_time():
                    break


if __name__ == "__main__":
    main()
