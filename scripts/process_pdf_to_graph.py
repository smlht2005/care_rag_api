"""
處理 PDF 文件並構建圖結構
從 PDF 文件提取文字，新增到向量資料庫，並構建 GraphRAG 圖結構

更新時間：2025-12-26 16:25
作者：AI Assistant
修改摘要：添加 --overwrite 選項，當重複處理相同來源 PDF 時，先刪除現有數據以避免重複
更新時間：2025-12-26 14:20
作者：AI Assistant
修改摘要：添加抑制 PyPDF2 CropBox 警告功能，減少終端輸出噪音
更新時間：2025-12-26 14:14
作者：AI Assistant
修改摘要：修復縮排錯誤（IndentationError），if 語句塊內的代碼缺少正確縮排
"""
import asyncio
import sys
import os
import uuid
import warnings
from pathlib import Path
from typing import Optional

# 添加專案路徑
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 抑制 PyPDF2 的 CropBox 警告
warnings.filterwarnings("ignore", message=".*CropBox.*")

from app.config import settings
from app.core.graph_store import SQLiteGraphStore, Entity
from app.core.entity_extractor import EntityExtractor
from app.services.graph_builder import GraphBuilder
from app.services.llm_service import LLMService
from app.services.vector_service import VectorService

# 嘗試導入 PDF 處理庫
try:
    import PyPDF2
    HAS_PYPDF2 = True
except ImportError:
    HAS_PYPDF2 = False

try:
    import pdfplumber
    HAS_PDFPLUMBER = True
except ImportError:
    HAS_PDFPLUMBER = False


def extract_text_from_pdf(pdf_path: str) -> str:
    """
    從 PDF 文件提取文字
    
    Args:
        pdf_path: PDF 文件路徑
    
    Returns:
        提取的文字內容
    """
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"PDF 文件不存在: {pdf_path}")
    
    text_content = []
    
    # 優先使用 pdfplumber（更好的中文支援）
    if HAS_PDFPLUMBER:
        try:
            with pdfplumber.open(pdf_path) as pdf:
                print(f"PDF 總頁數: {len(pdf.pages)}")
                for i, page in enumerate(pdf.pages):
                    text = page.extract_text()
                    if text:
                        text_content.append(text)
                        if (i + 1) % 10 == 0:
                            print(f"  已處理 {i + 1} 頁...")
            return "\n\n".join(text_content)
        except Exception as e:
            print(f"pdfplumber 處理失敗: {str(e)}，嘗試 PyPDF2...")
    
    # 降級使用 PyPDF2
    if HAS_PYPDF2:
        try:
            # 抑制 PyPDF2 的 CropBox 警告
            with warnings.catch_warnings():
                warnings.filterwarnings("ignore", message=".*CropBox.*")
                with open(pdf_path, 'rb') as file:
                    pdf_reader = PyPDF2.PdfReader(file)
                    print(f"PDF 總頁數: {len(pdf_reader.pages)}")
                    for i, page in enumerate(pdf_reader.pages):
                        text = page.extract_text()
                        if text:
                            text_content.append(text)
                        if (i + 1) % 10 == 0:
                            print(f"  已處理 {i + 1} 頁...")
            return "\n\n".join(text_content)
        except Exception as e:
            print(f"PyPDF2 處理失敗: {str(e)}")
    
    # 如果都沒有安裝
    if not HAS_PDFPLUMBER and not HAS_PYPDF2:
        raise ImportError(
            "需要安裝 PDF 處理庫。請執行：\n"
            "  pip install pdfplumber  # 推薦（更好的中文支援）\n"
            "  或\n"
            "  pip install PyPDF2"
        )
    
    raise Exception("無法提取 PDF 文字內容")


