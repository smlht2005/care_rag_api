更新時間：2026-03-18 15:56
作者：AI Assistant
修改摘要：補充 nginx.conf 中 root/index/try_files（SPA fallback）的用途與請求路徑對照說明

更新時間：2026-03-18 15:47
作者：AI Assistant
修改摘要：整理 Windows Server 上 Nginx + FastAPI（Uvicorn）部署前端 dist 與 /api 反向代理的安裝與設定流程，含常見錯誤排查與服務化建議

## 目標情境（本專案建議）

- **同一台 Windows Server** 同時跑：
  - 前端（Vite build 後的 `dist/` 靜態檔）
  - 後端（FastAPI/Uvicorn）
  - Nginx 做反向代理（同一個對外入口 port）
- **建議對外入口**：`http://172.31.6.123:8000`
- **建議後端內部 port**：`8002`（或其他未被占用的 port）
  - 重要：同一台機器同一個 IP 上，**同一個 port 只能被一個程式 listen**。
  - 因此若 Nginx 對外 listen `8000`，FastAPI 請改成 listen `8002`（或 8001…）。

---

## 1) 安裝 Nginx（Windows Server）

1. 下載 Nginx Windows zip（stable）。
2. 解壓到固定路徑（例）：`C:\nginx`
3. 確認目錄：
   - `C:\nginx\conf\nginx.conf`
   - `C:\nginx\logs\`
   - `C:\nginx\html\`（我們會把前端 dist 放到這裡的子資料夾）

啟動/停止/重載：

```bat
cd C:\nginx
nginx.exe
nginx.exe -s reload
nginx.exe -s stop
```

---

## 2) 前端 build 與發佈（dist → Nginx html）

### 2.1 Build 前端

在專案前端目錄：

```bat
cd C:\Development\langChain\source\care_rag\care_rag_api\frontend
npm install
npm run build
```

會產生：

- `frontend\dist\index.html`
- `frontend\dist\assets\...`

### 2.2 複製到 Windows Server（robocopy）

假設你要把站台放在 Nginx 的 `C:\nginx\html\rag\`：

```bat
robocopy .\dist \\172.31.6.123\c$\nginx\html\rag /MIR
```

建議複製後檢查 `\\172.31.6.123\c$\nginx\html\rag\assets\` 裡是否還殘留舊的 `index-*.js`（快取/殘檔可能導致仍載入舊 bundle）。

---

## 3) 後端 FastAPI（Uvicorn）建議啟動方式

**讓 Nginx 對外 8000，後端改 8002：**

```bat
cd C:\Development\langChain\source\care_rag\care_rag_api
uvicorn app.main:app --host 0.0.0.0 --port 8002
```

---

## 4) Nginx 設定（同一入口 port 提供 UI + /api 代理）

編輯：`C:\nginx\conf\nginx.conf`

以下為核心範例（請依實際路徑調整 `root`）：

```nginx
http {
    include       mime.types;
    default_type  application/octet-stream;

    sendfile        on;
    keepalive_timeout  65;

    server {
        listen       8000;
        server_name  172.31.6.123;

        # 前端 dist（本例使用 C:\nginx\html\rag）
        root   C:/nginx/html/rag;
        index  index.html;

        # SPA：所有非 /api 的路徑 fallback 到 index.html
        location / {
            try_files $uri $uri/ /index.html;
        }

        # 說明（為什麼要這樣寫）
        # - root：把網址路徑對應到檔案系統目錄
        #   - 例如 GET /assets/index-XXX.js → C:\nginx\html\rag\assets\index-XXX.js
        # - index：使用者打開 / 時預設回傳的檔案
        #   - 例如 GET / → C:\nginx\html\rag\index.html
        # - try_files：支援 SPA（React）前端路由的關鍵
        #   - 先找「是否真的有這個檔案/資料夾」：$uri、$uri/
        #   - 若不存在（例如使用者直接開 /some/page），就回傳 /index.html
        #     讓前端 JS Router 接手解析路由並渲染頁面
        #
        # 沒有 try_files 的常見症狀：
        # - 直接貼子路徑（/some/page）或在子路徑按重新整理會 404

        # API：轉發到內部 FastAPI（8002）
        location /api/ {
            proxy_pass         http://127.0.0.1:8002;
            proxy_set_header   Host             $host;
            proxy_set_header   X-Real-IP        $remote_addr;
            proxy_set_header   X-Forwarded-For  $proxy_add_x_forwarded_for;
        }
    }
}
```

重載：

```bat
cd C:\nginx
nginx.exe -s reload
```

驗證：
- `http://172.31.6.123:8000/` 看到前端 UI
- 前端送出問題時呼叫 `/api/v1/query`，由 Nginx 轉到 `127.0.0.1:8002/api/v1/query`

---

## 5) 常見問題排查

### 5.1 Nginx 啟動失敗：bind() failed 10013（Access permissions）

錯誤樣例：

```text
nginx: [emerg] bind() to 0.0.0.0:8002 failed (10013: An attempt was made to access a socket in a way forbidden by its access permissions)
```

含意：通常是 **權限/政策** 禁止綁定該 port（不是單純被占用）。

建議檢查：
- 用「系統管理員」開 CMD/PowerShell 再啟動 Nginx。
- Windows 防火牆 / 端口策略是否限制該 port。
- 確認 `listen` 的 port 是否是你要對外的 port（通常 Nginx listen 8000；後端 listen 8002）。

補充：若是 port 被占用，較常見錯誤碼是 `10048`。

### 5.2 前端送出後無反應 / Console 報 JS 錯

- 可能是瀏覽器環境不支援某些 API（例如舊環境沒有 `crypto.randomUUID()`）。\n
- 部署時請確保已更新 `dist/`，且清除瀏覽器快取（`Ctrl+Shift+R`）。\n
- 若 robocopy 顯示目標端有 `*其他檔案 index-*.js`，請確認目標端 `assets/` 目錄沒有殘留舊 bundle。

### 5.3 Vite dev proxy 的 ECONNREFUSED

這是開發模式常見：Vite proxy `/api` 轉發到後端，但後端未啟動/port 不一致。\n
在 PROD（Nginx）模式，請以 Nginx 的 `location /api/` 為準。

---

## 6)（選用）把 Nginx / Uvicorn 做成 Windows 服務（nssm）

Nginx 與 Uvicorn 建議在 PROD 以服務形式常駐。\n
可使用 nssm 建立 Windows Service，開機自動啟動並可從「服務」管理介面操作。\n

（若你要我幫你產出 nssm 的完整指令與參數，請提供：Nginx 路徑、Python/venv 路徑、啟動命令與想要的服務名稱。）

