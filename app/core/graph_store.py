"""
GraphRAG 圖結構儲存系統
"""
import json
import uuid
import asyncio
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path

try:
    import aiosqlite
except ImportError:
    aiosqlite = None

from app.config import settings

logger = logging.getLogger("GraphStore")


@dataclass
class Entity:
    """實體類別"""
    id: str
    type: str
    name: str
    properties: Dict[str, Any]
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.updated_at is None:
            self.updated_at = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典"""
        return {
            "id": self.id,
            "type": self.type,
            "name": self.name,
            "properties": self.properties,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Entity":
        """從字典建立實體"""
        return cls(
            id=data["id"],
            type=data["type"],
            name=data["name"],
            properties=data.get("properties", {}),
            created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else None,
            updated_at=datetime.fromisoformat(data["updated_at"]) if data.get("updated_at") else None
        )


@dataclass
class Relation:
    """關係類別"""
    id: str
    source_id: str
    target_id: str
    type: str
    properties: Dict[str, Any]
    weight: float = 1.0
    created_at: Optional[datetime] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.source_id == self.target_id:
            raise ValueError("Source and target cannot be the same entity")
    
    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典"""
        return {
            "id": self.id,
            "source_id": self.source_id,
            "target_id": self.target_id,
            "type": self.type,
            "properties": self.properties,
            "weight": self.weight,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Relation":
        """從字典建立關係"""
        return cls(
            id=data["id"],
            source_id=data["source_id"],
            target_id=data["target_id"],
            type=data["type"],
            properties=data.get("properties", {}),
            weight=data.get("weight", 1.0),
            created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else None
        )


class GraphStore(ABC):
    """圖儲存抽象介面"""
    
    @abstractmethod
    async def initialize(self) -> bool:
        """初始化儲存系統"""
        pass
    
    @abstractmethod
    async def add_entity(self, entity: Entity) -> bool:
        """新增實體"""
        pass
    
    @abstractmethod
    async def get_entity(self, entity_id: str) -> Optional[Entity]:
        """取得實體"""
        pass
    
    @abstractmethod
    async def delete_entity(self, entity_id: str) -> bool:
        """刪除實體（級聯刪除關係）"""
        pass
    
    @abstractmethod
    async def add_relation(self, relation: Relation) -> bool:
        """新增關係"""
        pass
    
    @abstractmethod
    async def get_relation(self, relation_id: str) -> Optional[Relation]:
        """取得關係"""
        pass
    
    @abstractmethod
    async def delete_relation(self, relation_id: str) -> bool:
        """刪除關係"""
        pass
    
    @abstractmethod
    async def get_entities_by_type(self, entity_type: str, limit: int = 100) -> List[Entity]:
        """依類型查詢實體"""
        pass
    
    @abstractmethod
    async def search_entities(self, query: str, limit: int = 10) -> List[Entity]:
        """搜尋實體"""
        pass
    
    @abstractmethod
    async def get_neighbors(
        self,
        entity_id: str,
        relation_type: Optional[str] = None,
        direction: str = "both"
    ) -> List[Entity]:
        """取得實體的鄰居節點"""
        pass
    
    @abstractmethod
    async def get_path(
        self,
        source_id: str,
        target_id: str,
        max_hops: int = 3
    ) -> List[List[str]]:
        """取得從 source_id 到 target_id 的所有路徑（BFS）"""
        pass
    
    @abstractmethod
    async def get_subgraph(
        self,
        entity_ids: List[str],
        max_depth: int = 2
    ) -> Dict[str, Any]:
        """取得包含指定實體的子圖"""
        pass
    
    @abstractmethod
    async def get_statistics(self) -> Dict[str, Any]:
        """
        取得圖結構統計資訊
        
        Returns:
            包含以下鍵的字典：
            - total_entities: 實體總數
            - total_relations: 關係總數
            - entity_types: 實體類型統計 {type: count}
            - relation_types: 關係類型統計 {type: count}
        """
        pass
    
    @abstractmethod
    async def get_relations_by_entity(
        self,
        entity_id: str,
        direction: str = "both"
    ) -> List[Relation]:
        """
        獲取實體的所有關係
        
        Args:
            entity_id: 實體 ID
            direction: 關係方向 ("incoming", "outgoing", "both")
        
        Returns:
            關係列表
        """
        pass
    
    @abstractmethod
    async def get_relations_by_type(
        self,
        relation_type: str,
        limit: int = 100
    ) -> List[Relation]:
        """
        按類型查詢關係
        
        Args:
            relation_type: 關係類型
            limit: 查詢限制
        
        Returns:
            關係列表
        """
        pass


class SQLiteGraphStore(GraphStore):
    """SQLite 圖儲存實作"""
    
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or settings.GRAPH_DB_PATH
        self.conn: Optional[Any] = None
        self.logger = logging.getLogger("SQLiteGraphStore")
        
        if aiosqlite is None:
            raise ImportError("aiosqlite is required for SQLiteGraphStore. Install it with: pip install aiosqlite")
    
    async def initialize(self) -> bool:
        """初始化資料庫"""
        try:
            # 確保目錄存在
            db_dir = Path(self.db_path).parent
            db_dir.mkdir(parents=True, exist_ok=True)
            
            self.conn = await aiosqlite.connect(self.db_path)
            self.conn.row_factory = aiosqlite.Row
            
            # 建立資料表
            await self._create_tables()
            
            self.logger.info(f"GraphStore initialized: {self.db_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize GraphStore: {str(e)}")
            raise
    
    async def _create_tables(self):
        """建立資料表"""
        async with self.conn.cursor() as cursor:
            # Entities 表
            await cursor.execute("""
                CREATE TABLE IF NOT EXISTS entities (
                    id TEXT PRIMARY KEY,
                    type TEXT NOT NULL,
                    name TEXT NOT NULL,
                    properties TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)
            
            await cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_entities_type ON entities(type)
            """)
            
            await cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_entities_name ON entities(name)
            """)
            
            # Relations 表
            await cursor.execute("""
                CREATE TABLE IF NOT EXISTS relations (
                    id TEXT PRIMARY KEY,
                    source_id TEXT NOT NULL,
                    target_id TEXT NOT NULL,
                    type TEXT NOT NULL,
                    properties TEXT NOT NULL,
                    weight REAL DEFAULT 1.0,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (source_id) REFERENCES entities(id) ON DELETE CASCADE,
                    FOREIGN KEY (target_id) REFERENCES entities(id) ON DELETE CASCADE,
                    CHECK (source_id != target_id)
                )
            """)
            
            await cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_relations_source ON relations(source_id)
            """)
            
            await cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_relations_target ON relations(target_id)
            """)
            
            await cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_relations_type ON relations(type)
            """)
            
            await self.conn.commit()
    
    async def add_entity(self, entity: Entity) -> bool:
        """新增實體"""
        try:
            async with self.conn.cursor() as cursor:
                await cursor.execute("""
                    INSERT OR REPLACE INTO entities (id, type, name, properties, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    entity.id,
                    entity.type,
                    entity.name,
                    json.dumps(entity.properties, ensure_ascii=False),
                    entity.created_at.isoformat(),
                    entity.updated_at.isoformat()
                ))
                await self.conn.commit()
                return True
        except Exception as e:
            self.logger.error(f"Failed to add entity: {str(e)}")
            await self.conn.rollback()
            return False
    
    async def get_entity(self, entity_id: str) -> Optional[Entity]:
        """取得實體"""
        try:
            async with self.conn.cursor() as cursor:
                await cursor.execute("""
                    SELECT * FROM entities WHERE id = ?
                """, (entity_id,))
                row = await cursor.fetchone()
                
                if row:
                    return Entity(
                        id=row["id"],
                        type=row["type"],
                        name=row["name"],
                        properties=json.loads(row["properties"]),
                        created_at=datetime.fromisoformat(row["created_at"]),
                        updated_at=datetime.fromisoformat(row["updated_at"])
                    )
                return None
        except Exception as e:
            self.logger.error(f"Failed to get entity: {str(e)}")
            return None
    
    async def delete_entity(self, entity_id: str) -> bool:
        """刪除實體（級聯刪除關係）"""
        try:
            async with self.conn.cursor() as cursor:
                await cursor.execute("DELETE FROM entities WHERE id = ?", (entity_id,))
                await self.conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            self.logger.error(f"Failed to delete entity: {str(e)}")
            await self.conn.rollback()
            return False
    
    async def add_relation(self, relation: Relation) -> bool:
        """新增關係"""
        try:
            # 檢查實體是否存在
            source = await self.get_entity(relation.source_id)
            target = await self.get_entity(relation.target_id)
            
            if not source or not target:
                self.logger.warning(f"Source or target entity not found for relation {relation.id}")
                return False
            
            async with self.conn.cursor() as cursor:
                await cursor.execute("""
                    INSERT OR REPLACE INTO relations 
                    (id, source_id, target_id, type, properties, weight, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    relation.id,
                    relation.source_id,
                    relation.target_id,
                    relation.type,
                    json.dumps(relation.properties, ensure_ascii=False),
                    relation.weight,
                    relation.created_at.isoformat()
                ))
                await self.conn.commit()
                return True
        except Exception as e:
            self.logger.error(f"Failed to add relation: {str(e)}")
            await self.conn.rollback()
            return False
    
    async def get_relation(self, relation_id: str) -> Optional[Relation]:
        """取得關係"""
        try:
            async with self.conn.cursor() as cursor:
                await cursor.execute("""
                    SELECT * FROM relations WHERE id = ?
                """, (relation_id,))
                row = await cursor.fetchone()
                
                if row:
                    return Relation(
                        id=row["id"],
                        source_id=row["source_id"],
                        target_id=row["target_id"],
                        type=row["type"],
                        properties=json.loads(row["properties"]),
                        weight=row["weight"],
                        created_at=datetime.fromisoformat(row["created_at"])
                    )
                return None
        except Exception as e:
            self.logger.error(f"Failed to get relation: {str(e)}")
            return None
    
    async def delete_relation(self, relation_id: str) -> bool:
        """刪除關係"""
        try:
            async with self.conn.cursor() as cursor:
                await cursor.execute("DELETE FROM relations WHERE id = ?", (relation_id,))
                await self.conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            self.logger.error(f"Failed to delete relation: {str(e)}")
            await self.conn.rollback()
            return False
    
    async def get_entities_by_type(self, entity_type: str, limit: int = 100) -> List[Entity]:
        """依類型查詢實體"""
        try:
            async with self.conn.cursor() as cursor:
                await cursor.execute("""
                    SELECT * FROM entities WHERE type = ? LIMIT ?
                """, (entity_type, limit))
                rows = await cursor.fetchall()
                
                return [
                    Entity(
                        id=row["id"],
                        type=row["type"],
                        name=row["name"],
                        properties=json.loads(row["properties"]),
                        created_at=datetime.fromisoformat(row["created_at"]),
                        updated_at=datetime.fromisoformat(row["updated_at"])
                    )
                    for row in rows
                ]
        except Exception as e:
            self.logger.error(f"Failed to get entities by type: {str(e)}")
            return []
    
    async def search_entities(self, query: str, limit: int = 10) -> List[Entity]:
        """搜尋實體（依名稱）"""
        try:
            async with self.conn.cursor() as cursor:
                await cursor.execute("""
                    SELECT * FROM entities 
                    WHERE name LIKE ? OR type LIKE ?
                    LIMIT ?
                """, (f"%{query}%", f"%{query}%", limit))
                rows = await cursor.fetchall()
                
                return [
                    Entity(
                        id=row["id"],
                        type=row["type"],
                        name=row["name"],
                        properties=json.loads(row["properties"]),
                        created_at=datetime.fromisoformat(row["created_at"]),
                        updated_at=datetime.fromisoformat(row["updated_at"])
                    )
                    for row in rows
                ]
        except Exception as e:
            self.logger.error(f"Failed to search entities: {str(e)}")
            return []
    
    async def get_neighbors(
        self,
        entity_id: str,
        relation_type: Optional[str] = None,
        direction: str = "both"
    ) -> List[Entity]:
        """取得實體的鄰居節點"""
        try:
            neighbors = []
            
            async with self.conn.cursor() as cursor:
                if direction in ["outgoing", "both"]:
                    query = "SELECT target_id FROM relations WHERE source_id = ?"
                    params = [entity_id]
                    if relation_type:
                        query += " AND type = ?"
                        params.append(relation_type)
                    
                    await cursor.execute(query, params)
                    target_ids = [row[0] for row in await cursor.fetchall()]
                    
                    for target_id in target_ids:
                        entity = await self.get_entity(target_id)
                        if entity:
                            neighbors.append(entity)
                
                if direction in ["incoming", "both"]:
                    query = "SELECT source_id FROM relations WHERE target_id = ?"
                    params = [entity_id]
                    if relation_type:
                        query += " AND type = ?"
                        params.append(relation_type)
                    
                    await cursor.execute(query, params)
                    source_ids = [row[0] for row in await cursor.fetchall()]
                    
                    for source_id in source_ids:
                        entity = await self.get_entity(source_id)
                        if entity and entity not in neighbors:
                            neighbors.append(entity)
            
            return neighbors
        except Exception as e:
            self.logger.error(f"Failed to get neighbors: {str(e)}")
            return []
    
    async def get_path(
        self,
        source_id: str,
        target_id: str,
        max_hops: int = 3
    ) -> List[List[str]]:
        """取得從 source_id 到 target_id 的所有路徑（BFS）"""
        if source_id == target_id:
            return [[source_id]]
        
        paths = []
        queue = [(source_id, [source_id])]
        visited = set()
        
        while queue and len(paths) < 100:  # 限制路徑數量
            current_id, path = queue.pop(0)
            
            if len(path) > max_hops:
                continue
            
            if current_id in visited:
                continue
            
            visited.add(current_id)
            
            # 取得鄰居
            neighbors = await self.get_neighbors(current_id, direction="outgoing")
            
            for neighbor in neighbors:
                if neighbor.id == target_id:
                    paths.append(path + [neighbor.id])
                elif neighbor.id not in path:  # 避免循環
                    queue.append((neighbor.id, path + [neighbor.id]))
        
        return paths
    
    async def get_subgraph(
        self,
        entity_ids: List[str],
        max_depth: int = 2
    ) -> Dict[str, Any]:
        """取得包含指定實體的子圖"""
        entities_set = set(entity_ids)
        relations_list = []
        
        # BFS 擴展
        queue = [(entity_id, 0) for entity_id in entity_ids]
        visited = set()
        
        while queue:
            entity_id, depth = queue.pop(0)
            
            if entity_id in visited or depth > max_depth:
                continue
            
            visited.add(entity_id)
            entity = await self.get_entity(entity_id)
            if entity:
                entities_set.add(entity_id)
            
            # 取得關係
            async with self.conn.cursor() as cursor:
                await cursor.execute("""
                    SELECT * FROM relations 
                    WHERE source_id = ? OR target_id = ?
                """, (entity_id, entity_id))
                rows = await cursor.fetchall()
                
                for row in rows:
                    relation = Relation(
                        id=row["id"],
                        source_id=row["source_id"],
                        target_id=row["target_id"],
                        type=row["type"],
                        properties=json.loads(row["properties"]),
                        weight=row["weight"],
                        created_at=datetime.fromisoformat(row["created_at"])
                    )
                    
                    if relation not in relations_list:
                        relations_list.append(relation)
                    
                    # 添加到隊列
                    next_id = relation.target_id if relation.source_id == entity_id else relation.source_id
                    if next_id not in visited and depth < max_depth:
                        queue.append((next_id, depth + 1))
        
        # 取得所有實體
        entities = []
        for entity_id in entities_set:
            entity = await self.get_entity(entity_id)
            if entity:
                entities.append(entity)
        
        return {
            "entities": [e.to_dict() for e in entities],
            "relations": [r.to_dict() for r in relations_list]
        }
    
    async def get_statistics(self) -> Dict[str, Any]:
        """取得圖結構統計資訊"""
        try:
            if not self.conn:
                await self.initialize()
            
            async with self.conn.cursor() as cursor:
                # 獲取實體總數
                await cursor.execute("SELECT COUNT(*) FROM entities")
                total_entities = (await cursor.fetchone())[0]
                
                # 獲取關係總數
                await cursor.execute("SELECT COUNT(*) FROM relations")
                total_relations = (await cursor.fetchone())[0]
                
                # 獲取實體類型統計
                await cursor.execute("""
                    SELECT type, COUNT(*) as count 
                    FROM entities 
                    GROUP BY type
                """)
                entity_types = {row['type']: row['count'] for row in await cursor.fetchall()}
                
                # 獲取關係類型統計
                await cursor.execute("""
                    SELECT type, COUNT(*) as count 
                    FROM relations 
                    GROUP BY type
                """)
                relation_types = {row['type']: row['count'] for row in await cursor.fetchall()}
            
            return {
                "total_entities": total_entities,
                "total_relations": total_relations,
                "entity_types": entity_types,
                "relation_types": relation_types
            }
        except Exception as e:
            self.logger.error(f"Failed to get statistics: {str(e)}")
            return {
                "total_entities": 0,
                "total_relations": 0,
                "entity_types": {},
                "relation_types": {}
            }
    
    async def get_relations_by_entity(
        self,
        entity_id: str,
        direction: str = "both"
    ) -> List[Relation]:
        """獲取實體的所有關係"""
        try:
            if not self.conn:
                await self.initialize()
            
            relations = []
            async with self.conn.cursor() as cursor:
                if direction == "both":
                    await cursor.execute("""
                        SELECT * FROM relations 
                        WHERE source_id = ? OR target_id = ?
                    """, (entity_id, entity_id))
                elif direction == "outgoing":
                    await cursor.execute("""
                        SELECT * FROM relations 
                        WHERE source_id = ?
                    """, (entity_id,))
                elif direction == "incoming":
                    await cursor.execute("""
                        SELECT * FROM relations 
                        WHERE target_id = ?
                    """, (entity_id,))
                else:
                    return []
                
                rows = await cursor.fetchall()
                for row in rows:
                    relations.append(Relation(
                        id=row["id"],
                        source_id=row["source_id"],
                        target_id=row["target_id"],
                        type=row["type"],
                        properties=json.loads(row["properties"]),
                        weight=row["weight"],
                        created_at=datetime.fromisoformat(row["created_at"])
                    ))
            
            return relations
        except Exception as e:
            self.logger.error(f"Failed to get relations by entity: {str(e)}")
            return []
    
    async def get_relations_by_type(
        self,
        relation_type: str,
        limit: int = 100
    ) -> List[Relation]:
        """按類型查詢關係"""
        try:
            if not self.conn:
                await self.initialize()
            
            relations = []
            async with self.conn.cursor() as cursor:
                await cursor.execute("""
                    SELECT * FROM relations 
                    WHERE type = ?
                    LIMIT ?
                """, (relation_type, limit))
                
                rows = await cursor.fetchall()
                for row in rows:
                    relations.append(Relation(
                        id=row["id"],
                        source_id=row["source_id"],
                        target_id=row["target_id"],
                        type=row["type"],
                        properties=json.loads(row["properties"]),
                        weight=row["weight"],
                        created_at=datetime.fromisoformat(row["created_at"])
                    ))
            
            return relations
        except Exception as e:
            self.logger.error(f"Failed to get relations by type: {str(e)}")
            return []
    
    async def close(self):
        """關閉資料庫連線"""
        if self.conn:
            try:
                # 確保連接正確關閉，但允許被取消
                await self.conn.close()
                self.conn = None
            except asyncio.CancelledError:
                # 如果被取消，嘗試強制關閉連接
                if self.conn:
                    try:
                        # 嘗試同步關閉（如果可能）
                        if hasattr(self.conn, '_conn') and self.conn._conn:
                            self.conn._conn.close()
                    except:
                        pass
                    self.conn = None
                raise  # 重新拋出 CancelledError


