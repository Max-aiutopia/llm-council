---
name: llm-council
description: LLM 議會：把同一題並行發給三家外部模型（ChatGPT／codex、Gemini／agy、Grok／grok CLI），收回意見後由 Claude 當主席合成決議，並標註各家貢獻。觸發詞：「開議會」「召開議會」「問議會」「問問其他模型」「跨模型意見」「consult the council」。適用：策略、切角、架構這類開放性決策題。不適用：生圖生片、單純查資料、日常產出。
---

# LLM 議會（主席議事規則）

你是主席。三位外部議員透過訂閱制 CLI 出席：**ChatGPT**（`codex`）、**Gemini**（`agy`）、**Grok**（`grok`）。全程用使用者既有的訂閱登入，不需要 API key，不另外計費（只消耗各家訂閱額度）。

**模型配置（寫死在 `scripts/council.py` 的 `MEMBERS`）**：ChatGPT = gpt-5.5＋xhigh 推理；Gemini = 3.1 Pro (High)；Grok = grok-4.5＋high 推理。某席在 JSON 回報模型名稱錯誤，代表那家改版了，查該 CLI 現況後更新 `MEMBERS`。

## 流程

### 1. 擬 brief（最關鍵的一步）
- Brief 必須**自包含**：外部模型讀不到本機檔案，必要的脈絡（產品、市場、限制、本機資料的摘要）都要寫進去。
- 指定回覆語言，並給明確的輸出結構（例：3 個切角，各含名稱／邏輯／鉤子句），不然收回來很難合成。
- 要求議員直接講重點、不要客套、限制長度（例如 600 字）。
- **隱私閘門**：brief 送出就進了 OpenAI／Google／xAI 的伺服器。含客戶名稱、未公開數據、營業機密時，先給使用者看過 brief，或先脫敏（改代號、去數字），由使用者決定。一般策略題可以直接發。

### 2. 開會（跑腳本）
```bash
python3 ~/.claude/skills/llm-council/scripts/council.py --brief-file <brief 路徑>
# 短題直接：python3 ~/.claude/skills/llm-council/scripts/council.py "<brief>"
# 只問部分議員：--only chatgpt,grok；調逾時：--timeout 300
```
- Brief 長一點就寫成暫存檔，用 `--brief-file`，避免 shell 跳脫字元出問題。
- 輸出是 JSON：每位議員有 `ok/response/error/elapsed_s`。一家掛掉照常開會，決議裡如實註明哪位缺席、原因是什麼。
- 某家沒登入：ChatGPT 用 `codex login`、Gemini 直接執行 `agy` 走登入流程、Grok 用 `grok login`。這些要使用者本人在終端機操作，不要代跑。

### 3. 合成決議（主席的價值所在）
Claude 自己也要有立場，你是第四份意見，不是傳聲筒。決議格式：

1. **收斂點**：兩家以上獨立走到同一結論的，標為最強訊號，優先採納。
2. **建議排序**：合成後的方案列表（表格佳），每項標註來源（例：「ChatGPT＋Grok 合成」「Gemini 獨有」）。
3. **獨有貢獻**：只有某一家想到的點，單獨列出。
4. **風險與反對意見**：議員之間互相矛盾的地方如實呈現，附上主席裁決和理由，不要和稀泥。
5. **缺席聲明**：哪家沒回、為什麼。

### 4. 搭配本機資料
外部議員拿不到本機檔案，但 Claude 拿得到。做法：先從本機資料（評論、SOP、研究文件）萃取摘要放進 brief，讓三家帶著真實依據發言；合成時 Claude 再對照原始檔案驗證。

## 紀律
- 這是**諮詢工具**，不是生產工具。
- 三家 CLI 都是 coding agent，腳本讓它們在空目錄開會，不會讀到你的工作區。
- 預設逾時 360 秒；三家並行，一次議會要等的時間約等於最慢的那家。
