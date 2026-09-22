# TP/BOM/AW 비교 사이트

같은 **Style번호 + AW(컬러)코드**를 가진 TP(테크팩) · BOM · AW(아트워크) 파일을 여러 개 업로드하면,
같은 카테고리 안에서 오래된 버전 → 최신 버전을 자동으로 비교해 그래픽/텍스트 차이를 보여주는
Streamlit 웹앱입니다. 한국어 / English / Tiếng Việt를 지원하며, 언어를 바꾸면 비교 이미지 위의
라벨("이전 파일"/"새 파일" 등)도 함께 바뀝니다. 결과는 체크박스로 검토 표시를 하고 엑셀로
다운로드할 수 있습니다.

## 폴더 구조

```
tp_bom_aw_compare/
├── app.py                 # Streamlit 메인 앱 (UI)
├── requirements.txt        # Python 패키지 목록
├── packages.txt             # Streamlit Cloud용 시스템 패키지(poppler, 한글 폰트)
├── .streamlit/config.toml    # 테마/업로드 용량 설정
└── src/
    ├── i18n.py             # 한/영/베 문구 사전
    ├── matching.py          # 파일명 → Style/AW번호 파싱 + 그룹핑
    ├── render.py            # PDF/AI 렌더링, 차이 검출, 비교 이미지 합성
    └── excel_export.py       # 체크리스트 포함 엑셀 내보내기
```

## 동작 방식

1. 파일명에서 정규식으로 다음을 자동 인식합니다.
   - **Style번호**: 6~8자리 숫자 토큰 (예: `1197192`)
   - **AW/컬러코드**: `C-33268`처럼 영문 1~3자 + `-` + 숫자 3~6자
   - **리비전 날짜**: `9.16.26`, `8.12`처럼 파일명 끝쪽의 날짜 형태 토큰(있는 경우)
2. Style번호(+AW코드)가 같은 파일끼리 묶고, 같은 카테고리(TP/BOM/AW) 안에서 파일명 날짜 →
   PDF 내부 생성일시(메타데이터) → 업로드 순서 순으로 정렬해 오래된 버전부터 최신 버전까지
   순서대로 비교합니다.
3. 비교는 poppler(pdf2image)로 각 페이지를 같은 해상도로 래스터화한 뒤, 픽셀 단위로 다른
   영역을 찾아 빨간 박스로 표시하고, 그 영역을 확대한 crop을 이전/새 파일 나란히 보여줍니다.
   AI 파일도 내부적으로 PDF 호환 스트림을 포함하고 있어 별도 변환 없이 바로 렌더링됩니다.
4. 텍스트(스타일명, 담당자 등)가 동일한지도 별도로 비교해 표시합니다.
5. 화면에 그려지는 라벨은 렌더링 시점의 언어로 그려지므로, 언어를 바꾸면 이미 계산해둔
   차이 영역(픽셀 diff)은 재사용하고 라벨만 다시 그려 빠르게 갱신됩니다.

## 로컬에서 먼저 확인하기

```bash
pip install -r requirements.txt
# poppler-utils, 한글 폰트(fonts-noto-cjk)가 시스템에 없다면 먼저 설치
#   Debian/Ubuntu: sudo apt-get install poppler-utils fonts-noto-cjk
#   macOS: brew install poppler
streamlit run app.py
```

브라우저에서 `http://localhost:8501` 로 접속됩니다.

## GitHub + Streamlit Community Cloud로 배포하기

### 1) GitHub 저장소 만들기

1. [github.com](https://github.com) 에 로그인 → 오른쪽 위 `+` → **New repository**
2. 저장소 이름(예: `tp-bom-aw-compare`) 입력 → Private/Public 선택 → **Create repository**

### 2) 이 폴더를 저장소에 올리기 (터미널에서)

```bash
cd tp_bom_aw_compare
git init
git add .
git commit -m "Initial commit: TP/BOM/AW 비교 사이트"
git branch -M main
git remote add origin https://github.com/<본인계정>/<저장소이름>.git
git push -u origin main
```

(GitHub Desktop 같은 GUI 프로그램을 쓰셔도 됩니다 — 폴더를 그대로 저장소로 만들고 Push만
누르면 됩니다.)

### 3) Streamlit Community Cloud에 배포하기

1. [share.streamlit.io](https://share.streamlit.io) 접속 → GitHub 계정으로 로그인
2. **New app** 클릭
3. Repository: 방금 만든 저장소 선택 / Branch: `main` / Main file path: `app.py`
4. **Deploy** 클릭

몇 분 뒤 `https://<앱이름>.streamlit.app` 형태의 공개 링크가 생성됩니다. `packages.txt`가
저장소에 포함되어 있으면 Streamlit Cloud가 poppler와 한글 폰트를 자동으로 설치합니다.

### 이후 수정 사항 반영

로컬에서 파일을 수정한 뒤,

```bash
git add .
git commit -m "수정 내용"
git push
```

하면 Streamlit Cloud 앱이 자동으로 다시 배포됩니다.

## 커스터마이즈 팁

- **파일명 규칙이 다른 경우**: `src/matching.py`의 `STYLE_RE`, `AW_CODE_RE`, `DATE_TOKEN_RE`
  정규식을 실제 파일명 규칙에 맞게 수정하세요.
- **비교 민감도**: `src/render.py`의 `find_diff_regions()`에서 `threshold`(픽셀 밝기 차이
  민감도)와 `min_area_px`(무시할 최소 크기)를 조정할 수 있습니다.
- **렌더링 해상도**: `src/render.py`의 `RENDER_DPI`를 높이면 더 정밀하게 비교하지만 느려지고
  메모리를 더 씁니다(기본 150).
- **문구 추가/수정**: `src/i18n.py`의 `STRINGS` 딕셔너리에 ko/en/vi 세 언어를 모두 채워
  넣으면 됩니다.

## 알아두어야 할 점

- 자동 이미지 비교는 참고용입니다. 최종 승인 전에는 반드시 원본 파일로 직접 확인하세요.
- 파일이 크고(특히 배너형 큰 아트보드) 페이지 수가 많으면 비교에 시간이 걸릴 수 있습니다.
- 같은 카테고리에 파일이 1개뿐이면 비교할 대상이 없다는 안내만 표시됩니다(2개 이상부터 비교).
- Style/AW 번호를 인식하지 못한 파일은 "매칭되지 않은 파일" 목록에 표시됩니다.
