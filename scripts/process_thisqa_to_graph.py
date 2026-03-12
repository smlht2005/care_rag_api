"""
從 Thisqa 來源檔（.md / .txt）建圖並寫入 graph.db、向量庫
供主線 GraphRAG（/api/v1/query）使用；與 graph_qa.db / QA 搜尋端點獨立。

更新時間：2026-03-11 10:05
作者：AI Assistant
修改摘要：[Fix 4] extract_ic_field_qa_from_txt keywords 補齊 [code] 格式與「資料」關鍵字，改善 [D12] 等欄位代碼查詢命中率
更新時間：2026-03-11 09:13
作者：AI Assistant
修改摘要：[Fix A] 新增 _reset_qa_vectors_db()，--reset 時同步清空 qa_vectors.db，確保向量庫與 graph.db 一致
更新時間：2026-03-10 16:54
作者：AI Assistant
修改摘要：[Fix #1] StubEmbeddingService 加入 dim=VECTOR_DIMENSION 確保 fallback 向量維度與 Gemini 一致；[Fix #2] qa_index 初始化為 None 並在 finally 區塊呼叫 close() 釋放 SQLite 連線
更新時間：2026-03-09 20:35
作者：AI Assistant
修改摘要：新增 --file 參數，可僅處理指定檔名（例如 IC 卡對照檔）
更新時間：2026-03-09 18:30
作者：AI Assistant
修改摘要：Gemini embed 失敗或回傳空時改為使用 StubEmbeddingService 寫入 QA 索引，確保建圖流程可完成
更新時間：2026-03-09 15:22
作者：AI Assistant
修改摘要：從 Thisqa .md 解析 QA block，建立 type=\"QA\" 的 Entity（含 question/answer/keywords/document_id），供 QA 向量索引與 GraphRAG 使用
更新時間：2026-03-06
作者：AI Assistant
修改摘要：Phase 2 實作；依句/段邊界切塊、build_graph_from_text、--reset 支援
"""
import asyncio
import re
import sys
import os
from pathlib import Path
from typing import List, Optional, Tuple

# 專案根目錄
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config import settings
from app.core.graph_store import SQLiteGraphStore, Entity
from app.core.entity_extractor import EntityExtractor
from app.services.graph_builder import GraphBuilder
from app.services.llm_service import LLMService
from app.services.vector_service import VectorService
from app.services.embedding_service import get_default_embedding_service, StubEmbeddingService
from app.services.qa_embedding_index import QAEmbeddingIndex


# 預設 4 檔：3 個 .md + 1 個 .txt（相對專案根）
DEFAULT_THISQA_DIR = Path("data/Thisqa")
DEFAULT_FILES = [
    ("衛生所門診批價管理系統操作指引.md", "doc_thisqa_billing"),
    ("衛生所病歷與掛號系統操作指南.md", "doc_thisqa_registration"),
    ("衛生所醫令系統操作指南與常見問題彙編.md", "doc_thisqa_orders"),
    ("IC卡資料上傳錯誤對照.txt", "doc_thisqa_ic_error"),
]
ENTITY_TYPES = ["Person", "Organization", "Location", "Concept", "Document", "Policy"]
MAX_CHUNK_CHARS = 4000
FALLBACK_CHUNK_SIZE = 2000
FALLBACK_OVERLAP = 200


def read_utf8(path: Path) -> str:
    """讀取 UTF-8 全文，輕量過濾 BOM 與多餘空白。"""
    raw = path.read_text(encoding="utf-8")
    if raw.startswith("\ufeff"):
        raw = raw[1:]
    return raw.strip()


