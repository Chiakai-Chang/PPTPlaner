#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PPTPlaner Validator
- 檢查 slides/ 與 notes/ 是否一一對齊（同頁碼）
- 檢查備忘稿是否包含英文術語（是否有英文字母）
- 估算備忘稿口述時間（中英文字數 → 分鐘），是否落在設定範圍
- Windows / macOS / Linux 皆可用

用法：
  python scripts/validate.py \
    --slides-dir slides \
    --notes-dir notes \
    --check-alignment true \
    --check-keywords true \
    --check-time true \
    --time-min 2 \
    --time-max 3
"""

from __future__ import annotations
import sys
import argparse
import re
from pathlib import Path

# ----------------------------
# Utils
# ----------------------------

def str2bool(s: str) -> bool:
    return str(s).strip().lower() in {"1", "true", "yes", "y", "on"}

def read_text(p: Path) -> str:
    try:
        return p.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        # 最後一招：用 errors ignore 避免因編碼失敗中斷
        return p.read_text(encoding="utf-8", errors="ignore")

def extract_page_topic(filename: str) -> tuple[str | None, str | None]:
    """
    盡量從檔名推斷 page 與 topic。
    規則（盡量相容）：
      - 取第一組連續數字作為 page（01、1、007 均可）
      - topic 取第一個 '_' 或 '-' 後到副檔名之間的字串（若存在）
    """
    name = filename
    # 去副檔名
    if "." in name:
        name = ".".join(name.split(".")[:-1])

    # page: 第一組數字
    m_page = re.search(r"(\d{1,3})", name)
    page = None
    if m_page:
        page = f"{int(m_page.group(1)):02d}"

    topic = None
    m_topic = re.search(r"(?:^|[_-])([A-Za-z0-9][\w\-]*)$", name)  # 取最後一段
    if m_topic:
        topic = m_topic.group(1)

    return page, topic

def estimate_speaking_minutes(text: str) -> float:
    """
    粗略估算口述時間（分鐘）：
      - 中文（含 CJK）：以每分鐘 ~250 字估算
      - 英文（含數字單詞）：以每分鐘 ~150 單詞估算
    公式： time = (CJK_count / 250) + (EN_words / 150)
    """
    # CJK 字元：\u4E00-\u9FFF 基本漢字 + 擴展 A（可再擴）
    cjk_chars = re.findall(r"[\u4e00-\u9fff]", text)
    cjk_count = len(cjk_chars)

    # 英文/數字詞
    en_words = re.findall(r"[A-Za-z0-9][A-Za-z0-9\-]*", text)
    # 但把全為數字的長編號稍微折扣（不計入英詞數）
    en_words = [w for w in en_words if re.search(r"[A-Za-z]", w)]

    return (cjk_count / 250.0) + (len(en_words) / 150.0)

def has_english_terms(text: str) -> bool:
    """
    是否有英文字母（A–Z / a–z）。
    目的：確認備忘稿保留原文術語（研究者名、模型、實驗名等）。
    """
    return bool(re.search(r"[A-Za-z]", text))

def load_files_map(folder: Path, exts=(".md", ".txt")) -> dict[str, Path]:
    """
    掃描資料夾，回傳 { page -> Path } 的對應（若同頁碼多檔，取字母序最前）。
    """
    mapping: dict[str, Path] = {}
    for p in folder.rglob("*"):
        if p.is_file() and p.suffix.lower() in exts:
            page, _ = extract_page_topic(p.name)
            if page:
                # 若已有同頁，保留字母序最小者（避免覆蓋較「穩定」的命名）
                if page not in mapping or str(p) < str(mapping[page]):
                    mapping[page] = p
    return mapping

# ----------------------------
# Main
# ----------------------------

def main():
    ap = argparse.ArgumentParser(description="Validate slides & notes quality/alignment.")
    ap.add_argument("--slides-dir", required=True, help="slides 目錄")
    ap.add_argument("--notes-dir", required=True, help="notes 目錄")
    ap.add_argument("--check-alignment", default="true", help="是否檢查對齊（true/false）")
    ap.add_argument("--check-keywords",  default="true", help="是否檢查英文術語（true/false）")
    ap.add_argument("--check-time",      default="true", help="是否檢查口述時間（true/false）")
    ap.add_argument("--time-min", type=float, default=2.0, help="每頁口述時間下限（分鐘）")
    ap.add_argument("--time-max", type=float, default=3.0, help="每頁口述時間上限（分鐘）")
    args = ap.parse_args()

    slides_dir = Path(args.slides_dir).resolve()
    notes_dir  = Path(args.notes_dir).resolve()

    if not slides_dir.exists():
        print(f"⚠ slides 目錄不存在：{slides_dir}", file=sys.stderr)
    if not notes_dir.exists():
        print(f"⚠ notes 目錄不存在：{notes_dir}", file=sys.stderr)

    check_alignment = str2bool(args.check_alignment)
    check_keywords  = str2bool(args.check_keywords)
    check_time      = str2bool(args.check_time)

    time_min = float(args.time_min)
    time_max = float(args.time_max)

    errors = 0
    warns  = 0

    # 掃描檔案
    slide_map = load_files_map(slides_dir)
    note_map  = load_files_map(notes_dir)

    pages_all = sorted(set(slide_map.keys()) | set(note_map.keys()))

    print("── 檔案概況 ─────────────────────────")
    print(f"slides: {len(slide_map)} 檔 | notes: {len(note_map)} 檔 | 合計頁面：{len(pages_all)}")
    print()

    # 1) Alignment
    if check_alignment:
        print("▶ 對齊檢查（Alignment）")
        missing_notes = [p for p in sorted(slide_map.keys()) if p not in note_map]
        missing_slides = [p for p in sorted(note_map.keys()) if p not in slide_map]

        if missing_notes:
            errors += 1
            print(f"  ✗ 下列頁面缺少 notes：{', '.join(missing_notes)}")
        if missing_slides:
            # 這通常是流程上問題，也算錯誤
            errors += 1
            print(f"  ✗ 下列頁面缺少 slides：{', '.join(missing_slides)}")

        if not missing_notes and not missing_slides:
            print("  ✓ slides 與 notes 頁碼一一對齊")
        print()

    # 2) Keywords (English terms)
    if check_keywords and note_map:
        print("▶ 英文術語檢查（English terms present）")
        for page in sorted(note_map.keys()):
            note_path = note_map[page]
            text = read_text(note_path)
            if not has_english_terms(text):
                warns += 1
                print(f"  ⚠ 第 {page} 頁：未偵測到英文字母（可能未保留英文原文術語） → {note_path.name}")
        if warns == 0:
            print("  ✓ 備忘稿皆含英文字母（保留原文術語）")
        print()

    # 3) Time estimation
    if check_time and note_map:
        print("▶ 口述時間估算（Target: %.1f–%.1f 分鐘/頁）" % (time_min, time_max))
        too_short, too_long = [], []
        for page in sorted(note_map.keys()):
            note_path = note_map[page]
            minutes = estimate_speaking_minutes(read_text(note_path))
            if minutes < time_min - 0.15:  # 容忍微小誤差
                too_short.append((page, minutes, note_path.name))
            elif minutes > time_max + 0.15:
                too_long.append((page, minutes, note_path.name))
        if too_short:
            errors += 1
            print("  ✗ 過短頁面（可能過於精簡，教學內容不足）：")
            for p, m, fn in too_short:
                print(f"    - 第 {p} 頁：{m:.2f} 分 → {fn}")
        if too_long:
            errors += 1
            print("  ✗ 過長頁面（可能超過 3 分鐘，建議拆分或刪減）：")
            for p, m, fn in too_long:
                print(f"    - 第 {p} 頁：{m:.2f} 分 → {fn}")
        if not too_short and not too_long:
            print("  ✓ 各頁口述時間落在合理範圍")
        print()

    # 結論
    print("── 檢查結論 ────────────────────────")
    if errors == 0:
        print("✓ 驗證通過。")
        if warns > 0:
            print(f"⚠ 有 {warns} 則提醒（非致命），建議調整後再發佈。")
        sys.exit(0)
    else:
        print(f"✗ 驗證未通過：發現 {errors} 類錯誤。請修正後重跑。")
        sys.exit(1)

if __name__ == "__main__":
    main()
