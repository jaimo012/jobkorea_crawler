from __future__ import annotations
import os
import datetime
from selenium import webdriver
from config import Config

def save_debug_snapshot(driver: webdriver.Chrome, prefix: str = "error") -> None:
    """
    현재 브라우저의 스크린샷과 HTML 소스를 저장합니다.
    """
    # 저장할 폴더 생성 (temp_files)
    os.makedirs(Config.TEMP_DIR, exist_ok=True)
    
    # 파일명 생성 (예: error_20260317_213005)
    now_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    base_name = f"{prefix}_{now_str}"
    
    # 1. 스크린샷 저장
    img_path = os.path.join(Config.TEMP_DIR, f"{base_name}.png")
    driver.save_screenshot(img_path)
    
    # 2. HTML 소스 저장
    html_path = os.path.join(Config.TEMP_DIR, f"{base_name}.html")
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(driver.page_source)
        
    print(f"\n[디버깅] 📸 현장 스냅샷 저장 완료!")
    print(f"  - 스크린샷: {img_path}")
    print(f"  - HTML 소스: {html_path}")
    print(f"  - WinSCP로 이 파일들을 가져와서 확인해 보세요!")
