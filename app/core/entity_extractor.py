"""
實體和關係提取器
使用 LLM 從文字中提取實體和關係

更新時間：2026-03-11 09:13
作者：AI Assistant
修改摘要：[Fix B] 重寫 _rule_based_entity_extraction() 中文分段邏輯：改用標點邊界切段（split by 標點/空白）取代原 r'[\u4e00-\u9fff]{2,6}' 6-char 滑動視窗，消除截斷詞語的垃圾實體；最小長度 3 字、最大 12 字
更新時間：2026-03-09 20:55
作者：AI Assistant
修改摘要：修正 2 open/1 close 誤判：以括號配對擷取陣列（跳過字串內 ] 如 \"[02]\"），並在括號不匹配時用該法重取再修復
更新時間：2026-03-09 20:45
作者：AI Assistant
修改摘要：放寬實體解析：接受 description/code/label/title 作為實體名稱（對照表/IC 檔等 LLM 常回傳此類欄位），減少「LLM entity extraction returned empty」
更新時間：2026-03-09 20:25
作者：AI Assistant
修改摘要：加強不完整 JSON 修復：先試補 ]，再試補 }+]，並 strip 尾端逗號，以處理截斷在最後一個物件內的情況（2 open / 1 close）
更新時間：2026-03-09 20:15
作者：AI Assistant
修改摘要：LLM 回傳 JSON 括號不完整時（如截斷）嘗試修復：補齊缺少的 ] 後再解析，成功則沿用 LLM 結果，失敗再降級 rule-based
更新時間：2026-03-06
作者：AI Assistant
修改摘要：建立 Relation 前跳過 source_id == target_id，避免 "Source and target cannot be the same entity" 觸發例外與 warning 日誌
更新時間：2025-12-30 09:34
作者：AI Assistant
修改摘要：優化 LLM Token 限制：實體提取和關係提取的 max_tokens 從 1000 增加到 3000，以支援提取更多實體和關係（目標：50+ 實體，128+ 關係）
更新時間：2025-12-26 16:15
作者：AI Assistant
修改摘要：修復 JSON 解析問題：1) 將非貪婪匹配改為貪婪匹配確保完整 JSON 陣列匹配；2) 統一 json 模組導入修復變數作用域問題；3) 增強 JSON 解析失敗日誌記錄；4) 添加 JSON 完整性驗證（括號平衡檢查）
更新時間：2025-12-26 15:50
作者：AI Assistant
修改摘要：增強日誌記錄，添加更多上下文信息（實體列表、LLM回應、匹配過程、解析摘要）以便診斷降級原因
更新時間：2025-12-26 15:43
作者：AI Assistant
修改摘要：改善實體名稱匹配邏輯，添加模糊匹配以解決實體名稱不完全匹配的問題，減少降級到 rule-based 的情況
更新時間：2025-12-26 12:44
作者：AI Assistant
修改摘要：添加規則基礎關係提取降級方案，當 LLM 提取失敗時自動降級
"""
import json
import logging
import os
import re
from typing import List, Dict, Any, Optional
from app.core.graph_store import Entity, Relation
from app.services.llm_service import LLMService
from datetime import datetime
import uuid

logger = logging.getLogger("EntityExtractor")

# 確保 logs 目錄存在，供 debug.log 使用（避免在 prod 無 .cursor 目錄時寫檔失敗）
try:
    os.makedirs("logs", exist_ok=True)
except Exception:
    # 若建立失敗，不影響主流程，只是之後寫 log 可能失敗
    pass

