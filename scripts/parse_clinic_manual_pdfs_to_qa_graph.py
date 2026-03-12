"""
解析衛生所操作手冊 PDF 並建立問答知識圖譜
從 PDF 文件提取問答對和知識點，建立專門的 graph_qa.db 圖資料庫

更新時間：2025-12-30 09:34
作者：AI Assistant
修改摘要：優化 LLM 實體和關係提取：1) Token 限制從 1000 增加到 3000；2) 文字處理長度從 5000 增加到 20000 字元；3) 擴展實體類型列表（17 種類型）；4) 關係提取也使用優化文字長度
更新時間：2025-12-29 18:45
作者：AI Assistant
修改摘要：添加版權聲明過濾功能，自動移除「版權所有 非經授權請勿翻印」等非知識內容
更新時間：2025-12-29 15:00
作者：AI Assistant
修改摘要：建立衛生所操作手冊 PDF 解析腳本，提取問答對並建立 graph_qa.db
"""
import asyncio
import sys
import os
import uuid
import warnings
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple
import re

# 添加專案路徑
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 抑制 PyPDF2 的 CropBox 警告
warnings.filterwarnings("ignore", message=".*CropBox.*")

from app.config import settings
from app.core.graph_store import SQLiteGraphStore, Entity, Relation
from app.core.entity_extractor import EntityExtractor
from app.services.llm_service import LLMService


def filter_copyright_text(text: str) -> str:
    """
    過濾版權聲明等非知識內容
    
    Args:
        text: 原始文字內容
    
    Returns:
        過濾後的文字內容
    """
    if not text:
        return text
    
    # 常見的版權聲明模式（使用正則表達式）
    copyright_patterns = [
        r'版權所有[^\n]*非經授權[^\n]*翻印[^\n]*',
        r'版權所有[^\n]*',
        r'Copyright[^\n]*All[^\n]*Reserved[^\n]*',
        r'非經授權[^\n]*請勿翻印[^\n]*',
        r'請勿翻印[^\n]*',
        r'All[^\n]*Rights[^\n]*Reserved[^\n]*',
        r'©[^\n]*',
        r'本文件[^\n]*版權所有[^\n]*',
        r'本手冊[^\n]*版權所有[^\n]*',
        r'本資料[^\n]*版權所有[^\n]*',
    ]
    
    filtered_text = text
    
    # 移除版權聲明
    for pattern in copyright_patterns:
        filtered_text = re.sub(pattern, '', filtered_text, flags=re.IGNORECASE | re.MULTILINE)
    
    # 移除頁碼（單獨一行的數字）
    filtered_text = re.sub(r'^\s*\d+\s*$', '', filtered_text, flags=re.MULTILINE)
    
    # 移除多餘的空白行（超過 3 個連續換行）
    filtered_text = re.sub(r'\n{4,}', '\n\n\n', filtered_text)
    
    # 移除行首行尾空白
    filtered_text = filtered_text.strip()
    
    return filtered_text

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


