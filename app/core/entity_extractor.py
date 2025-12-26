"""
實體和關係提取器
使用 LLM 從文字中提取實體和關係
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
import re
from typing import List, Dict, Any, Optional
from app.core.graph_store import Entity, Relation
from app.services.llm_service import LLMService
from datetime import datetime
import uuid

logger = logging.getLogger("EntityExtractor")


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
            response = await self.llm_service.generate(prompt, max_tokens=1000)
            
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
                with open(".cursor/debug.log", "a", encoding="utf-8") as f:
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
                with open(".cursor/debug.log", "a", encoding="utf-8") as f:
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
            with open(".cursor/debug.log", "a", encoding="utf-8") as f:
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
            with open(".cursor/debug.log", "a", encoding="utf-8") as f:
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
            with open(".cursor/debug.log", "a", encoding="utf-8") as f:
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
        with open(".cursor/debug.log", "a", encoding="utf-8") as f:
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
            with open(".cursor/debug.log", "a", encoding="utf-8") as f:
                f.write(json.dumps(log_data, ensure_ascii=False) + "\n")
            # #endregion
            return []
        
        try:
            # 構建提示詞
            prompt = self._build_relation_extraction_prompt(text, entities)
            
            # 使用 LLM 提取關係
            response = await self.llm_service.generate(prompt, max_tokens=1000)
            
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
            with open(".cursor/debug.log", "a", encoding="utf-8") as f:
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
            with open(".cursor/debug.log", "a", encoding="utf-8") as f:
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
                with open(".cursor/debug.log", "a", encoding="utf-8") as f:
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
            with open(".cursor/debug.log", "a", encoding="utf-8") as f:
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
    
    def _parse_entity_response(self, response: str, original_text: str) -> List[Entity]:
        """解析 LLM 回應為實體列表"""
        # json 模組已在文件頂部統一導入
        entities = []
        matched_pattern = None  # 記錄匹配到的正則表達式模式
        
        try:
            # 嘗試提取 JSON（更嚴格的匹配）
            # 尋找 JSON 陣列，可能包含在 markdown 代碼塊中
            json_patterns = [
                (r'```json\s*(\[.*?\])\s*```', 'markdown_json_codeblock'),  # markdown JSON 代碼塊（非貪婪，但代碼塊內完整）
                (r'```\s*(\[.*?\])\s*```', 'codeblock'),      # 普通代碼塊（非貪婪，但代碼塊內完整）
                (r'(\[[\s\S]*\])', 'direct_array'),              # 直接 JSON 陣列（貪婪匹配，匹配到最後一個 ]）
            ]
            
            json_str = None
            for pattern, pattern_name in json_patterns:
                match = re.search(pattern, response, re.DOTALL)
                if match:
                    json_str = match.group(1) if match.groups() else match.group(0)
                    matched_pattern = pattern_name
                    break
            
            # 如果沒找到，嘗試直接解析整個回應
            if not json_str:
                # 檢查是否整個回應就是 JSON
                response_stripped = response.strip()
                if response_stripped.startswith('[') and response_stripped.endswith(']'):
                    json_str = response_stripped
                    matched_pattern = 'full_response'
                else:
                    # 嘗試找到第一個 [ 到最後一個 ]
                    start = response.find('[')
                    end = response.rfind(']')
                    if start != -1 and end != -1 and end > start:
                        json_str = response[start:end+1]
                        matched_pattern = 'find_brackets'
            
            if json_str:
                # 清理可能的多餘空白和換行
                json_str = json_str.strip()
                
                # 驗證 JSON 完整性：檢查 [ 和 ] 數量是否匹配
                open_brackets = json_str.count('[')
                close_brackets = json_str.count(']')
                if open_brackets != close_brackets:
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
                    with open(".cursor/debug.log", "a", encoding="utf-8") as f:
                        f.write(json.dumps(log_data, ensure_ascii=False) + "\n")
                    return entities  # 返回空列表，觸發降級
                
                # 嘗試解析 JSON
                data = json.loads(json_str)
                
                if isinstance(data, list):
                    for item in data:
                        if isinstance(item, dict) and "name" in item:
                            entity = Entity(
                                id=str(uuid.uuid4()),
                                type=item.get("type", "Concept"),
                                name=item.get("name", ""),
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
            with open(".cursor/debug.log", "a", encoding="utf-8") as f:
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
            with open(".cursor/debug.log", "a", encoding="utf-8") as f:
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
            # 嘗試提取 JSON（更嚴格的匹配）
            json_patterns = [
                (r'```json\s*(\[.*?\])\s*```', 'markdown_json_codeblock'),  # markdown JSON 代碼塊（非貪婪，但代碼塊內完整）
                (r'```\s*(\[.*?\])\s*```', 'codeblock'),      # 普通代碼塊（非貪婪，但代碼塊內完整）
                (r'(\[[\s\S]*\])', 'direct_array'),              # 直接 JSON 陣列（貪婪匹配，匹配到最後一個 ]）
            ]
            
            json_str = None
            for pattern, pattern_name in json_patterns:
                match = re.search(pattern, response, re.DOTALL)
                if match:
                    json_str = match.group(1) if match.groups() else match.group(0)
                    matched_pattern = pattern_name
                    break
            
            # 如果沒找到，嘗試直接解析整個回應
            if not json_str:
                response_stripped = response.strip()
                if response_stripped.startswith('[') and response_stripped.endswith(']'):
                    json_str = response_stripped
                    matched_pattern = 'full_response'
                else:
                    start = response.find('[')
                    end = response.rfind(']')
                    if start != -1 and end != -1 and end > start:
                        json_str = response[start:end+1]
                        matched_pattern = 'find_brackets'
            
            if json_str:
                json_str = json_str.strip()
                
                # 驗證 JSON 完整性：檢查 [ 和 ] 數量是否匹配
                open_brackets = json_str.count('[')
                close_brackets = json_str.count(']')
                if open_brackets != close_brackets:
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
                    with open(".cursor/debug.log", "a", encoding="utf-8") as f:
                        f.write(json.dumps(log_data, ensure_ascii=False) + "\n")
                    return relations  # 返回空列表，觸發降級
                
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
                            
                            if source_entity and target_entity:
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
                                    with open(".cursor/debug.log", "a", encoding="utf-8") as f:
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
                        with open(".cursor/debug.log", "a", encoding="utf-8") as f:
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
            with open(".cursor/debug.log", "a", encoding="utf-8") as f:
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
            with open(".cursor/debug.log", "a", encoding="utf-8") as f:
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
        
        # 1. 提取中文名詞（2-6個中文字）
        chinese_pattern = r'[\u4e00-\u9fff]{2,6}'
        chinese_matches = re.findall(chinese_pattern, text)
        for match in chinese_matches:
            if match not in seen_names and len(match) >= 2:
                seen_names.add(match)
                entity = Entity(
                    id=str(uuid.uuid4()),
                    type="Concept",
                    name=match,
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
        with open(".cursor/debug.log", "a", encoding="utf-8") as f:
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
            with open(".cursor/debug.log", "a", encoding="utf-8") as f:
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
                            if relation_key not in seen_relations:
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
        with open(".cursor/debug.log", "a", encoding="utf-8") as f:
            f.write(json.dumps(log_data, ensure_ascii=False) + "\n")
        # #endregion
        
        self.logger.info(f"Extracted {len(relations)} relations using rule-based method")
        return relations

