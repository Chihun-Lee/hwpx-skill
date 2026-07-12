# HWPX 문서 생성/편집 프로젝트

## 개요

HWPX는 한컴오피스 한글의 개방형 문서 포맷이다. 내부는 **ZIP 패키지 + XML 파트** 구조이며, KS X 6101(OWPML) 표준에 기반한다. 이 프로젝트는 `python-hwpx` 라이브러리를 사용하여 HWPX 문서를 프로그래밍 방식으로 생성/편집/템플릿 치환한다.

'한글 문서', 'hwpx', 'HWPX', '한글파일', '.hwpx 파일 만들어줘', 'HWP 문서 생성', '보고서', '공문', '기안문', '한글로 작성' 등의 키워드가 나오면 이 스킬을 사용할 것.

## 경로 규칙 (로컬 맥북 환경)

| 역할 | 경로 |
|------|------|
| 프로젝트 루트 | `/Users/chihun/Code/스킬/hwp_claude/` |
| 기본 양식 템플릿 | `/Users/chihun/Code/스킬/hwp_claude/assets/report-template.hwpx` |
| 네임스페이스 수정 스크립트 | `/Users/chihun/Code/스킬/hwp_claude/scripts/fix_namespaces.py` |
| 레퍼런스 문서 | `/Users/chihun/Code/스킬/hwp_claude/references/` |
| 작업 디렉토리 | `/Users/chihun/Code/스킬/hwp_claude/work/` |
| 출력 디렉토리 | `/Users/chihun/Code/스킬/hwp_claude/outputs/` |

## 설치

```bash
pip install python-hwpx
```

---

## 최우선 규칙: 양식(템플릿) 선택 정책

> **HWPX 문서를 만들 때 반드시 아래 순서를 따른다. 예외 없음.**

### 1단계: 사용자 업로드 양식이 있는가?

사용자가 `.hwpx` 양식 파일 경로를 지정했다면 **반드시 해당 파일을 템플릿으로 사용**한다.
- 사용자가 "이 양식으로 만들어줘", "이 파일 기반으로" 등의 표현을 쓰면 100% 해당 파일 사용

### 2단계: 기본 제공 양식 사용

사용자 업로드 양식이 없으면 **반드시 기본 제공 양식**을 사용한다:
- 보고서 -> `assets/report-template.hwpx`

### 3단계: HwpxDocument.new()는 최후의 수단

`HwpxDocument.new()`로 빈 문서를 만드는 것은 **아주 단순한 메모/목록 수준의 문서에만** 허용한다.

---

## 양식 활용 시 필수 워크플로우

어떤 양식을 쓰든 아래 워크플로우를 따른다:

```
[1] 양식 파일을 work/ 로 복사
     |
[2] ObjectFinder로 양식 내 텍스트 전수 조사 (+ 셀별 원본 길이 기록)
     |
[3] 플레이스홀더 목록 작성 (어떤 텍스트를 뭘로 바꿀지 매핑)
     |  새 텍스트는 원본 대비 ±15% 이내 길이로 작성 (표 셀 겹침 방지)
[4] ZIP-level 전체 치환 (표 내부 포함)
     |  (동일 플레이스홀더가 여러 번 나오면 순차 치환 사용)
[5] 네임스페이스 후처리 (fix_namespaces.py)
     |
[6] 레이아웃 캐시 제거 (strip_linesegarray.py)  ← 필수, 빈 줄/겹침 방지
     |
[7] 길이 검증 (verify_lengths.py) — 원본 대비 +15% 초과 셀 확인
     |
[8] ObjectFinder로 치환 결과 텍스트 검증
     |
[9] (NFEC 심의문서일 경우) 지침 부합성 검증 — references/nfec-checklist.md 참조
     |  - 8개 심의기준 본문 채움 확인 (사업부합성·국가전략·중복성·활용성·적정성·운영계획·관리실태·구축비용)
     |  - 필수 제출서류 체크 (심의요청서·구축계획서·비교견적서 2건+·사전기획보고서 10억+)
     |
[10] (권장) 한글에서 열어 레이아웃 시각 확인 후 outputs/ 로 복사
```

### 핵심: HwpxDocument.open()은 사용하지 않는다

`python-hwpx` 버전에 따라 `HwpxDocument.open()`이 복잡한 양식 파일을 파싱하지 못할 수 있다. **ZIP-level 치환만 사용**하는 것이 안전하다.

---

## ZIP-level 치환 함수 (직접 구현)

### 일괄 치환 (동일 텍스트를 모두 같은 값으로)

