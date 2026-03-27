## Cloud Run 存取控制（IAM / VPC）摘要

更新時間：2026-03-26 00:00
作者：AI Assistant
修改摘要：整理 Cloud Run「IAM only vs VPC/internal」差異、建議選項與呼叫方式（本專案選 IAM only）

### 你要解決的問題分兩層

- **網路層（Ingress / VPC）**：誰「在網路上」能打到你的 Cloud Run 服務端點。
- **身分層（IAM）**：誰「被授權」可以呼叫（即使拿到 URL 也不一定能呼叫）。

Cloud Run 最常見不是二選一，而是 **IAM +（可選）網路限制** 疊加。

### A) IAM only（本專案採用）

**定義**

- Cloud Run 仍有公開 HTTPS URL（可被網路到達）。
- 但 **不允許匿名**：未帶有效身分憑證者會收到 **401/403**。

**你要做的設定**

- Cloud Run：**不要**加 `--allow-unauthenticated`（或用 `--no-allow-unauthenticated`）。
- IAM：對允許呼叫的「使用者/服務帳號」授予 `roles/run.invoker`。

**呼叫端怎麼打**

- 呼叫端取得 **Google OIDC ID token**（通常用 service account）。
- 每次 request 帶：
  - `Authorization: Bearer <ID_TOKEN>`

**優點**

- 上線最快、管理清楚（以 IAM 管控誰能呼叫）。
- 不需要額外 Load Balancer 才能達到「不開放匿名」。

**限制/注意**

- 這不是 IP allowlist；端點在網路上仍可到達，只是未授權會被擋。
- 若要更強「網路不可達」，改用下述 internal ingress。

### B) VPC / internal ingress（進階：讓公網直接打不到）

**定義**

- 將 Cloud Run 的 Ingress 設為 **internal**（或 internal + LB）。
- 公網無法直接對 Cloud Run URL 發起請求；通常需要從 **同 VPC**、或透過 **VPN/Interconnect**、或透過 **Load Balancer / API Gateway** 轉發進來。

**何時需要**

- 組織政策要求「服務端點在公網不可達」。
- 你希望把所有外部入口收斂到單一 WAF/LB/API gateway。

**常見誤解釐清**

- Cloud Run 的「VPC connector」多用於 **出站（egress）**，例如 Cloud Run 連內網 Redis/SQL；它本身不等於「入站封鎖」。
- 入站封鎖要看 Ingress 設定與你是否採用 internal 方案。

### 建議選型（快速）

- **只要不開放匿名**：選 **IAM only**（本專案）。
- **要公網不可達**：選 **internal ingress**（再搭配 IAM）。

