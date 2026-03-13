"""
解析 IC 卡資料上傳欄位與錯誤對照表並建立問答知識圖譜子圖
從純文字規格檔 `IC卡資料上傳錯誤對照.txt` 提取欄位代碼與錯誤代碼，寫入共用的 graph_qa.db

更新時間：2026-03-06 17:45
作者：AI Assistant
修改摘要：預設改使用 data/Thisqa 版本的 IC 卡錯誤對照檔，並建議以固定 doc-id 搭配 overwrite 方式維護單一版本
更新時間：2026-03-06 15:23
作者：AI Assistant
修改摘要：建立 IC 卡欄位與錯誤代碼匯入腳本，將規格轉換為 graph_qa.db 中的 IC_Field / IC_Error 子圖
"""
import asyncio
import os
import re
import sys
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# 添加專案路徑
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.graph_store import SQLiteGraphStore, Entity, Relation


def parse_ic_spec_file(spec_path: str) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    解析 IC 卡資料上傳欄位與錯誤對照表

    Args:
        spec_path: 規格檔案路徑（純文字）

    Returns:
        (fields, errors)
        - fields: 欄位列表，每筆包含 field_id, name, section, description, raw_line
        - errors: 錯誤列表，每筆包含 code, message, category, related_field_ids, raw_line
    """
    spec_path_obj = Path(spec_path)
    if not spec_path_obj.exists():
        raise FileNotFoundError(f"IC 卡錯誤對照檔不存在: {spec_path}")

    with spec_path_obj.open("r", encoding="utf-8") as f:
        lines = [line.rstrip("\n") for line in f]

    fields: List[Dict[str, Any]] = []
    errors: List[Dict[str, Any]] = []

    # 區段判斷：遇到「錯誤代碼:中文對照註釋」後即進入錯誤區段
    in_error_section = False

    # 欄位區段：格式大致為 <M01>: 說明    <M02>: 說明 ...
    field_pattern = re.compile(r"<([A-Z]\d{2})>:\s*([^<]+?)(?=(?:<[A-Z]\d{2}>:|$))")

    # 錯誤代碼區段：格式大致為 [01  ]: 說明 或 [AD69]: 說明
    error_pattern = re.compile(r"^\[([^\]]+)\]:\s*(.+)$")

    # 欄位代碼偵測，用於從錯誤說明中找出相關欄位
    field_ref_pattern = re.compile(r"\b([MDHEV]\d{2})\b")

    for raw_line in lines:
        line = raw_line.strip()
        if not line:
            continue

        if line.startswith("錯誤代碼"):
            in_error_section = True
            continue

        if not in_error_section:
            # 欄位區段解析
            for match in field_pattern.finditer(raw_line):
                field_id = match.group(1).strip()
                desc = match.group(2).strip()
                if not field_id or not desc:
                    continue

                section = field_id[0]
                fields.append(
                    {
                        "field_id": field_id,
                        "name": desc,
                        "section": section,
                        "description": desc,
                        "raw_line": raw_line,
                    }
                )
        else:
            # 錯誤代碼區段解析
            m = error_pattern.match(line)
            if not m:
                continue

            code_raw = m.group(1).strip()
            message = m.group(2).strip()
            if not code_raw or not message:
                continue

            # 分類：簡單用首字母或數字前綴分群
            category = code_raw[0]

            # 從說明文字中找出相關欄位代碼
            related_field_ids = sorted(set(field_ref_pattern.findall(message)))

            errors.append(
                {
                    "code": code_raw,
                    "message": message,
                    "category": category,
                    "related_field_ids": related_field_ids,
                    "raw_line": raw_line,
                }
            )

    return fields, errors


async def import_ic_spec_to_graph(
    spec_path: str,
    document_id: Optional[str] = None,
    db_path: str = "./data/graph_qa.db",
    overwrite_doc: bool = False,
) -> None:
    """
    將 IC 卡欄位與錯誤對照表匯入共用的 graph_qa.db

    Args:
        spec_path: 規格檔案路徑
        document_id: 自訂文件 ID（預設自動產生）
        db_path: 圖資料庫路徑
        overwrite_doc: 是否先刪除同一 Document.id 底下既有資料後重建
    """
    graph_store: Optional[SQLiteGraphStore] = None
    try:
        print("=" * 60)
        print("IC 卡欄位與錯誤對照表匯入 graph_qa.db")
        print("=" * 60)

        print(f"\n[步驟 1/4] 解析規格檔案...")
        print(f"檔案路徑: {spec_path}")

        fields, errors = parse_ic_spec_file(spec_path)
        print(f"解析完成，欄位數量：{len(fields)}，錯誤代碼數量：{len(errors)}")

        print(f"\n[步驟 2/4] 初始化圖資料庫...")
        print(f"資料庫路徑: {db_path}")

        db_dir = os.path.dirname(db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir)
            print(f"建立資料目錄: {db_dir}")

        graph_store = SQLiteGraphStore(db_path)
        await graph_store.initialize()
        print("圖資料庫初始化完成")

        # 生成或確認 Document ID
        if document_id is None:
            name = Path(spec_path).stem
            document_id = f"ic_error_spec_{name}_{str(uuid.uuid4())[:8]}"

        print(f"\n[步驟 3/4] 準備 Document 實體，ID: {document_id}")

        if overwrite_doc:
            print("啟用 overwrite_doc，嘗試清理同一 Document 既有資料...")
            existing_doc = await graph_store.get_entity(document_id)
            if existing_doc:
                # 找出所有鄰居實體並刪除 IC_Field / IC_Error 子節點
                from app.core.graph_store import Entity as GraphEntity  # type: ignore

                neighbors = await graph_store.get_neighbors(document_id, direction="outgoing")
                for neighbor in neighbors:
                    if neighbor.type in {"IC_Field", "IC_Error"}:
                        await graph_store.delete_entity(neighbor.id)
                # 最後刪掉舊的 Document
                await graph_store.delete_entity(document_id)
                print("已刪除舊的 Document 與相關 IC_Field / IC_Error")

        # 建立新的 Document 實體
        doc_entity = Entity(
            id=document_id,
            type="Document",
            name=Path(spec_path).name,
            properties={
                "source": str(Path(spec_path)),
                "type": "ic_error_spec",
                "field_count": len(fields),
                "error_count": len(errors),
            },
            created_at=None,
        )
        await graph_store.add_entity(doc_entity)
        print("建立 Document 實體完成")

        print(f"\n[步驟 4/4] 建立欄位與錯誤實體及關係...")

        # 先建立欄位實體，方便之後錯誤與欄位連線
        field_id_to_entity_id: Dict[str, str] = {}
        field_count = 0
        for field in fields:
            field_entity_id = f"{document_id}_field_{field['field_id']}"
            field_id_to_entity_id[field["field_id"]] = field_entity_id

            field_entity = Entity(
                id=field_entity_id,
                type="IC_Field",
                name=field["name"][:100],
                properties={
                    "field_id": field["field_id"],
                    "section": field["section"],
                    "description": field["description"],
                    "raw_line": field["raw_line"],
                    "source": "ic_error_spec",
                },
                created_at=None,
            )

            if await graph_store.add_entity(field_entity):
                field_count += 1
                relation = Relation(
                    id=f"{document_id}_contains_field_{field['field_id']}",
                    source_id=document_id,
                    target_id=field_entity_id,
                    type="CONTAINS_FIELD",
                    properties={"field_id": field["field_id"]},
                    weight=1.0,
                    created_at=None,
                )
                await graph_store.add_relation(relation)

        print(f"建立 {field_count} 個 IC_Field 實體與 CONTAINS_FIELD 關係")

        # 再建立錯誤實體與 ERROR_ON_FIELD 關係
        error_count = 0
        relation_count = 0
        for error in errors:
            error_entity_id = f"{document_id}_error_{error['code']}"

            error_entity = Entity(
                id=error_entity_id,
                type="IC_Error",
                name=error["message"][:100],
                properties={
                    "code": error["code"],
                    "message": error["message"],
                    "category": error["category"],
                    "related_field_ids": error["related_field_ids"],
                    "raw_line": error["raw_line"],
                    "source": "ic_error_spec",
                },
                created_at=None,
            )

            if await graph_store.add_entity(error_entity):
                error_count += 1

                contains_error_rel = Relation(
                    id=f"{document_id}_contains_error_{error['code']}",
                    source_id=document_id,
                    target_id=error_entity_id,
                    type="CONTAINS_ERROR",
                    properties={"code": error["code"]},
                    weight=1.0,
                    created_at=None,
                )
                await graph_store.add_relation(contains_error_rel)
                relation_count += 1

                # 建立錯誤到欄位的關係
                for field_id in error["related_field_ids"]:
                    field_entity_id = field_id_to_entity_id.get(field_id)
                    if not field_entity_id:
                        continue
                    rel = Relation(
                        id=f"{error_entity_id}_on_{field_entity_id}",
                        source_id=error_entity_id,
                        target_id=field_entity_id,
                        type="ERROR_ON_FIELD",
                        properties={"field_id": field_id},
                        weight=1.0,
                        created_at=None,
                    )
                    if await graph_store.add_relation(rel):
                        relation_count += 1

        print(f"建立 {error_count} 個 IC_Error 實體與 {relation_count} 筆關係")

        print("\n" + "=" * 60)
        print("IC 卡欄位與錯誤對照表匯入完成")
        print("=" * 60)
        print(f"\nDocument ID: {document_id}")
        print(f"欄位實體數量: {field_count}")
        print(f"錯誤實體數量: {error_count}")
        print(f"資料庫路徑: {db_path}")
        print("\n可以使用以下命令檢視圖結構：")
        print("  python scripts/query_qa_graph.py")

    except KeyboardInterrupt:
        print("\n處理被用戶中斷（Ctrl+C）")
    except Exception as e:
        print(f"\n匯入失敗: {str(e)}")
        import traceback

        traceback.print_exc()
    finally:
        if graph_store:
            try:
                await graph_store.close()
                print("資源清理完成")
            except Exception as e:
                print(f"清理資源時發生錯誤: {str(e)}")


async def main() -> None:
    """主函數"""
    import argparse

    parser = argparse.ArgumentParser(
        description="解析 IC 卡資料上傳欄位與錯誤對照表並匯入 graph_qa.db"
    )
    parser.add_argument(
        "--spec-file",
        type=str,
        default="data/Thisqa/IC卡資料上傳錯誤對照.txt",
        help="IC 卡欄位與錯誤對照表路徑（預設: data/Thisqa/IC卡資料上傳錯誤對照.txt，可改為 data/hisqa/... 等其他來源）",
    )
    parser.add_argument(
        "--db-path",
        type=str,
        default="./data/graph_qa.db",
        help="圖資料庫路徑（預設: ./data/graph_qa.db）",
    )
    parser.add_argument(
        "--doc-id",
        type=str,
        default=None,
        help="自訂 Document ID（未指定則自動產生）",
    )
    parser.add_argument(
        "--overwrite-doc",
        action="store_true",
        help="若指定則先刪除同一 Document ID 下既有 IC_Field / IC_Error 再重建",
    )

    args = parser.parse_args()

    spec_path_obj = Path(args.spec_file)
    if not spec_path_obj.is_absolute():
        # 以專案根目錄為參考點
        script_root = Path(__file__).parent.parent
        spec_path_obj = (script_root / args.spec_file).resolve()

    await import_ic_spec_to_graph(
        spec_path=str(spec_path_obj),
        document_id=args.doc_id,
        db_path=args.db_path,
        overwrite_doc=args.overwrite_doc,
    )


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n程式被用戶中斷（Ctrl+C）")
        print("正在退出...")
        sys.exit(0)

