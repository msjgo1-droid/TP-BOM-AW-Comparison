# -*- coding: utf-8 -*-
"""
TP/BOM/AW 비교 사이트 — Streamlit 앱.

같은 Style번호(+AW/컬러코드)를 가진 TP(테크팩)·BOM·AW(아트워크) 파일을
카테고리별로 여러 개 업로드하면, 각 카테고리 안에서 버전(오래된 것 -> 최신)을
자동으로 비교해 그래픽/텍스트 차이를 보여준다. 한국어/영어/베트남어를 지원하며,
언어를 바꾸면 비교 이미지 위의 라벨도 함께 바뀐다.
"""
import streamlit as st

from src.i18n import LANGS, t
from src.matching import build_parsed_file, group_files, CATEGORIES
from src.render import compute_page_diffs, render_page_image
from src.excel_export import build_excel

st.set_page_config(page_title="TP/BOM/AW", page_icon="🧵", layout="wide")

if "lang" not in st.session_state:
    st.session_state["lang"] = "ko"
if "diff_cache" not in st.session_state:
    st.session_state["diff_cache"] = {}  # row_id -> compute_page_diffs() 결과
if "groups" not in st.session_state:
    st.session_state["groups"] = None
if "unmatched" not in st.session_state:
    st.session_state["unmatched"] = None

# 체크박스/메모는 각 위젯의 key(rid 기반, 언어와 무관)가 st.session_state에서 값을 그대로
# 들고 있으므로 별도 dict가 필요 없다 — 언어를 바꿔 rerun 되어도 rid가 그대로라 값이 유지된다.


# ---------- 사이드바: 언어 ----------
with st.sidebar:
    lang_choice = st.radio(
        t(st.session_state["lang"], "lang_label"),
        options=list(LANGS.keys()),
        format_func=lambda k: LANGS[k],
        index=list(LANGS.keys()).index(st.session_state["lang"]),
        key="lang_radio",
    )
    st.session_state["lang"] = lang_choice
    lang = lang_choice

    st.divider()
    st.subheader(t(lang, "sidebar_how_title"))
    st.caption(t(lang, "sidebar_how_body"))

lang = st.session_state["lang"]

st.title(t(lang, "app_title"))
st.caption(t(lang, "app_subtitle"))

# ---------- 업로드 ----------
st.subheader(t(lang, "upload_section_title"))
col_tp, col_bom, col_aw = st.columns(3)
with col_tp:
    tp_uploads = st.file_uploader(
        t(lang, "upload_tp_label"), type=["pdf", "ai"], accept_multiple_files=True,
        help=t(lang, "upload_hint"), key="tp_uploader",
    )
with col_bom:
    bom_uploads = st.file_uploader(
        t(lang, "upload_bom_label"), type=["pdf", "ai"], accept_multiple_files=True,
        help=t(lang, "upload_hint"), key="bom_uploader",
    )
with col_aw:
    aw_uploads = st.file_uploader(
        t(lang, "upload_aw_label"), type=["pdf", "ai"], accept_multiple_files=True,
        help=t(lang, "upload_hint"), key="aw_uploader",
    )

run_clicked = st.button(t(lang, "run_button"), type="primary")


def _row_id(style, aw_code, category, old_name, new_name, page_num):
    # 언어와 무관한 고정 키 — 언어를 바꿔도 체크박스/메모 상태가 유지되도록 group_label(번역 문자열)을 쓰지 않는다.
    return f"{style}|{aw_code or ''}|{category}|{old_name}|{new_name}|p{page_num}"


def _process_uploads():
    files_by_category = {"TP": [], "BOM": [], "AW": []}
    uploads_by_category = {"TP": tp_uploads or [], "BOM": bom_uploads or [], "AW": aw_uploads or []}

    idx = 0
    for category, uploads in uploads_by_category.items():
        for f in uploads:
            data = f.getvalue()
            pf = build_parsed_file(f.name, category, data, idx)
            idx += 1
            files_by_category[category].append(pf)

    groups, unmatched = group_files(files_by_category)
    st.session_state["groups"] = groups
    st.session_state["unmatched"] = unmatched
    st.session_state["diff_cache"] = {}
    st.session_state["row_meta"] = {}

    # 카테고리별 인접 버전끼리(오래된->최신) diff 미리 계산해 캐시 (언어와 무관, 한 번만 계산)
    for (style, aw_code), cat_map in groups.items():
        for category in CATEGORIES:
            versions = cat_map[category]
            for i in range(len(versions) - 1):
                old_pf, new_pf = versions[i], versions[i + 1]
                cache_key = (style, aw_code, category, old_pf.filename, new_pf.filename)
                diffs = compute_page_diffs(old_pf.file_bytes, new_pf.file_bytes)
                st.session_state["diff_cache"][cache_key] = diffs


