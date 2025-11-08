import argparse
from pathlib import Path
import re

def combine_slides(slides_dir: Path):
    """
    Finds all .md files in a directory, sorts them numerically,
    and combines them into a single markdown file separated by '---'.
    """
    # 1. Validate input directory
    if not slides_dir.is_dir():
        print(f"❌ 錯誤：找不到指定的資料夾 '{slides_dir}'")
        return

    # 2. Find all markdown files
    print(f"🔍 正在搜尋 '{slides_dir}' 中的 .md 檔案...")
    slide_files = sorted(slides_dir.glob("*.md"))
    if not slide_files:
        print(f"🟡 在 '{slides_dir}' 中沒有找到任何 .md 檔案。")
        return

    # 3. Sort files numerically based on the prefix to be robust
    def get_numeric_prefix(p: Path) -> int:
        match = re.match(r'^(\d+)', p.name)
        # Return a large number for files that don't match, so they go to the end.
        return int(match.group(1)) if match else 9999

    slide_files.sort(key=get_numeric_prefix)

    # 4. Read content from each file
    all_content = []
    print("\n📑 將依照以下順序合併投影片：")
    for slide_path in slide_files:
        print(f"   - {slide_path.name}")
        all_content.append(slide_path.read_text(encoding="utf-8"))

    # 5. Combine content with a clear separator
    # Using four newlines (two before, two after) ensures good spacing in most Markdown renderers.
    combined_content = "\n\n---\n\n".join(all_content)

    # 6. Write to the output file in the parent directory
    output_file = slides_dir.parent / "combined_slides.md"
    try:
        output_file.write_text(combined_content, encoding="utf-8")
        print(f"\n✅ 成功！ {len(slide_files)} 頁投影片已合併至：")
        print(f"   -> {output_file.resolve()}")
    except Exception as e:
        print(f"\n❌ 錯誤：寫入檔案失敗。原因：{e}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="將 PPTPlaner 產生的多個 slide .md 檔案，合併成一個單獨的 Markdown 檔案。",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument(
        "slides_directory",
        type=str,
        help="包含投影片 .md 檔案的資料夾路徑。\n例如: output/20251108_143000_MyRun/slides"
    )
    args = parser.parse_args()

    # Create a Path object from the input string for robust handling
    slides_path = Path(args.slides_directory)

    combine_slides(slides_path)
