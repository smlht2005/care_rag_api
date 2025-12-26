"""
LLM 服務抽象化
更新時間：2025-12-26 15:35
作者：AI Assistant
修改摘要：修正 API Key 優先順序，改為 .env 檔案（Settings）優先，環境變數其次，確保專案配置一致性
更新時間：2025-12-26 15:00
作者：AI Assistant
修改摘要：簡化 Gemini API Key 配置，移除 GEMINI_API_KEY，統一使用 GOOGLE_API_KEY，優先使用環境變數（與 care_rag 一致），移除 GOOGLE_CLOUD_PROJECT 警告
更新時間：2025-12-26 14:37
作者：AI Assistant
修改摘要：添加 Gemini API 配額錯誤重試機制（429 錯誤自動等待並重試），改善串流生成的重試處理
更新時間：2025-12-26 14:03
作者：AI Assistant
修改摘要：將預設 Gemini 模型名稱從 gemini-1.5-flash 改為 gemini-3.0-flash
更新時間：2025-12-26 13:57
作者：AI Assistant
修改摘要：修復 Gemini API 模型名稱錯誤（gemini-pro 已棄用，改用 gemini-1.5-flash），支援可配置模型名稱
更新時間：2025-12-26 13:42
作者：AI Assistant
修改摘要：修復 _stub_generate 方法異步問題（將同步方法改為異步，並在所有調用處添加 await）
更新時間：2025-12-26 13:28
作者：AI Assistant
修改摘要：實作真正的 LLM API 整合（Gemini、OpenAI、DeepSeek），支援真實 API 呼叫和降級機制
更新時間：2025-12-26 11:50
作者：AI Assistant
修改摘要：重構 LLMService，採用 BaseLLM 抽象類別架構，支援多 provider（Gemini、DeepSeek、OpenAI）
"""
import asyncio
import logging
import json
import os
from abc import ABC, abstractmethod
from typing import Optional, AsyncGenerator
from app.config import settings

# 嘗試導入真實的 API SDK，如果失敗則使用 stub
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

try:
    from openai import AsyncOpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

try:
    import httpx
    DEEPSEEK_AVAILABLE = True
except ImportError:
    DEEPSEEK_AVAILABLE = False

class BaseLLM(ABC):
    """LLM 基礎抽象類別"""
    
    @abstractmethod
    async def generate(
        self, 
        prompt: str, 
        max_tokens: int = 2000,
        temperature: float = 0.7
    ) -> str:
        """生成回答"""
        pass
    
    @abstractmethod
    async def generate_chunk(
        self, 
        prompt: str
    ) -> AsyncGenerator[str, None]:
        """串流生成回答（用於 SSE）"""
        pass


