## Cloud Run：用環境變數/Secret 取代 `.env`（含 API Key 部署）

更新時間：2026-03-26 14:04
作者：AI Assistant
修改摘要：整理 `.env` 在本機/Docker/Cloud Run 的使用方式；Cloud Run 用 env vars 與 Secret Manager 部署 API key（對應 app/config.py）

### 核心結論

- **本機開發**：用 `.env` / `.env.local` 很方便。
- **Docker 本機跑**：用 `--env-file .env`（不要把 `.env` COPY 進映像）。
- **Cloud Run 正式部署**：用 **Cloud Run 環境變數** + **Secret Manager**（不要上傳 `.env` 檔到雲端、不要把金鑰塞在映像內）。

### 為什麼 Cloud Run 不用 `.env`

你的專案在 `app/config.py` 會先 `load_dotenv()`，再由 `pydantic_settings.BaseSettings` 從 **OS 環境變數**讀取設定（也宣告了 `env_file = ".env"`）。

在 Cloud Run 上：

- 最可靠的是 **直接設定環境變數**（Cloud Run 會注入到容器環境）。
- 即使容器內沒有 `.env`，也能正常運作。
- 若同時存在 `.env` 與 Cloud Run 環境變數，通常以「已存在的環境變數」為準（避免被檔案覆蓋）。

### 哪些是非敏感環境變數（建議直接用 env vars）

可用 Cloud Run `--set-env-vars` 設定，例如：

- `LLM_PROVIDER`（例如 `gemini`）
- `GEMINI_MODEL_NAME`、`USE_GOOGLE_GENAI_SDK`、`GEMINI_EMBEDDING_MODEL`
- `QA_MIN_SCORE`、`QUERY_TYPE`
- `GRAPH_DB_PATH`（若要改路徑）
- `API_KEY`（若你要額外做 API key header 驗證；仍屬敏感程度較低但依組織規範可改用 Secret）

### 哪些是敏感資訊（API Key 建議用 Secret Manager）

依 `app/config.py`，常見敏感欄位：

- `GOOGLE_API_KEY`（Gemini）
- `OPENAI_API_KEY`
- `DEEPSEEK_API_KEY`

**原則**：金鑰不要 commit、不要放 Dockerfile、不要透過命令列明文寫進 shell history。

### Cloud Run + Secret Manager 部署流程（摘要）

以下以你的專案資訊為例：

- Project：`gen-lang-client-0567547134`
- Region：`asia-east1`

1) 建立 Secret（以 `GOOGLE_API_KEY` 為例）

- 在 GCP Console 的 **Secret Manager** 建立 secret：`GOOGLE_API_KEY`
- value 填入你的 Gemini key
- version 使用 `latest`

2) 讓 Cloud Run 的 Service Account 可以讀取 Secret

- 對 Cloud Run 使用的 service account（預設或自訂）授權：
  - `roles/secretmanager.secretAccessor`

3) 部署/更新 Cloud Run 時，把 Secret 掛成環境變數

- 用 `--update-secrets` 把 secret 以 env var 形式注入容器。
- 你的程式就能透過 `os.environ["GOOGLE_API_KEY"]` / `BaseSettings` 讀到。

### Docker 本機如何使用 `.env`（摘要）

- **推薦**：
  - `docker run --env-file .env -p 8002:8002 <image>`
- **不推薦**：
  - 在 Dockerfile `COPY .env`（會把金鑰寫進映像層）

### 和本專案部署設定的對齊提醒

- 你已決定 Cloud Run API container port 使用 **8002**。
- 若要維持「本機 `.env`」與「Cloud Run env/secret」一致，請確保變數名稱完全一致（例如 `GOOGLE_API_KEY`、`LLM_PROVIDER` 等）。

