# -*- coding: utf-8 -*-
"""
PDF/AI 파일 래스터화, 페이지별 픽셀 diff 검출, 언어별 라벨이 들어간 비교 이미지 합성.

주의: AI 파일도 내부적으로 PDF 호환 스트림을 포함하고 있어 poppler(pdf2image)로 문제없이
렌더링된다 (Adobe Illustrator의 "PDF 호환 파일 만들기" 옵션이 기본 켜짐).
"""
import io
import os
from typing import List, Optional, Tuple, Dict

import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageFont
from scipy import ndimage
from pdf2image import convert_from_bytes
from pypdf import PdfReader

from src.i18n import t

import glob as _glob

# Noto Sans CJK 폰트(패키지: fonts-noto-cjk)는 배포 환경에 따라 정확한 경로가 조금씩 다를 수
# 있어, 후보 경로를 순서대로 찾는다. 이 폰트 하나로 한글/영문/베트남어(라틴 확장) 라벨을
# 전부 커버한다 — 없으면 DejaVu Sans로 대체(단, 이 경우 한글은 표시되지 않는다).
_FONT_CANDIDATES = [
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
] + sorted(_glob.glob("/usr/share/fonts/**/NotoSansCJK*.ttc", recursive=True)) \
  + sorted(_glob.glob("/usr/share/fonts/**/NotoSansCJK*.otf", recursive=True))
_FONT_FALLBACK = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONT_INDEX = 1  # .ttc 컬렉션 내 "Noto Sans CJK KR" — 한글 자형 기준(cmap 자체는 공용)


def _resolve_font_path():
    for path in _FONT_CANDIDATES:
        if os.path.exists(path):
            return path
    return None


FONT_PATH = _resolve_font_path()

RENDER_DPI = 150
COL_W = 640             # 이전/새 파일 컬럼 하나의 고정 폭(px) — 모든 행(전체페이지, 영역별)이
                        # 이 폭을 공유해야 빨간 구분선이 항상 같은 x좌표에 와서 세로로 일직선을 이룬다.
DIVIDER_W = 10           # 구분선 두께(px)
MAX_REGIONS = 4        # 화면 표시용 페이지 합성 이미지에서 확대해서 보여줄 최대 영역 수
MAX_EXPORT_REGIONS = 20  # 엑셀로 내보낼 때 영역당 1행씩 만들 때의 안전 상한
CROP_MARGIN = 24        # 영역 크롭시 여백(px, RENDER_DPI 기준)
EXPORT_COL_W = 420       # 엑셀에 삽입하는 영역별 이미지의 컬럼 폭(px)


def _font(size: int) -> ImageFont.FreeTypeFont:
    if FONT_PATH:
        try:
            return ImageFont.truetype(FONT_PATH, size, index=FONT_INDEX)
        except Exception:
            try:
                return ImageFont.truetype(FONT_PATH, size)
            except Exception:
                pass
    try:
        return ImageFont.truetype(_FONT_FALLBACK, size)
    except Exception:
        return ImageFont.load_default()


def rasterize(pdf_bytes: bytes, dpi: int = RENDER_DPI) -> List[Image.Image]:
    images = convert_from_bytes(pdf_bytes, dpi=dpi)
    return [im.convert("RGB") for im in images]


def page_count(pdf_bytes: bytes) -> int:
    try:
        return len(PdfReader(io.BytesIO(pdf_bytes)).pages)
    except Exception:
        return 0


def extract_page_texts(pdf_bytes: bytes) -> List[str]:
    try:
        reader = PdfReader(io.BytesIO(pdf_bytes))
    except Exception:
        return []
    texts = []
    for page in reader.pages:
        try:
            texts.append((page.extract_text() or "").strip())
        except Exception:
            texts.append("")
    return texts


def normalize_text(s: str) -> str:
    return "\n".join(line.strip() for line in s.splitlines() if line.strip())


