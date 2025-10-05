# PDF 轉 Markdown 指南

以下整理三種常用方式，協助將原文書（PDF）轉換為 `.md` 檔案，供 PPTPlaner 使用。

## 1. Docling（建議優先）
- 專案：<https://github.com/docling-project/docling>
- 安裝（需 Python 3.9+）：
  ```bash
  pip install docling
  ```
- 基本用法：
  ```bash
  docling extract your_chapter.pdf --format markdown --output Chapter07.md
  ```
- 優點：保留標題層級、段落架構與列表格式。

## 2. MinerU Extractor
- 下載：<https://mineru.net/OpenSourceTools/Extractor>
- 適合人員：對 GUI 工具較熟悉者，或需要輸出多種格式（`.html`、`.md`、LaTeX）。
- 操作步驟：
  1. 安裝後開啟程式，匯入 PDF。
  2. 選擇輸出格式為 Markdown。
  3. 下載完成後，將檔案重新命名為 `ChapterXX.md`。
- 注意：若文本含公式，MinerU 的 LaTeX 輸出可做後續編修。

## 3. AnyIMG_to_Markdown GPT
- 網址：<https://chatgpt.com/g/g-68e122adb2508191ad323ad85385d7f3-anyimg-to-markdown>
- 適用情境：PDF 僅能轉為圖片或 OCR 品質較佳時。
- 操作步驟：
  1. 將 PDF 逐頁輸出為圖片（jpg/png）。
  2. 將圖片上傳至上述 GPT，要求轉成 Markdown。
  3. 合併輸出並整理段落後存成 `ChapterXX.md`。
- 提示：若 GPT 內容有錯漏，可搭配人工修正或再次上傳修補。

## 檔案命名建議
- 章節檔名：`ChapterXX.md`（例如 `Chapter05.md`）。
- 保留原 PDF 於 `source/` 或 `docs/raw/` 以備追溯。
- 轉換完成後檢查：
  - 標題層級 (`#`, `##`, `###`)
  - 列表是否正確對齊
  - 圖片、表格是否需額外使用 mermaid 或手動重繪

完成上述步驟後，即可按照 README 的流程，使用 Codex CLI 產出 slides / notes / diagrams / 指引等檔案。