def extract_text_from_pdf(pdf_path: str) -> Tuple[str, int]:
    """
    從 PDF 文件提取文字
    
    Args:
        pdf_path: PDF 文件路徑
    
    Returns:
        (提取的文字內容, 總頁數)
    """
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"PDF 文件不存在: {pdf_path}")
    
    text_content = []
    total_pages = 0
    
    # 優先使用 pdfplumber（更好的中文支援）
    if HAS_PDFPLUMBER:
        try:
            with pdfplumber.open(pdf_path) as pdf:
                total_pages = len(pdf.pages)
                print(f"PDF 總頁數: {total_pages}")
                for i, page in enumerate(pdf.pages):
                    text = page.extract_text()
                    if text:
                        # 過濾版權聲明
                        text = filter_copyright_text(text)
                        if text.strip():  # 只添加非空內容
                            text_content.append(f"=== 第 {i+1} 頁 ===\n{text}")
                        if (i + 1) % 10 == 0:
                            print(f"  已處理 {i + 1} 頁...")
                return "\n\n".join(text_content), total_pages
        except Exception as e:
            print(f"pdfplumber 處理失敗: {str(e)}，嘗試 PyPDF2...")
    
    # 降級使用 PyPDF2
    if HAS_PYPDF2:
        try:
            with warnings.catch_warnings():
                warnings.filterwarnings("ignore", message=".*CropBox.*")
                with open(pdf_path, 'rb') as file:
                    pdf_reader = PyPDF2.PdfReader(file)
                    total_pages = len(pdf_reader.pages)
                    print(f"PDF 總頁數: {total_pages}")
                    for i, page in enumerate(pdf_reader.pages):
                        text = page.extract_text()
                        if text:
                            # 過濾版權聲明
                            text = filter_copyright_text(text)
                            if text.strip():  # 只添加非空內容
                                text_content.append(f"=== 第 {i+1} 頁 ===\n{text}")
                        if (i + 1) % 10 == 0:
                            print(f"  已處理 {i + 1} 頁...")
                return "\n\n".join(text_content), total_pages
        except Exception as e:
            print(f"PyPDF2 處理失敗: {str(e)}")
    
    if not HAS_PDFPLUMBER and not HAS_PYPDF2:
        raise ImportError(
            "需要安裝 PDF 處理庫。請執行：\n"
            "  pip install pdfplumber  # 推薦（更好的中文支援）\n"
            "  或\n"
            "  pip install PyPDF2"
        )
    
    raise Exception("無法提取 PDF 文字內容")


def extract_qa_pairs_from_text(text: str) -> List[Dict[str, Any]]:
    """
    從文字中提取問答對
    
    Args:
        text: 文字內容
    
    Returns:
        問答對列表，每個包含 question, answer, context
    """
    qa_pairs = []
    
    # 模式1: Q: ... A: ... 格式
    qa_pattern1 = re.compile(r'[Q問]：?\s*(.+?)\s*[A答]：?\s*(.+?)(?=[Q問]：|$)', re.DOTALL | re.IGNORECASE)
    matches1 = qa_pattern1.finditer(text)
    for match in matches1:
        question = match.group(1).strip()
        answer = match.group(2).strip()
        if len(question) > 5 and len(answer) > 10:  # 過濾太短的問答
            qa_pairs.append({
                "question": question,
                "answer": answer,
                "source": "qa_pattern1"
            })
    
    # 模式2: 問題：... 答案：... 格式
    qa_pattern2 = re.compile(r'問題[：:]\s*(.+?)\s*答案[：:]\s*(.+?)(?=問題[：:]|$)', re.DOTALL)
    matches2 = qa_pattern2.finditer(text)
    for match in matches2:
        question = match.group(1).strip()
        answer = match.group(2).strip()
        if len(question) > 5 and len(answer) > 10:
            qa_pairs.append({
                "question": question,
                "answer": answer,
                "source": "qa_pattern2"
            })
    
    # 模式3: 標題作為問題，後續段落作為答案
    # 尋找標題模式（通常是單獨一行，字數較少）
    lines = text.split('\n')
    current_question = None
    current_answer = []
    
    for i, line in enumerate(lines):
        line = line.strip()
        if not line:
            continue
        
        # 判斷是否為標題（短行，可能是問題）
        if len(line) < 50 and (line.endswith('？') or line.endswith('?') or 
                               '如何' in line or '什麼' in line or '怎樣' in line or
                               '步驟' in line or '流程' in line or '操作' in line):
            # 保存前一個問答對
            if current_question and current_answer:
                answer_text = '\n'.join(current_answer).strip()
                if len(answer_text) > 10:
                    qa_pairs.append({
                        "question": current_question,
                        "answer": answer_text,
                        "source": "title_pattern"
                    })
            
            # 開始新的問答對
            current_question = line
            current_answer = []
        else:
            # 累積答案內容
            if current_question:
                current_answer.append(line)
    
    # 保存最後一個問答對
    if current_question and current_answer:
        answer_text = '\n'.join(current_answer).strip()
        if len(answer_text) > 10:
            qa_pairs.append({
                "question": current_question,
                "answer": answer_text,
                "source": "title_pattern"
            })
    
    return qa_pairs


