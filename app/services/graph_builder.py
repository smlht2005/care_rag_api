"""
圖構建服務
從文件內容構建圖結構
"""
import logging
from typing import Dict, List, Any, Optional
from app.core.graph_store import GraphStore, Entity, Relation
from app.core.entity_extractor import EntityExtractor

logger = logging.getLogger("GraphBuilder")


class GraphBuilder:
    """圖構建服務"""
    
    def __init__(
        self,
        graph_store: GraphStore,
        entity_extractor: EntityExtractor
    ):
        self.graph_store = graph_store
        self.entity_extractor = entity_extractor
        self.logger = logging.getLogger("GraphBuilder")
    
    async def build_graph_from_text(
        self,
        text: str,
        document_id: str,
        entity_types: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        從文字構建圖結構
        
        Args:
            text: 文件文字內容
            document_id: 文件 ID
            entity_types: 要提取的實體類型列表（可選）
        
        Returns:
            構建結果統計
        """
        try:
            self.logger.info(f"Building graph from text for document: {document_id}")
            
            # 1. 提取實體
            entities = await self.entity_extractor.extract_entities(text, entity_types)
            
            # 2. 建立文件實體
            doc_entity = Entity(
                id=document_id,
                type="Document",
                name=f"Document_{document_id}",
                properties={"source": "graph_builder"},
                created_at=None
            )
            entities.append(doc_entity)
            
            # 3. 儲存實體
            saved_entities = []
            for entity in entities:
                success = await self.graph_store.add_entity(entity)
                if success:
                    saved_entities.append(entity)
            
            # #region agent log
            import json
            log_data = {
                "sessionId": "debug-session",
                "runId": "run1",
                "hypothesisId": "A",
                "location": "graph_builder.py:build_graph_from_text:before_extract_relations",
                "message": "Before extract_relations call",
                "data": {
                    "saved_entities_count": len(saved_entities),
                    "saved_entities": [{"id": e.id, "name": e.name, "type": e.type} for e in saved_entities[:10]],
                    "document_id": document_id
                },
                "timestamp": int(__import__("time").time() * 1000)
            }
            with open(".cursor/debug.log", "a", encoding="utf-8") as f:
                f.write(json.dumps(log_data, ensure_ascii=False) + "\n")
            # #endregion
            
            # 4. 提取關係
            relations = await self.entity_extractor.extract_relations(text, saved_entities)
            
            # #region agent log
            log_data = {
                "sessionId": "debug-session",
                "runId": "run1",
                "hypothesisId": "E",
                "location": "graph_builder.py:build_graph_from_text:after_extract_relations",
                "message": "After extract_relations call",
                "data": {
                    "extracted_relations_count": len(relations) if relations else 0,
                    "relations": [{"id": r.id, "source": r.source_id, "target": r.target_id, "type": r.type} for r in relations[:5]] if relations else []
                },
                "timestamp": int(__import__("time").time() * 1000)
            }
            with open(".cursor/debug.log", "a", encoding="utf-8") as f:
                f.write(json.dumps(log_data, ensure_ascii=False) + "\n")
            # #endregion
            
            # 5. 建立文件與實體的關係
            contains_relations_count = 0
            for entity in saved_entities:
                if entity.id != document_id:
                    relation = Relation(
                        id=f"{document_id}_contains_{entity.id}",
                        source_id=document_id,
                        target_id=entity.id,
                        type="CONTAINS",
                        properties={"extracted_from": "document"},
                        weight=1.0,
                        created_at=None
                    )
                    relations.append(relation)
                    contains_relations_count += 1
            
            # #region agent log
            log_data = {
                "sessionId": "debug-session",
                "runId": "run1",
                "hypothesisId": "E",
                "location": "graph_builder.py:build_graph_from_text:after_contains_relations",
                "message": "After adding CONTAINS relations",
                "data": {
                    "total_relations_count": len(relations),
                    "contains_relations_count": contains_relations_count,
                    "extracted_relations_count": len(relations) - contains_relations_count
                },
                "timestamp": int(__import__("time").time() * 1000)
            }
            with open(".cursor/debug.log", "a", encoding="utf-8") as f:
                f.write(json.dumps(log_data, ensure_ascii=False) + "\n")
            # #endregion
            
            # 6. 儲存關係
            saved_relations = []
            failed_relations = []
            for relation in relations:
                success = await self.graph_store.add_relation(relation)
                if success:
                    saved_relations.append(relation)
                else:
                    failed_relations.append(relation.id)
            
            # #region agent log
            log_data = {
                "sessionId": "debug-session",
                "runId": "run1",
                "hypothesisId": "E",
                "location": "graph_builder.py:build_graph_from_text:after_save_relations",
                "message": "After saving relations to database",
                "data": {
                    "total_relations": len(relations),
                    "saved_relations_count": len(saved_relations),
                    "failed_relations_count": len(failed_relations),
                    "failed_relation_ids": failed_relations[:5]
                },
                "timestamp": int(__import__("time").time() * 1000)
            }
            with open(".cursor/debug.log", "a", encoding="utf-8") as f:
                f.write(json.dumps(log_data, ensure_ascii=False) + "\n")
            # #endregion
            
            result = {
                "document_id": document_id,
                "entities_count": len(saved_entities),
                "relations_count": len(saved_relations),
                "entities": [e.id for e in saved_entities],
                "relations": [r.id for r in saved_relations]
            }
            
            self.logger.info(
                f"Graph built: {len(saved_entities)} entities, "
                f"{len(saved_relations)} relations"
            )
            
            return result
            
        except Exception as e:
            self.logger.error(f"Failed to build graph from text: {str(e)}")
            raise
    
    async def build_graph_from_document(
        self,
        document: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        從文件物件構建圖結構
        
        Args:
            document: 文件字典，包含 id 和 content 欄位
        
        Returns:
            構建結果統計
        """
        document_id = document.get("id", "")
        content = document.get("content", "")
        
        if not document_id or not content:
            raise ValueError("Document must have 'id' and 'content' fields")
        
        return await self.build_graph_from_text(content, document_id)
    
    async def update_graph_from_text(
        self,
        text: str,
        document_id: str
    ) -> Dict[str, Any]:
        """
        更新文件的圖結構（先刪除舊的，再建立新的）
        
        Args:
            text: 新的文件文字內容
            document_id: 文件 ID
        
        Returns:
            更新結果統計
        """
        try:
            self.logger.info(f"Updating graph for document: {document_id}")
            
            # 刪除舊的實體和關係（級聯刪除會自動處理關係）
            await self.graph_store.delete_entity(document_id)
            
            # 重新構建
            return await self.build_graph_from_text(text, document_id)
            
        except Exception as e:
            self.logger.error(f"Failed to update graph: {str(e)}")
            raise
    
    async def build_graph_from_documents_batch(
        self,
        documents: List[Dict[str, Any]],
        batch_size: int = 10
    ) -> Dict[str, Any]:
        """
        批次構建圖結構
        
        Args:
            documents: 文件列表
            batch_size: 批次大小
        
        Returns:
            批次構建結果統計
        """
        total_entities = 0
        total_relations = 0
        success_count = 0
        error_count = 0
        
        for i in range(0, len(documents), batch_size):
            batch = documents[i:i + batch_size]
            
            for doc in batch:
                try:
                    result = await self.build_graph_from_document(doc)
                    total_entities += result.get("entities_count", 0)
                    total_relations += result.get("relations_count", 0)
                    success_count += 1
                except Exception as e:
                    self.logger.error(f"Failed to build graph for document {doc.get('id')}: {str(e)}")
                    error_count += 1
        
        return {
            "total_documents": len(documents),
            "success_count": success_count,
            "error_count": error_count,
            "total_entities": total_entities,
            "total_relations": total_relations
        }

