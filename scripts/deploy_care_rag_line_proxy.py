#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
部署 Cloud Run Service A：care-rag-line-proxy（LINE webhook → 既有 care-rag-api）

更新時間：2026-03-31 09:25
作者：AI Assistant
修改摘要：提供可在 Windows 上重複執行的部署腳本；自動從 `care-rag-api` 讀取承接流量的 revision image、複製 env/secret，覆寫 LINE proxy 相關設定，並將 LINE Channel Secret / X-API-Key 以 Secret Manager 掛載到 Service A。
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Tuple

ROOT = Path(__file__).resolve().parents[1]

# 以你現有專案為預設值；你也可以用參數覆寫
DEFAULT_PROJECT = "gen-lang-client-0567547134"
DEFAULT_REGION = "asia-east1"

TARGET_SERVICE = "care-rag-api"
PROXY_SERVICE = "care-rag-line-proxy"

# 你指定的 runtime service account
RUNTIME_SA = "441535054378-compute@developer.gserviceaccount.com"

# 專案規範的容器端口
CONTAINER_PORT = "8002"


def _gcloud_cmd() -> str:
    # Windows 環境：subprocess 需要 .cmd 才能正確載入環境
    p = shutil.which("gcloud.cmd") or shutil.which("gcloud")
    if p:
        return p
    # fallback（避免 shutil.which 取不到）
    return r"C:\Program Files (x86)\Google\Cloud SDK\google-cloud-sdk\bin\gcloud.cmd"


GCLOUD = _gcloud_cmd()


def _load_dotenv_simple(path: Path) -> Dict[str, str]:
    out: Dict[str, str] = {}
    if not path.is_file():
        return out
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        out[k.strip()] = v.strip().strip('"').strip("'")
    return out


def _run(cmd: List[str], check: bool = True) -> subprocess.CompletedProcess[str]:
    # debug：輸出命令，但不印 secret value（secret 只走 stdin / secret manager，不會進 cmd）
    print("+", " ".join(cmd))
    return subprocess.run(cmd, check=check, capture_output=True, text=True)


