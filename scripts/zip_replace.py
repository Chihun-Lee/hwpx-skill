#!/usr/bin/env python3
"""HWPX ZIP-level 텍스트 치환 공통 유틸리티

HwpxDocument.open()은 복잡한 양식에서 실패할 수 있으므로
ZIP 내부 XML을 직접 열어 문자열 치환한다.

제공 함수:
  zip_replace(src, dst, replacements: dict)
      일괄 치환 (동일 old → 동일 new, 모든 위치)
  zip_replace_sequential(src, dst, old, new_list)
      순차 치환 (동일 old → 리스트를 순서대로 하나씩)

두 함수 모두 Contents/*.xml 만 손대며, 이미지/바이너리는 그대로 보존.
치환 후 반드시 fix_namespaces.py + strip_linesegarray.py 후처리 권장.
"""
import os
import zipfile


def zip_replace(src_path, dst_path, replacements):
    """HWPX ZIP 내 Contents/*.xml 에서 문자열 일괄 치환."""
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


def zip_replace_sequential(src_path, dst_path, old, new_list):
    """section*.xml 에서 동일 old 를 순서대로 new_list 값들로 하나씩 치환."""
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


def check_unique(src_path, old_texts):
    """치환 전 검증: 각 old_text 가 Contents/*.xml 에서 정확히 1회 나오는지 확인.
    반환: (missing[], duplicates[])"""
    missing, dup = [], []
    with zipfile.ZipFile(src_path, "r") as zin:
        blob = "\n".join(
            zin.read(n).decode("utf-8")
            for n in zin.namelist()
            if n.startswith("Contents/") and n.endswith(".xml")
        )
    for t in old_texts:
        c = blob.count(t)
        if c == 0:
            missing.append(t[:80])
        elif c > 1:
            dup.append((c, t[:80]))
    return missing, dup
