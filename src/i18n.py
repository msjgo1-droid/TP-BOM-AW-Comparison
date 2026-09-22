# -*- coding: utf-8 -*-
"""
다국어(한국어/영어/베트남어) 텍스트 사전.
- UI에 쓰이는 문구와, 비교 이미지 위에 그려지는 라벨(이전 파일/새 파일 등)을 함께 관리한다.
- 새 문구가 필요하면 세 언어 모두 추가할 것. 누락 시 t()가 ko 값으로 대체한다.
"""

LANGS = {
    "ko": "한국어",
    "en": "English",
    "vi": "Tiếng Việt",
}

STRINGS = {
    "app_title": {
        "ko": "TP/BOM/AW 비교 사이트",
        "en": "TP / BOM / AW Comparison Site",
        "vi": "Trang so sánh TP/BOM/AW",
    },
    "app_subtitle": {
        "ko": "같은 Style번호·AW번호를 가진 TP(테크팩)·BOM·AW(아트워크) 파일을 자동으로 매칭해 버전 차이를 비교합니다.",
        "en": "Automatically matches TP (tech pack), BOM, and AW (artwork) files that share the same style and AW number, and compares versions.",
        "vi": "Tự động khớp các tệp TP (tech pack), BOM và AW (artwork) có cùng số Style và số AW, sau đó so sánh sự khác biệt giữa các phiên bản.",
    },
    "lang_label": {
        "ko": "언어",
        "en": "Language",
        "vi": "Ngôn ngữ",
    },
    "sidebar_how_title": {
        "ko": "사용 방법",
        "en": "How it works",
        "vi": "Cách sử dụng",
    },
    "sidebar_how_body": {
        "ko": "1. 아래에 TP, BOM, AW 파일을 각각 1개 이상 업로드하세요.\n"
              "2. 파일명에서 Style번호(예: 1197192)와 AW/컬러코드(예: C-33268)를 자동으로 인식합니다.\n"
              "3. 같은 Style+AW 조합을 가진 파일이 같은 카테고리에 2개 이상 있으면 자동으로 이전 버전과 새 버전을 비교합니다.\n"
              "4. 결과를 확인하고 체크박스로 검토 완료 표시를 한 뒤, 엑셀로 다운로드할 수 있습니다.",
        "en": "1. Upload one or more TP, BOM, and AW files below.\n"
              "2. The style number (e.g. 1197192) and AW/color code (e.g. C-33268) are detected automatically from the filename.\n"
              "3. When a category has 2+ files sharing the same style + AW combination, the older and newer versions are compared automatically.\n"
              "4. Review the results, mark items as reviewed with the checkboxes, then download an Excel summary.",
        "vi": "1. Tải lên bên dưới ít nhất 1 tệp cho mỗi loại TP, BOM và AW.\n"
              "2. Số Style (vd: 1197192) và mã AW/màu (vd: C-33268) sẽ được nhận diện tự động từ tên tệp.\n"
              "3. Khi một loại có từ 2 tệp trở lên cùng cặp Style + AW, hệ thống sẽ tự động so sánh phiên bản cũ và mới.\n"
              "4. Xem kết quả, đánh dấu đã kiểm tra bằng hộp chọn, rồi tải kết quả xuống dưới dạng Excel.",
    },
    "upload_section_title": {
        "ko": "파일 업로드",
        "en": "Upload files",
        "vi": "Tải tệp lên",
    },
    "upload_tp_label": {
        "ko": "TP (테크팩) 파일",
        "en": "TP (Tech Pack) files",
        "vi": "Tệp TP (Tech Pack)",
    },
    "upload_bom_label": {
        "ko": "BOM 파일",
        "en": "BOM files",
        "vi": "Tệp BOM",
    },
    "upload_aw_label": {
        "ko": "AW (아트워크) 파일",
        "en": "AW (Artwork) files",
        "vi": "Tệp AW (Artwork)",
    },
    "upload_hint": {
        "ko": "PDF 또는 AI 파일, 여러 개 선택 가능",
        "en": "PDF or AI files, multiple selection allowed",
        "vi": "Tệp PDF hoặc AI, có thể chọn nhiều tệp",
    },
    "run_button": {
        "ko": "비교 실행",
        "en": "Run comparison",
        "vi": "Chạy so sánh",
    },
    "processing": {
        "ko": "파일을 분석하고 비교하는 중입니다...",
        "en": "Analyzing and comparing files...",
        "vi": "Đang phân tích và so sánh các tệp...",
    },
    "no_files_warning": {
        "ko": "TP, BOM, AW 중 최소 1개 카테고리에는 파일을 올려야 합니다.",
        "en": "Please upload at least one file in at least one of TP, BOM, or AW.",
        "vi": "Vui lòng tải lên ít nhất một tệp cho một trong các loại TP, BOM hoặc AW.",
    },
    "group_header": {
        "ko": "Style {style} · AW {aw}",
        "en": "Style {style} · AW {aw}",
        "vi": "Style {style} · AW {aw}",
    },
    "group_header_no_aw": {
        "ko": "Style {style} (AW코드 없음)",
        "en": "Style {style} (no AW code)",
        "vi": "Style {style} (không có mã AW)",
    },
    "category_tp": {"ko": "TP", "en": "TP", "vi": "TP"},
    "category_bom": {"ko": "BOM", "en": "BOM", "vi": "BOM"},
    "category_aw": {"ko": "AW", "en": "AW", "vi": "AW"},
    "old_file": {
        "ko": "이전 파일",
        "en": "Old file",
        "vi": "Tệp cũ",
    },
    "new_file": {
        "ko": "새 파일",
        "en": "New file",
        "vi": "Tệp mới",
    },
    "page_label": {
        "ko": "페이지 {n}",
        "en": "Page {n}",
        "vi": "Trang {n}",
    },
    "diff_found": {
        "ko": "차이 발견됨",
        "en": "Difference found",
        "vi": "Phát hiện khác biệt",
    },
    "no_diff": {
        "ko": "차이 없음 (동일)",
        "en": "No difference (identical)",
        "vi": "Không có khác biệt (giống nhau)",
    },
    "text_identical": {
        "ko": "텍스트 내용은 동일합니다.",
        "en": "Text content is identical.",
        "vi": "Nội dung văn bản giống hệt nhau.",
    },
    "text_different": {
        "ko": "텍스트 내용이 다릅니다.",
        "en": "Text content differs.",
        "vi": "Nội dung văn bản khác nhau.",
    },
    "single_version_note": {
        "ko": "이 카테고리에는 파일이 1개뿐이라 비교할 대상이 없습니다.",
        "en": "Only one file in this category — nothing to compare against.",
        "vi": "Loại này chỉ có 1 tệp nên không có gì để so sánh.",
    },
    "checklist_label": {
        "ko": "검토 완료로 표시",
        "en": "Mark as reviewed",
        "vi": "Đánh dấu đã kiểm tra",
    },
    "results_header": {
        "ko": "비교 결과",
        "en": "Comparison results",
        "vi": "Kết quả so sánh",
    },
    "unmatched_header": {
        "ko": "매칭되지 않은 파일 (Style/AW 번호를 인식하지 못했거나 짝이 없음)",
        "en": "Unmatched files (style/AW number not recognized, or no matching pair)",
        "vi": "Các tệp chưa khớp (không nhận diện được số Style/AW, hoặc không có tệp tương ứng)",
    },
    "download_excel_button": {
        "ko": "엑셀로 다운로드",
        "en": "Download as Excel",
        "vi": "Tải xuống dạng Excel",
    },
    "excel_col_group": {"ko": "그룹(Style·AW)", "en": "Group (Style·AW)", "vi": "Nhóm (Style·AW)"},
    "excel_col_category": {"ko": "카테고리", "en": "Category", "vi": "Loại"},
    "excel_col_old_file": {"ko": "이전 파일명", "en": "Old file name", "vi": "Tên tệp cũ"},
    "excel_col_new_file": {"ko": "새 파일명", "en": "New file name", "vi": "Tên tệp mới"},
    "excel_col_page": {"ko": "페이지", "en": "Page", "vi": "Trang"},
    "excel_col_status": {"ko": "결과", "en": "Result", "vi": "Kết quả"},
    "excel_col_text_status": {"ko": "텍스트 비교", "en": "Text comparison", "vi": "So sánh văn bản"},
    "excel_col_confirmed": {"ko": "검토 완료", "en": "Reviewed", "vi": "Đã kiểm tra"},
    "excel_col_note": {"ko": "메모", "en": "Note", "vi": "Ghi chú"},
    "excel_yes": {"ko": "예", "en": "Yes", "vi": "Có"},
    "excel_no": {"ko": "아니오", "en": "No", "vi": "Không"},
    "footer_disclaimer": {
        "ko": "※ 자동 이미지 비교는 참고용입니다. 최종 승인 전 반드시 원본 파일로 직접 확인하세요.",
        "en": "※ Automated image comparison is for reference only. Please verify against the original files before final approval.",
        "vi": "※ So sánh hình ảnh tự động chỉ mang tính tham khảo. Vui lòng kiểm tra lại tệp gốc trước khi phê duyệt cuối cùng.",
    },
    "not_pdf_error": {
        "ko": "'{name}' 파일을 열 수 없습니다 (PDF 호환 형식이 아니거나 손상됨).",
        "en": "Could not open '{name}' (not a PDF-compatible file, or it is corrupted).",
        "vi": "Không thể mở tệp '{name}' (không tương thích PDF hoặc bị hỏng).",
    },
    "detected_style_aw": {
        "ko": "인식된 파일 목록",
        "en": "Recognized files",
        "vi": "Danh sách tệp đã nhận diện",
    },
    "region_label": {
        "ko": "영역 {n}",
        "en": "Region {n}",
        "vi": "Khu vực {n}",
    },
    "more_regions": {
        "ko": "+{n}개 영역에서 추가로 차이가 발견되었습니다 (화면에는 표시되지 않음).",
        "en": "+{n} more region(s) with differences were found (not shown here).",
        "vi": "+{n} khu vực khác có khác biệt (không hiển thị ở đây).",
    },
    "page_count_mismatch": {
        "ko": "페이지 수가 다릅니다 (이전 파일 {old_n}페이지 · 새 파일 {new_n}페이지). 공통 페이지까지만 비교합니다.",
        "en": "Page counts differ (old file: {old_n} pages · new file: {new_n} pages). Only the common pages are compared.",
        "vi": "Số trang khác nhau (tệp cũ: {old_n} trang · tệp mới: {new_n} trang). Chỉ so sánh các trang chung.",
    },
    "page_size_diff": {
        "ko": "페이지 크기가 달라 자동 비교할 수 없습니다. 두 페이지를 직접 확인하세요.",
        "en": "Page sizes differ, so an automatic comparison isn't possible. Please review both pages manually.",
        "vi": "Kích thước trang khác nhau nên không thể so sánh tự động. Vui lòng kiểm tra thủ công cả hai trang.",
    },
    "rendering_error": {
        "ko": "이 파일을 렌더링하는 중 오류가 발생했습니다.",
        "en": "An error occurred while rendering this file.",
        "vi": "Đã xảy ra lỗi khi hiển thị tệp này.",
    },
}


def t(lang: str, key: str, **kwargs) -> str:
    """언어별 문구를 반환. 없으면 ko로 대체하고, 그래도 없으면 key 자체를 반환."""
    entry = STRINGS.get(key)
    if not entry:
        return key
    text = entry.get(lang) or entry.get("ko") or key
    if kwargs:
        try:
            return text.format(**kwargs)
        except (KeyError, IndexError):
            return text
    return text