```python
import zipfile, os

def zip_replace(src_path, dst_path, replacements):
    """HWPX ZIP 내 모든 XML에서 텍스트 치환 (표 내부 포함)"""
    tmp = dst_path + ".tmp"
    with zipfile.ZipFile(src_path, "r") as zin:
        with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as zout:
            for item in zin.infolist():
                data = zin.read(item.filename)
                if item.filename.startswith("Contents/") and item.filename.endswith(".xml"):
                    text = data.decode("utf-8")
                    for old, new in replacements.items():
                        text = text.replace(old, new)
                    data = text.encode("utf-8")
                zout.writestr(item, data)
    if os.path.exists(dst_path):
        os.remove(dst_path)
    os.rename(tmp, dst_path)
```

### 순차 치환 (동일 플레이스홀더를 순서대로 다른 값으로)

```python
def zip_replace_sequential(src_path, dst_path, old, new_list):
    """section XML에서 old를 순서대로 new_list 값으로 하나씩 치환"""
    tmp = dst_path + ".tmp"
    with zipfile.ZipFile(src_path, "r") as zin:
        with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as zout:
            for item in zin.infolist():
                data = zin.read(item.filename)
                if "section" in item.filename and item.filename.endswith(".xml"):
                    text = data.decode("utf-8")
                    for new_val in new_list:
                        text = text.replace(old, new_val, 1)
                    data = text.encode("utf-8")
                zout.writestr(item, data)
    if os.path.exists(dst_path):
        os.remove(dst_path)
    os.rename(tmp, dst_path)
```

---

## 양식 내 텍스트 전수 조사 방법

```python
from hwpx import ObjectFinder

finder = ObjectFinder("양식파일.hwpx")
results = finder.find_all(tag="t")
for r in results:
    if r.text and r.text.strip():
        print(repr(r.text))
```

---

## 기본 양식(report-template.hwpx) 활용 가이드

### 양식 구조

```
1쪽: 표지      -> 기관명(30pt) + 보고서 제목(25pt) + 작성일(25pt)
2쪽: 목차      -> 로마숫자(I~V) + 제목 + 페이지, 붙임/참고
3쪽~: 본문     -> 결재란 + 제목(22pt) + 섹션 바(I~IV) + 본문 계층
```

### 본문 기호 체계

```
1단계:  □    (HY헤드라인M 16pt, 문단 위 15)
2단계:  ○    (휴먼명조 15pt, 문단 위 10)
3단계:  ―    (휴먼명조 15pt, 문단 위 6)
4단계:  ※    (한양중고딕 13pt, 문단 위 3)
```

### 치환 가능한 플레이스홀더 목록

| 플레이스홀더 | 위치 | 치환 방법 |
|------------|------|----------|
| `브라더 공기관` | 표지 기관명 | 일괄 치환 |
| `기본 보고서 양식` | 표지 제목 | 일괄 치환 |
| `2024. 5. 23.` | 표지 작성일 | 일괄 치환 |
| `제 목` | 본문 제목 | 일괄 치환 |
| `. 개요` 등 | 목차 항목 | 일괄 치환 |
| ` 추진 배경` 등 | 섹션 바 제목 | 일괄 치환 |
| `헤드라인M 폰트 16포인트(문단 위 15)` | □ 본문 (8개) | **순차 치환** |
| `  ○ 휴면명조 15포인트(문단위 10)` | ○ 본문 (8개) | **순차 치환** |
| `   ― 휴면명조 15포인트(문단 위 6)` | ― 본문 (8개) | **순차 치환** |
| `     ※ 중고딕 13포인트(문단 위 3)` | ※ 주석 (7개) | **순차 치환** |
| `  1. 세부내용` / `  2. 세부내용` | 붙임/참고 | 일괄 치환 |

### 기본 양식 사용 예시

```python
import shutil, subprocess

TEMPLATE = "/Users/chihun/Code/스킬/hwp_claude/assets/report-template.hwpx"
WORK = "/Users/chihun/Code/스킬/hwp_claude/work/report.hwpx"
OUTPUT = "/Users/chihun/Code/스킬/hwp_claude/outputs/report.hwpx"
shutil.copy(TEMPLATE, WORK)

# 1. 일괄 치환
zip_replace(WORK, WORK, {
    "브라더 공기관": "실제 기관명",
    "기본 보고서 양식": "실제 보고서 제목",
    "2024. 5. 23.": "2026. 4. 12.",
    "제 목": "실제 보고서 제목",
})

# 2. 순차 치환 (□, ○, ―, ※ 각각)
zip_replace_sequential(WORK, WORK,
    "헤드라인M 폰트 16포인트(문단 위 15)",
    ["첫번째 내용", "두번째 내용", ...]
)

# 3. 네임스페이스 후처리 (필수!)
subprocess.run(
    ["python", "/Users/chihun/Code/스킬/hwp_claude/scripts/fix_namespaces.py", WORK],
    check=True
)

# 4. 결과 검증
from hwpx import ObjectFinder
finder = ObjectFinder(WORK)
for r in finder.find_all(tag="t"):
    if r.text and r.text.strip():
        print(r.text)

# 5. 출력
shutil.copy(WORK, OUTPUT)
```

