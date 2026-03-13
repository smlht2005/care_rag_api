"""
批次匯入 Thisqa Markdown QA 檔案至 graph_qa.db
使用既有的結構化 Q&A 解析流程，將 data/Thisqa 下的操作指引 Markdown 匯入 QA 圖資料庫

更新時間：2026-03-06 17:45
作者：AI Assistant
修改摘要：新增批次匯入腳本，重用 parse_qa_markdown_to_graph 將 Thisqa 的 Q&A 模板寫入 graph_qa.db
"""
import asyncio
import os
import sys
from pathlib import Path
from typing import List

# 添加專案路徑
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.parse_qa_markdown_to_graph import process_qa_markdown_to_graph


async def import_thisqa_markdown_batch(
    qa_dir: str = "data/Thisqa",
    db_path: str = "./data/graph_qa.db",
    doc_id_prefix: str = "",
) -> None:
    """
    將指定目錄下的 Thisqa Markdown QA 檔案批次匯入 graph_qa.db

    Args:
        qa_dir: 存放 Thisqa Markdown 的目錄（預設 data/Thisqa）
        db_path: QA 圖資料庫路徑（預設 ./data/graph_qa.db）
        doc_id_prefix: 可選的 Document ID 前綴（用於穩定命名）
    """
    qa_dir_path = Path(qa_dir)
    if not qa_dir_path.exists():
        raise FileNotFoundError(f"指定的 QA 目錄不存在: {qa_dir}")

    # 僅處理 .md 檔案（IC 卡錯誤對照是 .txt，會由專用腳本處理）
    md_files: List[Path] = sorted(qa_dir_path.glob("*.md"))

    if not md_files:
        print(f"在目錄中找不到任何 Markdown 檔案: {qa_dir}")
        return

    print("=" * 60)
    print("Thisqa Markdown QA 批次匯入開始")
    print("=" * 60)
    print(f"來源目錄: {qa_dir_path.resolve()}")
    print(f"目標資料庫: {Path(db_path).resolve()}")
    print(f"偵測到 Markdown 檔案數量: {len(md_files)}")

    # 逐檔匯入
    for index, md_file in enumerate(md_files, start=1):
        md_path = str(md_file.resolve())
        print("\n" + "-" * 60)
        print(f"處理檔案 {index}/{len(md_files)}: {md_file.name}")
        print(f"完整路徑: {md_path}")

        # 可選的 Document ID（若提供前綴則固定命名，否則沿用原腳本自動產生）
        document_id = None
        if doc_id_prefix:
            stem = md_file.stem
            document_id = f"{doc_id_prefix}{stem}"

        await process_qa_markdown_to_graph(
            md_path=md_path,
            document_id=document_id,
            db_path=db_path,
        )

    print("\n" + "=" * 60)
    print("Thisqa Markdown QA 批次匯入完成")
    print("=" * 60)
    print(f"總共匯入檔案數量: {len(md_files)}")
    print(f"資料庫路徑: {Path(db_path).resolve()}")


async def main() -> None:
    """主函數"""
    import argparse

    parser = argparse.ArgumentParser(
        description="批次匯入 data/Thisqa 下的 Markdown QA 檔案到 graph_qa.db"
    )
    parser.add_argument(
        "--qa-dir",
        type=str,
        default="data/Thisqa",
        help="Thisqa Markdown QA 檔案目錄（預設: data/Thisqa）",
    )
    parser.add_argument(
        "--db-path",
        type=str,
        default="./data/graph_qa.db",
        help="QA 圖資料庫路徑（預設: ./data/graph_qa.db）",
    )
    parser.add_argument(
        "--doc-id-prefix",
        type=str,
        default="",
        help="可選的 Document ID 前綴（例如 thisqa_，預設為空）",
    )

    args = parser.parse_args()

    await import_thisqa_markdown_batch(
        qa_dir=args.qa_dir,
        db_path=args.db_path,
        doc_id_prefix=args.doc_id_prefix,
    )


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n程式被用戶中斷（Ctrl+C），正在退出...")
        sys.exit(0)

