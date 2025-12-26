"""
測試 PDF 文字提取功能
"""
import sys
import os

# 添加專案路徑
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.process_pdf_to_graph import extract_text_from_pdf

def test_pdf_extract():
    """測試 PDF 提取"""
    pdf_path = "data/example/1051219長期照護2.0核定本.pdf"
    
    print(f"測試 PDF 文字提取...")
    print(f"文件路徑: {pdf_path}")
    
    try:
        text = extract_text_from_pdf(pdf_path)
        print(f"\n✅ 提取成功！")
        print(f"文字長度: {len(text)} 字元")
        print(f"\n前 500 字元預覽:")
        print("-" * 60)
        print(text[:500])
        print("-" * 60)
        return True
    except Exception as e:
        print(f"\n❌ 提取失敗: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_pdf_extract()
    sys.exit(0 if success else 1)


