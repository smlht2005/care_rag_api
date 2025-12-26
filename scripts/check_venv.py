"""
檢查虛擬環境和依賴狀態
"""
import sys
import os
import subprocess

print("=" * 60)
print("虛擬環境診斷")
print("=" * 60)

# 1. 檢查 Python 路徑
print("\n[1] Python 環境資訊:")
print(f"  Python 版本: {sys.version}")
print(f"  Python 路徑: {sys.executable}")
print(f"  是否在虛擬環境: {hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)}")

# 2. 檢查 site-packages
try:
    import site
    site_packages = site.getsitepackages()
    print(f"  Site-packages: {site_packages}")
except:
    pass

# 3. 檢查關鍵依賴
print("\n[2] 檢查關鍵依賴:")

dependencies = [
    "prometheus_client",
    "aiosqlite",
    "fastapi",
    "uvicorn",
    "pydantic",
    "pdfplumber",
    "PyPDF2"
]

missing = []
for dep in dependencies:
    try:
        module = __import__(dep)
        version = getattr(module, '__version__', 'unknown')
        print(f"  ✅ {dep}: {version}")
    except ImportError:
        print(f"  ❌ {dep}: 未安裝")
        missing.append(dep)

# 4. 檢查 pip 路徑
print("\n[3] Pip 資訊:")
try:
    result = subprocess.run(
        [sys.executable, "-m", "pip", "--version"],
        capture_output=True,
        text=True
    )
    print(f"  {result.stdout.strip()}")
except Exception as e:
    print(f"  ❌ 無法取得 pip 資訊: {e}")

# 5. 建議
print("\n[4] 建議:")
if missing:
    print(f"  ⚠️ 缺少以下依賴: {', '.join(missing)}")
    print(f"\n  請執行以下命令安裝:")
    print(f"    pip install {' '.join(missing)}")
    print(f"\n  或安裝所有依賴:")
    print(f"    pip install -r requirements.txt")
else:
    print("  ✅ 所有依賴都已安裝")

print("\n" + "=" * 60)