class GeminiLLM(BaseLLM):
    """Gemini LLM 實作"""
    
    def __init__(self, api_key: Optional[str] = None):
        # 優先順序：1. 參數 2. .env 檔案（Settings）3. 環境變數
        # 這樣可以確保專案配置的一致性，避免被系統環境變數覆蓋
        self.api_key = api_key or settings.GOOGLE_API_KEY or os.getenv("GOOGLE_API_KEY")
        self.logger = logging.getLogger("GeminiLLM")
        self._model = None
        self._use_real_api = GEMINI_AVAILABLE and self.api_key is not None
        
        if self._use_real_api:
            try:
                genai.configure(api_key=self.api_key)
                
                # 使用 gemini-3.0-flash, gemini-1.5-flash (更快) 或 gemini-1.5-pro (更強)
                # gemini-pro 已棄用，改用新模型名稱
                model_name = getattr(settings, 'GEMINI_MODEL_NAME', 'gemini-3.0-flash')
                self._model = genai.GenerativeModel(model_name)
                self.logger.info(f"Gemini API initialized with API key, model: {model_name}")
            except Exception as e:
                self.logger.warning(f"Failed to initialize Gemini API: {e}, falling back to stub")
                self._use_real_api = False
        else:
            if not GEMINI_AVAILABLE:
                self.logger.warning("google-generativeai not installed, using stub mode")
            elif not self.api_key:
                self.logger.warning("GOOGLE_API_KEY not configured, using stub mode")
    
    async def generate(
        self, 
        prompt: str, 
        max_tokens: int = 2000,
        temperature: float = 0.7,
        max_retries: int = 1
    ) -> str:
        """生成回答"""
        if self._use_real_api and self._model:
            for attempt in range(max_retries + 1):
                try:
                    # 使用真實的 Gemini API
                    response = await asyncio.to_thread(
                        self._model.generate_content,
                        prompt,
                        generation_config=genai.types.GenerationConfig(
                            max_output_tokens=max_tokens,
                            temperature=temperature
                        )
                    )
                    return response.text
                except Exception as e:
                    error_str = str(e)
                    
                    # 檢查是否為配額錯誤（429）
                    if "429" in error_str and "quota" in error_str.lower() and attempt < max_retries:
                        # 嘗試解析重試延遲時間
                        import re
                        retry_match = re.search(r'retry in ([\d.]+)s', error_str)
                        if retry_match:
                            retry_seconds = float(retry_match.group(1))
                            # 限制最大等待時間為 60 秒
                            wait_time = min(retry_seconds + 1, 60)
                            self.logger.warning(
                                f"Gemini API quota exceeded, waiting {wait_time:.1f}s before retry "
                                f"(attempt {attempt + 1}/{max_retries + 1})"
                            )
                            await asyncio.sleep(wait_time)
                            continue
                        else:
                            # 如果無法解析重試時間，等待 5 秒後重試
                            self.logger.warning(
                                f"Gemini API quota exceeded, waiting 5s before retry "
                                f"(attempt {attempt + 1}/{max_retries + 1})"
                            )
                            await asyncio.sleep(5)
                            continue
                    
                    # 非配額錯誤或重試次數已用完，降級到 Stub
                    self.logger.error(f"Gemini API call failed: {e}, falling back to stub")
                    return await self._stub_generate(prompt, max_tokens, temperature)
        else:
            return await self._stub_generate(prompt, max_tokens, temperature)
    
    async def _stub_generate(self, prompt: str, max_tokens: int, temperature: float) -> str:
        """Stub 實作（降級方案）"""
        await asyncio.sleep(0.1)
        return f"[Gemini Stub] 回答: {prompt}\n\n這是一個基於 Gemini 模型的回答，已處理 {max_tokens} tokens，溫度 {temperature}。"
    
    async def generate_chunk(self, prompt: str, max_retries: int = 1) -> AsyncGenerator[str, None]:
        """串流生成回答"""
        if self._use_real_api and self._model:
            for attempt in range(max_retries + 1):
                try:
                    # 使用真實的 Gemini API 串流
                    response = await asyncio.to_thread(
                        self._model.generate_content,
                        prompt,
                        stream=True
                    )
                    for chunk in response:
                        if chunk.text:
                            yield chunk.text
                    return  # 成功，退出重試循環
                except Exception as e:
                    error_str = str(e)
                    
                    # 檢查是否為配額錯誤（429）
                    if "429" in error_str and "quota" in error_str.lower() and attempt < max_retries:
                        import re
                        retry_match = re.search(r'retry in ([\d.]+)s', error_str)
                        if retry_match:
                            retry_seconds = float(retry_match.group(1))
                            wait_time = min(retry_seconds + 1, 60)
                            self.logger.warning(
                                f"Gemini API quota exceeded (stream), waiting {wait_time:.1f}s before retry "
                                f"(attempt {attempt + 1}/{max_retries + 1})"
                            )
                            await asyncio.sleep(wait_time)
                            continue
                        else:
                            self.logger.warning(
                                f"Gemini API quota exceeded (stream), waiting 5s before retry "
                                f"(attempt {attempt + 1}/{max_retries + 1})"
                            )
                            await asyncio.sleep(5)
                            continue
                    
                    # 非配額錯誤或重試次數已用完，降級到 Stub
                    self.logger.error(f"Gemini API stream failed: {e}, falling back to stub")
                    async for chunk in self._stub_generate_chunk(prompt):
                        yield chunk
                    return
        else:
            async for chunk in self._stub_generate_chunk(prompt):
                yield chunk
    
    async def _stub_generate_chunk(self, prompt: str) -> AsyncGenerator[str, None]:
        """Stub 串流實作（降級方案）"""
        chunks = [
            f"[Gemini Stub] 開始回答",
            f"關於「{prompt}」",
            "這是第一個回答片段",
            "這是第二個回答片段",
            "回答完成"
        ]
        
        for chunk in chunks:
            await asyncio.sleep(0.05)
            yield chunk + " "


