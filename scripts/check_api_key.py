#!/usr/bin/env python3
"""
檢查 API Key 配置的腳本
用於驗證環境變數和 Settings 中的 API Key 值
"""
import os
import sys
from dotenv import load_dotenv

# 載入 .env 檔案
load_dotenv()

# 添加專案路徑
sys.path.insert(0, '.')

from app.config import settings
from app.services.llm_service import GeminiLLM

print("=" * 70)
print("API Key 配置檢查")
print("=" * 70)

# 1. 檢查環境變數（載入 .env 前）
print("\n1. 環境變數 (os.getenv, 載入 .env 前):")
env_key_before = os.getenv("GOOGLE_API_KEY")
if env_key_before:
    print(f"   ✅ 已設置: {env_key_before[:10]}...{env_key_before[-4:]}")
else:
    print("   ❌ 未設置")

# 2. 重新載入 .env
load_dotenv(override=True)
env_key_after = os.getenv("GOOGLE_API_KEY")
print("\n2. 環境變數 (os.getenv, 載入 .env 後):")
if env_key_after:
    print(f"   ✅ 已設置: {env_key_after[:10]}...{env_key_after[-4:]}")
else:
    print("   ❌ 未設置")

# 3. 檢查 Settings
print("\n3. Settings (settings.GOOGLE_API_KEY):")
settings_key = settings.GOOGLE_API_KEY
if settings_key:
    print(f"   ✅ 已設置: {settings_key[:10]}...{settings_key[-4:]}")
else:
    print("   ❌ 未設置")

# 4. 檢查 GeminiLLM 實際使用的 API Key
print("\n4. GeminiLLM 實際使用的 API Key:")
llm = GeminiLLM()
if llm.api_key:
    print(f"   ✅ 已設置: {llm.api_key[:10]}...{llm.api_key[-4:]}")
    print(f"   來源: {'環境變數' if llm.api_key == env_key_after else 'Settings' if llm.api_key == settings_key else '未知'}")
else:
    print("   ❌ 未設置")

# 5. 比較
print("\n5. 比較結果:")
print("   " + "-" * 66)
if env_key_after and settings_key:
    if env_key_after == settings_key:
        print("   ✅ 環境變數和 Settings 中的 API Key 相同")
    else:
        print("   ⚠️  環境變數和 Settings 中的 API Key 不同！")
        print(f"      環境變數: {env_key_after[:10]}...{env_key_after[-4:]}")
        print(f"      Settings: {settings_key[:10]}...{settings_key[-4:]}")
        print("      這可能導致不一致的行為！")
else:
    print("   ⚠️  無法比較（其中一個未設置）")

if llm.api_key:
    if llm.api_key == env_key_after:
        print("   ✅ GeminiLLM 使用環境變數中的 API Key")
    elif llm.api_key == settings_key:
        print("   ✅ GeminiLLM 使用 Settings 中的 API Key")
    else:
        print("   ⚠️  GeminiLLM 使用的 API Key 與環境變數和 Settings 都不同！")

print("\n" + "=" * 70)
print("檢查完成")
print("=" * 70)

