"""
scraper.py
잡코리아 크롤링 핵심 로직을 담당합니다.

1. scrape_all_accepted_candidates  : 수락 후보자 목록 전체 수집
2. extract_resume_details          : 개별 이력서 상세 정보 + PDF 저장
3. extract_offer_details           : 제안 상세 페이지(포지션명·발송일) 추출
4. extract_portfolio_links         : 포트폴리오·첨부파일 링크 최대 3건 추출
5. save_page_as_pdf                : CDP 기반 PDF 저장
"""

from __future__ import annotations
import base64
import datetime
import os
import random
import re
import time
from typing import Tuple, List, Dict # 구버전 호환용

import pandas as pd
from bs4 import BeautifulSoup
from selenium import webdriver

from config import Config
from google_services import upload_file_to_drive, make_drive_url
from ocr import extract_text_from_base64

from utils_debug import save_debug_snapshot


# ──────────────────────────────────────────────
# 1. 수락 후보자 목록 전체 수집
# ──────────────────────────────────────────────

def scrape_all_accepted_candidates(
    driver: webdriver.Chrome,
    max_pages: int = 100,
) -> tuple[webdriver.Chrome, pd.DataFrame]:
    """
    수락 후보자 목록 페이지를 순회하며 기본 정보를 DataFrame으로 반환합니다.

    Args:
        max_pages: 안전장치용 최대 페이지 수 (기본값 100)
    """
    all_data: list[dict] = []
    page_num = 1

    print("\n[크롤러] 🚀 전체 페이지 데이터 수집을 시작합니다...")

    while page_num <= max_pages:
        target_url = Config.ACCEPT_URL.replace("PAGE_NUM", str(page_num))
        print(f"\n[크롤러] 👉 {page_num}페이지 이동 중...")
        driver.get(target_url)
        time.sleep(random.uniform(3.0, 5.0))

        soup = BeautifulSoup(driver.page_source, "html.parser")

        # ── 페이지 유효성 검사 ──────────────────
        current_page_tag = soup.find("span", class_="now")
        if not current_page_tag:
            # [추가] 페이지를 못 찾으면 즉시 사진을 찍습니다!
            print(f"[크롤러] 🛑 페이지 번호를 찾을 수 없습니다. (현재 URL: {driver.current_url})")
            save_debug_snapshot(driver, f"page_error_p{page_num}")
            break

        if current_page_tag.text.strip() != str(page_num):
            print(
                f"[크롤러] 🛑 마지막 페이지 도달 "
                f"(확인된 마지막 페이지: {current_page_tag.text.strip()})"
            )
            break

        candidate_rows = soup.find_all("tr", class_="title-case")
        if not candidate_rows:
            print(f"[크롤러] 🛑 {page_num}페이지에 데이터가 없어 종료합니다.")
            break

        print(f"[크롤러] ✅ {page_num}페이지 — {len(candidate_rows)}명 발견")

        # ── 행(row) 파싱 ────────────────────────
        for row in candidate_rows:
            try:
                name_tag  = row.find("div", class_="name")
                name      = name_tag.text.strip() if name_tag else "이름없음"

                line_list = row.find("ul", class_="line-list")
                gender, age = "", ""
                if line_list:
                    li_tags = line_list.find_all("li")
                    gender  = li_tags[0].text.strip() if len(li_tags) > 0 else ""
                    age     = li_tags[1].text.strip() if len(li_tags) > 1 else ""

                td_tags = row.find_all("td")

                edu_tag    = td_tags[3].find("div", class_="strong") if len(td_tags) > 3 else None
                education  = edu_tag.text.strip() if edu_tag else ""

                exp_tag    = td_tags[4].find("div", class_="strong") if len(td_tags) > 4 else None
                experience = exp_tag.text.strip() if exp_tag else ""

                mgr_tag  = td_tags[5].find("div", class_="read") if len(td_tags) > 5 else None
                manager  = mgr_tag.text.strip() if mgr_tag else ""

                r_no       = row.get("data-r-no", "")
                co_pass_no = row.get("data-posg-no", "")
                resume_url = (
                    f"https://www.jobkorea.co.kr/corp/person/resumedb"
                    f"?R_No={r_no}&Pass_R_No=0&Co_Pass_No={co_pass_no}"
                )

                all_data.append({
                    "이름":     name,
                    "성별":     gender,
                    "나이":     age,
                    "최종학력": education,
                    "총경력":   experience,
                    "담당자":   manager,
                    "이력서URL": resume_url,
                })

            except Exception as e:
                print(f"[크롤러] ⚠️ {page_num}페이지 특정 행 파싱 오류 (스킵): {e}")

        page_num += 1

    print(f"\n[크롤러] 🎉 수집 완료 — 총 {len(all_data)}명")
    return driver, pd.DataFrame(all_data)


