#!/usr/bin/env python3
"""HWPX 치환 전후 텍스트 길이 비교 유틸리티

표 셀 등 고정 높이 영역에 원본보다 긴 텍스트를 넣으면 겹침이 발생.
원본 대비 각 <hp:t> 길이를 비교해 +15% 초과 항목을 경고로 표시한다.

사용법:
  python verify_lengths.py <original.hwpx> <new.hwpx> [threshold=1.15]
"""
import sys
from hwpx import ObjectFinder


def main(orig_path, new_path, threshold=1.15):
    ro = ObjectFinder(orig_path).find_all(tag="t")
    rn = ObjectFinder(new_path).find_all(tag="t")
    n = min(len(ro), len(rn))

    over = []
    diffs = []
    for i in range(n):
        to = ro[i].text or ""
        tn = rn[i].text or ""
        if not to.strip() and not tn.strip():
            continue
        lo, ln = len(to), len(tn)
        if lo == 0:
            continue
        ratio = ln / lo
        if ratio > threshold:
            over.append((i, lo, ln, tn[:60]))
        diffs.append((i, lo, ln))

    print(f"=== Length comparison ({orig_path} vs {new_path}) ===")
    print(f"Compared {len(diffs)} non-empty cells, {len(over)} exceed {threshold:.0%}\n")

    if over:
        print("Cells exceeding threshold (potential overlap):")
        print(f"{'idx':>5} {'orig':>5} {'new':>5} {'ratio':>6}  preview")
        for i, lo, ln, prev in over:
            print(f"{i:>5} {lo:>5} {ln:>5} {ln/lo:>6.1%}  {prev}")
    else:
        print("All cells within threshold. OK.")

    return len(over)


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python verify_lengths.py <original.hwpx> <new.hwpx> [threshold]",
              file=sys.stderr)
        sys.exit(1)
    th = float(sys.argv[3]) if len(sys.argv) >= 4 else 1.15
    sys.exit(min(main(sys.argv[1], sys.argv[2], th), 1))
