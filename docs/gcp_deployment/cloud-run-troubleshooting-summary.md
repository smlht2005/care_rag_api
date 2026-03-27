## Cloud Run 部署與疑難排解摘要（本次對話結論）

更新時間：2026-03-26 15:56
作者：AI Assistant
修改摘要：彙整本次 Cloud Run 部署（8002、IAM only、Secret Manager）與常見錯誤根因/修復指令

### 部署目標（本次最終狀態）

- **Project**：`gen-lang-client-0567547134`
- **Region**：`asia-east1`
- **Cloud Run**：service `care-rag-api`，**IAM only（不開放匿名）**
- **Container port**：**8002**
- **DB 檔內建映像**：`data/graph_qa.db`、`data/graph.db`、`data/qa_vectors.db`
- **Secrets**：用 Secret Manager 注入（例：`GOOGLE_API_KEY`）

### 重要產出/設定（為什麼能成功）

- **`.dockerignore`**：排除 `.env`、`.git`、`__pycache__` 等，避免 build context 夾帶秘密/雜檔。
- **`Dockerfile`**：
  - `EXPOSE 8002`
  - uvicorn 監聽 `PORT`（fallback 8002）
  - 健康檢查改用 `httpx`
  - 先 `mkdir -p /app/data` 再 `COPY data/*.db` 進 `/app/data/`
- **`.gcloudignore`**（關鍵）：避免 `gcloud builds submit` 因 `.gitignore` 的 `*.db` 而把 DB 排除，導致 Cloud Build 找不到 `data/graph_qa.db`。

### 常見錯誤與根因（本次實際遇到）

#### A) Cloud Build 失敗：`COPY failed: file not found ... data/graph_qa.db`

- **現象**：本機 docker build OK，但 `gcloud builds submit` 失敗，提示 build context 沒有 DB。
- **根因**：repo 的 `.gitignore` 有 `*.db`，Cloud Build 送出 source 時預設會套用忽略規則，把 `data/*.db` 排除。
- **修復**：新增 `care_rag_api/.gcloudignore`，確保 `data/*.db` 會被上傳到 Cloud Build。

#### B) Cloud Run `--update-secrets` 失敗：Permission denied on secret

- **現象**：
  - `Permission denied on secret: ... for Revision service account 441535054378-compute@developer.gserviceaccount.com`
- **根因**：Cloud Run Revision 的 **執行用 service account** 沒有 `roles/secretmanager.secretAccessor` 讀取 secret。
- **修復指令（範例：GOOGLE_API_KEY）**：

```bash
gcloud secrets add-iam-policy-binding GOOGLE_API_KEY ^
  --project gen-lang-client-0567547134 ^
  --member="serviceAccount:441535054378-compute@developer.gserviceaccount.com" ^
  --role="roles/secretmanager.secretAccessor"
```

#### C) 直接用瀏覽器打 `/api/v1/health` → 403 Forbidden

- **根因**：Cloud Run 設定為 **IAM only（不允許匿名）**，未帶 ID token 必定 401/403。

#### D) CMD 下用 `$(gcloud ...)` 取 token → 401

- **根因**：`$(...)` 是 bash 語法，**Windows CMD 不會展開**，header 變成無效 token。
- **修復**：用 `for /f` 接 `gcloud ...` 的輸出設定到 `%TOKEN%`。

#### E) `gcloud auth print-identity-token --audiences=<URL>` 報錯：Requires valid service account

- **根因**：你用的是 **user account**，此模式下 `--audiences` 需要 service account（或 impersonation）。
- **解法**：用 `--impersonate-service-account=<SA>` 產生 token。

#### F) Impersonation 失敗：缺 `roles/iam.serviceAccountTokenCreator`

- **現象**：`PERMISSION_DENIED ... iam.serviceAccounts.getAccessToken`
- **根因**：user 沒有 impersonate 該 SA 的權限（缺 token creator）。
- **修復指令（範例）**：

```bash
gcloud iam service-accounts add-iam-policy-binding 441535054378-compute@developer.gserviceaccount.com ^
  --project gen-lang-client-0567547134 ^
  --member="user:hungtao.liu@tmhtc.net" ^
  --role="roles/iam.serviceAccountTokenCreator"
```

#### G) 用 SA token 呼叫 Cloud Run → 403 `insufficient_scope`

- **根因**：你用 SA 身分呼叫，但 `roles/run.invoker` 只授權給 user，**未授權給該 SA**。
- **修復指令（範例）**：

```bash
gcloud run services add-iam-policy-binding care-rag-api ^
  --region asia-east1 ^
  --member="serviceAccount:441535054378-compute@developer.gserviceaccount.com" ^
  --role="roles/run.invoker"
```

#### H) `/api/v1/health` 307 Redirect + `location: http://.../api/v1/health/`

- **現象**：打無尾斜線會 307，`location` 變 `http://...`；用 `curl -L` 跟轉址後可能 403。
- **根因**：
  - 尾斜線 redirect 是 FastAPI/Starlette 的常見行為；
  - `location` 出現 `http` 多與 proxy header / scheme 判斷有關；
  - `curl -L` 跟轉址時，Authorization/token 可能不被沿用或 audience 不匹配。
- **暫時解法**：直接打帶尾斜線的路徑（`/api/v1/health/`），避免 redirect。

### 本次驗證成功的 CMD 範例（IAM only + SA impersonation）

```bat
set URL=https://care-rag-api-441535054378.asia-east1.run.app
set SA=441535054378-compute@developer.gserviceaccount.com

for /f "delims=" %T in ('gcloud auth print-identity-token --audiences=%URL% --impersonate-service-account=%SA%') do set TOKEN=%T

curl -i -H "Authorization: Bearer %TOKEN%" "%URL%/api/v1/health/"
```

#### I) Python `subprocess` 呼叫 `gcloud` 出現 `FileNotFoundError: WinError 2`

- **現象**：`python -c "subprocess.check_output(['gcloud', ...])"` 報「系統找不到指定的檔案」。
- **根因**：Windows 上 `CreateProcess` 以列表啟動 `gcloud` 時，未必能像 CMD 一樣解析到 `gcloud.cmd` 或 PATH 中的啟動器。
- **修復**：
  - 改用 **`shell=True`** 整段字串呼叫（與 CMD 手打相同），或
  - 先用 `shutil.which('gcloud')` / `which('gcloud.cmd')` 取得完整路徑再 `[path, ...]` 呼叫。

### 建議後續（若要減少踩雷）

- **固定使用 `/api/v1/health/`**（帶尾斜線）當作健康檢查路徑。
- 若要徹底避免 scheme/redirect 問題，可評估在 uvicorn 啟動加入 `--proxy-headers`（需配合專案/環境驗證）。

