"""
QA 向量索引（基於 sqlite 的簡易實作）
更新時間：2026-03-11 00:00
作者：AI Assistant
修改摘要：search() 新增 min_score 參數（預設 0.0），過濾低相似度結果，解決負向查詢誤報問題
更新時間：2026-03-10 11:35
作者：AI Assistant
修改摘要：sqlite3 連線改為 check_same_thread=False，修正 API 執行緒與建置執行緒共用連線時的 thread 錯誤
更新時間：2026-03-09 17:40
作者：AI Assistant
修改摘要：新增 QAEmbeddingIndex，儲存 QA Entity 的文字與 embedding，支援 cosine 相似度搜尋
"""
import json
import logging
import math
import os
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Tuple

logger = logging.getLogger("QAEmbeddingIndex")


class QAEmbeddingIndex:
    """
    QA 向量索引：
    - 使用 sqlite 檔案（預設 data/qa_vectors.db）
    - 儲存 entity_id, text, embedding(JSON), metadata(JSON)
    - 搜尋時讀入所有向量到記憶體，計算 cosine 相似度
    """

    def __init__(self, db_path: str = "data/qa_vectors.db") -> None:
        self.db_path = db_path
        self._conn: sqlite3.Connection | None = None
        self._loaded_cache: List[Tuple[str, List[float], Dict[str, Any]]] | None = None
        self._ensure_db()

    def _ensure_db(self) -> None:
        Path(os.path.dirname(self.db_path) or ".").mkdir(parents=True, exist_ok=True)
        # 在 API 環境中，QAEmbeddingIndex 可能在一個執行緒建立、在另一個執行緒（請求處理）中使用，
        # 因此關閉 sqlite 預設的同執行緒檢查，避免出現
        # "SQLite objects created in a thread can only be used in that same thread" 錯誤。
        self._conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS qa_vectors (
                entity_id TEXT PRIMARY KEY,
                text      TEXT NOT NULL,
                embedding TEXT NOT NULL,
                metadata  TEXT
            )
            """
        )
        self._conn.commit()

    def close(self) -> None:
        if self._conn is not None:
            self._conn.close()
            self._conn = None

    def upsert(self, entity_id: str, text: str, embedding: List[float], metadata: Dict[str, Any]) -> None:
        """新增或更新一筆 QA 向量紀錄。"""
        if self._conn is None:
            self._ensure_db()
        emb_json = json.dumps(embedding, ensure_ascii=False)
        meta_json = json.dumps(metadata or {}, ensure_ascii=False)
        self._conn.execute(
            """
            INSERT INTO qa_vectors (entity_id, text, embedding, metadata)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(entity_id) DO UPDATE SET
                text = excluded.text,
                embedding = excluded.embedding,
                metadata = excluded.metadata
            """,
            (entity_id, text, emb_json, meta_json),
        )
        self._conn.commit()
        # 資料變更時清除快取，讓下次搜尋重新載入
        self._loaded_cache = None

    def _load_all(self) -> List[Tuple[str, List[float], Dict[str, Any]]]:
        """從 DB 載入所有 QA 向量到記憶體。"""
        if self._loaded_cache is not None:
            return self._loaded_cache
        if self._conn is None:
            self._ensure_db()
        cur = self._conn.execute("SELECT entity_id, embedding, metadata FROM qa_vectors")
        rows = cur.fetchall()
        result: List[Tuple[str, List[float], Dict[str, Any]]] = []
        for entity_id, emb_json, meta_json in rows:
            try:
                emb = json.loads(emb_json)
                if not isinstance(emb, list):
                    continue
                meta = json.loads(meta_json) if meta_json else {}
                result.append((entity_id, emb, meta))
            except Exception:
                continue
        self._loaded_cache = result
        logger.info(f"QAEmbeddingIndex 載入 {len(result)} 筆向量")
        return result

    def search(
        self,
        query_emb: List[float],
        top_k: int = 5,
        min_score: float = 0.0,
    ) -> List[Tuple[str, float, Dict[str, Any]]]:
        """以 cosine 相似度搜尋最相近的 QA，回傳 (entity_id, score, metadata)。
        min_score：低於此門檻的結果不回傳（預設 0.0 不過濾；建議由呼叫端傳入 settings.QA_MIN_SCORE）。
        """
        if not query_emb:
            return []
        all_vectors = self._load_all()
        if not all_vectors:
            return []

        def cosine(a: List[float], b: List[float]) -> float:
            if not a or not b or len(a) != len(b):
                return 0.0
            dot = sum(x * y for x, y in zip(a, b))
            na = math.sqrt(sum(x * x for x in a))
            nb = math.sqrt(sum(y * y for y in b))
            if na == 0.0 or nb == 0.0:
                return 0.0
            return dot / (na * nb)

        threshold = max(0.0, min_score)
        scored: List[Tuple[str, float, Dict[str, Any]]] = []
        for entity_id, emb, meta in all_vectors:
            score = cosine(query_emb, emb)
            if score >= threshold:
                scored.append((entity_id, float(score), meta))

        if not scored:
            return []
        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[:top_k]

