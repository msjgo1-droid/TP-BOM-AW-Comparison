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
MAX_PAGE_W = 900       # 전체 페이지 썸네일 한 장의 최대 폭(px)
MAX_REGIONS = 4        # 페이지당 확대해서 보여줄 최대 영역 수
CROP_MARGIN = 24        # 영역 크롭시 여백(px, RENDER_DPI 기준)
CROP_TARGET_MAX = 640    # 영역 확대 이미지 한 장의 최대 폭(px)


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


def _fit_width(im: Image.Image, max_w: int) -> Image.Image:
    if im.width <= max_w:
        return im
    r = max_w / im.width
    return im.resize((max_w, max(1, int(im.height * r))), Image.LANCZOS)


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


def _hstack(images: List[Image.Image], gap=10, bg="white", divider_color=(214, 39, 39)) -> Image.Image:
    h = max(im.height for im in images)
    w = sum(im.width for im in images) + gap * (len(images) - 1)
    out = Image.new("RGB", (w, h), bg)
    x = 0
    for i, im in enumerate(images):
        out.paste(im, (x, 0))
        x += im.width
        if i < len(images) - 1:
            d = ImageDraw.Draw(out)
            d.rectangle([x, 0, x + gap - 1, h], fill=divider_color)
            x += gap
    return out


def _crop_with_margin(img: Image.Image, box, margin=CROP_MARGIN):
    x0, y0, x1, y1 = box
    x0 = max(0, x0 - margin)
    y0 = max(0, y0 - margin)
    x1 = min(img.width, x1 + margin)
    y1 = min(img.height, y1 + margin)
    return img.crop((x0, y0, x1, y1))


def _scale_to_target(im: Image.Image, target_max=CROP_TARGET_MAX) -> Image.Image:
    scale = target_max / max(im.width, im.height)
    # 너무 작은 영역은 최대 6배까지 확대, 큰 영역은 축소
    scale = min(scale, 6.0)
    new_size = (max(1, int(im.width * scale)), max(1, int(im.height * scale)))
    return im.resize(new_size, Image.LANCZOS)


def build_page_comparison_image(
    img_old: Image.Image,
    img_new: Image.Image,
    boxes: List[Tuple[int, int, int, int]],
    lang: str,
    page_num: int,
) -> bytes:
    """한 페이지의 이전/새 파일 비교 이미지를 PNG bytes로 반환."""
    old_label = t(lang, "old_file")
    new_label = t(lang, "new_file")

    old_boxed = _fit_width(_draw_boxes(img_old, boxes), MAX_PAGE_W)
    new_boxed = _fit_width(_draw_boxes(img_new, boxes), MAX_PAGE_W)
    label_h = 34
    old_block = _vstack([_label_row(old_boxed.width, label_h, old_label, (90, 90, 90), lang), old_boxed], gap=4)
    new_block = _vstack([_label_row(new_boxed.width, label_h, new_label, (192, 20, 20), lang), new_boxed], gap=4)
    top_row = _hstack([old_block, new_block], gap=14)

    rows = [top_row]
    shown = boxes[:MAX_REGIONS]
    for i, box in enumerate(shown):
        crop_o = _scale_to_target(_crop_with_margin(img_old, box))
        crop_n = _scale_to_target(_crop_with_margin(img_new, box))
        h = max(crop_o.height, crop_n.height)
        if crop_o.height != h:
            crop_o = crop_o.resize((int(crop_o.width * h / crop_o.height), h), Image.LANCZOS)
        if crop_n.height != h:
            crop_n = crop_n.resize((int(crop_n.width * h / crop_n.height), h), Image.LANCZOS)
        region_label = t(lang, "region_label", n=i + 1)
        lbl = _label_row(top_row.width, 30, region_label, (40, 40, 40), lang)
        pair = _hstack([crop_o, crop_n], gap=10)
        pair = _fit_width(pair, top_row.width)
        rows.append(_vstack([lbl, pair], gap=2))

    if len(boxes) > MAX_REGIONS:
        note = t(lang, "more_regions", n=len(boxes) - MAX_REGIONS)
        rows.append(_label_row(top_row.width, 30, note, (120, 120, 120), lang))

    final = _vstack(rows, gap=18)
    canvas = Image.new("RGB", (final.width + 24, final.height + 24), "white")
    canvas.paste(final, (12, 12))
    buf = io.BytesIO()
    canvas.save(buf, format="PNG")
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


def render_page_image(page_entry: Dict, lang: str) -> Optional[bytes]:
    """compute_page_diffs()가 만든 page_entry를 주어진 언어로 합성. 차이가 없거나 크기가 다르면 None."""
    boxes = page_entry.get("boxes")
    if not boxes:
        return None
    return build_page_comparison_image(
        page_entry["img_old"], page_entry["img_new"], boxes, lang, page_entry["page_num"]
    )


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