---

## 문서 유형별 스타일 가이드

- 보고서(내부 보고용) -> `references/report-style.md` 를 먼저 읽고 따를 것
- 공문서(기안문) -> `references/official-doc-style.md` 를 먼저 읽고 따를 것
- **연구과제 제안서/계획서 -> `references/korean-proposal-style.md` 를 먼저 읽고 따를 것**
- **NFEC 시설장비 심의문서 (심의요청서·구축계획서·사전기획보고서) -> `references/nfec-checklist.md` 를 먼저 읽고 따를 것 + 작성 후 8개 심의기준 체크리스트로 검증할 것**
- 저수준 XML 조작 -> `references/xml-internals.md` 를 읽을 것

### 연구과제 제안서 작성 핵심 규칙 (korean-proposal-style.md 요약)

1. **개조식 우선**: `○ 대항목 / - 세부항목` 형식. 통문장 회피
2. **명사형 종결**: "~할 계획임" → "~확보", "~하고자 함" → "~개발"
3. **쉼표 위주** 나열 (· 는 최소화, 사용자 선호)
4. **정량 표현**: "기술격차 ~년", "~억원", "~단계별" 로 구체화
5. **정부 키워드** 자연스럽게 배치: "12대 국가전략기술", "기술주권", "탄소중립", "글로벌 TOP"
6. 통과 표본은 `master_refrerence/*.pdf` 참고 (KIST 반도체, 에기연 수소, TOP CCU, 소재AI)

---

## 필수 후처리 (이 순서로 실행)

### 1단계: 네임스페이스 수정

> 빠뜨리면 한글 Viewer에서 빈 페이지로 표시된다.

```python
subprocess.run(
    ["python", "/Users/chihun/Code/스킬/hwp_claude/scripts/fix_namespaces.py", "output.hwpx"],
    check=True
)
```

### 2단계: 레이아웃 캐시 제거 (linesegarray)

> 빠뜨리면 치환한 셀에 빈 줄이 생기거나 텍스트가 겹쳐 보인다.
> HWPX 는 문단별 줄 높이/위치를 `<hp:linesegarray>` 로 미리 계산해 저장하므로,
> ZIP-level 치환 후에는 이 캐시가 stale 상태가 되어 한글이 잘못된 레이아웃으로 렌더링한다.
> 스페이스를 넣었다 지우면 정상화되는 현상의 원인.

```python
subprocess.run(
    ["python", "/Users/chihun/Code/스킬/hwp_claude/scripts/strip_linesegarray.py", "output.hwpx"],
    check=True
)
```

### 3단계: 길이 검증 (선택 권장)

```python
subprocess.run(
    ["python", "/Users/chihun/Code/스킬/hwp_claude/scripts/verify_lengths.py", "template.hwpx", "output.hwpx"],
    check=True
)
```

> `exec(open(...).read())` 방식은 오동작할 수 있다. 반드시 `subprocess.run()` 방식을 사용한다.

---

## 주의사항

1. **양식 우선**: 사용자 업로드 양식 > 기본 제공 양식 > HwpxDocument.new()
2. **ZIP-level 치환 우선**: HwpxDocument.open()보다 ZIP-level 치환이 안전
3. **3단계 후처리 필수**: `fix_namespaces.py` → `strip_linesegarray.py` → `verify_lengths.py`
4. **양식 텍스트 조사 필수**: 치환 전에 반드시 ObjectFinder로 텍스트 전수 조사
5. **셀 길이 원본 ±15% 이내 유지**: 표 셀 오버플로우 방지
6. **순차 치환 주의**: 동일 플레이스홀더가 여러 번 나오면 `zip_replace_sequential` 사용
7. **나열 구분자는 쉼표**: `·` 대신 `,` 사용 (사용자 선호, 원본의 · 는 보존)
8. **명사형 종결**: 제안서 본문은 "~할 계획임" → "~확보", "~하고자 함" → "~개발"
9. **공문서 날짜 형식**: `2026-02-13`이 아닌 `2026. 2. 13.` (월/일 앞 0 생략)
10. **HWPX만 지원**: python-hwpx는 HWPX만 처리. 레거시 `.hwp`는 한글에서 저장→HWPX 로 변환 필요
11. **`.hwp` → `.hwpx` 변환 후 보안 경고**: 한글 보안 설정 문제일 뿐 파일 이상 아님 (환경설정→보안→낮음)
12. **fix_namespaces 호출법**: `exec()` 말고 `subprocess.run()` 사용
13. **보고서/공문서/제안서 스타일**: `references/*.md` 를 작업 전에 먼저 읽을 것
