"""
notify.py
Slack 웹훅을 통한 알림 모듈입니다.
크롤러 상태 변화, 오류, 2FA 인증 요청 등을 Slack으로 전송합니다.
"""
from __future__ import annotations

import datetime
import json
import traceback
from typing import Optional

import requests

from config import Config


def _send_slack(text: str) -> bool:
    """Slack 웹훅으로 메시지를 전송합니다."""
    url = Config.SLACK_WEBHOOK_URL
    if not url:
        return False

    try:
        resp = requests.post(
            url,
            json={"text": text},
            timeout=10,
        )
        return resp.status_code == 200
    except Exception as e:
        print(f"[알림] Slack 전송 실패: {e}")
        return False


def _now_str() -> str:
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


# ── 크롤러 상태 알림 ──────────────────────────────

def notify_crawler_started() -> None:
    _send_slack(
        f"<@alpha> :white_check_mark: *크롤러 시작*\n"
        f"시각: {_now_str()}\n"
        f"워킹타임: {Config.WORK_START_HOUR:02d}:00 ~ {Config.WORK_END_HOUR:02d}:00 | 간격: {Config.CRAWL_INTERVAL_MIN}분"
    )


def notify_crawler_stopped(reason: str = "정상 종료") -> None:
    _send_slack(
        f"<@alpha> :octagonal_sign: *크롤러 종료*\n"
        f"시각: {_now_str()}\n"
        f"사유: {reason}"
    )


# ── 크롤링 사이클 알림 ─────────────────────────────

def notify_cycle_complete(total: int, new: int, updated: int, elapsed: float) -> None:
    _send_slack(
        f":arrows_counterclockwise: *크롤링 사이클 완료*\n"
        f"시각: {_now_str()} | 소요: {elapsed:.0f}초\n"
        f"총 후보자: {total}명 | 신규: {new}명 | 상세 업데이트: {updated}명"
    )


def notify_cycle_error(error: Exception) -> None:
    tb = traceback.format_exception(type(error), error, error.__traceback__)
    tb_short = "".join(tb[-3:])[:500]
    _send_slack(
        f"<@alpha> :rotating_light: *크롤링 사이클 오류*\n"
        f"시각: {_now_str()}\n"
        f"오류: `{type(error).__name__}: {error}`\n"
        f"```{tb_short}```"
    )


# ── 로그인 / 2FA 알림 ─────────────────────────────

def notify_login_success() -> None:
    _send_slack(
        f":key: *로그인 성공*\n"
        f"시각: {_now_str()}"
    )


def notify_2fa_started() -> None:
    _send_slack(
        f"<@alpha> :lock: *2FA 인증 시작*\n"
        f"시각: {_now_str()}\n"
        f"GAS가 인증코드를 수집할 때까지 대기 중... (최대 {Config.OTP_TIMEOUT}초)"
    )


def notify_2fa_success() -> None:
    _send_slack(
        f":unlocked: *2FA 인증 완료*\n"
        f"시각: {_now_str()}"
    )


def notify_2fa_failed(reason: str) -> None:
    _send_slack(
        f"<@alpha> :x: *2FA 인증 실패*\n"
        f"시각: {_now_str()}\n"
        f"사유: {reason}\n"
        f"수동 확인이 필요할 수 있습니다."
    )


# ── 브라우저 알림 ──────────────────────────────────

def notify_browser_restart(reason: str = "일일 재시작") -> None:
    _send_slack(
        f":globe_with_meridians: *브라우저 재시작*\n"
        f"시각: {_now_str()}\n"
        f"사유: {reason}"
    )


def notify_browser_crash(error: Optional[Exception] = None) -> None:
    msg = f"<@alpha> :warning: *브라우저 크래시*\n시각: {_now_str()}"
    if error:
        msg += f"\n오류: `{error}`"
    _send_slack(msg)
