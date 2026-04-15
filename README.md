# hwpx-skill

**Claude Code / Claude Desktop 용 HWPX(한글) 문서 생성·편집 스킬.**

한컴오피스 한글의 `.hwpx` 포맷을 프로그래밍 방식으로 다룹니다. 보고서·공문·기안문·연구과제 제안서 양식을 템플릿으로 삼아, 본문을 프로그램이 채워 넣는 워크플로우를 제공합니다.

---

## 주요 기능

- HWPX 양식 파일 내 **ZIP-level 텍스트 치환** (표 내부 포함)
- **네임스페이스 후처리** — macOS 한글 Viewer 에서 빈 페이지로 뜨는 문제 해결
- **레이아웃 캐시(`linesegarray`) 제거** — 치환 후 발생하는 빈 줄/겹침 문제 근본 해결
- **셀 길이 검증** — 원본 대비 ±15% 초과 셀 자동 경고
- **보고서 기본 양식** 내장 (`assets/report-template.hwpx`)
- **문서 유형별 스타일 가이드** 내장 (`references/*.md`)
  - 보고서, 공문서, 연구과제 제안서, XML 내부 구조

## 설치

### Claude Desktop (skill):

```bash
cd ~/.claude/skills/
git clone https://github.com/Chihun-Lee/hwpx-skill.git hwpx
```

### Claude Code (프로젝트):

해당 프로젝트 루트에서:
```bash
git clone https://github.com/Chihun-Lee/hwpx-skill.git
```
그 후 Claude Code 가 `CLAUDE.md` / `SKILL.md` 를 자동 인식.

### 의존성

```bash
pip install python-hwpx
```

## 사용법

**"이 양식으로 보고서 만들어줘"**, **"hwpx 파일 만들어줘"**, **"제안서 작성"** 등의 요청을 Claude 에게 하면 자동 활성화됩니다.

예:
```
사용자: assets/report-template.hwpx 로 "AI 소재 연구 보고서" 만들어줘.
        기관명은 재료연구원, 작성일 2026. 4. 13.
```

Claude 가 ZIP-level 치환 → 네임스페이스 수정 → 캐시 제거 → 길이 검증 파이프라인을 자동 실행합니다.

## 워크플로우 (Claude 내부 자동 수행)

```
1. 양식 선택 (사용자 업로드 > assets/ 기본 양식 > new() 최후수단)
2. ObjectFinder 로 텍스트 전수 조사 + 원본 길이 기록
3. 새 텍스트 작성 (원본 ±15% 길이, 쉼표 사용, 명사형 종결)
4. ZIP-level 치환
5. fix_namespaces.py     → 네임스페이스 표준화
6. strip_linesegarray.py → 레이아웃 캐시 제거 (필수!)
7. verify_lengths.py     → 길이 검증
8. 한글에서 시각 확인 (권장)
```

## 디렉토리 구조

```
hwpx/
├── SKILL.md                 # Claude Skill 진입점 (Desktop)
├── CLAUDE.md                # Claude Code 프로젝트 지침 (동일 내용)
├── assets/
│   └── report-template.hwpx # 보고서 기본 양식
├── references/
│   ├── report-style.md          # 보고서 스타일 가이드
│   ├── official-doc-style.md    # 공문서 스타일 가이드
│   ├── korean-proposal-style.md # 국내 연구과제 제안서 스타일 가이드
│   └── xml-internals.md         # HWPX XML 내부 구조 참고
└── scripts/
    ├── fix_namespaces.py        # ns0/ns1 자동 프리픽스 → 한컴 표준
    ├── strip_linesegarray.py    # 레이아웃 캐시 제거
    ├── verify_lengths.py        # 셀 길이 검증
    └── zip_replace.py           # ZIP-level 치환 유틸
```

## 한계

- `.hwp` (레거시 포맷)은 지원 안 함 — 한글에서 "다른 이름으로 저장 → .hwpx" 로 변환 필요
- `HwpxDocument.open()` 은 복잡한 양식에서 실패할 수 있어 ZIP-level 치환 우선 사용
- 한글에서 "문서보안 낮음으로 설정" 경고는 파일 문제가 아닌 한글 보안 정책 문제 (환경설정→보안→낮음)

## 라이선스

MIT
