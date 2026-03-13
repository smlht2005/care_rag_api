"""
快速驗證 graph.db 是否包含 process_thisqa_to_graph 寫入的 4 個 Thisqa 主文件
"""
import sqlite3
import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.config import settings

def main():
    db_path = settings.GRAPH_DB_PATH
    if not os.path.exists(db_path):
        print("[X] graph.db 不存在:", db_path)
        return 1
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    expected = ["doc_thisqa_billing", "doc_thisqa_registration", "doc_thisqa_orders", "doc_thisqa_ic_error"]
    placeholders = ",".join("?" * len(expected))
    c.execute(
        "SELECT id, name, properties FROM entities WHERE type='Document' AND id IN (" + placeholders + ")",
        expected,
    )
    rows = c.fetchall()
    found = {r["id"] for r in rows}
    print("[graph.db 驗證] Thisqa 主文件")
    print("-" * 50)
    for r in rows:
        p = json.loads(r["properties"]) if r["properties"] else {}
        print(" ", r["id"], "|", r["name"], "| chunks:", p.get("chunks"), "| total_length:", p.get("total_length"))
    print("-" * 50)
    print("  Expected:", expected)
    print("  Found:  ", list(found))
    if set(expected) == found:
        print("[OK] 4 個 Thisqa 主文件皆存在")
    else:
        print("[X] 缺少:", set(expected) - found)
    c.execute("SELECT COUNT(*) FROM entities")
    n_ent = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM relations")
    n_rel = c.fetchone()[0]
    print("  實體總數:", n_ent, " 關係總數:", n_rel)
    conn.close()
    return 0 if set(expected) == found else 1

if __name__ == "__main__":
    sys.exit(main())
