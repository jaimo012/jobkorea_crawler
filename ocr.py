"""
ocr.py
Base64 이미지를 Tesseract OCR로 텍스트 변환하는 유틸리티 모듈입니다.
잡코리아의 휴대전화·이메일 이미지 보호 방식을 해독합니다.
"""
from __future__ import annotations

import base64
import os
import datetime
from io import BytesIO

import pytesseract
from PIL import Image, ImageFilter

from config import Config

# Tesseract 실행 파일 경로 지정
pytesseract.pytesseract.tesseract_cmd = Config.TESSERACT_CMD
print(f"[OCR] Tesseract 경로: {Config.TESSERACT_CMD}")


def extract_text_from_base64(base64_string: str, label: str = "") -> str:
    """
    Base64 인코딩된 이미지 문자열을 받아 OCR로 텍스트를 추출합니다.

    - 휴대전화·이메일은 영문+숫자+기호만 존재하므로 lang='eng' 고정
    - 인식률 향상을 위해 이미지를 3배 업스케일 + 샤프닝 처리

    Args:
        base64_string: data URI 또는 순수 base64 문자열
        label: 디버그 로그용 라벨 (예: "휴대폰", "Email")

    Returns:
        추출된 텍스트 문자열. 실패 시 빈 문자열.
    """
    if not base64_string:
        print(f"[OCR] [{label}] 이미지 데이터 없음 (빈 문자열)")
        return ""

    try:
        # "data:image/png;base64,XXXX" 형식에서 순수 데이터 분리
        pure_data = (
            base64_string.split(",")[1]
            if "," in base64_string
            else base64_string
        )

        # 바이트 디코딩 → PIL 이미지 변환
        image_bytes = base64.b64decode(pure_data)
        img = Image.open(BytesIO(image_bytes))
        print(f"[OCR] [{label}] 원본 이미지: {img.size}, mode={img.mode}")

        # 디버그: 원본 이미지 저장
        _save_debug_image(img, label, "original")

        # 전처리: 그레이스케일 변환
        if img.mode != "L":
            img = img.convert("L")

        # 3배 업스케일 (인식률 향상)
        img = img.resize(
            (img.width * 3, img.height * 3),
            Image.Resampling.LANCZOS,
        )

        # 샤프닝 적용
        img = img.filter(ImageFilter.SHARPEN)

        # 디버그: 전처리 후 이미지 저장
        _save_debug_image(img, label, "processed")

        # OCR 실행 (영문 모드, PSM 7 = 한 줄 텍스트)
        result = pytesseract.image_to_string(
            img,
            lang="eng",
            config="--psm 7 -c tessedit_char_whitelist=0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ@.-+_",
        ).strip()

        print(f"[OCR] [{label}] 인식 결과: '{result}'")
        return result

    except Exception as e:
        print(f"[OCR] [{label}] 이미지 판독 실패: {e}")
        return ""


def _save_debug_image(img: Image.Image, label: str, stage: str) -> None:
    """OCR 디버그용 이미지를 temp_files에 저장합니다."""
    try:
        os.makedirs(Config.TEMP_DIR, exist_ok=True)
        now_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_label = label.replace(" ", "_").replace("/", "_")
        path = os.path.join(Config.TEMP_DIR, f"ocr_{safe_label}_{stage}_{now_str}.png")
        img.save(path)
        print(f"[OCR] [{label}] 디버그 이미지 저장: {path}")
    except Exception:
        pass  # 디버그 이미지 저장 실패는 무시