class DeepSeekLLM(BaseLLM):
    """DeepSeek LLM 實作"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.DEEPSEEK_API_KEY
        self.logger = logging.getLogger("DeepSeekLLM")
        self._use_real_api = DEEPSEEK_AVAILABLE and self.api_key is not None
        self._base_url = "https://api.deepseek.com/v1"
        
        if self._use_real_api:
            self.logger.info("DeepSeek API initialized with real API key")
        else:
            if not DEEPSEEK_AVAILABLE:
                self.logger.warning("httpx not available, using stub mode")
            elif not self.api_key:
                self.logger.warning("DEEPSEEK_API_KEY not configured, using stub mode")
    
    async def generate(
        self, 
        prompt: str, 
        max_tokens: int = 2000,
        temperature: float = 0.7
    ) -> str:
        """生成回答"""
        if self._use_real_api:
            try:
                # 使用真實的 DeepSeek API
                async with httpx.AsyncClient(timeout=30.0) as client:
                    response = await client.post(
                        f"{self._base_url}/chat/completions",
                        headers={
                            "Authorization": f"Bearer {self.api_key}",
                            "Content-Type": "application/json"
                        },
                        json={
                            "model": "deepseek-chat",
                            "messages": [{"role": "user", "content": prompt}],
                            "max_tokens": max_tokens,
                            "temperature": temperature
                        }
                    )
                    response.raise_for_status()
                    result = response.json()
                    return result["choices"][0]["message"]["content"]
            except Exception as e:
                self.logger.error(f"DeepSeek API call failed: {e}, falling back to stub")
                return await self._stub_generate(prompt, max_tokens, temperature)
        else:
            return await self._stub_generate(prompt, max_tokens, temperature)
    
    async def _stub_generate(self, prompt: str, max_tokens: int, temperature: float) -> str:
        """Stub 實作（降級方案）"""
        await asyncio.sleep(0.1)
        return f"[DeepSeek Stub] 回答: {prompt}\n\n這是一個基於 DeepSeek 模型的回答，已處理 {max_tokens} tokens，溫度 {temperature}。"
    
    async def generate_chunk(self, prompt: str) -> AsyncGenerator[str, None]:
        """串流生成回答"""
        if self._use_real_api:
            try:
                # 使用真實的 DeepSeek API 串流
                async with httpx.AsyncClient(timeout=30.0) as client:
                    async with client.stream(
                        "POST",
                        f"{self._base_url}/chat/completions",
                        headers={
                            "Authorization": f"Bearer {self.api_key}",
                            "Content-Type": "application/json"
                        },
                        json={
                            "model": "deepseek-chat",
                            "messages": [{"role": "user", "content": prompt}],
                            "stream": True
                        }
                    ) as response:
                        response.raise_for_status()
                        async for line in response.aiter_lines():
                            if line.startswith("data: "):
                                data = line[6:]
                                if data == "[DONE]":
                                    break
                                try:
                                    chunk_data = json.loads(data)
                                    if "choices" in chunk_data and len(chunk_data["choices"]) > 0:
                                        delta = chunk_data["choices"][0].get("delta", {})
                                        if "content" in delta:
                                            yield delta["content"]
                                except json.JSONDecodeError:
                                    continue
            except Exception as e:
                self.logger.error(f"DeepSeek API stream failed: {e}, falling back to stub")
                async for chunk in self._stub_generate_chunk(prompt):
                    yield chunk
        else:
            async for chunk in self._stub_generate_chunk(prompt):
                yield chunk
    
    async def _stub_generate_chunk(self, prompt: str) -> AsyncGenerator[str, None]:
        """Stub 串流實作（降級方案）"""
        chunks = [
            f"[DeepSeek Stub] 開始回答",
            f"關於「{prompt}」",
            "這是第一個回答片段",
            "這是第二個回答片段",
            "回答完成"
        ]
        
        for chunk in chunks:
            await asyncio.sleep(0.05)
            yield chunk + " "


class OpenAILLM(BaseLLM):
    """OpenAI LLM 實作"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.OPENAI_API_KEY
        self.logger = logging.getLogger("OpenAILLM")
        self._client = None
        self._use_real_api = OPENAI_AVAILABLE and self.api_key is not None
        
        if self._use_real_api:
            try:
                self._client = AsyncOpenAI(api_key=self.api_key)
                self.logger.info("OpenAI API initialized with real API key")
            except Exception as e:
                self.logger.warning(f"Failed to initialize OpenAI API: {e}, falling back to stub")
                self._use_real_api = False
        else:
            if not OPENAI_AVAILABLE:
                self.logger.warning("openai SDK not installed, using stub mode")
            elif not self.api_key:
                self.logger.warning("OPENAI_API_KEY not configured, using stub mode")
    
    async def generate(
        self, 
        prompt: str, 
        max_tokens: int = 2000,
        temperature: float = 0.7
    ) -> str:
        """生成回答"""
        if self._use_real_api and self._client:
            try:
                # 使用真實的 OpenAI API
                response = await self._client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=max_tokens,
                    temperature=temperature
                )
                return response.choices[0].message.content
            except Exception as e:
                self.logger.error(f"OpenAI API call failed: {e}, falling back to stub")
                return await self._stub_generate(prompt, max_tokens, temperature)
        else:
            return await self._stub_generate(prompt, max_tokens, temperature)
    
    async def _stub_generate(self, prompt: str, max_tokens: int, temperature: float) -> str:
        """Stub 實作（降級方案）"""
        await asyncio.sleep(0.1)
        return f"[OpenAI Stub] 回答: {prompt}\n\n這是一個基於 OpenAI 模型的回答，已處理 {max_tokens} tokens，溫度 {temperature}。"
    
    async def generate_chunk(self, prompt: str) -> AsyncGenerator[str, None]:
        """串流生成回答"""
        if self._use_real_api and self._client:
            try:
                # 使用真實的 OpenAI API 串流
                stream = await self._client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[{"role": "user", "content": prompt}],
                    stream=True
                )
                async for chunk in stream:
                    if chunk.choices[0].delta.content:
                        yield chunk.choices[0].delta.content
            except Exception as e:
                self.logger.error(f"OpenAI API stream failed: {e}, falling back to stub")
                async for chunk in self._stub_generate_chunk(prompt):
                    yield chunk
        else:
            async for chunk in self._stub_generate_chunk(prompt):
                yield chunk
    
    async def _stub_generate_chunk(self, prompt: str) -> AsyncGenerator[str, None]:
        """Stub 串流實作（降級方案）"""
        chunks = [
            f"[OpenAI Stub] 開始回答",
            f"關於「{prompt}」",
            "這是第一個回答片段",
            "這是第二個回答片段",
            "回答完成"
        ]
        
        for chunk in chunks:
            await asyncio.sleep(0.05)
            yield chunk + " "


