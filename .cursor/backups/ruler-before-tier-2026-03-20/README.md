# Ruler 備份：導入變更分級前（2026-03-20）

## 備份說明

- **備份時點**：導入 `.cursor/rules/*.mdc` 變更治理規則之前。
- **專案內 `.cursor` 狀態**：僅存在執行期除錯日誌（`debug.log`、`debug_1.log`），**尚無** Cursor Project Rules（`.mdc`）檔案。
- **使用者／全域規則**：若你原先將規則寫在 Cursor **User Rules** 或 **Project Rules（UI）**，其內容**不在 git 內**；請視需要自行從 Cursor 設定複製到本目錄留存。

## 本目錄檔案

| 檔案 | 說明 |
|------|------|
| `user-rules-legacy-snapshot.md` | 自對話脈絡整理之「舊版常用規則」文字快照，供對照；**非** Cursor 官方匯出格式。 |
| `INVENTORY.md` | 備份當下 repo 內 `.cursor` 檔案清單。 |

## 還原方式

- 若要回到「僅依賴使用者規則、無專案 `.mdc`」：刪除或重新命名 `.cursor/rules/` 目錄即可（建議先另存一份再刪）。
