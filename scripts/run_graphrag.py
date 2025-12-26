#!/usr/bin/env python3
"""
運行完整的 GraphRAG 處理腳本
"""
import sys
import os
import asyncio

# 添加專案路徑
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.process_pdf_to_graph import process_pdf_to_graph

async def main():
    """主函數"""
    pdf_path = "data/example/1051219長期照護2.0核定本.pdf"
    
    print("=" * 70)
    print("開始處理 PDF 並創建完整的 GraphRAG")
    print("=" * 70)
    print(f"\nPDF 文件: {pdf_path}")
    print("這將執行以下步驟：")
    print("1. 提取 PDF 文字")
    print("2. 初始化服務（GraphStore, LLMService, EntityExtractor, GraphBuilder, VectorService）")
    print("3. 生成文件 ID")
    print("4. 處理文件內容（提取實體和關係）")
    print("5. 新增到向量資料庫")
    print("\n開始處理...\n")
    
    try:
        await process_pdf_to_graph(
            pdf_path=os.path.abspath(pdf_path),
            document_id=None,
            chunk_size=2000
        )
        print("\n" + "=" * 70)
        print("✅ GraphRAG 處理完成！")
        print("=" * 70)
    except KeyboardInterrupt:
        print("\n\n⚠️ 處理被用戶中斷（Ctrl+C）")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ 處理失敗: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⚠️ 程式被用戶中斷（Ctrl+C）")
        sys.exit(0)

