# -*- coding: utf-8 -*-
"""비교 결과 + 체크리스트를 엑셀(xlsx)로 내보내기.

차이점(영역) 1개당 1행, 그 행의 "이미지" 칸에 이전/새 crop을 합친 비교 이미지를 직접
삽입한다. 이미지가 없는 행(차이 없음/페이지 크기 다름)은 이미지 칸을 비워둔다.
"""
import io
from typing import List, Dict, Optional

from PIL import Image as PILImage
from openpyxl import Workbook
from openpyxl.drawing.image import Image as XLImage
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.utils import get_column_letter

from src.i18n import t

IMG_COL_TARGET_W = 480  # 엑셀에 표시할 이미지 폭(px) 상한 — 이보다 크면 축소
PX_TO_PT = 0.75          # 96dpi 기준 픽셀->포인트 환산(엑셀 행 높이는 포인트 단위)
ROW_PADDING_PT = 6


def build_excel(rows: List[Dict], lang: str) -> bytes:
    """
    rows: [{
      "group": str, "category": str, "old_file": str, "new_file": str,
      "page": int|str, "region": int|str, "status": str, "text_status": str,
      "confirmed": bool, "note": str, "image_bytes": bytes|None,
    }, ...]
    """
    wb = Workbook()
    ws = wb.active
    ws.title = "Comparison"

    headers = [
        t(lang, "excel_col_group"),
        t(lang, "excel_col_category"),
        t(lang, "excel_col_old_file"),
        t(lang, "excel_col_new_file"),
        t(lang, "excel_col_page"),
        t(lang, "excel_col_region"),
        t(lang, "excel_col_image"),
        t(lang, "excel_col_status"),
        t(lang, "excel_col_text_status"),
        t(lang, "excel_col_confirmed"),
        t(lang, "excel_col_note"),
    ]
    IMG_COL_IDX = 7  # "이미지" 컬럼(1-based) — headers 순서와 반드시 맞출 것

    ws.append(headers)
    header_fill = PatternFill(start_color="1F2A44", end_color="1F2A44", fill_type="solid")
    for col_idx in range(1, len(headers) + 1):
        cell = ws.cell(row=1, column=col_idx)
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = header_fill
        cell.alignment = Alignment(vertical="center", wrap_text=True)

    row_idx = 1
    for row in rows:
        row_idx += 1
        confirmed_text = t(lang, "excel_yes") if row.get("confirmed") else t(lang, "excel_no")
        ws.cell(row=row_idx, column=1, value=row.get("group", ""))
        ws.cell(row=row_idx, column=2, value=row.get("category", ""))
        ws.cell(row=row_idx, column=3, value=row.get("old_file", ""))
        ws.cell(row=row_idx, column=4, value=row.get("new_file", ""))
        ws.cell(row=row_idx, column=5, value=row.get("page", ""))
        ws.cell(row=row_idx, column=6, value=row.get("region", ""))
        # 7번(이미지) 컬럼은 텍스트를 넣지 않고 아래에서 그림으로 채운다
        ws.cell(row=row_idx, column=8, value=row.get("status", ""))
        ws.cell(row=row_idx, column=9, value=row.get("text_status", ""))
        ws.cell(row=row_idx, column=10, value=confirmed_text)
        ws.cell(row=row_idx, column=11, value=row.get("note", ""))

        img_bytes: Optional[bytes] = row.get("image_bytes")
        if img_bytes:
            pil_im = PILImage.open(io.BytesIO(img_bytes))
            w, h = pil_im.size
            scale = min(1.0, IMG_COL_TARGET_W / w)
            disp_w, disp_h = int(w * scale), int(h * scale)

            xl_img = XLImage(io.BytesIO(img_bytes))
            xl_img.width = disp_w
            xl_img.height = disp_h
            anchor = f"{get_column_letter(IMG_COL_IDX)}{row_idx}"
            ws.add_image(xl_img, anchor)
            ws.row_dimensions[row_idx].height = max(18, disp_h * PX_TO_PT + ROW_PADDING_PT)
        else:
            ws.row_dimensions[row_idx].height = 18

    widths = [22, 10, 30, 30, 8, 10, IMG_COL_TARGET_W / 7 + 2, 18, 20, 12, 28]
    for i, w in enumerate(widths, start=1):
        ws.column_dimensions[get_column_letter(i)].width = w

    ws.freeze_panes = "A2"
    ws.auto_filter.ref = f"A1:{get_column_letter(len(headers))}{ws.max_row}"

    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()