def extract_qa_blocks_from_markdown(text: str) -> List[dict]:
    """
    從 Thisqa markdown 中解析 QA 區塊：
    - 以 '## Q:' 分段
    - 抽取 question / answer / keywords
    """
    if not text.strip():
        return []

    parts = re.split(r"\n(?=## Q:)", text)
    blocks: List[dict] = []

    for p in parts:
        p = p.strip()
        if not p.startswith("## Q:"):
            continue

        lines = p.split("\n")
        header = lines[0].strip()
        question = header.replace("## Q:", "", 1).strip()

        answer_lines: List[str] = []
        keywords: List[str] = []
        in_answer = False

        for line in lines[1:]:
            stripped = line.strip()
            if not stripped:
                # 空行保留在 answer 內文中，維持段落結構
                if in_answer:
                    answer_lines.append(line)
                continue

            # 關鍵字行：**關鍵字 (Keywords)**：搜尋, 讀取健保卡, ...
            if stripped.startswith("**關鍵字"):
                # 取出「：」後的文字作為關鍵字來源
                sep = "："
                idx = stripped.find(sep)
                if idx == -1:
                    idx = stripped.find(":")
                kw_text = stripped[idx + 1 :].strip() if idx != -1 else stripped
                for token in re.split(r"[、,，；; ]+", kw_text):
                    token = token.strip()
                    if token:
                        keywords.append(token)
                continue

            # Answer 起始行：**Answer**：...
            if stripped.startswith("**Answer**"):
                # 取得冒號後的第一行回答內容
                sep = "："
                idx = stripped.find(sep)
                if idx == -1:
                    idx = stripped.find(":")
                first_answer = stripped[idx + 1 :].strip() if idx != -1 else ""
                in_answer = True
                if first_answer:
                    answer_lines.append(first_answer)
                continue

            if in_answer:
                # Answer 內文（包含後續步驟與說明）
                answer_lines.append(line)

        answer = "\n".join(answer_lines).strip()
        if not question and not answer:
            continue

        blocks.append(
            {
                "question": question,
                "answer": answer,
                "keywords": keywords,
            }
        )

    return blocks


def extract_ic_error_qa_from_txt(text: str) -> List[dict]:
    """
    從 IC 卡錯誤對照 .txt 中解析「錯誤代碼 → 中文說明」為 QA 區塊。
    範例：
    錯誤代碼:中文對照註釋

    [01  ]: 資料型態檢核錯誤
    """
    if not text.strip():
        return []

    lines = text.split("\n")
    blocks: List[dict] = []
    # 錯誤碼區塊通常出現在「欄位與中文對照表」之後，標題為「錯誤代碼:中文對照註釋」
    in_section = False
    for raw in lines:
        line = raw.strip()
        if not line:
            continue
        if not in_section:
            if "錯誤代碼" in line and "註釋" in line:
                in_section = True
            continue

        # 解析 [CODE]: 說明
        m = re.match(r"^\[(?P<code>[^\]]+)\]\s*:\s*(?P<desc>.+)$", line)
        if not m:
            continue
        raw_code = m.group("code").strip()
        # 正規化錯誤代碼：去除多餘空白並轉成大寫，保留英數內容（例如 01, C001, AA01）
        code = re.sub(r"\s+", "", raw_code).upper()
        desc = m.group("desc").strip()
        if not code or not desc:
            continue

        question = f"IC 卡資料上傳錯誤代碼 [{code}] 代表什麼？"
        blocks.append(
            {
                "code": code,
                "question": question,
                "answer": desc,
                "keywords": [code, f"[{code}]", "IC 卡", "錯誤代碼"],
            }
        )

    return blocks


