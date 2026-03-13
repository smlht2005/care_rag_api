"""
Gemini LLM 服務測試腳本
用於驗證 Gemini API 是否正常工作

更新時間：2025-12-26 14:32
作者：AI Assistant
修改摘要：優化錯誤處理，添加配額錯誤診斷和解決方案建議
更新時間：2025-12-26 14:25
作者：AI Assistant
修改摘要：建立 Gemini LLM 服務測試腳本，驗證 API Key、模型名稱、基本功能
"""
import asyncio
import sys
import os
from pathlib import Path

# 添加專案路徑
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config import settings
from app.services.llm_service import GeminiLLM, LLMService


async def test_gemini_api_key():
    """測試 1: 驗證 API Key 是否配置"""
    print("=" * 60)
    print("測試 1: 驗證 API Key 配置")
    print("=" * 60)
    
    # 優先順序：1. .env 檔案（Settings）2. 環境變數
    # 這樣可以確保專案配置的一致性
    api_key = settings.GOOGLE_API_KEY or os.getenv("GOOGLE_API_KEY")
    
    if not api_key:
        print("[X] API Key 未配置")
        print("   請在 .env 檔案中設置 GOOGLE_API_KEY")
        return False
    
    print(f"[OK] API Key 已配置: {api_key[:10]}...{api_key[-4:]}")
    return True


async def test_gemini_model_initialization():
    """測試 2: 驗證模型初始化"""
    print("\n" + "=" * 60)
    print("測試 2: 驗證模型初始化")
    print("=" * 60)
    
    try:
        gemini_llm = GeminiLLM()
        
        if gemini_llm._use_real_api:
            print("[OK] 模型初始化成功")
            print(f"   使用真實 API: {gemini_llm._use_real_api}")
            print(f"   模型名稱: {settings.GEMINI_MODEL_NAME}")
            return True
        else:
            print("[WARN] 使用 Stub 模式（降級）")
            if not gemini_llm.api_key:
                print("   原因: API Key 未配置")
            else:
                print("   原因: 初始化失敗或依賴套件未安裝")
            return False
            
    except Exception as e:
        print(f"[X] 模型初始化失敗: {str(e)}")
        return False


async def test_gemini_basic_generation():
    """測試 3: 測試基本生成功能"""
    print("\n" + "=" * 60)
    print("測試 3: 測試基本生成功能")
    print("=" * 60)
    
    try:
        gemini_llm = GeminiLLM()
        
        test_prompt = "請用一句話介紹人工智慧。"
        print(f"測試提示詞: {test_prompt}")
        print("正在呼叫 Gemini API...")
        
        result = await gemini_llm.generate(test_prompt, max_tokens=100, temperature=0.7)
        
        if result and not result.startswith("[Gemini Stub]"):
            print("[OK] API 呼叫成功")
            print(f"   回應長度: {len(result)} 字元")
            print(f"   回應預覽: {result[:100]}...")
            return True
        else:
            print("[WARN] 使用 Stub 模式（降級）")
            print(f"   回應: {result[:100]}...")
            return False
            
    except Exception as e:
        error_str = str(e)
        print(f"[X] API 呼叫失敗: {error_str}")
        
        if "429" in error_str or "quota" in error_str.lower():
            print("   原因: API 配額已用完（免費層配額限制）")
            print("   詳細資訊:")
            if "free_tier" in error_str:
                print("     - 免費層配額已用完")
                print("     - 需要等待配額重置或升級到付費方案")
            if "retry_delay" in error_str or "retry in" in error_str:
                import re
                retry_match = re.search(r'retry in ([\d.]+)s', error_str)
                if retry_match:
                    retry_seconds = float(retry_match.group(1))
                    retry_minutes = retry_seconds / 60
                    print(f"     - 建議等待 {retry_minutes:.1f} 分鐘後重試")
            print("   解決方案:")
            print("     1. 等待配額重置（通常每分鐘或每天重置）")
            print("     2. 升級到 Google Cloud 付費方案")
            print("     3. 檢查配額使用情況: https://ai.dev/usage?tab=rate-limit")
            print("     4. 暫時使用 Stub 模式（已自動降級）")
        elif "404" in error_str:
            print("   原因: 模型名稱不正確或模型不存在")
            print(f"   當前模型: {settings.GEMINI_MODEL_NAME}")
            print("   建議嘗試以下模型:")
            print("     - gemini-1.5-flash（穩定，推薦）")
            print("     - gemini-1.5-pro（更強）")
            print("     - gemini-1.0-pro（舊版）")
        elif "401" in error_str or "403" in error_str:
            print("   原因: API Key 無效或權限不足")
            print("   建議:")
            print("     1. 檢查 API Key 是否正確")
            print("     2. 確認 API Key 是否有 Gemini API 權限")
            print("     3. 重新生成 API Key: https://makersuite.google.com/app/apikey")
        else:
            print(f"   錯誤類型: {type(e).__name__}")
            print("   建議: 檢查錯誤訊息並查看 Gemini API 文檔")
        
        return False