def texts_identical(old_bytes: bytes, new_bytes: bytes) -> bool:
    old_pages = [normalize_text(p) for p in extract_page_texts(old_bytes)]
    new_pages = [normalize_text(p) for p in extract_page_texts(new_bytes)]
    return old_pages == new_pages


def find_diff_regions(
    img_a: Image.Image,
    img_b: Image.Image,
    threshold: int = 24,
    dilate_iter: int = 10,
    min_area_px: int = 40,
) -> Optional[List[Tuple[int, int, int, int]]]:
    """반환: [(x0,y0,x1,y1), ...] 면적 큰 순. 페이지 크기가 다르면 None.

    벡터 PDF를 같은 DPI로 렌더링하면 동일한 내용은 픽셀까지 완전히 같게 나오므로
    (스캔 이미지처럼 노이즈가 끼지 않음), 페이지 크기에 비례한 임계값이 아니라
    작은 절대 픽셀 기준을 사용한다 — 그래야 큰 페이지 안의 구멍 1~2개 같은
    작은 실제 차이도 놓치지 않는다.
    """
    if img_a.size != img_b.size:
        return None
    diff = ImageChops.difference(img_a, img_b).convert("L")
    arr = np.array(diff) > threshold
    if not arr.any():
        return []
    dilated = ndimage.binary_dilation(arr, iterations=dilate_iter)
    labeled, _ = ndimage.label(dilated)
    min_area = min_area_px
    boxes = []
    for sl in ndimage.find_objects(labeled):
        y0, y1 = sl[0].start, sl[0].stop
        x0, x1 = sl[1].start, sl[1].stop
        area = (x1 - x0) * (y1 - y0)
        if area < min_area:
            continue
        boxes.append((x0, y0, x1, y1))
    boxes.sort(key=lambda b: (b[2] - b[0]) * (b[3] - b[1]), reverse=True)
    return boxes


def _draw_boxes(img: Image.Image, boxes, color=(214, 39, 39), width=5) -> Image.Image:
    im = img.copy()
    d = ImageDraw.Draw(im)
    for i, (x0, y0, x1, y1) in enumerate(boxes):
        d.rectangle([x0, y0, x1, y1], outline=color, width=width)
    return im