# ──────────────────────────────────────────────
# 2. 개별 이력서 상세 정보 추출 + PDF 저장
# ──────────────────────────────────────────────

def extract_resume_details(
    driver: webdriver.Chrome,
    resume_url: str,
    candidate_name: str,
) -> dict:
    """
    이력서 상세 페이지에서 연락처(OCR), 포트폴리오, 제안URL을 추출하고
    이력서 PDF를 Google Drive에 업로드합니다.

    Returns:
        {휴대전화번호, 이메일, 첨부파일1~3, 제안URL, 이력서파일URL}
    """
    driver.get(resume_url)
    time.sleep(random.uniform(2.5, 3.5))

    soup = BeautifulSoup(driver.page_source, "html.parser")

    # ── 1. 연락처 OCR 추출 ──────────────────────
    phone, email = "비공개", "비공개"
    info_detail  = soup.find("div", class_="info-detail")

    if info_detail:
        for item in info_detail.find_all("div", class_="item"):
            label_tag = item.find("div", class_="label")
            value_tag = item.find("div", class_="value")
            if not label_tag or not value_tag:
                continue

            label   = label_tag.text.strip()
            img_tag = value_tag.find("img")

            if img_tag and "src" in img_tag.attrs:
                b64_src = img_tag["src"]
                if label == "휴대폰":
                    phone = extract_text_from_base64(b64_src)
                elif label == "Email":
                    email = extract_text_from_base64(b64_src)

    # ── 2. 포트폴리오 링크 추출 ─────────────────
    portfolio_links = extract_portfolio_links(soup)

    # ── 3. 제안 수락 URL 추출 ───────────────────
    accepted_link  = ""
    history_detail = soup.find("div", class_="history-detail")
    if history_detail and history_detail.get("data-href"):
        accepted_link = "https://www.jobkorea.co.kr" + history_detail["data-href"]

    # ── 4. 이력서 PDF → Google Drive 업로드 ─────
    safe_phone  = phone.replace("-", "").replace(" ", "") if phone else "번호없음"
    now_str     = datetime.datetime.now().strftime("%Y%m%d%H%M")
    pdf_filename = f"{now_str}_{candidate_name}_{safe_phone}.pdf"

    os.makedirs(Config.TEMP_DIR, exist_ok=True)
    local_pdf_path = os.path.join(Config.TEMP_DIR, pdf_filename)

    pdf_drive_url = ""
    print(f"\n[이력서] 📄 [{candidate_name}] PDF 저장 시작...")

    if save_page_as_pdf(driver, local_pdf_path):
        file_id = upload_file_to_drive(local_pdf_path, pdf_filename)
        if file_id:
            pdf_drive_url = make_drive_url(file_id)
            print(f"[이력서] ✅ Drive 저장 완료: {pdf_filename}")
            os.remove(local_pdf_path)  # 임시 파일 삭제

    return {
        "휴대전화번호": phone,
        "이메일":       email,
        "첨부파일1":    portfolio_links[0],
        "첨부파일2":    portfolio_links[1],
        "첨부파일3":    portfolio_links[2],
        "제안URL":      accepted_link,
        "이력서파일URL": pdf_drive_url,
    }


