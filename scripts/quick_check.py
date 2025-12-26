"""快速檢查依賴"""
import sys

print("Python:", sys.executable)

# 檢查關鍵依賴
deps = ["prometheus_client", "aiosqlite", "fastapi"]
for dep in deps:
    try:
        __import__(dep)
        print(f"✅ {dep}")
    except ImportError:
        print(f"❌ {dep} - 未安裝")