if run_clicked:
    if not (tp_uploads or bom_uploads or aw_uploads):
        st.warning(t(lang, "no_files_warning"))
    else:
        with st.spinner(t(lang, "processing")):
            _process_uploads()

groups = st.session_state["groups"]
unmatched = st.session_state["unmatched"]

# ---------- 결과 표시 ----------
if groups:
    st.subheader(t(lang, "results_header"))
    excel_rows = []

    for (style, aw_code), cat_map in groups.items():
        group_label = t(lang, "group_header", style=style, aw=aw_code) if aw_code else \
            t(lang, "group_header_no_aw", style=style)
        any_files = any(cat_map[c] for c in CATEGORIES)
        if not any_files:
            continue

        with st.expander(group_label, expanded=True):
            for category in CATEGORIES:
                versions = cat_map[category]
                if not versions:
                    continue
                cat_name = t(lang, f"category_{category.lower()}")
                st.markdown(f"**{cat_name}**")

                if len(versions) == 1:
                    st.caption(f"{versions[0].filename} — {t(lang, 'single_version_note')}")
                    continue

                for i in range(len(versions) - 1):
                    old_pf, new_pf = versions[i], versions[i + 1]
                    cache_key = (style, aw_code, category, old_pf.filename, new_pf.filename)
                    diffs = st.session_state["diff_cache"].get(cache_key)
                    if diffs is None:
                        continue

                    st.caption(f"{old_pf.filename}  →  {new_pf.filename}")

                    if diffs.get("error"):
                        st.error(t(lang, "rendering_error") + f" ({diffs['error']})")
                        continue

                    if diffs["page_count_old"] != diffs["page_count_new"]:
                        st.info(t(
                            lang, "page_count_mismatch",
                            old_n=diffs["page_count_old"], new_n=diffs["page_count_new"],
                        ))

                    text_status_key = "text_identical" if diffs["text_identical"] else "text_different"
                    text_status = t(lang, text_status_key)

                    for page_entry in diffs["pages"]:
                        page_num = page_entry["page_num"]
                        rid = _row_id(style, aw_code, category, old_pf.filename, new_pf.filename, page_num)
                        boxes = page_entry["boxes"]

                        if boxes is None:
                            status = t(lang, "page_size_diff")
                            st.warning(f"{t(lang, 'page_label', n=page_num)}: {status}")
                            excel_rows.append({
                                "group": group_label, "category": cat_name,
                                "old_file": old_pf.filename, "new_file": new_pf.filename,
                                "page": page_num, "status": status, "text_status": text_status,
                                "confirmed": False, "note": "",
                            })
                            continue

                        if not boxes:
                            st.success(f"{t(lang, 'page_label', n=page_num)}: {t(lang, 'no_diff')}")
                            excel_rows.append({
                                "group": group_label, "category": cat_name,
                                "old_file": old_pf.filename, "new_file": new_pf.filename,
                                "page": page_num, "status": t(lang, "no_diff"), "text_status": text_status,
                                "confirmed": True, "note": "",
                            })
                            continue

                        st.markdown(f"**{t(lang, 'page_label', n=page_num)} — {t(lang, 'diff_found')}**")
                        img_bytes = render_page_image(page_entry, lang)
                        if img_bytes:
                            st.image(img_bytes, width="stretch")
                        checked = st.checkbox(
                            t(lang, "checklist_label"),
                            key=f"chk_{rid}",
                        )
                        note_val = st.text_input(
                            t(lang, "excel_col_note"),
                            key=f"note_{rid}",
                            label_visibility="collapsed",
                            placeholder=t(lang, "excel_col_note"),
                        )
                        excel_rows.append({
                            "group": group_label, "category": cat_name,
                            "old_file": old_pf.filename, "new_file": new_pf.filename,
                            "page": page_num, "status": t(lang, "diff_found"), "text_status": text_status,
                            "confirmed": checked, "note": note_val,
                        })
                        st.divider()

    if unmatched:
        with st.expander(t(lang, "unmatched_header")):
            for pf in unmatched:
                st.write(f"[{pf.category}] {pf.filename}")

    if excel_rows:
        st.divider()
        xlsx_bytes = build_excel(excel_rows, lang)
        st.download_button(
            t(lang, "download_excel_button"),
            data=xlsx_bytes,
            file_name="tp_bom_aw_comparison.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            type="primary",
        )

st.divider()
st.caption(t(lang, "footer_disclaimer"))