async def process_pdf_to_graph(
    pdf_path: str,
    document_id: Optional[str] = None,
    chunk_size: int = 2000,
    overwrite: bool = False
):
    """
    處理 PDF 文件並構建圖結構
    
    Args:
        pdf_path: PDF 文件路徑
        document_id: 文件 ID（如果為 None，則自動生成）
        chunk_size: 文字分塊大小（字元數）
        overwrite: 如果為 True，當檢測到相同來源的 PDF 時，先刪除現有數據
    """
    graph_store = None
    try:
        print("=" * 60)
        print("PDF 文件處理和圖構建")
        print("=" * 60)
        
        # 1. 提取 PDF 文字
        print(f"\n[步驟 1/5] 提取 PDF 文字內容...")
        print(f"文件路徑: {pdf_path}")
        
        try:
            full_text = extract_text_from_pdf(pdf_path)
            print(f"✅ 文字提取完成，總長度: {len(full_text)} 字元")
        except KeyboardInterrupt:
            print(f"\n⚠️ 用戶中斷（Ctrl+C）")
            return
        except Exception as e:
            print(f"❌ PDF 文字提取失敗: {str(e)}")
            return
        
        # 2. 初始化服務
        print(f"\n[步驟 2/5] 初始化服務...")
        graph_store = SQLiteGraphStore(settings.GRAPH_DB_PATH)
        await graph_store.initialize()
        
        llm_service = LLMService()
        entity_extractor = EntityExtractor(llm_service)
        graph_builder = GraphBuilder(graph_store, entity_extractor)
        vector_service = VectorService()
        
        print("✅ 服務初始化完成")
        
        # 2.5. 檢查並清理現有數據（如果啟用 overwrite）
        if overwrite:
            print(f"\n[步驟 2.5/5] 檢查現有數據...")
            pdf_path_abs = os.path.abspath(pdf_path)
            
            # 查找所有 Document 類型的實體
            existing_docs = await graph_store.get_entities_by_type("Document", limit=10000)
            deleted_count = 0
            doc_ids_to_delete = []
            
            # 第一步：找出所有匹配來源的 document 實體
            for doc_entity in existing_docs:
                # 檢查 properties 中的 source 是否匹配
                doc_source = doc_entity.properties.get("source", "")
                if doc_source == pdf_path_abs or doc_source == pdf_path:
                    print(f"  發現現有文件實體: {doc_entity.id} (來源: {doc_source})")
                    doc_ids_to_delete.append(doc_entity.id)
            
            # 第二步：刪除所有相關的 chunk 實體（先刪除 chunk，再刪除主 document）
            for doc_id in doc_ids_to_delete:
                chunk_prefix = f"{doc_id}_chunk_"
                for entity in existing_docs:
                    if entity.id.startswith(chunk_prefix):
                        if await graph_store.delete_entity(entity.id):
                            deleted_count += 1
                            print(f"    ✅ 已刪除區塊實體: {entity.id}")
            
            # 第三步：刪除主文件實體（級聯刪除會自動刪除 CONTAINS 關係）
            for doc_id in doc_ids_to_delete:
                if await graph_store.delete_entity(doc_id):
                    deleted_count += 1
                    print(f"    ✅ 已刪除文件實體: {doc_id}")
            
            if deleted_count > 0:
                print(f"  ✅ 已清理 {deleted_count} 個現有實體（包含 {len(doc_ids_to_delete)} 個文件實體）")
            else:
                print(f"  ℹ️  未發現相同來源的現有數據")
        
        # 3. 生成文件 ID
        if document_id is None:
            pdf_name = Path(pdf_path).stem
            document_id = f"doc_{pdf_name}_{str(uuid.uuid4())[:8]}"
        
        print(f"\n[步驟 3/5] 文件 ID: {document_id}")
        
        # 4. 分塊處理（如果文字太長）
        print(f"\n[步驟 4/5] 處理文件內容...")
        
        if len(full_text) > chunk_size:
            print(f"文字過長 ({len(full_text)} 字元)，進行分塊處理...")
            chunks = []
            for i in range(0, len(full_text), chunk_size):
                chunk = full_text[i:i + chunk_size]
                chunks.append(chunk)
            
            print(f"分為 {len(chunks)} 個區塊")
            
            # 處理每個區塊
            total_entities = 0
            total_relations = 0
            
            try:
                for i, chunk in enumerate(chunks):
                    chunk_id = f"{document_id}_chunk_{i+1}"
                    print(f"\n處理區塊 {i+1}/{len(chunks)}...")
                    
                    # 構建圖結構
                    try:
                        result = await graph_builder.build_graph_from_text(
                            chunk,
                            chunk_id,
                            entity_types=["Person", "Organization", "Location", "Concept", "Document", "Policy"]
                        )
                        total_entities += result.get("entities_count", 0)
                        total_relations += result.get("relations_count", 0)
                        print(f"  ✅ 區塊 {i+1} 完成: {result.get('entities_count', 0)} 實體, {result.get('relations_count', 0)} 關係")
                    except KeyboardInterrupt:
                        print(f"\n⚠️ 用戶中斷（Ctrl+C），已處理 {i} 個區塊")
                        raise
                    except Exception as e:
                        print(f"  ⚠️ 區塊 {i+1} 處理失敗: {str(e)}")
            except KeyboardInterrupt:
                print(f"\n⚠️ 處理被用戶中斷（Ctrl+C）")
                print(f"   已處理區塊: {i+1}/{len(chunks)}")
                print(f"   已提取實體: {total_entities}")
                print(f"   已提取關係: {total_relations}")
                raise
            
            # 建立主文件實體
            main_doc_entity = Entity(
                id=document_id,
                type="Document",
                name=Path(pdf_path).name,
                properties={
                    "source": pdf_path,
                    "chunks": len(chunks),
                    "total_length": len(full_text)
                },
                created_at=None
            )
            await graph_store.add_entity(main_doc_entity)
            
            print(f"\n✅ 所有區塊處理完成")
            print(f"   總實體數: {total_entities}")
            print(f"   總關係數: {total_relations}")
            
        else:
            # 單一區塊處理
            print("文字長度適中，單一區塊處理...")
            
            result = await graph_builder.build_graph_from_text(
                full_text,
                document_id,
                entity_types=["Person", "Organization", "Location", "Concept", "Document", "Policy"]
            )
            
            print(f"✅ 圖構建完成:")
            print(f"   實體數: {result.get('entities_count', 0)}")
            print(f"   關係數: {result.get('relations_count', 0)}")
    
        # 5. 新增到向量資料庫
        print(f"\n[步驟 5/5] 新增到向量資料庫...")
        try:
            await vector_service.add_documents([{
                "id": document_id,
                "content": full_text[:5000],  # 限制長度
                "metadata": {
                    "source": pdf_path,
                    "type": "pdf",
                    "length": len(full_text)
                },
                "source": Path(pdf_path).name
            }])
            print("✅ 向量資料庫更新完成")
        except Exception as e:
            print(f"⚠️ 向量資料庫更新失敗: {str(e)}")
        
    except KeyboardInterrupt:
        print(f"\n⚠️ 處理被用戶中斷（Ctrl+C）")
        print(f"正在清理資源...")
    finally:
        # 確保關閉連線
        if graph_store:
            try:
                await graph_store.close()
                print("✅ 資源清理完成")
            except Exception as e:
                print(f"⚠️ 清理資源時發生錯誤: {str(e)}")
    
    # 只有在正常完成時才顯示完成訊息
    try:
        print("\n" + "=" * 60)
        print("處理完成！")
        print("=" * 60)
        print(f"\n文件 ID: {document_id}")
        print(f"可以使用以下命令查詢圖結構:")
        print(f"  python scripts/check_db.py")
    except NameError:
        # 如果 document_id 未定義（中斷太早），跳過
        pass


async def main():
    """主函數"""
    import argparse
    
    parser = argparse.ArgumentParser(description="處理 PDF 文件並構建圖結構")
    parser.add_argument(
        "pdf_path",
        nargs="?",
        default="data/example/1051219長期照護2.0核定本.pdf",
        help="PDF 文件路徑（預設: data/example/1051219長期照護2.0核定本.pdf）"
    )
    parser.add_argument(
        "--doc-id",
        type=str,
        default=None,
        help="文件 ID（預設: 自動生成）"
    )
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=2000,
        help="文字分塊大小（預設: 2000 字元）"
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="如果檢測到相同來源的 PDF，先刪除現有數據再處理（避免重複數據）"
    )
    
    args = parser.parse_args()
    
    # 轉換為絕對路徑
    pdf_path = os.path.abspath(args.pdf_path)
    
    await process_pdf_to_graph(
        pdf_path=pdf_path,
        document_id=args.doc_id,
        chunk_size=args.chunk_size,
        overwrite=args.overwrite
    )


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⚠️ 程式被用戶中斷（Ctrl+C）")
        print("正在退出...")
        sys.exit(0)