class LLMService:
    """抽象化 LLM 服務（統一介面）"""

    def __init__(self, provider: Optional[str] = None):
        self.provider = provider or settings.LLM_PROVIDER
        self.logger = logging.getLogger("LLMService")
        
        # 延遲初始化（Lazy Initialization）- 只在需要時創建實例
        self._clients: dict[str, BaseLLM] = {}
        
        # 初始化當前 provider
        self.client = self._get_client(self.provider.lower())
        self.logger.info(f"Initialized LLM service with provider: {self.provider}")

    def _get_client(self, provider: str) -> BaseLLM:
        """取得或創建 provider 實例（延遲初始化）"""
        provider_lower = provider.lower()
        
        if provider_lower not in self._clients:
            if provider_lower == "gemini":
                self._clients[provider_lower] = GeminiLLM()
                self.logger.debug(f"Created GeminiLLM instance")
            elif provider_lower == "deepseek":
                self._clients[provider_lower] = DeepSeekLLM()
                self.logger.debug(f"Created DeepSeekLLM instance")
            elif provider_lower == "openai":
                self._clients[provider_lower] = OpenAILLM()
                self.logger.debug(f"Created OpenAILLM instance")
            else:
                # 預設使用 Gemini
                self.logger.warning(f"Unknown provider: {provider}, using Gemini as default")
                self._clients[provider_lower] = GeminiLLM()
        
        return self._clients[provider_lower]

    async def generate(
        self, 
        prompt: str, 
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None
    ) -> str:
        """根據 provider 生成回答（保持現有介面）"""
        max_tokens = max_tokens or settings.LLM_MAX_TOKENS
        temperature = temperature or settings.LLM_TEMPERATURE
        
        return await self.client.generate(prompt, max_tokens, temperature)

    async def stream_generate(self, prompt: str):
        """串流生成回答（保持現有介面）"""
        async for chunk in self.client.generate_chunk(prompt):
            yield chunk

    async def generate_chunk(self, prompt: str):
        """串流生成回答（新方法，用於 SSE）"""
        async for chunk in self.client.generate_chunk(prompt):
            yield chunk

    def set_provider(self, provider: str):
        """切換 LLM provider"""
        provider_lower = provider.lower()
        if provider_lower in ["gemini", "deepseek", "openai"]:
            self.provider = provider_lower
            self.client = self._get_client(provider_lower)
            self.logger.info(f"LLM provider switched to: {provider}")
        else:
            self.logger.warning(f"Unknown provider: {provider}, keeping current: {self.provider}")