class MemoryGraphStore(GraphStore):
    """記憶體圖儲存（用於測試）"""
    
    def __init__(self):
        self.entities: Dict[str, Entity] = {}
        self.relations: Dict[str, Relation] = {}
        self.entity_relations: Dict[str, List[str]] = {}  # entity_id -> [relation_ids]
        self.logger = logging.getLogger("MemoryGraphStore")
    
    async def initialize(self) -> bool:
        """初始化（記憶體模式不需要）"""
        return True
    
    async def add_entity(self, entity: Entity) -> bool:
        """新增實體"""
        self.entities[entity.id] = entity
        if entity.id not in self.entity_relations:
            self.entity_relations[entity.id] = []
        return True
    
    async def get_entity(self, entity_id: str) -> Optional[Entity]:
        """取得實體"""
        return self.entities.get(entity_id)
    
    async def delete_entity(self, entity_id: str) -> bool:
        """刪除實體"""
        if entity_id in self.entities:
            # 刪除相關關係
            relation_ids = self.entity_relations.get(entity_id, [])
            for rel_id in relation_ids[:]:
                await self.delete_relation(rel_id)
            
            del self.entities[entity_id]
            del self.entity_relations[entity_id]
            return True
        return False
    
    async def add_relation(self, relation: Relation) -> bool:
        """新增關係"""
        if relation.source_id not in self.entities or relation.target_id not in self.entities:
            return False
        
        self.relations[relation.id] = relation
        
        if relation.source_id not in self.entity_relations:
            self.entity_relations[relation.source_id] = []
        if relation.target_id not in self.entity_relations:
            self.entity_relations[relation.target_id] = []
        
        self.entity_relations[relation.source_id].append(relation.id)
        self.entity_relations[relation.target_id].append(relation.id)
        
        return True
    
    async def get_relation(self, relation_id: str) -> Optional[Relation]:
        """取得關係"""
        return self.relations.get(relation_id)
    
    async def delete_relation(self, relation_id: str) -> bool:
        """刪除關係"""
        if relation_id in self.relations:
            relation = self.relations[relation_id]
            
            if relation.source_id in self.entity_relations:
                self.entity_relations[relation.source_id].remove(relation_id)
            if relation.target_id in self.entity_relations:
                self.entity_relations[relation.target_id].remove(relation_id)
            
            del self.relations[relation_id]
            return True
        return False
    
    async def get_entities_by_type(self, entity_type: str, limit: int = 100) -> List[Entity]:
        """依類型查詢實體"""
        return [e for e in self.entities.values() if e.type == entity_type][:limit]
    
    async def search_entities(self, query: str, limit: int = 10) -> List[Entity]:
        """搜尋實體"""
        results = []
        query_lower = query.lower()
        
        for entity in self.entities.values():
            if query_lower in entity.name.lower() or query_lower in entity.type.lower():
                results.append(entity)
                if len(results) >= limit:
                    break
        
        return results
    
    async def get_neighbors(
        self,
        entity_id: str,
        relation_type: Optional[str] = None,
        direction: str = "both"
    ) -> List[Entity]:
        """取得實體的鄰居節點"""
        neighbors = []
        relation_ids = self.entity_relations.get(entity_id, [])
        
        for rel_id in relation_ids:
            relation = self.relations.get(rel_id)
            if not relation:
                continue
            
            if relation_type and relation.type != relation_type:
                continue
            
            if direction in ["outgoing", "both"] and relation.source_id == entity_id:
                neighbor = self.entities.get(relation.target_id)
                if neighbor and neighbor not in neighbors:
                    neighbors.append(neighbor)
            
            if direction in ["incoming", "both"] and relation.target_id == entity_id:
                neighbor = self.entities.get(relation.source_id)
                if neighbor and neighbor not in neighbors:
                    neighbors.append(neighbor)
        
        return neighbors
    
    async def get_path(
        self,
        source_id: str,
        target_id: str,
        max_hops: int = 3
    ) -> List[List[str]]:
        """取得路徑（BFS）"""
        if source_id == target_id:
            return [[source_id]]
        
        paths = []
        queue = [(source_id, [source_id])]
        visited = set()
        
        while queue and len(paths) < 100:
            current_id, path = queue.pop(0)
            
            if len(path) > max_hops:
                continue
            
            if current_id in visited:
                continue
            
            visited.add(current_id)
            neighbors = await self.get_neighbors(current_id, direction="outgoing")
            
            for neighbor in neighbors:
                if neighbor.id == target_id:
                    paths.append(path + [neighbor.id])
                elif neighbor.id not in path:
                    queue.append((neighbor.id, path + [neighbor.id]))
        
        return paths
    
    async def get_subgraph(
        self,
        entity_ids: List[str],
        max_depth: int = 2
    ) -> Dict[str, Any]:
        """取得子圖"""
        entities_set = set(entity_ids)
        relations_list = []
        queue = [(entity_id, 0) for entity_id in entity_ids]
        visited = set()
        
        while queue:
            entity_id, depth = queue.pop(0)
            
            if entity_id in visited or depth > max_depth:
                continue
            
            visited.add(entity_id)
            entities_set.add(entity_id)
            
            relation_ids = self.entity_relations.get(entity_id, [])
            for rel_id in relation_ids:
                relation = self.relations.get(rel_id)
                if relation and relation not in relations_list:
                    relations_list.append(relation)
                    
                    next_id = relation.target_id if relation.source_id == entity_id else relation.source_id
                    if next_id not in visited and depth < max_depth:
                        queue.append((next_id, depth + 1))
        
        entities = [self.entities[eid] for eid in entities_set if eid in self.entities]
        
        return {
            "entities": [e.to_dict() for e in entities],
            "relations": [r.to_dict() for r in relations_list]
        }
    
    async def get_statistics(self) -> Dict[str, Any]:
        """取得圖結構統計資訊"""
        try:
            # 統計實體類型
            entity_types: Dict[str, int] = {}
            for entity in self.entities.values():
                entity_types[entity.type] = entity_types.get(entity.type, 0) + 1
            
            # 統計關係類型
            relation_types: Dict[str, int] = {}
            for relation in self.relations.values():
                relation_types[relation.type] = relation_types.get(relation.type, 0) + 1
            
            return {
                "total_entities": len(self.entities),
                "total_relations": len(self.relations),
                "entity_types": entity_types,
                "relation_types": relation_types
            }
        except Exception as e:
            self.logger.error(f"Failed to get statistics: {str(e)}")
            return {
                "total_entities": 0,
                "total_relations": 0,
                "entity_types": {},
                "relation_types": {}
            }
    
    async def get_relations_by_entity(
        self,
        entity_id: str,
        direction: str = "both"
    ) -> List[Relation]:
        """獲取實體的所有關係"""
        relations = []
        relation_ids = self.entity_relations.get(entity_id, [])
        
        for rel_id in relation_ids:
            relation = self.relations.get(rel_id)
            if not relation:
                continue
            
            if direction == "both":
                relations.append(relation)
            elif direction == "outgoing" and relation.source_id == entity_id:
                relations.append(relation)
            elif direction == "incoming" and relation.target_id == entity_id:
                relations.append(relation)
        
        return relations
    
    async def get_relations_by_type(
        self,
        relation_type: str,
        limit: int = 100
    ) -> List[Relation]:
        """按類型查詢關係"""
        relations = []
        for relation in self.relations.values():
            if relation.type == relation_type:
                relations.append(relation)
                if len(relations) >= limit:
                    break
        return relations

