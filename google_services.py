"""
google_services.py
Google Sheets 읽기/쓰기 및 Google Drive 파일 업로드를 담당합니다.
"""

from __future__ import annotations
import time
from typing import Optional, Tuple

import gspread
import pandas as pd
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

from config import Config

# Google API 공통 스코프
_SCOPES = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive",
]


def _get_credentials() -> Credentials:
    return Credentials.from_service_account_file(Config.JSON_FILE_NAME, scopes=_SCOPES)


# ──────────────────────────────────────────────
# Google Sheets
# ──────────────────────────────────────────────

def open_google_sheet(
    spreadsheet_url: str = Config.TARGET_URL,
    sheet_name: str      = Config.SHEET_NAME,
) -> Tuple[Optional[gspread.Worksheet], Optional[pd.DataFrame]]:
    """
    구글 시트에 연결하고 (worksheet, DataFrame) 튜플을 반환합니다.
    실패 시 (None, None) 반환.
    """
    print("[시트] 구글 시트 연동을 시도합니다...")

    try:
        gc        = gspread.authorize(_get_credentials())
        doc       = gc.open_by_url(spreadsheet_url)
        worksheet = doc.worksheet(sheet_name)

        records = worksheet.get_all_values()

        if not records:
            df_existing = pd.DataFrame()
        else:
            df_existing = pd.DataFrame(records[1:], columns=records[0])

        print(f"[시트] ✅ 연동 성공 (기존 데이터 {len(df_existing)}행)")
        return worksheet, df_existing

    except Exception as e:
        print(f"[시트] ❌ 구글 시트 접근 오류: {e}")
        return None, None


def append_dataframe_to_gsheet(
    worksheet: gspread.Worksheet,
    df: pd.DataFrame,
    chunk_size: int = 500,
) -> None:
    """
    DataFrame을 구글 시트 마지막 행 아래에 청크 단위로 추가합니다.
    """
    df   = df.fillna("")
    data = df.values.tolist()

    print(f"[시트] 총 {len(data)}건을 업로드합니다...")

    for i in range(0, len(data), chunk_size):
        chunk = data[i : i + chunk_size]
        worksheet.append_rows(chunk)
        time.sleep(1)
        print(f"  - {i + len(chunk)}건 완료...")

    print("[시트] ✅ 업로드 완료!")


def batch_update_cells(
    worksheet: gspread.Worksheet,
    cells: list[gspread.Cell],
) -> None:
    """gspread Cell 리스트를 한 번에 업데이트합니다."""
    worksheet.update_cells(cells)


# ──────────────────────────────────────────────
# Google Drive
# ──────────────────────────────────────────────

def upload_file_to_drive(local_file_path: str, file_name: str) -> str | None:
    """
    로컬 파일을 Google Drive 지정 폴더에 업로드하고 file_id를 반환합니다.
    실패 시 None 반환.
    """
    try:
        drive_service = build("drive", "v3", credentials=_get_credentials())

        file_metadata = {
            "name":    file_name,
            "parents": [Config.DRIVE_FOLDER_ID],
        }
        media = MediaFileUpload(local_file_path, resumable=True)

        uploaded = (
            drive_service.files()
            .create(body=file_metadata, media_body=media, fields="id")
            .execute()
        )
        return uploaded.get("id")

    except Exception as e:
        print(f"[드라이브] ❌ 업로드 오류: {e}")
        return None


def make_drive_url(file_id: str) -> str:
    """Drive file_id → 공유 가능한 URL 변환"""
    return f"https://drive.google.com/file/d/{file_id}/view"
