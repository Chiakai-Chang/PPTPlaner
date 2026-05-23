# PPTPlaner 參考研究指南 (Research & Distillation Guide)
> 版本：v1.0 | 適用對象：負責研究外部 repo 並優化本專案的 AI 代理

本文件定義當使用者提供外部 GitHub repo 連結時，AI 代理應如何有系統地研究、評估、並將有價值的設計導入 PPTPlaner，同時確保本 repo 保持乾淨、不受汙染。

---

## 核心原則：智慧萃取，而非盲目搬運

追求「邏輯的精煉」，不是「功能的複製貼上」。

- **價值優先**：導入的唯一理由是該設計能讓 PPTPlaner 更好用、品質更高、或覆蓋更多場景
- **高保真萃取**：一旦決定導入某個想法，確保其核心邏輯完整，非殘廢式閹割版
- **果斷放棄**：若設計讓 PPTPlaner 變臃腫、難維護、或增加使用者安裝負擔，直接略過
- **Config 優先**：優先採用 `config.yaml` 可控制的整合方式，避免硬編碼行為

---

## 研究流程 SOP

### 第一步：隔離 Clone（執行前必看）

```bash
# 在 PPTPlaner 根目錄下操作
git clone <使用者提供的 repo URL> research/<repo名稱>/
```

**確認 `.gitignore` 包含 `research/`，確保研究素材不會被提交到本 repo。**

若 `.gitignore` 尚未設定，立即補上：
```
# Research (external repos cloned for evaluation only)
research/
```

---

### 第二步：戰略評估（SWOT）

閱讀 clone 回來的 repo 後，針對 PPTPlaner 進行分析：

| 面向 | 問題 |
|------|------|
| **優勢 (S)** | 這個 repo 有什麼是 PPTPlaner 目前缺少的？對哪個場景特別有用？ |
| **劣勢 (W)** | 導入它的代價是什麼？會讓使用者需要安裝額外工具嗎？ |
| **機會 (O)** | 它是否能補強 PPTPlaner 的某個弱點（如：影片輸出、視覺風格、互動性）？ |
| **威脅 (T)** | 它的設計假設是否與 PPTPlaner「Source MD → 高品質簡報」的核心流程衝突？ |

---

### 第三步：決策矩陣（TOWS）

根據 SWOT 推演最適的導入路徑：

| 策略 | 條件 | 行動 |
|------|------|------|
| **SO** | 設計強大且與現有 pipeline 相容 | 深度整合，加入 `config.yaml` 控制開關 |
| **WO** | 設計有價值但過於龐大或有外部依賴 | 只萃取核心概念或 API 介面，設為 optional 功能 |
| **ST** | 設計好但更新頻繁不穩 | 以快照方式導入，標記來源，不追蹤上游 |
| **WT** | 代價高於收益 | **果斷放棄**，記錄原因即可 |

---

### 第四步：導入目標對照表

評估後，將有價值的設計對應到 PPTPlaner 的具體文件：

| 外部設計 | 可能影響的 PPTPlaner 文件 |
|---------|--------------------------|
| 更好的文件切分邏輯 | `scripts/orchestrate.py` |
| 更精良的 Prompt 框架 | `scripts/prompts/*.md` |
| 新的輸出格式或媒體類型 | `scripts/orchestrate.py` + 新 phase prompt |
| 視覺模板設計 | `templates/` 或新的 `video/templates/` |
| Config 參數設計 | `config.yaml` + `scripts/orchestrate.py` 的 config 讀取邏輯 |
| 整體工作流程優化 | `docs/` 設計文件 |
| 驗證機制改進 | `scripts/validate.py` + `scripts/prompts/VALIDATE_*.md` |

---

### 第五步：執行導入 + 更新文件

確認導入路徑後：

1. 修改對應的 PPTPlaner 文件（prompts/、scripts/、templates/、config.yaml）
2. 若影響整體架構設計，同步更新 `docs/` 下的設計文件
3. 在 `docs/research/RATIONALE.md` 記錄：
   - 參考了哪個 repo 的哪個設計
   - 為什麼選擇導入（或放棄）
   - 做了哪些調整以符合 PPTPlaner 的架構

---

### 第六步：驗收檢查

導入完成後自我檢核：

- [ ] 導入的設計是否讓 PPTPlaner 的輸出品質更好？
- [ ] 是否維持「source MD → 高品質簡報+備忘稿」的核心體驗？
- [ ] 新功能是否用 `config.yaml` 開關控制，預設關閉不影響現有使用者？
- [ ] 有無增加強制性的額外安裝依賴？（若有，是否值得？）
- [ ] `research/` 是否確實在 gitignore 中，沒有汙染本 repo？
- [ ] 相關文件是否已同步更新？

---

## 嚴禁行為

- **嚴禁** 將 research/ 裡的原始碼直接複製進本 repo
- **嚴禁** 引入讓使用者必須安裝額外系統工具才能執行核心功能的依賴
- **嚴禁** 因為「某個設計很酷」就導入，必須有明確的 PPTPlaner 使用場景
- **嚴禁** 導入後不記錄來源與理由（黑箱操作）

---

## 快速參考：PPTPlaner 的核心設計約束

在評估任何外部設計時，必須確保不違反以下約束：

1. **Source-driven**：一切從 source 文件出發，不允許跳過文件分析直接生成
2. **Agent-agnostic**：PPTPlaner 支援多種 AI agent，不應綁定特定廠商
3. **Config as control**：所有功能開關都應反映在 `config.yaml`，使用者不需改程式碼
4. **Optional by default**：新增功能預設關閉，不影響現有使用者的基本工作流
5. **進度可見**：所有執行結果寫入結構化目錄（slides/、notes/、output/），人眼可讀
6. **品質循環**：重要輸出有 rework 機制（max_reworks 設定），確保品質可控