def _label_row(width: int, height: int, text: str, color, lang) -> Image.Image:
    im = Image.new("RGB", (width, height), "white")
    d = ImageDraw.Draw(im)
    f = _font(max(16, int(height * 0.62)))
    d.text((6, height // 2), text, font=f, fill=color, anchor="lm")
    return im


def _vstack(images: List[Image.Image], gap=8, bg="white") -> Image.Image:
    w = max(im.width for im in images)
    h = sum(im.height for im in images) + gap * (len(images) - 1)
    out = Image.new("RGB", (w, h), bg)
    y = 0
    for im in images:
        out.paste(im, (0, y))
        y += im.height + gap
    return out


def _fit_to_col(im: Image.Image, col_w: int, max_upscale: float = 6.0) -> Image.Image:
    """이미지를 컬럼 폭에 맞춘다. 큰 이미지는 col_w로 축소, 작은 이미지는 최대 max_upscale배까지
    확대한다 — 어느 쪽이든 결과 이미지는 col_w보다 클 수 없다(작을 수는 있음, 이 경우 컬럼 안에서
    가운데 정렬해 배치한다)."""
    scale = col_w / im.width
    scale = min(scale, max_upscale)
    new_w = max(1, int(im.width * scale))
    new_h = max(1, int(im.height * scale))
    return im.resize((new_w, new_h), Image.LANCZOS)


def _two_col_row(left_im: Image.Image, right_im: Image.Image, col_w=COL_W, gap=DIVIDER_W,
                  divider_color=(214, 39, 39), bg="white") -> Image.Image:
    """왼쪽/오른쪽 이미지를 폭이 항상 2*col_w+gap로 고정된 캔버스 위, 각자의 col_w 폭 칸
    한가운데에 배치하고 그 사이에 구분선을 그린다. 캔버스 폭이 행마다 항상 같으므로,
    여러 행을 세로로 쌓아도 구분선이 처음부터 끝까지 일직선으로 이어진다."""
    h = max(left_im.height, right_im.height)
    canvas = Image.new("RGB", (2 * col_w + gap, h), bg)
    lx = (col_w - left_im.width) // 2
    ly = (h - left_im.height) // 2
    canvas.paste(left_im, (lx, ly))
    rx = col_w + gap + (col_w - right_im.width) // 2
    ry = (h - right_im.height) // 2
    canvas.paste(right_im, (rx, ry))
    d = ImageDraw.Draw(canvas)
    d.rectangle([col_w, 0, col_w + gap - 1, h], fill=divider_color)
    return canvas


def _crop_with_margin(img: Image.Image, box, margin=CROP_MARGIN):
    x0, y0, x1, y1 = box
    x0 = max(0, x0 - margin)
    y0 = max(0, y0 - margin)
    x1 = min(img.width, x1 + margin)
    y1 = min(img.height, y1 + margin)
    return img.crop((x0, y0, x1, y1))


def _labeled_pair(left_im: Image.Image, right_im: Image.Image, lang: str, col_w: int,
                   label_h: int = 30) -> Image.Image:
    """(이전 파일 라벨 | 새 파일 라벨) 위에 (left_im | right_im)을 고정폭 두 컬럼으로 합성."""
    canvas_w = 2 * col_w + DIVIDER_W
    label_left = _label_row(col_w, label_h, t(lang, "old_file"), (90, 90, 90), lang)
    label_right = _label_row(col_w, label_h, t(lang, "new_file"), (192, 20, 20), lang)
    label_canvas = Image.new("RGB", (canvas_w, label_h), "white")
    label_canvas.paste(label_left, (0, 0))
    label_canvas.paste(label_right, (col_w + DIVIDER_W, 0))
    body = _two_col_row(left_im, right_im, col_w=col_w)
    return _vstack([label_canvas, body], gap=4)


def render_page_overview_image(
    img_old: Image.Image,
    img_new: Image.Image,
    boxes: List[Tuple[int, int, int, int]],
    lang: str,
) -> bytes:
    """페이지 전체를 축소해 차이 영역을 빨간 박스로 표시한 이전/새 파일 비교 이미지(PNG bytes).
    화면에서 "이 페이지 어디가 달라졌는지" 한눈에 보는 용도 — 영역별 확대 이미지는
    render_region_export_image()가 따로 만든다(화면·엑셀 공용)."""
    old_boxed = _fit_to_col(_draw_boxes(img_old, boxes), COL_W, max_upscale=1.0)
    new_boxed = _fit_to_col(_draw_boxes(img_new, boxes), COL_W, max_upscale=1.0)
    final = _labeled_pair(old_boxed, new_boxed, lang, COL_W, label_h=34)
    canvas = Image.new("RGB", (final.width + 24, final.height + 24), "white")
    canvas.paste(final, (12, 12))
    buf = io.BytesIO()
    canvas.save(buf, format="PNG")
    return buf.getvalue()


def render_region_export_image(
    img_old: Image.Image,
    img_new: Image.Image,
    box: Tuple[int, int, int, int],
    lang: str,
    col_w: int = EXPORT_COL_W,
) -> bytes:
    """영역 하나짜리 이전/새 비교 이미지(라벨 포함) PNG bytes. 화면 표시와 엑셀 삽입에 공용으로
    쓴다 — 두 곳에서 똑같은 이미지를 보게 되고, 한 번만 렌더링하면 되므로 더 빠르다."""
    crop_o = _fit_to_col(_crop_with_margin(img_old, box), col_w)
    crop_n = _fit_to_col(_crop_with_margin(img_new, box), col_w)
    final = _labeled_pair(crop_o, crop_n, lang, col_w, label_h=24)
    buf = io.BytesIO()
    final.save(buf, format="PNG")
    return buf.getvalue()


def compute_page_diffs(old_bytes: bytes, new_bytes: bytes) -> Dict:
    """언어와 무관한 무거운 계산(래스터화 + diff 영역 검출)만 수행하고 결과를 캐시 가능한 형태로 반환.

    반환 pages[i]: {"page_num", "img_old": PIL.Image, "img_new": PIL.Image, "boxes": list|None}
    boxes가 None이면 페이지 크기가 달라 비교 불가, []이면 차이 없음, 값이 있으면 차이 발견.
    """
    result = {
        "text_identical": None,
        "page_count_old": 0,
        "page_count_new": 0,
        "pages": [],
        "error": None,
    }
    try:
        result["text_identical"] = texts_identical(old_bytes, new_bytes)
        imgs_old = rasterize(old_bytes)
        imgs_new = rasterize(new_bytes)
    except Exception as e:
        result["error"] = str(e)
        return result

    result["page_count_old"] = len(imgs_old)
    result["page_count_new"] = len(imgs_new)
    n_pages = min(len(imgs_old), len(imgs_new))
    for i in range(n_pages):
        a, b = imgs_old[i], imgs_new[i]
        boxes = find_diff_regions(a, b)
        result["pages"].append({"page_num": i + 1, "img_old": a, "img_new": b, "boxes": boxes})
    return result


def export_region_images(page_entry: Dict, lang: str, max_regions: int = MAX_EXPORT_REGIONS) -> List[Tuple[int, bytes]]:
    """엑셀 내보내기용: 이 페이지에서 검출된 영역마다 (영역번호, PNG bytes) 리스트를 반환."""
    boxes = page_entry.get("boxes") or []
    out = []
    for i, box in enumerate(boxes[:max_regions]):
        img_bytes = render_region_export_image(page_entry["img_old"], page_entry["img_new"], box, lang)
        out.append((i + 1, img_bytes))
    return out


def render_page_image(page_entry: Dict, lang: str) -> Optional[bytes]:
    """compute_page_diffs()가 만든 page_entry의 전체 페이지 개요 이미지를 언어에 맞게 합성.
    차이가 없거나 페이지 크기가 다르면 None."""
    boxes = page_entry.get("boxes")
    if not boxes:
        return None
    return render_page_overview_image(page_entry["img_old"], page_entry["img_new"], boxes, lang)


def compare_file_pair(old_pf, new_pf, lang: str) -> Dict:
    """
    old_pf, new_pf: matching.ParsedFile (file_bytes 포함)
    반환: {
      "text_identical": bool,
      "page_count_old": int, "page_count_new": int,
      "pages": [ {"page_num": int, "diff_found": bool, "image_bytes": bytes|None,
                   "region_count": int, "size_mismatch": bool}, ... ],
      "error": str|None,
    }
    """
    diffs = compute_page_diffs(old_pf.file_bytes, new_pf.file_bytes)
    result = {
        "text_identical": diffs["text_identical"],
        "page_count_old": diffs["page_count_old"],
        "page_count_new": diffs["page_count_new"],
        "pages": [],
        "error": diffs["error"],
    }
    if diffs["error"]:
        return result

    for page_entry in diffs["pages"]:
        boxes = page_entry["boxes"]
        if boxes is None:
            result["pages"].append(
                {"page_num": page_entry["page_num"], "diff_found": True, "image_bytes": None,
                 "region_count": 0, "size_mismatch": True}
            )
            continue
        if not boxes:
            result["pages"].append(
                {"page_num": page_entry["page_num"], "diff_found": False, "image_bytes": None,
                 "region_count": 0, "size_mismatch": False}
            )
            continue
        img_bytes = render_page_image(page_entry, lang)
        result["pages"].append(
            {"page_num": page_entry["page_num"], "diff_found": True, "image_bytes": img_bytes,
             "region_count": len(boxes), "size_mismatch": False}
        )
    return result