def _run_json(cmd: List[str]) -> Any:
    proc = subprocess.run(
        cmd + ["--format=json"],
        check=False,
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        sys.stderr.write((proc.stderr or proc.stdout or "")[:20000])
        raise SystemExit(proc.returncode)
    return json.loads(proc.stdout or "{}")


def _ensure_secret_exists_and_add_version(
    project: str, secret_id: str, payload: str, *, dry_run: bool
) -> None:
    # 只對 LINE 相關 secret 做版本寫入；其他 secret 只做 IAM 授權複用
    describe = subprocess.run(
        [GCLOUD, "secrets", "describe", secret_id, "--project", project, "--format=json"],
        capture_output=True,
        text=True,
    )
    if describe.returncode != 0:
        if dry_run:
            print("+ (would create secret)", secret_id)
        else:
            _run(
                [
                    GCLOUD,
                    "secrets",
                    "create",
                    secret_id,
                    "--project",
                    project,
                    "--replication-policy",
                    "automatic",
                ]
            )

    if dry_run:
        print("+ (would add secret version)", secret_id)
        return

    proc = subprocess.Popen(
        [GCLOUD, "secrets", "versions", "add", secret_id, "--project", project, "--data-file=-"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    assert proc.stdin is not None
    _, err = proc.communicate(payload)
    if proc.returncode != 0:
        sys.stderr.write(err or "")
        raise SystemExit(proc.returncode)


def _grant_secret_accessor(project: str, secret_id: str, member_sa: str, *, dry_run: bool) -> None:
    if dry_run:
        print("+ (would grant secretAccessor)", secret_id, member_sa)
        return
    _run(
        [
            GCLOUD,
            "secrets",
            "add-iam-policy-binding",
            secret_id,
            "--project",
            project,
            "--member",
            f"serviceAccount:{member_sa}",
            "--role",
            "roles/secretmanager.secretAccessor",
        ]
    )


def _parse_container_env_from_service_json(
    svc: Dict[str, Any],
) -> Tuple[Dict[str, str], Dict[str, str]]:
    """
    回傳 (plain_env, secret_env)

    secret_env 格式：{ENV_NAME: 'SECRET_ID:version'}
    """
    plain: Dict[str, str] = {}
    secrets: Dict[str, str] = {}

    tmpl = (svc.get("spec") or {}).get("template") or {}
    spec = (tmpl.get("spec") or {}) or {}
    containers = spec.get("containers") or []
    if not containers:
        return plain, secrets

    for item in containers[0].get("env") or []:
        name = item.get("name")
        if not name:
            continue
        if "value" in item:
            plain[name] = str(item["value"])
            continue

        vf = item.get("valueFrom") or {}
        sk = vf.get("secretKeyRef") or {}
        sid = sk.get("name")
        ver = sk.get("key") or "latest"
        if sid:
            secrets[name] = f"{sid}:{ver}"
    return plain, secrets


def _write_env_vars_file_quoted_strings(plain_env: Dict[str, str], path: Path) -> None:
    """
    gcloud `--env-vars-file` 使用 YAML。
    這裡用 json.dumps 包成字串，避免 true/false 被 YAML 解析成 bool。
    """
    lines = [f"{k}: {json.dumps(str(plain_env[k]))}" for k in sorted(plain_env.keys())]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Deploy care-rag-line-proxy from care-rag-api")
    parser.add_argument("--project", default=os.environ.get("GCP_PROJECT", DEFAULT_PROJECT))
    parser.add_argument("--region", default=os.environ.get("GCP_REGION", DEFAULT_REGION))
    parser.add_argument("--dry-run", action="store_true", help="只輸出將執行動作，不做修改")
    parser.add_argument(
        "--skip-secret-versions",
        action="store_true",
        help="不新增 LINE secret version（僅授權/部署）",
    )
    args = parser.parse_args()

    dot = _load_dotenv_simple(ROOT / ".env")

    line_secret_value = (os.environ.get("LINE_CHANNEL_SECRET") or dot.get("LINE_CHANNEL_SECRET") or "").strip()
    if not line_secret_value:
        sys.exit("Missing LINE_CHANNEL_SECRET (env or .env).")

    proxy_x_api_key_value = (
        os.environ.get("LINE_PROXY_X_API_KEY") or dot.get("LINE_PROXY_X_API_KEY") or os.environ.get("API_KEY") or dot.get("API_KEY") or "test-api-key"
    ).strip()

    # 1) 取得 care-rag-api（以承接流量 revision 為準）
    svc = _run_json(
        [GCLOUD, "run", "services", "describe", TARGET_SERVICE, "--project", args.project, "--region", args.region]
    )
    status = svc.get("status") or {}
    base_url = (status.get("url") or "").strip()
    if not base_url:
        sys.exit(f"Cannot read {TARGET_SERVICE}.status.url")

    traffic = status.get("traffic") or []
    traffic_rev = (traffic[0] or {}).get("revisionName") if traffic else None
    if not traffic_rev:
        traffic_rev = status.get("latestReadyRevisionName")
    if not traffic_rev:
        sys.exit("Cannot determine traffic revision.")

    rev = _run_json([GCLOUD, "run", "revisions", "describe", traffic_rev, "--project", args.project, "--region", args.region])
    image = (((rev.get("spec") or {}).get("containers") or [{}])[0]).get("image") or ""
    if not image:
        sys.exit("Cannot read revision container image.")

    plain_env, secret_env = _parse_container_env_from_service_json(svc)

    # 2) 覆寫 LINE proxy env
    plain_env["LINE_WEBHOOK_REQUIRE_SIGNATURE"] = "true"
    plain_env["LINE_PROXY_QUERY_ENDPOINT"] = base_url.rstrip("/") + "/api/v1/query"
    plain_env["LINE_PROXY_TARGET_AUDIENCE"] = base_url.rstrip("/")

    # 避免觸發 impersonation 路徑；在先前部署中已使用 leave empty（pop）
    plain_env.pop("LINE_PROXY_INVOKER_SERVICE_ACCOUNT", None)
    plain_env.pop("LINE_CHANNEL_SECRET", None)
    plain_env.pop("LINE_PROXY_X_API_KEY", None)

    # 3) 指定 LINE secret env（用戶指定 secret id）
    secret_env["LINE_CHANNEL_SECRET"] = "LINE_CHANNEL_SECRET:latest"
    secret_env["LINE_PROXY_X_API_KEY"] = "LINE_PROXY_X_API_KEY:latest"

    # 4) 對所有 secret env 做 IAM（包含 GOOGLE_API_KEY 等，確保容器可啟動）
    secret_ids = sorted({v.split(":", 1)[0] for v in secret_env.values() if v})
    for sid in secret_ids:
        _grant_secret_accessor(args.project, sid, RUNTIME_SA, dry_run=args.dry_run)

    # 5) 對 LINE secrets 生成新版本（必要時）
    if not args.skip_secret_versions:
        _ensure_secret_exists_and_add_version(args.project, "LINE_CHANNEL_SECRET", line_secret_value, dry_run=args.dry_run)
        _ensure_secret_exists_and_add_version(
            args.project, "LINE_PROXY_X_API_KEY", proxy_x_api_key_value, dry_run=args.dry_run
        )

    # 6) 產出 env-vars-file
    fd, tmp_path = tempfile.mkstemp(suffix=".yaml", text=True)
    os.close(fd)
    tmp_file = Path(tmp_path)
    try:
        _write_env_vars_file_quoted_strings(plain_env, tmp_file)

        # gcloud --update-secrets 需要：ENV_NAME=SECRET_ID:version
        updates = ",".join(
            f"{env_name}={spec}" for env_name, spec in sorted(secret_env.items(), key=lambda x: x[0])
        )

        deploy_cmd = [
            GCLOUD,
            "run",
            "deploy",
            PROXY_SERVICE,
            "--project",
            args.project,
            "--region",
            args.region,
            "--image",
            image,
            "--service-account",
            RUNTIME_SA,
            "--port",
            CONTAINER_PORT,
            "--allow-unauthenticated",
            "--env-vars-file",
            str(tmp_file),
            "--update-secrets",
            updates,
        ]
        if args.dry_run:
            print("+ (dry-run) deploy_cmd:", " ".join(deploy_cmd))
        else:
            _run(deploy_cmd)
    finally:
        if tmp_file.exists():
            tmp_file.unlink(missing_ok=True)

    print("OK: deployed. Service A URL: run services describe -> status.address.url")
    if not args.dry_run:
        svc2 = _run_json(
            [GCLOUD, "run", "services", "describe", PROXY_SERVICE, "--project", args.project, "--region", args.region]
        )
        print("Service URL:", (svc2.get("status") or {}).get("url"))


if __name__ == "__main__":
    main()

