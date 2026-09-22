# -*- coding: utf-8 -*-
"""
파일명 파싱 + Style/AW 번호 매칭 로직.

파일명 규칙 예시 (실제 사용 파일 기준):
  F27 1197192 M Birdlab Starting Line LS C-33268.ai
  F27 1197192 M Birdlab Starting Line LS C-33268 9.16.26.ai
  F27_1187314_RUN CLUB 5in SHORT_Laser Perf Schematics_8.12.pdf
  F27_1187314_RUN CLUB 5in SHORT_Laser Perf Schematics.ai

- Style번호: 공백/밑줄로 분리된 토큰 중 6~8자리 숫자
- AW/컬러 코드: "C-33268" 같은 [영문 1~3자]-[숫자 3~6자] 형태
- 리비전 날짜: "9.16.26", "8.12" 같은 파일명 끝쪽의 날짜 형태 토큰(있으면)
"""
import os
import re
from dataclasses import dataclass, field
from typing import Optional, Dict, List, Tuple

DATE_TOKEN_RE = re.compile(r"^\d{1,2}\.\d{1,2}(\.\d{2,4})?$")
AW_CODE_RE = re.compile(r"^[A-Za-z]{1,3}-\d{3,6}$")
STYLE_RE = re.compile(r"^\d{6,8}$")
PDF_DATE_RE = re.compile(
    r"D:(\d{4})(\d{2})(\d{2})(\d{2})?(\d{2})?(\d{2})?"
)

CATEGORIES = ["TP", "BOM", "AW"]


@dataclass
class ParsedFile:
    filename: str
    category: str
    style: Optional[str]
    aw_code: Optional[str]
    revision_tag: Optional[str]
    file_bytes: bytes = field(repr=False, default=b"")
    pdf_datetime_key: Tuple[int, ...] = (0, 0, 0, 0, 0, 0)
    order_index: int = 0  # 업로드 순서 (최후 보루 정렬 기준)

    @property
    def sort_key(self):
        # 1) 파일명 날짜 토큰 우선, 2) PDF 내부 생성일시, 3) 업로드 순서
        fn_key = _parse_filename_date(self.revision_tag)
        has_fn_date = 1 if fn_key else 0
        return (
            has_fn_date,
            fn_key or (0, 0, 0),
            self.pdf_datetime_key,
            self.order_index,
        )

    @property
    def display_label(self):
        if self.revision_tag:
            return f"{self.filename}"
        return self.filename


def _parse_filename_date(tag: Optional[str]):
    if not tag:
        return None
    parts = tag.split(".")
    try:
        month = int(parts[0])
        day = int(parts[1])
        year = int(parts[2]) if len(parts) > 2 else 0
        if 0 < year < 100:
            year += 2000
        return (year, month, day)
    except (ValueError, IndexError):
        return None


def parse_pdf_datetime(raw_bytes: bytes) -> Tuple[int, ...]:
    """PDF/AI 파일 내부 메타데이터(CreationDate)를 읽어 정렬용 튜플로 반환. 실패 시 전부 0."""
    try:
        import io
        from pypdf import PdfReader

        reader = PdfReader(io.BytesIO(raw_bytes))
        meta = reader.metadata or {}
        raw = meta.get("/CreationDate") or meta.get("/ModDate")
        if not raw:
            return (0, 0, 0, 0, 0, 0)
        m = PDF_DATE_RE.match(str(raw))
        if not m:
            return (0, 0, 0, 0, 0, 0)
        vals = [int(g) if g else 0 for g in m.groups()]
        return tuple(vals)
    except Exception:
        return (0, 0, 0, 0, 0, 0)


def parse_filename(filename: str) -> Dict[str, Optional[str]]:
    stem = os.path.splitext(filename)[0]
    tokens = [tok for tok in re.split(r"[ _]+", stem.strip()) if tok]

    style = None
    aw_code = None
    revision_tag = None

    for tok in tokens:
        clean = tok.strip()
        if style is None and STYLE_RE.match(clean):
            style = clean
            continue
        if aw_code is None and AW_CODE_RE.match(clean):
            aw_code = clean.upper()
            continue
        if revision_tag is None and DATE_TOKEN_RE.match(clean):
            revision_tag = clean

    return {"style": style, "aw_code": aw_code, "revision_tag": revision_tag}


def build_parsed_file(filename: str, category: str, raw_bytes: bytes, order_index: int) -> ParsedFile:
    info = parse_filename(filename)
    pdf_key = parse_pdf_datetime(raw_bytes)
    return ParsedFile(
        filename=filename,
        category=category,
        style=info["style"],
        aw_code=info["aw_code"],
        revision_tag=info["revision_tag"],
        file_bytes=raw_bytes,
        pdf_datetime_key=pdf_key,
        order_index=order_index,
    )


def group_files(files_by_category: Dict[str, List[ParsedFile]]):
    """
    Style번호(+AW코드)가 같은 파일끼리 묶는다.
    - AW코드가 있는 파일은 (style, aw_code)로, 없는 파일은 (style, None)으로 그룹핑.
    - style을 인식하지 못한 파일은 unmatched로 분리.
    반환: groups(dict[(style, aw_code)] -> {"TP":[...], "BOM":[...], "AW":[...]}), unmatched(list[ParsedFile])
    """
    groups: Dict[Tuple[str, Optional[str]], Dict[str, List[ParsedFile]]] = {}
    unmatched: List[ParsedFile] = []

    for category in CATEGORIES:
        for pf in files_by_category.get(category, []):
            if not pf.style:
                unmatched.append(pf)
                continue
            key = (pf.style, pf.aw_code)
            if key not in groups:
                groups[key] = {c: [] for c in CATEGORIES}
            groups[key][pf.category].append(pf)

    # 각 카테고리 내에서 날짜순(오래된 -> 최신) 정렬
    for key, cat_map in groups.items():
        for category in CATEGORIES:
            cat_map[category].sort(key=lambda pf: pf.sort_key)

    ordered_keys = sorted(groups.keys(), key=lambda k: (k[0], k[1] or ""))
    return {k: groups[k] for k in ordered_keys}, unmatched
