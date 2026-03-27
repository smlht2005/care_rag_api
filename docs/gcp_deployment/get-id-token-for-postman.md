# 產生 Cloud Run IAM 用 ID token（Postman `bearerToken`）

更新時間：2026-03-27 09:10

與 `docs/postman/Care_RAG_API_CloudRun_IAM.postman_README.md` 相同目的：用 **gcloud** 產生 **ID token**，貼到 Postman Environment 的 **`bearerToken`**。

## 變數（請依實際部署修改）

| 名稱 | 範例值 |
|------|--------|
| Cloud Run 根 URL | `https://care-rag-api-441535054378.asia-east1.run.app` |
| Impersonate 用 SA | `441535054378-compute@developer.gserviceaccount.com` |

## 方法 1：Windows CMD

```bat
set URL=https://care-rag-api-441535054378.asia-east1.run.app
set SA=441535054378-compute@developer.gserviceaccount.com
for /f "delims=" %T in ('gcloud auth print-identity-token --audiences=%URL% --impersonate-service-account=%SA%') do set TOKEN=%T
echo %TOKEN%
```

## 方法 2：Python 一行（建議，Windows 相容）

在 Windows 上，勿用 `subprocess.check_output(['gcloud', ...])`（易出現 **WinError 2：找不到 gcloud**）。請先用 `shutil.which` 找 `gcloud` 或 `gcloud.cmd`：

```bat
python -c "import subprocess,shutil; g=shutil.which('gcloud') or shutil.which('gcloud.cmd'); print(subprocess.check_output([g,'auth','print-identity-token','--audiences=https://care-rag-api-441535054378.asia-east1.run.app','--impersonate-service-account=441535054378-compute@developer.gserviceaccount.com'], text=True).strip())"
```

## 方法 3：Python 一行（`shell=True`）

與 CMD 手打 `gcloud` 相同，由 shell 解析 PATH：

```bat
python -c "import subprocess; print(subprocess.check_output('gcloud auth print-identity-token --audiences=https://care-rag-api-441535054378.asia-east1.run.app --impersonate-service-account=441535054378-compute@developer.gserviceaccount.com', shell=True, text=True).strip())"
```

**根因說明**：CMD 能找到 `gcloud`，是因為透過 `cmd.exe` 解析 PATH／`gcloud.cmd`；Python 以列表直接啟動字串 `gcloud` 時，CreateProcess 可能找不到同名執行檔。

## 貼到 Postman

1. 複製輸出整串（通常以 `eyJ` 開頭）。
2. Environment → **`bearerToken`** → 貼上（**不要**加字首 `Bearer `）。

## 權限

- 你的 Google 帳號需可 impersonate 該 SA：`roles/iam.serviceAccountTokenCreator`
- 該 SA 需可呼叫 Cloud Run：`roles/run.invoker`

詳見 `cloud-run-troubleshooting-summary.md`。