def extract_knowledge_points(text: str) -> List[Dict[str, Any]]:
    """
    從文字中提取知識點
    
    Args:
        text: 文字內容
    
    Returns:
        知識點列表，每個包含 topic, content, keywords
    """
    knowledge_points = []
    
    # 提取章節標題作為知識點主題
    section_pattern = re.compile(r'^第[一二三四五六七八九十\d]+[章節]\s*(.+?)$', re.MULTILINE)
    sections = section_pattern.findall(text)
    
    for section_title in sections:
        knowledge_points.append({
            "topic": section_title.strip(),
            "content": "",  # 將在後續處理中填充
            "keywords": [],
            "type": "section"
        })
    
    # 提取關鍵詞（常見的操作術語）
    keywords_pattern = re.compile(r'(批價|掛號|病歷|醫令|操作|功能|步驟|流程|設定|查詢|新增|修改|刪除|列印|匯出)')
    keywords = set(keywords_pattern.findall(text))
    
    if keywords:
        knowledge_points.append({
            "topic": "關鍵操作術語",
            "content": ", ".join(keywords),
            "keywords": list(keywords),
            "type": "keywords"
        })
    
    return knowledge_points


async def process_pdf_to_qa_graph(
    pdf_path: str,
    document_id: Optional[str] = None,
    db_path: str = "./data/graph_qa.db"
):
    """
    處理 PDF 文件並構建問答知識圖譜
    
    Args:
        pdf_path: PDF 文件路徑
        document_id: 文件 ID（如果為 None，則自動生成）
        db_path: 圖資料庫路徑
    """
    graph_store = None
    try:
        print("=" * 60)
        print("PDF 問答知識圖譜構建")
        print("=" * 60)
        
        # 1. 提取 PDF 文字
        print(f"\n[步驟 1/6] 提取 PDF 文字內容...")
        print(f"文件路徑: {pdf_path}")
        
        try:
            full_text, total_pages = extract_text_from_pdf(pdf_path)
            print(f"✅ 文字提取完成，總長度: {len(full_text)} 字元，共 {total_pages} 頁")
        except KeyboardInterrupt:
            print(f"\n⚠️ 用戶中斷（Ctrl+C）")
            return
        except Exception as e:
            print(f"❌ PDF 文字提取失敗: {str(e)}")
            return
        
        # 2. 初始化問答圖資料庫
        print(f"\n[步驟 2/6] 初始化問答圖資料庫...")
        print(f"資料庫路徑: {db_path}")
        
        # 確保資料目錄存在
        db_dir = os.path.dirname(db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir)
            print(f"✅ 建立資料目錄: {db_dir}")
        
        graph_store = SQLiteGraphStore(db_path)
        await graph_store.initialize()
        print("✅ 問答圖資料庫初始化完成")
        
        # 3. 初始化服務
        print(f"\n[步驟 3/6] 初始化服務...")
        llm_service = LLMService()
        entity_extractor = EntityExtractor(llm_service)
        print("✅ 服務初始化完成")
        
        # 4. 生成文件 ID
        if document_id is None:
            pdf_name = Path(pdf_path).stem
            document_id = f"qa_doc_{pdf_name}_{str(uuid.uuid4())[:8]}"
        
        print(f"\n[步驟 4/6] 文件 ID: {document_id}")
        
        # 5. 提取問答對和知識點
        print(f"\n[步驟 5/6] 提取問答對和知識點...")
        
        # 5.1 提取問答對
        qa_pairs = extract_qa_pairs_from_text(full_text)
        print(f"✅ 提取到 {len(qa_pairs)} 個問答對")
        
        # 5.2 提取知識點
        knowledge_points = extract_knowledge_points(full_text)
        print(f"✅ 提取到 {len(knowledge_points)} 個知識點")
        
        # 5.3 使用 LLM 提取更多實體和關係（優化版）
        print(f"\n[步驟 5.3/6] 使用 LLM 提取實體和關係（優化版）...")
        
        # 增加處理長度以提取更多實體（移到 try 外面，讓關係提取也能使用）
        text_for_llm = full_text[:20000]  # 從 5000 增加到 20000 字元
        
        # 擴展實體類型以提取更多實體
        entity_types = [
            "Concept", "Process", "Function", "Document", "Policy", "Procedure",
            "Person", "Organization", "Location", "Event", "System", "Service",
            "Rule", "Regulation", "Method", "Tool", "Technology"
        ]
        
        try:
            entities = await entity_extractor.extract_entities(
                text_for_llm,
                entity_types=entity_types
            )
            print(f"✅ LLM 提取到 {len(entities)} 個實體")
        except Exception as e:
            print(f"⚠️ LLM 實體提取失敗: {str(e)}，繼續處理...")
            entities = []
        
        # 6. 建立圖結構
        print(f"\n[步驟 6/6] 建立圖結構...")
        
        # 6.1 建立文件實體
        doc_entity = Entity(
            id=document_id,
            type="Document",
            name=Path(pdf_path).name,
            properties={
                "source": pdf_path,
                "type": "clinic_manual",
                "total_pages": total_pages,
                "total_length": len(full_text),
                "qa_pairs_count": len(qa_pairs),
                "knowledge_points_count": len(knowledge_points)
            },
            created_at=None
        )
        await graph_store.add_entity(doc_entity)
        print(f"✅ 建立文件實體: {document_id}")
        
        # 6.2 建立問答對實體和關係
        qa_count = 0
        for i, qa in enumerate(qa_pairs):
            qa_id = f"{document_id}_qa_{i+1}"
            
            # 建立問答實體
            qa_entity = Entity(
                id=qa_id,
                type="QA",
                name=qa["question"][:100],  # 限制名稱長度
                properties={
                    "question": qa["question"],
                    "answer": qa["answer"],
                    "source": qa.get("source", "unknown"),
                    "qa_index": i + 1
                },
                created_at=None
            )
            
            if await graph_store.add_entity(qa_entity):
                qa_count += 1
                
                # 建立文件到問答的關係
                relation = Relation(
                    id=f"{document_id}_to_{qa_id}",
                    source_id=document_id,
                    target_id=qa_id,
                    type="CONTAINS_QA",
                    properties={"qa_index": i + 1},
                    weight=1.0,
                    created_at=None
                )
                await graph_store.add_relation(relation)
        
        print(f"✅ 建立 {qa_count} 個問答實體和關係")
        
        # 6.3 建立知識點實體和關係
        kp_count = 0
        for i, kp in enumerate(knowledge_points):
            kp_id = f"{document_id}_kp_{i+1}"
            
            kp_entity = Entity(
                id=kp_id,
                type="KnowledgePoint",
                name=kp["topic"][:100],
                properties={
                    "topic": kp["topic"],
                    "content": kp.get("content", ""),
                    "keywords": kp.get("keywords", []),
                    "type": kp.get("type", "general")
                },
                created_at=None
            )
            
            if await graph_store.add_entity(kp_entity):
                kp_count += 1
                
                # 建立文件到知識點的關係
                relation = Relation(
                    id=f"{document_id}_to_{kp_id}",
                    source_id=document_id,
                    target_id=kp_id,
                    type="CONTAINS_KNOWLEDGE",
                    properties={"kp_index": i + 1},
                    weight=1.0,
                    created_at=None
                )
                await graph_store.add_relation(relation)
        
        print(f"✅ 建立 {kp_count} 個知識點實體和關係")
        
        # 6.4 建立 LLM 提取的實體和關係
        if entities:
            entity_count = 0
            relation_count = 0
            
            for entity in entities:
                if await graph_store.add_entity(entity):
                    entity_count += 1
                    
                    # 建立文件到實體的關係
                    relation = Relation(
                        id=f"{document_id}_to_{entity.id}",
                        source_id=document_id,
                        target_id=entity.id,
                        type="CONTAINS_ENTITY",
                        properties={},
                        weight=1.0,
                        created_at=None
                    )
                    await graph_store.add_relation(relation)
                    relation_count += 1
            
            # 提取關係（使用相同的優化文字長度）
            try:
                relations = await entity_extractor.extract_relations(
                    text_for_llm,  # 使用相同的優化文字長度（20000 字元）
                    entities
                )
                if relations:
                    for relation in relations:
                        await graph_store.add_relation(relation)
                        relation_count += 1
            except Exception as e:
                print(f"⚠️ 關係提取失敗: {str(e)}")
            
            print(f"✅ 建立 {entity_count} 個 LLM 實體和 {relation_count} 個關係")
        
        print("\n" + "=" * 60)
        print("處理完成！")
        print("=" * 60)
        print(f"\n文件 ID: {document_id}")
        print(f"問答對數量: {len(qa_pairs)}")
        print(f"知識點數量: {len(knowledge_points)}")
        print(f"資料庫路徑: {db_path}")
        print(f"\n可以使用以下命令查詢圖結構:")
        print(f"  python scripts/query_qa_graph.py")
        
    except KeyboardInterrupt:
        print(f"\n⚠️ 處理被用戶中斷（Ctrl+C）")
        print(f"正在清理資源...")
    except Exception as e:
        print(f"\n❌ 處理失敗: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        # 確保關閉連線
        if graph_store:
            try:
                await graph_store.close()
                print("✅ 資源清理完成")
            except Exception as e:
                print(f"⚠️ 清理資源時發生錯誤: {str(e)}")


async def process_multiple_pdfs(
    pdf_dir: str,
    db_path: str = "./data/graph_qa.db"
):
    """
    處理目錄中的所有 PDF 文件
    
    Args:
        pdf_dir: PDF 文件目錄
        db_path: 圖資料庫路徑
    """
    pdf_dir_path = Path(pdf_dir)
    if not pdf_dir_path.exists():
        raise FileNotFoundError(f"目錄不存在: {pdf_dir}")
    
    # 查找所有 PDF 文件
    pdf_files = list(pdf_dir_path.glob("*.pdf"))
    
    if not pdf_files:
        print(f"⚠️ 目錄中沒有找到 PDF 文件: {pdf_dir}")
        return
    
    print(f"找到 {len(pdf_files)} 個 PDF 文件")
    
    # 初始化資料庫（只初始化一次）
    db_dir = os.path.dirname(db_path)
    if db_dir and not os.path.exists(db_dir):
        os.makedirs(db_dir)
    
    graph_store = SQLiteGraphStore(db_path)
    await graph_store.initialize()
    await graph_store.close()
    
    # 處理每個 PDF
    for i, pdf_file in enumerate(pdf_files, 1):
        print(f"\n{'='*60}")
        print(f"處理文件 {i}/{len(pdf_files)}: {pdf_file.name}")
        print(f"{'='*60}")
        
        try:
            await process_pdf_to_qa_graph(
                pdf_path=str(pdf_file),
                document_id=None,
                db_path=db_path
            )
        except Exception as e:
            print(f"❌ 處理文件失敗 {pdf_file.name}: {str(e)}")
            continue
    
    print(f"\n{'='*60}")
    print(f"所有文件處理完成！")
    print(f"{'='*60}")
    print(f"資料庫路徑: {db_path}")


async def main():
    """主函數"""
    import argparse
    
    parser = argparse.ArgumentParser(description="解析衛生所操作手冊 PDF 並建立問答知識圖譜")
    parser.add_argument(
        "--pdf-dir",
        type=str,
        default="data/example/clinic his",
        help="PDF 文件目錄（預設: data/example/clinic his）"
    )
    parser.add_argument(
        "--pdf-file",
        type=str,
        default=None,
        help="單個 PDF 文件路徑（如果指定，則只處理該文件）"
    )
    parser.add_argument(
        "--db-path",
        type=str,
        default="./data/graph_qa.db",
        help="圖資料庫路徑（預設: ./data/graph_qa.db）"
    )
    
    args = parser.parse_args()
    
    if args.pdf_file:
        # 處理單個文件
        pdf_path = os.path.abspath(args.pdf_file)
        await process_pdf_to_qa_graph(
            pdf_path=pdf_path,
            document_id=None,
            db_path=args.db_path
        )
    else:
        # 處理目錄中的所有文件
        pdf_dir = os.path.abspath(args.pdf_dir)
        await process_multiple_pdfs(
            pdf_dir=pdf_dir,
            db_path=args.db_path
        )


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⚠️ 程式被用戶中斷（Ctrl+C）")
        print("正在退出...")
        sys.exit(0)

