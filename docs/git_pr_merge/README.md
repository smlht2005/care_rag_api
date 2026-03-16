# Care RAG API Git 分支與 PR Merge 流程說明

更新時間：2026-03-13 14:40
作者：AI Assistant
修改摘要：整理本次 `feature/ic-query-qa-refactor` 分支從開發、PR、審查到合併的實際操作步驟，作為未來 Git 分支與 PR 作業的標準參考文件。

---

## 一、分支策略與命名建議

- **主分支：**
  - `main`：穩定可部署版本，僅透過 PR 合併。
- **功能分支（Feature Branch）：**
  - 命名建議：`feature/<主題>`，例如：
    - `feature/ic-query-qa-refactor`
  - 從 `main` 切出（以下三步驟說明如下）：

```bash
git checkout main
git pull origin main
git checkout -b feature/ic-query-qa-refactor
```

對應說明：

- `git checkout main`  
  切換到本機的 `main` 分支，確保接下來的新功能分支是從主幹開出來的。

- `git pull origin main`  
  從遠端 `origin` 把 `main` 最新的 commit 拉下來並合併到本機 `main`，避免之後 PR 時出現「你是從舊 main 開分支」造成不必要的 diff。

- `git checkout -b feature/ic-query-qa-refactor`  
  以目前已更新到最新狀態的 `main` 為基準，新開一個功能分支 `feature/ic-query-qa-refactor`，並同時切換到這個分支，在其上進行本次 IC/QA 重構與測試相關開發。

---

## 二、本機開發與測試流程

1. **開發階段**
   - 在 `feature/...` 分支上修改程式與文件。
   - 嚴格遵守專案規則（如：不將 .db 等建置產物納入版本控制）。

2. **本機測試**

```bash
python -m pytest
```

必要時可針對單一模組執行，例如：

```bash
python -m pytest tests/test_core/test_orchestrator_llm_calls.py -v
python -m pytest tests/test_core/test_skip_cache.py -v
python -m pytest tests/test_services/test_stub_embedding_determinism.py -v
```

3. **提交變更**

```bash
git status
git add <變更檔案>
git commit -m "feat/fix: 描述此次變更重點"
git push -u origin feature/ic-query-qa-refactor
```

---

## 三、在 GitHub 建立 PR 的流程

1. 開啟瀏覽器前往：
   - `https://github.com/smlht2005/care_rag_api`
2. 建立 PR：
   - 點選 **Pull requests → New pull request**。
   - **base branch**：`main`
   - **compare branch**：`feature/ic-query-qa-refactor`
3. 填寫 PR 資訊：
   - **Title**：簡潔描述，如：`Add IC/QA refactor, tests, and docs`。
   - **Description**：建議包含：
     - 變更摘要（refactor 範圍、功能新增/修正）
     - 測試情況（執行哪些 pytest、結果是否通過）
     - 風險與相容性說明
4. 按下 **Create pull request** 建立 PR（例如 PR #1）。

---

## 四、PR 審查與修正（Code Review 回應）

1. **在 GitHub 上做 Review**
   - 進入 PR 頁面（例如：`https://github.com/smlht2005/care_rag_api/pull/1`）。
   - 使用 **Files changed** 檢視所有變更檔案。
   - 針對特定行留下註解，或在整體層級給出建議（安全性、可維護性、效能、測試覆蓋率等）。

2. **根據 Review 修正程式**
   - 依照 review 意見在 `feature/...` 分支持續修改，例如：
     - 修正 FastAPI DI bug（lambda Depends → 直接 Depends(get_xxx)）。
     - 讓 `StubEmbeddingService` 使用 `hashlib.sha256` 確保 deterministic。
     - 補上 `skip_cache` 與 LLM 呼叫次數的測試。
   - 每次修正後：

```bash
python -m pytest  # 確認所有測試通過
git add ...
git commit -m "fix: address PR review - <說明>"
git push
```

3. **更新開發記錄**
   - 在 `dev_readme.md` 的更新歷史中，記錄本次 PR 修正重點與測試結果，保留完整時間軸。

---

## 五、GitHub Actions / CI 狀態確認

- 若專案有設定 GitHub Actions：
  - 於 PR 頁面右側或下方的 **Checks / GitHub Actions** 檢查執行結果。
  - 必須等所有 workflow 變成 **Success（綠燈）** 才合併。
- 本次實例：
  - 針對 PR #2（說明 zh-TW merge-gate 文案）中，會等待 `Running Copilot coding agent` 等 workflow 成功後再允許合併。

---

## 六、在 GitHub 上合併 PR（Squash and merge）

當 PR 顯示：

- `No conflicts with base branch`
- Checks / Actions 全部 Success

操作步驟：

1. 進入 PR 頁面（例如 PR #1）。
2. 在綠色區塊下方找到：
   - 綠色按鈕：`Squash and merge`
3. 點擊 `Squash and merge`：
   - GitHub 會顯示一個視窗，包含最終的 **squash commit message**。
   - 可以保留預設訊息或稍作調整（建議以 PR 標題為主）。
4. 按下 **Confirm squash and merge**：
   - 會將 `feature/...` 分支上的所有 commits 壓縮為一個 commit，合併到 `main`。

**Squash and merge 的含義：**

- 保留「所有程式碼變更」，但在 `main` 上只新增一個乾淨的 commit。
- 適合：
  - 功能分支在開發過程有很多中途 commits（修 typo、加 log 等）。
  - 希望 `main` 的 commit 歷史簡潔，方便日後 rollback 與檢視。

---

## 七、合併後的收尾工作

1. **刪除遠端分支（選擇性但建議）**
   - 在 PR 已合併後，GitHub 會顯示：
     - `Pull request successfully merged and closed`
     - 右側有 `Delete branch` 按鈕。
   - 建議點擊 `Delete branch`，刪除遠端的 `feature/ic-query-qa-refactor`，保持遠端分支清爽。

2. **本機同步 main 並清理分支**

```bash
cd C:\Development\langChain\source\care_rag\care_rag_api

git checkout main
git pull origin main

# 若 feature 分支已無需使用，可在本機刪除
git branch -d feature/ic-query-qa-refactor
```

3. **再次驗證測試**

```bash
python -m pytest
```

確保合併後的 `main` 分支在本機環境中也能完整通過測試。

---

## 八、未來 PR 作業建議 Checklist

- **建立分支前**
  - [ ] 確認 `main` 已拉到最新。
- **開發過程**
  - [ ] 所有變更集中在 `feature/...` 分支。
  - [ ] 不將 `.db` 等建置產物加入 Git。
- **提交 PR 前**
  - [ ] 本機 `python -m pytest` 全部通過。
  - [ ] 重要行為、測試結果已記錄在 `dev_readme.md`。
- **PR 審查過程**
  - [ ] 針對 review 意見逐項修正並回覆。
  - [ ] 遇到設計衝突，先更新設計文件再改程式。
- **合併前**
  - [ ] PR 顯示「No conflicts with base branch」。
  - [ ] 所有 GitHub Actions / Checks 成功（綠燈）。
  - [ ] 使用 **Squash and merge**，保持 `main` 歷史乾淨。
- **合併後**
  - [ ] 刪除遠端 feature 分支（按 GitHub 的 `Delete branch`）。
  - [ ] 本機 `git checkout main && git pull` 同步。
  - [ ] 再跑一次主要測試，確保一切正常。

本文件以本次 `feature/ic-query-qa-refactor` 與 PR #1、PR #2 的實際經驗為範例，可作為未來 Git 分支與 PR 作業的標準操作說明。