class EntityExtractor:
    """實體和關係提取器"""
    
    def __init__(self, llm_service: LLMService):
        self.llm_service = llm_service
        self.logger = logging.getLogger("EntityExtractor")
    
    async def extract_entities(
        self,
        text: str,
        entity_types: Optional[List[str]] = None
    ) -> List[Entity]:
        """
        從文字中提取實體
        
        Args:
            text: 要提取實體的文字
            entity_types: 要提取的實體類型列表（可選）
        
        Returns:
            實體列表
        """
        try:
            # 構建提示詞
            prompt = self._build_entity_extraction_prompt(text, entity_types)
            
            # 使用 LLM 提取實體
            response = await self.llm_service.generate(prompt, max_tokens=3000)
            
            # 解析回應
            entities = self._parse_entity_response(response, text)
            
            # 去重和合併
            entities = self._deduplicate_entities(entities)
            
            # 如果 LLM 提取返回空列表，降級到規則基礎提取
            if not entities or len(entities) == 0:
                self.logger.warning("LLM entity extraction returned empty, falling back to rule-based")
                # #region agent log
                # json 模組已在文件頂部統一導入
                log_data = {
                    "sessionId": "debug-session",
                    "runId": "run1",
                    "hypothesisId": "A",
                    "location": "entity_extractor.py:extract_entities:empty_fallback",
                    "message": "LLM extraction returned empty, falling back to rule-based",
                    "data": {"response_preview": response[:200] if response else ""},
                    "timestamp": int(__import__("time").time() * 1000)
                }
                with open("logs/debug.log", "a", encoding="utf-8") as f:
                    f.write(json.dumps(log_data, ensure_ascii=False) + "\n")
                # #endregion
                # 降級到規則基礎提取
                rule_based_entities = self._rule_based_entity_extraction(text)
                # #region agent log
                log_data = {
                    "sessionId": "debug-session",
                    "runId": "run1",
                    "hypothesisId": "A",
                    "location": "entity_extractor.py:extract_entities:rule_based_fallback",
                    "message": "Rule-based entity extraction completed",
                    "data": {"entities_count": len(rule_based_entities) if rule_based_entities else 0},
                    "timestamp": int(__import__("time").time() * 1000)
                }
                with open("logs/debug.log", "a", encoding="utf-8") as f:
                    f.write(json.dumps(log_data, ensure_ascii=False) + "\n")
                # #endregion
                return rule_based_entities
            
            # #region agent log
            # json 模組已在文件頂部統一導入
            log_data = {
                "sessionId": "debug-session",
                "runId": "run1",
                "hypothesisId": "A",
                "location": "entity_extractor.py:extract_entities:success",
                "message": "Entities extracted successfully",
                "data": {
                    "entities_count": len(entities),
                    "entities": [{"id": e.id, "name": e.name, "type": e.type} for e in entities[:5]]
                },
                "timestamp": int(__import__("time").time() * 1000)
            }
            with open("logs/debug.log", "a", encoding="utf-8") as f:
                f.write(json.dumps(log_data, ensure_ascii=False) + "\n")
            # #endregion
            
            self.logger.info(f"Extracted {len(entities)} entities from text")
            return entities
            
        except Exception as e:
            self.logger.error(f"Failed to extract entities: {str(e)}")
            # #region agent log
            # json 模組已在文件頂部統一導入
            log_data = {
                "sessionId": "debug-session",
                "runId": "run1",
                "hypothesisId": "A",
                "location": "entity_extractor.py:extract_entities:exception",
                "message": "Exception in extract_entities, falling back to rule-based",
                "data": {"error": str(e), "error_type": type(e).__name__},
                "timestamp": int(__import__("time").time() * 1000)
            }
            with open("logs/debug.log", "a", encoding="utf-8") as f:
                f.write(json.dumps(log_data, ensure_ascii=False) + "\n")
            # #endregion
            # 降級到規則基礎提取
            rule_based_entities = self._rule_based_entity_extraction(text)
            # #region agent log
            log_data = {
                "sessionId": "debug-session",
                "runId": "run1",
                "hypothesisId": "A",
                "location": "entity_extractor.py:extract_entities:rule_based_fallback",
                "message": "Rule-based entity extraction completed",
                "data": {"entities_count": len(rule_based_entities) if rule_based_entities else 0},
                "timestamp": int(__import__("time").time() * 1000)
            }
            with open("logs/debug.log", "a", encoding="utf-8") as f:
                f.write(json.dumps(log_data, ensure_ascii=False) + "\n")
            # #endregion
            return rule_based_entities
    
    async def extract_relations(
        self,
        text: str,
        entities: List[Entity]
    ) -> List[Relation]:
        """
        從文字中提取關係
        
        Args:
            text: 要提取關係的文字
            entities: 已提取的實體列表
        
        Returns:
            關係列表
        """
        # #region agent log
        # json 模組已在文件頂部統一導入
        log_data = {
            "sessionId": "debug-session",
            "runId": "run1",
            "hypothesisId": "A",
            "location": "entity_extractor.py:extract_relations:entry",
            "message": "extract_relations called",
            "data": {
                "entities_count": len(entities) if entities else 0,
                "entities": [{"id": e.id, "name": e.name, "type": e.type} for e in entities[:5]] if entities else [],
                "text_length": len(text) if text else 0
            },
            "timestamp": int(__import__("time").time() * 1000)
        }
        with open("logs/debug.log", "a", encoding="utf-8") as f:
            f.write(json.dumps(log_data, ensure_ascii=False) + "\n")
        # #endregion
        
        if not entities or len(entities) < 2:
            # 至少需要 2 個實體才能建立關係
            # #region agent log
            log_data = {
                "sessionId": "debug-session",
                "runId": "run1",
                "hypothesisId": "A",
                "location": "entity_extractor.py:extract_relations:early_return",
                "message": "Not enough entities for relations",
                "data": {"entities_count": len(entities) if entities else 0},
                "timestamp": int(__import__("time").time() * 1000)
            }
            with open("logs/debug.log", "a", encoding="utf-8") as f:
                f.write(json.dumps(log_data, ensure_ascii=False) + "\n")
            # #endregion
            return []
        
        try:
            # 構建提示詞
            prompt = self._build_relation_extraction_prompt(text, entities)
            
            # 使用 LLM 提取關係
            response = await self.llm_service.generate(prompt, max_tokens=3000)
            
            # #region agent log
            log_data = {
                "sessionId": "debug-session",
                "runId": "run1",
                "hypothesisId": "B",
                "location": "entity_extractor.py:extract_relations:llm_response",
                "message": "LLM response received",
                "data": {
                    "response_preview": response[:500] if response else "",
                    "response_length": len(response) if response else 0,
                    "entities_count": len(entities),
                    "entity_names": [e.name for e in entities[:10]]  # 記錄前10個實體名稱
                },
                "timestamp": int(__import__("time").time() * 1000)
            }
            with open("logs/debug.log", "a", encoding="utf-8") as f:
                f.write(json.dumps(log_data, ensure_ascii=False) + "\n")
            # #endregion
            
            # 解析回應
            relations = self._parse_relation_response(response, entities)
            
            # #region agent log
            log_data = {
                "sessionId": "debug-session",
                "runId": "run1",
                "hypothesisId": "B",
                "location": "entity_extractor.py:extract_relations:llm_parsed",
                "message": "LLM relations parsed",
                "data": {
                    "relations_count": len(relations) if relations else 0,
                    "response_full": response[:1000] if response else ""  # 記錄完整回應（前1000字元）
                },
                "timestamp": int(__import__("time").time() * 1000)
            }
            with open("logs/debug.log", "a", encoding="utf-8") as f:
                f.write(json.dumps(log_data, ensure_ascii=False) + "\n")
            # #endregion
            
            if relations:
                # LLM 提取成功
                self.logger.info(f"Extracted {len(relations)} relations from text (LLM-based)")
                return relations
            else:
                # LLM 提取失敗，降級到規則基礎提取
                # 記錄詳細的失敗原因
                self.logger.warning(
                    f"LLM relation extraction returned empty, falling back to rule-based. "
                    f"Entities: {len(entities)}, Response length: {len(response) if response else 0}"
                )
                # #region agent log
                log_data = {
                    "sessionId": "debug-session",
                    "runId": "run1",
                    "hypothesisId": "C",
                    "location": "entity_extractor.py:extract_relations:fallback",
                    "message": "Falling back to rule-based extraction",
                    "data": {
                        "entities_count": len(entities),
                        "entity_names": [e.name for e in entities],  # 記錄所有實體名稱
                        "response_preview": response[:1000] if response else "",  # 記錄完整回應預覽
                        "response_length": len(response) if response else 0,
                        "text_preview": text[:500] if text else ""  # 記錄文本預覽
                    },
                    "timestamp": int(__import__("time").time() * 1000)
                }
                with open("logs/debug.log", "a", encoding="utf-8") as f:
                    f.write(json.dumps(log_data, ensure_ascii=False) + "\n")
                # #endregion
                return self._rule_based_relation_extraction(text, entities)
            
        except Exception as e:
            self.logger.error(f"Failed to extract relations (LLM-based): {str(e)}")
            # #region agent log
            log_data = {
                "sessionId": "debug-session",
                "runId": "run1",
                "hypothesisId": "D",
                "location": "entity_extractor.py:extract_relations:exception",
                "message": "Exception in extract_relations",
                "data": {"error": str(e), "error_type": type(e).__name__},
                "timestamp": int(__import__("time").time() * 1000)
            }
            with open("logs/debug.log", "a", encoding="utf-8") as f:
                f.write(json.dumps(log_data, ensure_ascii=False) + "\n")
            # #endregion
            # 降級到規則基礎提取
            return self._rule_based_relation_extraction(text, entities)
    
    def _build_entity_extraction_prompt(
        self,
        text: str,
        entity_types: Optional[List[str]] = None
    ) -> str:
        """構建實體提取提示詞"""
        entity_types_str = ", ".join(entity_types) if entity_types else "Person, Document, Concept, Location, Organization, Event"
        
        prompt = f"""請從以下文字中提取所有實體，並以 JSON 格式返回。

實體類型：{entity_types_str}

文字內容：
{text}

請返回 JSON 陣列，每個實體包含以下欄位：
- name: 實體名稱
- type: 實體類型
- properties: 其他屬性（字典格式）

範例回應：
[
  {{"name": "張三", "type": "Person", "properties": {{"role": "醫生"}}}},
  {{"name": "醫院", "type": "Organization", "properties": {{"location": "台北"}}}}
]

只返回 JSON，不要其他文字："""
        
        return prompt
    
    def _build_relation_extraction_prompt(
        self,
        text: str,
        entities: List[Entity]
    ) -> str:
        """構建關係提取提示詞"""
        entities_str = "\n".join([f"- {e.name} ({e.type})" for e in entities])
        
        prompt = f"""請從以下文字中提取實體間的關係，並以 JSON 格式返回。

已識別的實體：
{entities_str}

文字內容：
{text}

請返回 JSON 陣列，每個關係包含以下欄位：
- source: 來源實體名稱
- target: 目標實體名稱
- type: 關係類型（如 CONTAINS, RELATED_TO, MENTIONS, AUTHORED_BY, LOCATED_IN, PART_OF）
- properties: 其他屬性（字典格式）

範例回應：
[
  {{"source": "張三", "target": "醫院", "type": "WORKS_AT", "properties": {{"position": "醫生"}}}},
  {{"source": "文件", "target": "張三", "type": "AUTHORED_BY", "properties": {{}}}}
]

只返回 JSON，不要其他文字："""
        
        return prompt
    
    def _entity_name_from_item(self, item: dict) -> Optional[str]:
        """從 LLM 回傳的 item 取得實體名稱；對照表/代碼類內容可能回 description/code 而非 name。"""
        for key in ("name", "description", "code", "label", "title"):
            val = item.get(key)
            if val is not None and str(val).strip():
                return str(val).strip()
        return None

    def _extract_json_array_from_response(self, response: str, start: int) -> Optional[str]:
        """從 response[start:] 依括號配對擷取 JSON 陣列，跳過字串內的 [ ]，避免 \"[02]\" 等造成錯誤截斷。"""
        depth = 0
        i = start
        in_string = False
        escape = False
        quote_char = None
        n = len(response)
        while i < n:
            c = response[i]
            if escape:
                escape = False
                i += 1
                continue
            if c == "\\" and in_string:
                escape = True
                i += 1
                continue
            if in_string:
                if c == quote_char:
                    in_string = False
                i += 1
                continue
            if c == '"' or c == "'":
                in_string = True
                quote_char = c
                i += 1
                continue
            if c == "[":
                depth += 1
                i += 1
                continue
            if c == "]":
                depth -= 1
                if depth == 0:
                    return response[start : i + 1]
                i += 1
                continue
            i += 1
        return response[start:] if depth > 0 else None

    def _parse_entity_response(self, response: str, original_text: str) -> List[Entity]:
        """解析 LLM 回應為實體列表"""
        # json 模組已在文件頂部統一導入
        entities = []
        matched_pattern = None  # 記錄匹配到的正則表達式模式
        
        try:
            # 預先移除可能包裹 JSON 的 markdown code fence，避免不完整 ``` 導致匹配失敗
            clean_response = response
            stripped = clean_response.lstrip()
            if stripped.startswith("```"):
                lines = stripped.splitlines()
                if len(lines) > 1:
                    # 移除第一行 ```json / ```，保留後續內容
                    clean_response = "\n".join(lines[1:])

            # 嘗試提取 JSON（更嚴格的匹配）
            # 尋找 JSON 陣列，可能包含在 markdown 代碼塊中
            json_patterns = [
                (r'```json\s*(\[.*?\])\s*```', 'markdown_json_codeblock'),  # markdown JSON 代碼塊（非貪婪，但代碼塊內完整）
                (r'```\s*(\[.*?\])\s*```', 'codeblock'),      # 普通代碼塊（非貪婪，但代碼塊內完整）
                (r'(\[[\s\S]*\])', 'direct_array'),              # 直接 JSON 陣列（貪婪匹配，匹配到最後一個 ]）
            ]
            
            json_str = None
            for pattern, pattern_name in json_patterns:
                match = re.search(pattern, clean_response, re.DOTALL)
                if match:
                    json_str = match.group(1) if match.groups() else match.group(0)
                    matched_pattern = pattern_name
                    break
            
            # 如果沒找到，嘗試直接解析整個回應
            if not json_str:
                # 檢查是否整個回應就是 JSON
                response_stripped = clean_response.strip()
                if response_stripped.startswith('[') and response_stripped.endswith(']'):
                    json_str = response_stripped
                    matched_pattern = 'full_response'
                else:
                    # 以括號計數找陣列結尾（避免字串內 "]" 如 "[01]" 導致錯誤截斷）
                    start = clean_response.find('[')
                    if start != -1:
                        json_str = self._extract_json_array_from_response(clean_response, start)
                        if json_str:
                            matched_pattern = 'find_brackets'
            
            if json_str:
                # 清理可能的多餘空白和換行
                json_str = json_str.strip()
                
                # 驗證 JSON 完整性：檢查 [ 和 ] 數量是否匹配
                open_brackets = json_str.count('[')
                close_brackets = json_str.count(']')
                if open_brackets != close_brackets:
                    # 若可能被字串內的 ]（如 "[02]"）誤截，用括號配對重新擷取
                    first_bracket = response.find('[')
                    if first_bracket != -1:
                        reextracted = self._extract_json_array_from_response(response, first_bracket)
                        if reextracted and reextracted != json_str:
                            json_str = reextracted.strip()
                            open_brackets = json_str.count('[')
                            close_brackets = json_str.count(']')
                    # 嘗試修復：LLM 截斷可能少 ]（陣列結尾）或少 }]（物件+陣列結尾）
                    if open_brackets > close_brackets:
                        diff = open_brackets - close_brackets
                        raw = json_str.rstrip()
                        # 優先嘗試「砍到最後一個完整物件結束處」，避免落在半個欄位說明或未關閉的字串中
                        candidates = []
                        last_closing_obj = raw.rfind("}")
                        if last_closing_obj != -1:
                            candidates.append(raw[: last_closing_obj + 1])
                        # 退而求其次：沿用原本去掉尾逗號的整段內容
                        candidates.append(raw.rstrip(",").rstrip())

                        for base in candidates:
                            for repair_suffix in ["]" * diff, "}" + "]" * diff]:
                                repaired = base + repair_suffix
                                try:
                                    data = json.loads(repaired)
                                    if isinstance(data, list):
                                        for item in data:
                                            if isinstance(item, dict):
                                                name = self._entity_name_from_item(item)
                                                if name:
                                                    entity = Entity(
                                                        id=str(uuid.uuid4()),
                                                        type=item.get("type", "Concept"),
                                                        name=name,
                                                        properties=item.get("properties", {}),
                                                        created_at=datetime.now()
                                                    )
                                                    entities.append(entity)
                                        if entities:
                                            self.logger.info(
                                                f"Repaired incomplete JSON (entity): suffix {repr(repair_suffix)}, got {len(entities)} entities"
                                            )
                                            return entities
                                except json.JSONDecodeError:
                                    continue
                    self.logger.warning(
                        f"JSON string appears incomplete: {open_brackets} opening brackets, "
                        f"{close_brackets} closing brackets"
                    )
                    # 記錄到 debug.log
                    log_data = {
                        "sessionId": "debug-session",
                        "runId": "run1",
                        "hypothesisId": "H",
                        "location": "entity_extractor.py:_parse_entity_response:incomplete_json",
                        "message": "JSON string appears incomplete (bracket mismatch)",
                        "data": {
                            "open_brackets": open_brackets,
                            "close_brackets": close_brackets,
                            "json_str_preview": json_str[:500],
                            "json_str_length": len(json_str),
                            "matched_pattern": matched_pattern,
                            "response_preview": response[:500]
                        },
                        "timestamp": int(__import__("time").time() * 1000)
                    }
                    with open("logs/debug.log", "a", encoding="utf-8") as f:
                        f.write(json.dumps(log_data, ensure_ascii=False) + "\n")
                    return entities  # 返回空列表，觸發降級
                else:
                    data = json.loads(json_str)
                
                if isinstance(data, list):
                    for item in data:
                        if isinstance(item, dict):
                            name = self._entity_name_from_item(item)
                            if name:
                                entity = Entity(
                                    id=str(uuid.uuid4()),
                                    type=item.get("type", "Concept"),
                                    name=name,
                                    properties=item.get("properties", {}),
                                    created_at=datetime.now()
                                )
                                entities.append(entity)
        except json.JSONDecodeError as e:
            self.logger.debug(f"Failed to parse entity response as JSON: {str(e)}")
            self.logger.debug(f"Response preview: {response[:500]}")
            self.logger.debug(f"Extracted JSON string: {json_str[:500] if json_str else 'None'}")
            self.logger.debug(f"Response length: {len(response)}, JSON string length: {len(json_str) if json_str else 0}")
            
            # 記錄 JSON 解析錯誤到 debug.log
            log_data = {
                "sessionId": "debug-session",
                "runId": "run1",
                "hypothesisId": "H",
                "location": "entity_extractor.py:_parse_entity_response:json_error",
                "message": "JSON parsing failed in entity extraction",
                "data": {
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "response_preview": response[:1000],
                    "response_length": len(response),
                    "json_str_preview": json_str[:1000] if json_str else None,
                    "json_str_length": len(json_str) if json_str else 0,
                    "matched_pattern": matched_pattern
                },
                "timestamp": int(__import__("time").time() * 1000)
            }
            with open("logs/debug.log", "a", encoding="utf-8") as f:
                f.write(json.dumps(log_data, ensure_ascii=False) + "\n")
        except Exception as e:
            self.logger.warning(f"Failed to parse entity response: {str(e)}")
            # 記錄其他錯誤到 debug.log
            log_data = {
                "sessionId": "debug-session",
                "runId": "run1",
                "hypothesisId": "H",
                "location": "entity_extractor.py:_parse_entity_response:exception",
                "message": "Exception in entity parsing",
                "data": {
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "response_preview": response[:500] if response else "",
                    "matched_pattern": matched_pattern
                },
                "timestamp": int(__import__("time").time() * 1000)
            }
            with open("logs/debug.log", "a", encoding="utf-8") as f:
                f.write(json.dumps(log_data, ensure_ascii=False) + "\n")
        
        return entities
    
    def _parse_relation_response(
        self,
        response: str,
        entities: List[Entity]
    ) -> List[Relation]:
        """解析 LLM 回應為關係列表"""
        # json 模組已在文件頂部統一導入
        relations = []
        entity_map = {e.name: e for e in entities}
        unmatched_count = 0  # 記錄無法匹配的關係數量
        matched_pattern = None  # 記錄匹配到的正則表達式模式
        
        if not entities:
            self.logger.debug("No entities provided for relation extraction")
            return relations
        
        try:
            # 預先移除可能包裹 JSON 的 markdown code fence，避免不完整 ``` 導致匹配失敗
            clean_response = response
            stripped = clean_response.lstrip()
            if stripped.startswith("```"):
                lines = stripped.splitlines()
                if len(lines) > 1:
                    clean_response = "\n".join(lines[1:])

            # 嘗試提取 JSON（更嚴格的匹配）
            json_patterns = [
                (r'```json\s*(\[.*?\])\s*```', 'markdown_json_codeblock'),  # markdown JSON 代碼塊（非貪婪，但代碼塊內完整）
                (r'```\s*(\[.*?\])\s*```', 'codeblock'),      # 普通代碼塊（非貪婪，但代碼塊內完整）
                (r'(\[[\s\S]*\])', 'direct_array'),              # 直接 JSON 陣列（貪婪匹配，匹配到最後一個 ]）
            ]
            
            json_str = None
            for pattern, pattern_name in json_patterns:
                match = re.search(pattern, clean_response, re.DOTALL)
                if match:
                    json_str = match.group(1) if match.groups() else match.group(0)
                    matched_pattern = pattern_name
                    break
            
            # 如果沒找到，嘗試直接解析整個回應
            if not json_str:
                response_stripped = clean_response.strip()
                if response_stripped.startswith('[') and response_stripped.endswith(']'):
                    json_str = response_stripped
                    matched_pattern = 'full_response'
                else:
                    start = clean_response.find('[')
                    if start != -1:
                        json_str = self._extract_json_array_from_response(clean_response, start)
                        if json_str:
                            matched_pattern = 'find_brackets'
            
            if json_str:
                json_str = json_str.strip()
                
                # 驗證 JSON 完整性：檢查 [ 和 ] 數量是否匹配
                open_brackets = json_str.count('[')
                close_brackets = json_str.count(']')
                if open_brackets != close_brackets:
                    # 若可能被字串內的 ] 誤截，用括號配對重新擷取
                    first_bracket = response.find('[')
                    if first_bracket != -1:
                        reextracted = self._extract_json_array_from_response(response, first_bracket)
                        if reextracted and reextracted != json_str:
                            json_str = reextracted.strip()
                            open_brackets = json_str.count('[')
                            close_brackets = json_str.count(']')
                    # 嘗試修復：LLM 截斷可能少 ] 或少 }]，多種後綴依序嘗試；先去掉尾端逗號
                    if open_brackets > close_brackets:
                        diff = open_brackets - close_brackets
                        base = json_str.rstrip().rstrip(",").rstrip()
                        for repair_suffix in ["]" * diff, "}" + "]" * diff]:
                            repaired = base + repair_suffix
                            try:
                                data = json.loads(repaired)
                                if isinstance(data, list):
                                    parsed_items = 0
                                    for item in data:
                                        if isinstance(item, dict) and "source" in item and "target" in item:
                                            source_name = item.get("source", "")
                                            target_name = item.get("target", "")
                                            source_entity = entity_map.get(source_name)
                                            target_entity = entity_map.get(target_name)
                                            if not source_entity:
                                                for entity_name, entity in entity_map.items():
                                                    if source_name in entity_name or entity_name in source_name:
                                                        source_entity = entity
                                                        break
                                            if not target_entity:
                                                for entity_name, entity in entity_map.items():
                                                    if target_name in entity_name or entity_name in target_name:
                                                        target_entity = entity
                                                        break
                                            if source_entity and target_entity and source_entity.id != target_entity.id:
                                                relation = Relation(
                                                    id=str(uuid.uuid4()),
                                                    source_id=source_entity.id,
                                                    target_id=target_entity.id,
                                                    type=item.get("type", "RELATED_TO"),
                                                    properties=item.get("properties", {}),
                                                    weight=1.0,
                                                    created_at=datetime.now()
                                                )
                                                relations.append(relation)
                                                parsed_items += 1
                                    if parsed_items > 0:
                                        self.logger.info(
                                            f"Repaired incomplete JSON (relation): suffix {repr(repair_suffix)}, got {parsed_items} relations"
                                        )
                                        return relations
                            except json.JSONDecodeError:
                                continue
                    self.logger.warning(
                        f"JSON string appears incomplete: {open_brackets} opening brackets, "
                        f"{close_brackets} closing brackets"
                    )
                    # 記錄到 debug.log
                    log_data = {
                        "sessionId": "debug-session",
                        "runId": "run1",
                        "hypothesisId": "I",
                        "location": "entity_extractor.py:_parse_relation_response:incomplete_json",
                        "message": "JSON string appears incomplete (bracket mismatch)",
                        "data": {
                            "open_brackets": open_brackets,
                            "close_brackets": close_brackets,
                            "json_str_preview": json_str[:500],
                            "json_str_length": len(json_str),
                            "matched_pattern": matched_pattern,
                            "response_preview": response[:500],
                            "entities_count": len(entities)
                        },
                        "timestamp": int(__import__("time").time() * 1000)
                    }
                    with open("logs/debug.log", "a", encoding="utf-8") as f:
                        f.write(json.dumps(log_data, ensure_ascii=False) + "\n")
                    return relations  # 返回空列表，觸發降級
                else:
                    data = json.loads(json_str)
                
                if isinstance(data, list):
                    parsed_items = 0
                    for item in data:
                        if isinstance(item, dict) and "source" in item and "target" in item:
                            parsed_items += 1
                            source_name = item.get("source", "")
                            target_name = item.get("target", "")
                            
                            # 精確匹配
                            source_entity = entity_map.get(source_name)
                            target_entity = entity_map.get(target_name)
                            
                            # 如果精確匹配失敗，嘗試模糊匹配（包含關係）
                            if not source_entity:
                                for entity_name, entity in entity_map.items():
                                    if source_name in entity_name or entity_name in source_name:
                                        source_entity = entity
                                        break
                            
                            if not target_entity:
                                for entity_name, entity in entity_map.items():
                                    if target_name in entity_name or entity_name in target_name:
                                        target_entity = entity
                                        break
                            
                            if source_entity and target_entity and source_entity.id != target_entity.id:
                                relation = Relation(
                                    id=str(uuid.uuid4()),
                                    source_id=source_entity.id,
                                    target_id=target_entity.id,
                                    type=item.get("type", "RELATED_TO"),
                                    properties=item.get("properties", {}),
                                    weight=1.0,
                                    created_at=datetime.now()
                                )
                                relations.append(relation)
                            else:
                                unmatched_count += 1
                                # 記錄無法匹配的實體名稱，幫助診斷
                                unmatched_info = {}
                                if not source_entity:
                                    unmatched_info["source"] = {
                                        "requested": source_name,
                                        "available_entities": list(entity_map.keys())[:20],
                                        "fuzzy_match_attempted": True
                                    }
                                    self.logger.debug(f"無法匹配來源實體: '{source_name}' (可用實體: {list(entity_map.keys())[:10]})")
                                if not target_entity:
                                    unmatched_info["target"] = {
                                        "requested": target_name,
                                        "available_entities": list(entity_map.keys())[:20],
                                        "fuzzy_match_attempted": True
                                    }
                                    self.logger.debug(f"無法匹配目標實體: '{target_name}' (可用實體: {list(entity_map.keys())[:10]})")
                                
                                # 記錄到 debug.log
                                if unmatched_info:
                                    log_data = {
                                        "sessionId": "debug-session",
                                        "runId": "run1",
                                        "hypothesisId": "D",
                                        "location": "entity_extractor.py:_parse_relation_response:unmatched_entity",
                                        "message": "Entity name mismatch in relation extraction",
                                        "data": unmatched_info,
                                        "timestamp": int(__import__("time").time() * 1000)
                                    }
                                    with open("logs/debug.log", "a", encoding="utf-8") as f:
                                        f.write(json.dumps(log_data, ensure_ascii=False) + "\n")
                    
                    # 記錄解析摘要到 debug.log
                    if parsed_items > 0:
                        log_data = {
                            "sessionId": "debug-session",
                            "runId": "run1",
                            "hypothesisId": "G",
                            "location": "entity_extractor.py:_parse_relation_response:parsing_summary",
                            "message": "Relation parsing summary",
                            "data": {
                                "total_items_in_llm_response": parsed_items,
                                "relations_created": len(relations),
                                "unmatched_entity_pairs": unmatched_count,
                                "entities_count": len(entities),
                                "entity_names": list(entity_map.keys())[:20],
                                "matched_pattern": matched_pattern
                            },
                            "timestamp": int(__import__("time").time() * 1000)
                        }
                        with open("logs/debug.log", "a", encoding="utf-8") as f:
                            f.write(json.dumps(log_data, ensure_ascii=False) + "\n")
        except json.JSONDecodeError as e:
            self.logger.debug(f"Failed to parse relation response as JSON: {str(e)}")
            self.logger.debug(f"Response preview: {response[:500]}")
            self.logger.debug(f"Extracted JSON string: {json_str[:500] if json_str else 'None'}")
            self.logger.debug(f"Response length: {len(response)}, JSON string length: {len(json_str) if json_str else 0}")
            
            # 記錄 JSON 解析錯誤到 debug.log
            log_data = {
                "sessionId": "debug-session",
                "runId": "run1",
                "hypothesisId": "E",
                "location": "entity_extractor.py:_parse_relation_response:json_error",
                "message": "JSON parsing failed",
                "data": {
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "response_preview": response[:1000],
                    "response_length": len(response),
                    "json_str_preview": json_str[:1000] if json_str else None,
                    "json_str_length": len(json_str) if json_str else 0,
                    "entities_count": len(entities),
                    "matched_pattern": matched_pattern
                },
                "timestamp": int(__import__("time").time() * 1000)
            }
            with open("logs/debug.log", "a", encoding="utf-8") as f:
                f.write(json.dumps(log_data, ensure_ascii=False) + "\n")
        except Exception as e:
            self.logger.warning(f"Failed to parse relation response: {str(e)}")
            # 記錄其他錯誤到 debug.log
            log_data = {
                "sessionId": "debug-session",
                "runId": "run1",
                "hypothesisId": "F",
                "location": "entity_extractor.py:_parse_relation_response:exception",
                "message": "Exception in relation parsing",
                "data": {
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "response_preview": response[:1000] if response else "",
                    "response_length": len(response) if response else 0,
                    "entities_count": len(entities),
                    "matched_pattern": matched_pattern
                },
                "timestamp": int(__import__("time").time() * 1000)
            }
            with open("logs/debug.log", "a", encoding="utf-8") as f:
                f.write(json.dumps(log_data, ensure_ascii=False) + "\n")
        
        # 記錄解析結果摘要
        if unmatched_count > 0:
            self.logger.debug(f"Parsed {len(relations)} relations, {unmatched_count} unmatched entity pairs")
        
        return relations
    
    def _deduplicate_entities(self, entities: List[Entity]) -> List[Entity]:
        """實體去重和合併"""
        seen = {}
        result = []
        
        for entity in entities:
            # 使用 name 和 type 作為唯一鍵
            key = (entity.name.lower(), entity.type)
            
            if key not in seen:
                seen[key] = entity
                result.append(entity)
            else:
                # 合併屬性
                existing = seen[key]
                existing.properties.update(entity.properties)
        
        return result
    
    def _rule_based_entity_extraction(self, text: str) -> List[Entity]:
        """規則基礎的實體提取（降級方案）"""
        entities = []
        seen_names = set()  # 避免重複

        # 1. 先以標點/空白切成完整語意片段，再取純中文部分作為 Concept
        # 修改原因：原 r'[\u4e00-\u9fff]{2,6}' 為非重疊貪婪滑動視窗，
        # 會在 6-char 邊界截斷詞語（例如「畫面」→「一畫」+「面增」），產生大量無意義實體。
        # 改為先以標點切段，保留語意完整的片段（3~12字）。
        segments = re.split(r'[，。！？、；:\s\n\r\t]+', text)
        for seg in segments:
            chinese_only = re.sub(r'[^\u4e00-\u9fff]', '', seg).strip()
            if 3 <= len(chinese_only) <= 12 and chinese_only not in seen_names:
                seen_names.add(chinese_only)
                entity = Entity(
                    id=str(uuid.uuid4()),
                    type="Concept",
                    name=chinese_only,
                    properties={"extracted_by": "rule_based", "language": "chinese"},
                    created_at=datetime.now()
                )
                entities.append(entity)
        
        # 2. 提取常見的中文實體模式
        patterns = [
            (r'([\u4e00-\u9fff]+政策)', 'Policy'),
            (r'([\u4e00-\u9fff]+制度)', 'System'),
            (r'([\u4e00-\u9fff]+服務)', 'Service'),
            (r'([\u4e00-\u9fff]+計畫)', 'Plan'),
            (r'([\u4e00-\u9fff]+方案)', 'Program'),
            (r'([\u4e00-\u9fff]+機構)', 'Organization'),
            (r'([\u4e00-\u9fff]+單位)', 'Organization'),
            (r'([\u4e00-\u9fff]+部門)', 'Organization'),
            (r'([\u4e00-\u9fff]+人員)', 'Person'),
            (r'([\u4e00-\u9fff]+人員)', 'Person'),
        ]
        
        for pattern, entity_type in patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                if match not in seen_names:
                    seen_names.add(match)
                    entity = Entity(
                        id=str(uuid.uuid4()),
                        type=entity_type,
                        name=match,
                        properties={"extracted_by": "rule_based", "pattern": pattern},
                        created_at=datetime.now()
                    )
                    entities.append(entity)
        
        # 3. 提取英文專有名詞（大寫開頭的詞）
        english_pattern = r'\b[A-Z][a-z]+\b'
        english_matches = re.findall(english_pattern, text)
        for match in set(english_matches):
            if match not in seen_names and len(match) > 2:
                seen_names.add(match)
                entity = Entity(
                    id=str(uuid.uuid4()),
                    type="Concept",
                    name=match,
                    properties={"extracted_by": "rule_based", "language": "english"},
                    created_at=datetime.now()
                )
                entities.append(entity)
        
        # 限制實體數量，避免過多
        return entities[:50]  # 最多返回50個實體
    
    def _rule_based_relation_extraction(
        self, 
        text: str, 
        entities: List[Entity]
    ) -> List[Relation]:
        """
        規則基礎的關係提取（降級方案）
        
        基於關鍵詞模式匹配提取簡單關係
        """
        # #region agent log
        # json 模組已在文件頂部統一導入
        log_data = {
            "sessionId": "debug-session",
            "runId": "run1",
            "hypothesisId": "C",
            "location": "entity_extractor.py:_rule_based_relation_extraction:entry",
            "message": "Rule-based extraction started",
            "data": {
                "entities_count": len(entities) if entities else 0,
                "text_length": len(text) if text else 0
            },
            "timestamp": int(__import__("time").time() * 1000)
        }
        with open("logs/debug.log", "a", encoding="utf-8") as f:
            f.write(json.dumps(log_data, ensure_ascii=False) + "\n")
        # #endregion
        
        relations = []
        
        if len(entities) < 2:
            # #region agent log
            log_data = {
                "sessionId": "debug-session",
                "runId": "run1",
                "hypothesisId": "C",
                "location": "entity_extractor.py:_rule_based_relation_extraction:early_return",
                "message": "Not enough entities for rule-based extraction",
                "data": {"entities_count": len(entities) if entities else 0},
                "timestamp": int(__import__("time").time() * 1000)
            }
            with open("logs/debug.log", "a", encoding="utf-8") as f:
                f.write(json.dumps(log_data, ensure_ascii=False) + "\n")
            # #endregion
            return relations
        
        # 建立實體名稱映射（支援部分匹配）
        entity_map = {}
        for entity in entities:
            entity_map[entity.name] = entity
            # 也支援部分匹配（如果實體名稱在文字中出現）
            if entity.name in text:
                entity_map[entity.name] = entity
        
        # 關係模式匹配（中文和英文）
        patterns = [
            # 中文模式
            (r'([^，。\n、]+)在([^，。\n、]+)', 'LOCATED_IN'),
            (r'([^，。\n、]+)屬於([^，。\n、]+)', 'BELONGS_TO'),
            (r'([^，。\n、]+)是([^，。\n、]+)', 'IS_A'),
            (r'([^，。\n、]+)包含([^，。\n、]+)', 'CONTAINS'),
            (r'([^，。\n、]+)與([^，。\n、]+)相關', 'RELATED_TO'),
            (r'([^，。\n、]+)由([^，。\n、]+)組成', 'CONSISTS_OF'),
            (r'([^，。\n、]+)管理([^，。\n、]+)', 'MANAGES'),
            # 英文模式
            (r'\b([A-Z][a-z]+)\s+in\s+([A-Z][a-z]+)\b', 'LOCATED_IN'),
            (r'\b([A-Z][a-z]+)\s+belongs\s+to\s+([A-Z][a-z]+)\b', 'BELONGS_TO'),
            (r'\b([A-Z][a-z]+)\s+is\s+a\s+([A-Z][a-z]+)\b', 'IS_A'),
            (r'\b([A-Z][a-z]+)\s+contains\s+([A-Z][a-z]+)\b', 'CONTAINS'),
        ]
        
        seen_relations = set()  # 避免重複關係
        
        for pattern, relation_type in patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                source_name = match.group(1).strip()
                target_name = match.group(2).strip()
                
                # 嘗試找到匹配的實體（精確匹配或部分匹配）
                source_entity = None
                target_entity = None
                
                # 精確匹配
                if source_name in entity_map:
                    source_entity = entity_map[source_name]
                if target_name in entity_map:
                    target_entity = entity_map[target_name]
                
                # 部分匹配（如果實體名稱包含在匹配的文字中）
                if not source_entity or not target_entity:
                    for entity in entities:
                        if not source_entity and entity.name in source_name:
                            source_entity = entity
                        if not target_entity and entity.name in target_name:
                            target_entity = entity
                
                # 如果找到兩個不同的實體，建立關係
                if source_entity and target_entity and source_entity.id != target_entity.id:
                    relation_key = (source_entity.id, target_entity.id, relation_type)
                    if relation_key not in seen_relations:
                        relation = Relation(
                            id=str(uuid.uuid4()),
                            source_id=source_entity.id,
                            target_id=target_entity.id,
                            type=relation_type,
                            properties={
                                "extracted_by": "rule_based",
                                "source_text": source_name,
                                "target_text": target_name
                            },
                            weight=0.5,  # 規則基礎的權重較低
                            created_at=datetime.now()
                        )
                        relations.append(relation)
                        seen_relations.add(relation_key)
        
        # 如果沒有找到模式匹配的關係，嘗試基於實體共現建立關係
        if not relations and len(entities) >= 2:
            # 檢查實體是否在同一句子中出現
            sentences = re.split(r'[。！？\n]', text)
            for sentence in sentences:
                if len(sentence.strip()) < 5:  # 跳過太短的句子
                    continue
                
                # 找出在這個句子中出現的實體
                sentence_entities = [
                    e for e in entities 
                    if e.name in sentence and len(e.name) > 1
                ]
                
                # 如果句子中有多個實體，建立 RELATED_TO 關係
                if len(sentence_entities) >= 2:
                    for i in range(len(sentence_entities)):
                        for j in range(i + 1, len(sentence_entities)):
                            source = sentence_entities[i]
                            target = sentence_entities[j]
                            
                            relation_key = (source.id, target.id, 'RELATED_TO')
                            if relation_key not in seen_relations and source.id != target.id:
                                relation = Relation(
                                    id=str(uuid.uuid4()),
                                    source_id=source.id,
                                    target_id=target.id,
                                    type="RELATED_TO",
                                    properties={
                                        "extracted_by": "rule_based",
                                        "method": "co_occurrence",
                                        "sentence": sentence[:100]  # 保留前100字元
                                    },
                                    weight=0.3,  # 共現關係的權重更低
                                    created_at=datetime.now()
                                )
                                relations.append(relation)
                                seen_relations.add(relation_key)
        
        # #region agent log
        log_data = {
            "sessionId": "debug-session",
            "runId": "run1",
            "hypothesisId": "C",
            "location": "entity_extractor.py:_rule_based_relation_extraction:exit",
            "message": "Rule-based extraction completed",
            "data": {
                "relations_count": len(relations),
                "pattern_matches": len([r for r in relations if r.properties.get("extracted_by") == "rule_based" and r.properties.get("method") != "co_occurrence"]),
                "co_occurrence_matches": len([r for r in relations if r.properties.get("method") == "co_occurrence"])
            },
            "timestamp": int(__import__("time").time() * 1000)
        }
        with open("logs/debug.log", "a", encoding="utf-8") as f:
            f.write(json.dumps(log_data, ensure_ascii=False) + "\n")
        # #endregion
        
        self.logger.info(f"Extracted {len(relations)} relations using rule-based method")
        return relations

