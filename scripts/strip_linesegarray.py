#!/usr/bin/env python3
"""HWPX 레이아웃 캐시(linesegarray) 제거 유틸리티

HWPX는 문단별 줄 높이/위치를 `<hp:linesegarray>` 로 미리 계산해
저장한다. ZIP-level 텍스트 치환을 거치면 이 캐시가 실제 본문과
어긋나 한글에서 빈 줄/겹침/이상 여백으로 렌더링된다.

이 스크립트가 모든 `<hp:linesegarray>` 를 제거하면, 한글이 파일을
열 때 강제로 재-레이아웃을 수행하여 올바르게 표시된다.

워크플로우: 텍스트 치환 → fix_namespaces.py → strip_linesegarray.py

사용법:
  python strip_linesegarray.py <file.hwpx>
"""
import re
import sys
import zipfile
import os


LSA = re.compile(r"<hp:linesegarray\b[^>]*>.*?</hp:linesegarray>", re.DOTALL)
LSA_SELF = re.compile(r"<hp:linesegarray\b[^/]*/>")


def strip(hwpx_path):
    tmp = hwpx_path + ".tmp"
    with zipfile.ZipFile(hwpx_path, "r") as zin:
        with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as zout:
            total = 0
            for item in zin.infolist():
                data = zin.read(item.filename)
                if item.filename.startswith("Contents/") and item.filename.endswith(".xml"):
                    t = data.decode("utf-8")
                    before = t.count("<hp:linesegarray")
                    t = LSA.sub("", t)
                    t = LSA_SELF.sub("", t)
                    total += before
                    data = t.encode("utf-8")
                zout.writestr(item, data)
    os.replace(tmp, hwpx_path)
    print(f"[strip_linesegarray] removed {total} cache entries from {hwpx_path}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python strip_linesegarray.py <file.hwpx>", file=sys.stderr)
        sys.exit(1)
    strip(sys.argv[1])