def extract_ic_field_qa_from_txt(text: str) -> List[dict]:
    """
    從 IC 卡錯誤對照 .txt 開頭的「欄位與中文對照表」區塊解析欄位代碼 QA：
    例如：

    欄位與中文對照表

    <M01>: 安全模組代碼
    <M02>: 卡片號碼            <M03>: 身分證號或身分證明文<M04>: 出生日期

    解析出每個 <CODE>: 說明 為一筆 QA：
    - code: M01
    - question: IC 卡欄位 M01 代表什麼？
    - answer: 安全模組代碼
    """
    if not text.strip():
        return []

    lines = text.split("\n")
    blocks: List[dict] = []
    in_section = False
    for raw in lines:
        line = raw.strip()
        if not line:
            continue
        if not in_section:
            # 起始標題行
            if "欄位與中文對照表" in line:
                in_section = True
            continue
        # 欄位對照表與錯誤代碼區塊之間通常有「錯誤代碼:中文對照註釋」標題
        if "錯誤代碼" in line and "註釋" in line:
            break

        # 一行可能有多個 <CODE>: 說明，逐一解析
        for m in re.finditer(r"<(?P<code>[^>]+)>\s*:\s*(?P<desc>[^<]+)", line):
            raw_code = m.group("code").strip()
            code = re.sub(r"\s+", "", raw_code).upper()
            desc = m.group("desc").strip()
            if not code or not desc:
                continue
            question = f"IC 卡欄位 {code} 代表什麼？"
            blocks.append(
                {
                    "code": code,
                    "question": question,
                    "answer": desc,
                    "keywords": [code, f"<{code}>", f"[{code}]", "IC 卡", "欄位", "欄位對照", "資料"],
                }
            )

    return blocks


def chunk_markdown_by_qa_and_paragraph(text: str, max_chars: int = MAX_CHUNK_CHARS) -> List[str]:
    """
    依 .md 結構切塊：先依 ## Q: 或 \\n\\n 分段；單段過大再依 \\n\\n 切小。
    """
    if not text.strip():
        return []
    # 依 ## Q: 切出 QA 區塊（保留標題在塊內）
    parts = re.split(r"\n(?=## Q:)", text)
    chunks: List[str] = []
    for p in parts:
        p = p.strip()
        if not p:
            continue
        if len(p) <= max_chars:
            chunks.append(p)
            continue
        # 單塊過大：依雙換行再切
        sub_parts = re.split(r"\n\s*\n", p)
        buf = ""
        for sp in sub_parts:
            if len(buf) + len(sp) + 2 > max_chars and buf:
                chunks.append(buf.strip())
                buf = ""
            buf = f"{buf}\n\n{sp}" if buf else sp
        if buf.strip():
            chunks.append(buf.strip())
    return chunks


def chunk_txt_by_paragraph_or_lines(
    text: str,
    max_chars: int = MAX_CHUNK_CHARS,
    max_lines: int = 80,
) -> List[str]:
    """
    .txt：先依雙換行分段；單段過大則依固定行數再切。
    """
    if not text.strip():
        return []
    parts = re.split(r"\n\s*\n", text)
    chunks: List[str] = []
    buf_lines: List[str] = []
    buf_len = 0

    def flush():
        nonlocal buf_lines, buf_len
        if buf_lines:
            chunks.append("\n".join(buf_lines))
            buf_lines = []
            buf_len = 0

    for p in parts:
        lines = p.split("\n")
        for line in lines:
            buf_lines.append(line)
            buf_len += len(line) + 1
            if len(buf_lines) >= max_lines or buf_len >= max_chars:
                flush()
        if buf_len >= max_chars:
            flush()
    flush()
    return chunks


def chunk_text(path: Path, text: str) -> List[str]:
    """依副檔名選擇切塊策略；無結構時 fallback 固定字數 + overlap。"""
    suffix = path.suffix.lower()
    if suffix == ".md":
        chunks = chunk_markdown_by_qa_and_paragraph(text, MAX_CHUNK_CHARS)
    elif suffix == ".txt":
        chunks = chunk_txt_by_paragraph_or_lines(text, MAX_CHUNK_CHARS, max_lines=80)
    else:
        chunks = chunk_markdown_by_qa_and_paragraph(text, MAX_CHUNK_CHARS)

    if not chunks:
        # fallback: 固定字數 + overlap
        chunks = []
        for i in range(0, len(text), FALLBACK_CHUNK_SIZE - FALLBACK_OVERLAP):
            chunk = text[i : i + FALLBACK_CHUNK_SIZE]
            if chunk.strip():
                chunks.append(chunk)
    return chunks


def _reset_qa_vectors_db(db_path: Path) -> None:
    """清空 qa_vectors.db，確保 --reset 時向量庫與 graph.db 同步乾淨。"""
    import sqlite3
    if db_path.exists():
        conn = sqlite3.connect(str(db_path))
        conn.execute("DELETE FROM qa_vectors")
        conn.commit()
        conn.close()
        print(f"[OK] qa_vectors.db 已清空: {db_path}")
    else:
        print(f"[OK] qa_vectors.db 不存在，略過清空: {db_path}")


