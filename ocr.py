"""
ocr.py
Base64 이미지를 Tesseract OCR로 텍스트 변환하는 유틸리티 모듈입니다.
잡코리아의 휴대전화·이메일 이미지 보호 방식을 해독합니다.
"""

import base64
from io import BytesIO

import pytesseract
from PIL import Image

from config import Config

# Tesseract 실행 파일 경로 지정
pytesseract.pytesseract.tesseract_cmd = Config.TESSERACT_CMD


def extract_text_from_base64(base64_string: str) -> str:
    """
    Base64 인코딩된 이미지 문자열을 받아 OCR로 텍스트를 추출합니다.
    
    - 휴대전화·이메일은 영문+숫자+기호만 존재하므로 lang='eng' 고정
    - 인식률 향상을 위해 이미지를 2배 업스케일 후 처리
    
    Returns:
        추출된 텍스트 문자열. 실패 시 빈 문자열.
    """
    if not base64_string:
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

        # 2배 업스케일 (인식률 향상)
        img = img.resize(
            (img.width * 2, img.height * 2),
            Image.Resampling.LANCZOS,
        )

        # OCR 실행 (영문 모드)
        return pytesseract.image_to_string(img, lang="eng").strip()

    except Exception as e:
        print(f"[OCR] ❌ 이미지 판독 실패: {e}")
        return ""