async def test_gemini_streaming():
    """測試 4: 測試串流生成功能"""
    print("\n" + "=" * 60)
    print("測試 4: 測試串流生成功能")
    print("=" * 60)
    
    try:
        gemini_llm = GeminiLLM()
        
        test_prompt = "請數數 1 到 5。"
        print(f"測試提示詞: {test_prompt}")
        print("正在呼叫 Gemini API（串流模式）...")
        
        chunks = []
        async for chunk in gemini_llm.generate_chunk(test_prompt):
            chunks.append(chunk)
            print(f"   收到片段: {chunk[:50]}...")
            if len(chunks) >= 3:  # 只顯示前 3 個片段
                break
        
        if chunks and not chunks[0].startswith("[Gemini Stub]"):
            print("[OK] 串流 API 呼叫成功")
            print(f"   收到 {len(chunks)} 個片段")
            return True
        else:
            print("[WARN] 使用 Stub 模式（降級）")
            return False
            
    except Exception as e:
        print(f"[X] 串流 API 呼叫失敗: {str(e)}")
        return False


async def test_llm_service_integration():
    """測試 5: 測試 LLMService 整合"""
    print("\n" + "=" * 60)
    print("測試 5: 測試 LLMService 整合")
    print("=" * 60)
    
    try:
        llm_service = LLMService(provider="gemini")
        
        test_prompt = "什麼是 GraphRAG？"
        print(f"測試提示詞: {test_prompt}")
        print("正在呼叫 LLMService...")
        
        result = await llm_service.generate(test_prompt, max_tokens=200)
        
        if result and not result.startswith("[Gemini Stub]"):
            print("[OK] LLMService 整合成功")
            print(f"   回應長度: {len(result)} 字元")
            print(f"   回應預覽: {result[:150]}...")
            return True
        else:
            print("[WARN] 使用 Stub 模式（降級）")
            return False
            
    except Exception as e:
        print(f"[X] LLMService 整合失敗: {str(e)}")
        return False


async def test_available_models():
    """測試 6: 列出可用的模型"""
    print("\n" + "=" * 60)
    print("測試 6: 檢查可用模型")
    print("=" * 60)
    
    try:
        from google import genai as genai_new  # type: ignore
    except ImportError:
        print("⚠️ google-genai 未安裝")
        print("   請執行: pip install google-genai")
        return False

    # 優先順序：1. .env 檔案（Settings）2. 環境變數
    api_key = settings.GOOGLE_API_KEY or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("⚠️ API Key 未配置，無法檢查可用模型")
        return False

    try:
        client = genai_new.Client(api_key=api_key)
        print("正在查詢可用模型...")
        models = client.models.list()

        available_models = [m.name for m in models]
        if available_models:
            print(f"[OK] 找到 {len(available_models)} 個可用模型:")
            for model in available_models[:10]:  # 只顯示前 10 個
                print(f"   - {model}")

            current_model = settings.GEMINI_MODEL_NAME
            if any(current_model in model for model in available_models):
                print(f"\n[OK] 當前配置的模型 '{current_model}' 可用")
            else:
                print(f"\n[WARN] 當前配置的模型 '{current_model}' 不在可用列表中")
            return True
        else:
            print("[X] 未找到可用模型")
            return False
    except Exception as e:
        print(f"[X] 查詢模型失敗: {str(e)}")
        return False


async def main():
    """主測試函數"""
    print("\n" + "=" * 60)
    print("Gemini LLM 服務測試")
    print("=" * 60)
    print(f"當前配置:")
    print(f"  LLM_PROVIDER: {settings.LLM_PROVIDER}")
    print(f"  GEMINI_MODEL_NAME: {settings.GEMINI_MODEL_NAME}")
    print(f"  GOOGLE_API_KEY (ENV): {'已配置' if os.getenv('GOOGLE_API_KEY') else '未配置'}")
    print(f"  GOOGLE_API_KEY (Settings): {'已配置' if settings.GOOGLE_API_KEY else '未配置'}")
    
    results = []
    
    # 執行所有測試
    results.append(("API Key 配置", await test_gemini_api_key()))
    
    if results[-1][1]:  # 如果 API Key 已配置，繼續測試
        results.append(("模型初始化", await test_gemini_model_initialization()))
        results.append(("基本生成", await test_gemini_basic_generation()))
        results.append(("串流生成", await test_gemini_streaming()))
        results.append(("LLMService 整合", await test_llm_service_integration()))
        results.append(("可用模型", await test_available_models()))
    
    # 顯示測試結果摘要
    print("\n" + "=" * 60)
    print("測試結果摘要")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "[OK] 通過" if result else "[X] 失敗"
        print(f"{status}: {test_name}")
    
    print(f"\n總計: {passed}/{total} 測試通過")
    
    if passed == total:
        print("\n[OK] 所有測試通過，Gemini LLM 服務正常工作。")
    elif passed > 0:
        print("\n[WARN] 部分測試通過，請檢查失敗的測試項目。")
    else:
        print("\n[X] 所有測試失敗，請檢查配置和 API Key。")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n測試被用戶中斷（Ctrl+C）")
        sys.exit(0)
    except Exception as e:
        print(f"\n[X] 測試執行失敗: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