async def run_reset_graph_db() -> bool:
    """執行 reset_graph_db；若檔案被其他程序鎖定，改用直接清表的 fallback。"""
    import importlib.util
    import sqlite3
    reset_path = Path(__file__).resolve().parent / "reset_graph_db.py"
    spec = importlib.util.spec_from_file_location("reset_graph_db", str(reset_path))
    if spec is None or spec.loader is None:
        print("[X] 無法載入 reset_graph_db 模組")
        return False
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    ok = await mod.reset_graph_db()
    if ok:
        return True
    # Fallback：檔案被鎖定時改用 DELETE FROM 直接清空表格
    db_path = Path(settings.GRAPH_DB_PATH)
    if not db_path.exists():
        print("[WARN] graph.db 不存在，略過 fallback 清表")
        return False
    print("[WARN] reset_graph_db 失敗（可能被其他程序鎖定），改用直接清表 fallback...")
    try:
        conn = sqlite3.connect(str(db_path))
        conn.execute("DELETE FROM relations")
        conn.execute("DELETE FROM entities")
        conn.commit()
        conn.close()
        print("[OK] graph.db 資料已清空（DELETE FROM fallback）")
        return True
    except Exception as e:
        print(f"[X] fallback 清表失敗: {e}")
        return False


async def process_thisqa_to_graph(
    files_dir: Path,
    file_doc_id_pairs: List[Tuple[str, str]],
    reset: bool = False,
) -> None:
    """
    讀取指定 Thisqa 檔，依句/段邊界切塊，每塊 build_graph_from_text 寫入 graph.db，
    每檔處理完 add_documents 到向量庫。
    """
    graph_store = None
    qa_index = None
    try:
        print("=" * 60)
        print("Thisqa 建圖（graph.db + 向量庫）")
        print("=" * 60)

        if reset:
            print("\n[步驟 0] --reset：重置 graph.db...")
            ok = await run_reset_graph_db()
            if not ok:
                print("[X] reset 失敗，中止")
                return
            _reset_qa_vectors_db(Path(settings.GRAPH_DB_PATH).parent / "qa_vectors.db")
            print("[OK] reset 完成\n")

        print("[步驟 1] 初始化服務...")
        graph_store = SQLiteGraphStore(settings.GRAPH_DB_PATH)
        await graph_store.initialize()
        llm_service = LLMService()
        entity_extractor = EntityExtractor(llm_service)
        graph_builder = GraphBuilder(graph_store, entity_extractor)
        vector_service = VectorService(graph_store=graph_store)
        embedding_service = get_default_embedding_service()
        qa_index = QAEmbeddingIndex("data/qa_vectors.db")
        print("[OK] 服務初始化完成\n")

        for filename, document_id in file_doc_id_pairs:
            path = files_dir / filename
            if not path.exists():
                print(f"[WARN] 略過不存在的檔案: {path}")
                continue

            print(f"[步驟] 處理: {filename} (document_id={document_id})")
            try:
                full_text = read_utf8(path)
            except Exception as e:
                print(f"  [X] 讀取失敗: {e}")
                continue

            # 先從 markdown / IC txt 解析 QA 區塊，建立 QA / QA1 Entity 並寫入 QA 向量索引
            qa_blocks: List[dict] = []
            qa_ids: List[str] = []
            qa_texts: List[str] = []
            qa_metas: List[dict] = []

            if path.suffix.lower() == ".md":
                qa_blocks = extract_qa_blocks_from_markdown(full_text)
                if qa_blocks:
                    print(f"  QA 區塊數: {len(qa_blocks)}")
                    for idx, qa in enumerate(qa_blocks, 1):
                        qa_id = f"{document_id}_qa_{idx}"
                        question = qa.get("question") or qa_id
                        properties = {
                            "question": qa.get("question", ""),
                            "answer": qa.get("answer", ""),
                            "keywords": qa.get("keywords", []),
                            "document_id": document_id,
                            "source_file": path.name,
                        }
                        qa_entity = Entity(
                            id=qa_id,
                            type="QA",
                            name=question,
                            properties=properties,
                            created_at=None,
                        )
                        await graph_store.add_entity(qa_entity)

                        # 準備 embedding 用文字與 metadata
                        text_for_emb = (
                            (properties["question"] or "")
                            + "\n"
                            + (properties["answer"] or "")
                            + "\n"
                            + ",".join(properties["keywords"] or [])
                        )
                        qa_ids.append(qa_id)
                        qa_texts.append(text_for_emb)
                        qa_metas.append(
                            {
                                "document_id": document_id,
                                "source_file": path.name,
                            }
                        )

            elif path.name == "IC卡資料上傳錯誤對照.txt":
                field_blocks = extract_ic_field_qa_from_txt(full_text)
                error_blocks = extract_ic_error_qa_from_txt(full_text)
                if field_blocks:
                    print(f"  IC 欄位 QA 區塊數: {len(field_blocks)}")
                if error_blocks:
                    print(f"  IC 錯誤碼 QA 區塊數: {len(error_blocks)}")
                qa_blocks = field_blocks + error_blocks

                for qa in field_blocks:
                    code = qa.get("code") or ""
                    if not code:
                        continue
                    qa_id = f"doc_thisqa_ic_field_{code}"
                    question = qa.get("question") or qa_id
                    properties = {
                        "code": code,
                        "question": qa.get("question", ""),
                        "answer": qa.get("answer", ""),
                        "keywords": qa.get("keywords", []),
                        "document_id": document_id,
                        "source_file": path.name,
                    }
                    qa_entity = Entity(
                        id=qa_id,
                        type="QA1",
                        name=question,
                        properties=properties,
                        created_at=None,
                    )
                    await graph_store.add_entity(qa_entity)

                    text_for_emb = (
                        (properties["question"] or "")
                        + "\n"
                        + (properties["answer"] or "")
                        + "\n"
                        + ",".join(properties["keywords"] or [])
                    )
                    qa_ids.append(qa_id)
                    qa_texts.append(text_for_emb)
                    qa_metas.append(
                        {
                            "document_id": document_id,
                            "source_file": path.name,
                        }
                    )

                for qa in error_blocks:
                    code = qa.get("code") or ""
                    if not code:
                        continue
                    qa_id = f"{settings.GRAPH_IC_ERROR_QA_ENTITY_ID_PREFIX}{code}"
                    question = qa.get("question") or qa_id
                    properties = {
                        "code": code,
                        "question": qa.get("question", ""),
                        "answer": qa.get("answer", ""),
                        "keywords": qa.get("keywords", []),
                        "document_id": document_id,
                        "source_file": path.name,
                    }
                    qa_entity = Entity(
                        id=qa_id,
                        type="QA1",
                        name=question,
                        properties=properties,
                        created_at=None,
                    )
                    await graph_store.add_entity(qa_entity)

                    text_for_emb = (
                        (properties["question"] or "")
                        + "\n"
                        + (properties["answer"] or "")
                        + "\n"
                        + ",".join(properties["keywords"] or [])
                    )
                    qa_ids.append(qa_id)
                    qa_texts.append(text_for_emb)
                    qa_metas.append(
                        {
                            "document_id": document_id,
                            "source_file": path.name,
                        }
                    )

            # 批次計算 QA / QA1 embedding 並寫入 qa_vectors 索引（不論來源於 .md 或 IC .txt）
            if qa_blocks and qa_texts:
                try:
                    embeddings = await embedding_service.embed(qa_texts)
                except Exception as e:
                    print(f"  [WARN] QA embedding 計算失敗，降級為 Stub 向量: {e}")
                    embeddings = []
                if not embeddings or len(embeddings) != len(qa_ids):
                    print("  [WARN] Gemini 未回傳或長度不符，改用 Stub 向量寫入 QA 索引")
                    stub = StubEmbeddingService(dim=getattr(settings, "VECTOR_DIMENSION", 768))
                    embeddings = await stub.embed(qa_texts)
                if embeddings and len(embeddings) == len(qa_ids):
                    for eid, text_for_emb, emb, meta in zip(qa_ids, qa_texts, embeddings, qa_metas):
                        try:
                            qa_index.upsert(eid, text_for_emb, emb, meta)
                        except Exception as e:
                            print(f"  [WARN] QA 向量索引寫入失敗 (entity_id={eid}): {e}")

            chunks = chunk_text(path, full_text)
            print(f"  切塊數: {len(chunks)}")

            total_entities = 0
            total_relations = 0
            for i, chunk in enumerate(chunks):
                chunk_id = f"{document_id}_chunk_{i + 1}"
                print(f"  [chunk {i + 1}/{len(chunks)}] build_graph_from_text: {chunk_id}, length={len(chunk)}")
                try:
                    result = await graph_builder.build_graph_from_text(
                        chunk,
                        chunk_id,
                        entity_types=ENTITY_TYPES,
                    )
                    total_entities += result.get("entities_count", 0)
                    total_relations += result.get("relations_count", 0)
                except Exception as e:
                    print(f"  [WARN] 區塊 {i + 1} 失敗: {e}")
                    continue

            # 主 Document 實體（與 process_pdf_to_graph 一致）
            main_doc = Entity(
                id=document_id,
                type="Document",
                name=path.name,
                properties={
                    "source": str(path.resolve()),
                    "chunks": len(chunks),
                    "total_length": len(full_text),
                },
                created_at=None,
            )
            await graph_store.add_entity(main_doc)

            # 向量：每檔處理完 add_documents（摘要）
            try:
                await vector_service.add_documents([
                    {
                        "id": document_id,
                        "content": full_text[:5000],
                        "metadata": {"source": path.name, "type": "thisqa", "length": len(full_text)},
                        "source": path.name,
                    }
                ])
            except Exception as e:
                print(f"  [WARN] 向量寫入失敗: {e}")

            print(f"  [OK] 完成: 實體 {total_entities}, 關係 {total_relations}\n")

    except KeyboardInterrupt:
        print("\n[WARN] 用戶中斷（Ctrl+C）")
    finally:
        if graph_store:
            try:
                await graph_store.close()
            except Exception:
                pass
        if qa_index:
            try:
                qa_index.close()
            except Exception:
                pass

    print("=" * 60)
    print("處理結束")
    print("=" * 60)


