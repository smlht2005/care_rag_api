#!/usr/bin/env python3
"""
檢查環境變數和 .env 檔案的優先順序
"""
import os
import sys
from pathlib import Path

print("=" * 70)
print("環境變數和 .env 檔案優先順序檢查")
print("=" * 70)

# 1. 檢查 .env 檔案是否存在
env_file = Path(".env")
print("\n1. 檢查 .env 檔案:")
if env_file.exists():
    print("   ✅ .env 檔案存在")
    # 讀取 .env 檔案中的 GOOGLE_API_KEY（不載入到環境變數）
    env_content = env_file.read_text(encoding='utf-8')
    env_lines = [line.strip() for line in env_content.split('\n') if line.strip() and not line.strip().startswith('#')]
    env_key_from_file = None
    for line in env_lines:
        if line.startswith('GOOGLE_API_KEY='):
            env_key_from_file = line.split('=', 1)[1].strip().strip('"').strip("'")
            break
    
    if env_key_from_file:
        print(f"   ✅ .env 檔案中的 GOOGLE_API_KEY: {env_key_from_file[:10]}...{env_key_from_file[-4:]}")
    else:
        print("   ❌ .env 檔案中沒有 GOOGLE_API_KEY")
else:
    print("   ❌ .env 檔案不存在")
    env_key_from_file = None

# 2. 檢查系統環境變數（載入 .env 前）
print("\n2. 檢查系統環境變數（載入 .env 前）:")
env_key_before_dotenv = os.getenv("GOOGLE_API_KEY")
if env_key_before_dotenv:
    print(f"   ✅ 系統環境變數: {env_key_before_dotenv[:10]}...{env_key_before_dotenv[-4:]}")
else:
    print("   ❌ 系統環境變數未設置")

# 3. 載入 .env 檔案
print("\n3. 載入 .env 檔案:")
from dotenv import load_dotenv
load_dotenv(override=False)  # 不覆蓋現有環境變數
env_key_after_dotenv = os.getenv("GOOGLE_API_KEY")
if env_key_after_dotenv:
    print(f"   ✅ 載入後環境變數: {env_key_after_dotenv[:10]}...{env_key_after_dotenv[-4:]}")
    if env_key_before_dotenv and env_key_after_dotenv != env_key_before_dotenv:
        print("   ⚠️  環境變數被 .env 檔案覆蓋！")
    elif env_key_before_dotenv:
        print("   ✅ 環境變數保持不變（系統環境變數優先）")
    else:
        print("   ✅ 環境變數從 .env 檔案載入")
else:
    print("   ❌ 載入後環境變數仍未設置")

# 4. 檢查 Settings
print("\n4. 檢查 Settings:")
sys.path.insert(0, '.')
from app.config import settings
settings_key = settings.GOOGLE_API_KEY
if settings_key:
    print(f"   ✅ Settings.GOOGLE_API_KEY: {settings_key[:10]}...{settings_key[-4:]}")
else:
    print("   ❌ Settings.GOOGLE_API_KEY 未設置")

# 5. 檢查當前代碼的優先順序邏輯
print("\n5. 當前代碼的優先順序邏輯:")
print("   " + "-" * 66)
print("   代碼: api_key = os.getenv('GOOGLE_API_KEY') or settings.GOOGLE_API_KEY")
print("   優先順序:")
print("   1. os.getenv('GOOGLE_API_KEY') - 環境變數（系統環境變數或 .env 載入後）")
print("   2. settings.GOOGLE_API_KEY - Settings（從 .env 載入）")
print()
print("   ⚠️  問題：如果系統環境變數已設置，.env 檔案中的值會被忽略！")

# 6. 建議的優先順序
print("\n6. 建議的優先順序:")
print("   " + "-" * 66)
print("   1. .env 檔案（專案特定配置）")
print("   2. 系統環境變數（系統級配置）")
print("   理由：")
print("   - .env 檔案是專案特定的配置，應該優先")
print("   - 系統環境變數是全局配置，作為後備")
print("   - 這樣可以確保專案配置的一致性")

# 7. 比較值
print("\n7. 值比較:")
print("   " + "-" * 66)
if env_key_from_file and env_key_before_dotenv:
    if env_key_from_file == env_key_before_dotenv:
        print("   ✅ .env 檔案和系統環境變數的值相同")
    else:
        print("   ⚠️  .env 檔案和系統環境變數的值不同！")
        print(f"      .env 檔案: {env_key_from_file[:10]}...{env_key_from_file[-4:]}")
        print(f"      系統環境變數: {env_key_before_dotenv[:10]}...{env_key_before_dotenv[-4:]}")
        print("      這可能導致不一致的行為！")

if env_key_after_dotenv and settings_key:
    if env_key_after_dotenv == settings_key:
        print("   ✅ 環境變數和 Settings 的值相同")
    else:
        print("   ⚠️  環境變數和 Settings 的值不同！")
        print(f"      環境變數: {env_key_after_dotenv[:10]}...{env_key_after_dotenv[-4:]}")
        print(f"      Settings: {settings_key[:10]}...{settings_key[-4:]}")

print("\n" + "=" * 70)
print("檢查完成")
print("=" * 70)