# ──────────────────────────────────────────────
# 3. 제안 상세 페이지 정보 추출
# ──────────────────────────────────────────────

def extract_offer_details(
    driver: webdriver.Chrome,
    offer_url: str,
) -> dict:
    """
    제안 상세 URL에서 포지션명과 발송일(yyyy-mm-dd)을 추출합니다.

    Returns:
        {제안포지션, 제안일자}
    """
    if not offer_url:
        return {"제안포지션": "", "제안일자": ""}

    print("[제안] 🌐 제안 상세 페이지 정보 추출 중...")
    driver.get(offer_url)
    time.sleep(random.uniform(1.5, 2.5))

    soup          = BeautifulSoup(driver.page_source, "html.parser")
    position_name = ""
    send_date     = ""

    try:
        # 포지션명
        title_tag = soup.find("p", class_="plea-send-title-sub")
        if title_tag:
            position_name = title_tag.text.strip()

        # 발송일 (예: "2026년 03월 12일 오후 2:18" → "2026-03-12")
        day_dl = soup.find("dl", class_="plea-send-txt-day")
        if day_dl:
            dd_tag = day_dl.find("dd")
            if dd_tag:
                raw_date = dd_tag.text.strip()
                match    = re.search(r"(\d{4})년\s*(\d{1,2})월\s*(\d{1,2})일", raw_date)
                if match:
                    send_date = (
                        f"{match.group(1)}-"
                        f"{match.group(2).zfill(2)}-"
                        f"{match.group(3).zfill(2)}"
                    )

    except Exception as e:
        print(f"[제안] ❌ 추출 실패: {e}")

    return {"제안포지션": position_name, "제안일자": send_date}


# ──────────────────────────────────────────────
# 4. 포트폴리오 링크 추출 (최대 3건)
# ──────────────────────────────────────────────

def extract_portfolio_links(soup: BeautifulSoup) -> list[str]:
    """
    이력서 soup에서 file2.jobkorea 첨부파일 링크를 최대 3개 추출합니다.
    항상 길이 3인 리스트를 반환합니다 (부족하면 빈 문자열로 채움).
    """
    links: list[str] = []

    try:
        portfolio_box = soup.find("div", class_="base portfolio")

        if not portfolio_box:
            print("[포트폴리오] 등록된 포트폴리오가 없습니다.")
        else:
            for a in portfolio_box.find_all("a"):
                href = a.get("href", "").strip()
                if "file2.jobkorea" in href:
                    links.append(href)
                if len(links) == 3:
                    break

        # 길이를 항상 3으로 고정
        while len(links) < 3:
            links.append("")

        print(f"[포트폴리오] ✅ {3 - links.count('')}개 링크 수집")

    except Exception as e:
        print(f"[포트폴리오] ❌ 추출 오류: {e}")
        links = ["", "", ""]

    return links


# ──────────────────────────────────────────────
# 5. CDP 기반 PDF 저장
# ──────────────────────────────────────────────

def save_page_as_pdf(driver: webdriver.Chrome, save_path: str) -> bool:
    """
    Chrome DevTools Protocol을 사용하여 현재 페이지를 PDF로 저장합니다.
    인쇄 다이얼로그 없이 백그라운드에서 조용히 처리됩니다.

    Returns:
        성공 여부 (bool)
    """
    try:
        pdf_data = driver.execute_cdp_cmd(
            "Page.printToPDF",
            {
                "printBackground": True,
                "landscape":       False,
                "paperWidth":      8.27,   # A4 가로 (인치)
                "paperHeight":     11.69,  # A4 세로 (인치)
                "marginTop":       0.4,
                "marginBottom":    0.4,
                "marginLeft":      0.4,
                "marginRight":     0.4,
            },
        )

        with open(save_path, "wb") as f:
            f.write(base64.b64decode(pdf_data["data"]))

        return True

    except Exception as e:
        print(f"[PDF] ❌ PDF 생성 오류: {e}")
        return False