def main() -> None:
    import argparse
    parser = argparse.ArgumentParser(
        description="從 Thisqa 檔建 graph.db 與向量庫（Phase 2）",
    )
    parser.add_argument(
        "--dir",
        type=str,
        default=str(DEFAULT_THISQA_DIR),
        help=f"來源目錄（預設: {DEFAULT_THISQA_DIR}）",
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help="先執行 reset_graph_db 再建圖",
    )
    parser.add_argument(
        "--file",
        type=str,
        default=None,
        metavar="FILENAME",
        help="僅處理指定檔名（例如: IC卡資料上傳錯誤對照.txt）；不指定則處理全部預設檔",
    )
    args = parser.parse_args()
    files_dir = Path(args.dir)
    if not files_dir.is_absolute():
        root = Path(__file__).resolve().parent.parent
        files_dir = root / files_dir

    file_doc_id_pairs = DEFAULT_FILES
    if args.file:
        file_doc_id_pairs = [p for p in DEFAULT_FILES if p[0] == args.file]
        if not file_doc_id_pairs:
            print(f"[ERROR] 找不到指定檔名: {args.file!r}")
            print("可用檔名:", [p[0] for p in DEFAULT_FILES])
            sys.exit(1)

    asyncio.run(
        process_thisqa_to_graph(
            files_dir=files_dir,
            file_doc_id_pairs=file_doc_id_pairs,
            reset=args.reset,
        )
    )


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[WARN] 程式被用戶中斷（Ctrl+C）")
        sys.exit(0)
