"""
pipeline.py
크롤링 데이터의 가공·중복제거·Google Sheets 동기화를 담당합니다.

1. process_and_upload_candidates  : 후보자 기본 정보 → 시트 초기 적재
2. update_empty_resumes_in_sheet  : 연락처 미수집 후보자 → 상세 정보 업데이트
"""

import datetime
import time

import gspread
import pandas as pd
from selenium import webdriver

from config import Config
from google_services import open_google_sheet, append_dataframe_to_gsheet, batch_update_cells
from scraper import extract_resume_details, extract_offer_details


# ──────────────────────────────────────────────
# 1. 후보자 기본 정보 초기 적재
# ──────────────────────────────────────────────

def process_and_upload_candidates(df_new: pd.DataFrame) -> None:
    """
    스크래핑된 후보자 기본 정보를 정제·중복 제거 후 Google Sheets에 적재합니다.
    """
    if df_new.empty:
        print("[파이프라인] 새로운 크롤링 데이터가 없습니다.")
        return

    worksheet, df_existing = open_google_sheet()
    if worksheet is None:
        return

    # ── 컬럼 정렬 ──────────────────────────────
    df_upload = df_new.copy()
    df_upload["수집일시"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    col_order = ["수집일시", "담당자", "이름", "성별", "나이", "최종학력", "총경력", "이력서URL"]
    for col in col_order:
        if col not in df_upload.columns:
            df_upload[col] = ""
    df_upload = df_upload[col_order]

    # ── 중복 제거 ───────────────────────────────
    if not df_existing.empty and "이력서URL" in df_existing.columns:
        existing_urls    = set(df_existing["이력서URL"].tolist())
        df_final         = df_upload[~df_upload["이력서URL"].isin(existing_urls)]
        duplicates_count = len(df_upload) - len(df_final)
        print(f"[파이프라인] 중복 {duplicates_count}건 제외")
    else:
        df_final = df_upload

    # ── 업로드 ──────────────────────────────────
    if not df_final.empty:
        append_dataframe_to_gsheet(worksheet, df_final)
        print(f"[파이프라인] 🎉 {len(df_final)}건 신규 적재 완료!")
    else:
        print("[파이프라인] 모두 중복 데이터입니다. 추가 없음.")


# ──────────────────────────────────────────────
# 2. 상세 정보 업데이트 (연락처 미수집 행 대상)
# ──────────────────────────────────────────────

def update_empty_resumes_in_sheet(driver: webdriver.Chrome) -> None:
    """
    Google Sheets에서 '휴대전화번호'가 비어있는 행을 찾아
    이력서 상세 정보(OCR·PDF·제안정보)를 수집하고 시트를 업데이트합니다.
    
    멱등성 보장: 중단 후 재실행 시 미완료 행부터 이어서 처리합니다.
    """
    print("[파이프라인] 📊 업데이트 대상 탐색을 시작합니다...")

    worksheet, _ = open_google_sheet()
    if not worksheet:
        return

    all_values = worksheet.get_all_values()
    if len(all_values) < 2:
        print("[파이프라인] 시트에 데이터가 없습니다.")
        return

    headers = all_values[0]

    # ── 컬럼 인덱스 매핑 ────────────────────────
    required_cols = [
        "이름", "이력서URL", "휴대전화번호", "이메일",
        "첨부파일1", "첨부파일2", "첨부파일3",
        "제안URL", "제안포지션", "제안일자", "이력서파일URL",
    ]
    try:
        col_idx = {col: headers.index(col) + 1 for col in required_cols}
    except ValueError as e:
        print(f"[파이프라인] ❌ 필수 컬럼 누락: {e}")
        return

    update_count = 0

    for i, row_data in enumerate(all_values[1:], start=2):  # start=2: 실제 시트 행 번호
        def _cell(col: str) -> str:
            idx = col_idx[col] - 1
            return row_data[idx].strip() if len(row_data) > idx else ""

        name       = _cell("이름")
        phone      = _cell("휴대전화번호")
        resume_url = _cell("이력서URL")

        # 이름이 있고 아직 연락처가 없는 행만 처리
        if not name or phone:
            continue
        if not resume_url:
            continue

        try:
            # 이력서 상세 정보 + PDF 수집
            details = extract_resume_details(driver, resume_url, name)

            # 제안 상세 정보 수집
            offer_pos, offer_date = "", ""
            if details["제안URL"]:
                offer = extract_offer_details(driver, details["제안URL"])
                offer_pos  = offer["제안포지션"]
                offer_date = offer["제안일자"]

            # 셀 일괄 업데이트
            cells_to_update = [
                gspread.Cell(row=i, col=col_idx["휴대전화번호"], value=details["휴대전화번호"]),
                gspread.Cell(row=i, col=col_idx["이메일"],       value=details["이메일"]),
                gspread.Cell(row=i, col=col_idx["첨부파일1"],    value=details["첨부파일1"]),
                gspread.Cell(row=i, col=col_idx["첨부파일2"],    value=details["첨부파일2"]),
                gspread.Cell(row=i, col=col_idx["첨부파일3"],    value=details["첨부파일3"]),
                gspread.Cell(row=i, col=col_idx["제안URL"],      value=details["제안URL"]),
                gspread.Cell(row=i, col=col_idx["제안포지션"],   value=offer_pos),
                gspread.Cell(row=i, col=col_idx["제안일자"],     value=offer_date),
                gspread.Cell(row=i, col=col_idx["이력서파일URL"], value=details["이력서파일URL"]),
            ]
            batch_update_cells(worksheet, cells_to_update)

            print(f"[파이프라인] ✅ [{name}] 업데이트 완료\n")
            update_count += 1
            time.sleep(1.5)

        except Exception as e:
            print(f"[파이프라인] ❌ [{name}] 처리 중 오류 (스킵): {e}")
            continue

    print(f"\n[파이프라인] 🎉 완료 — 총 {update_count}명 업데이트")
