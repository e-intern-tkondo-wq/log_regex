import sqlite3


def view_database(db_path: str, limit: int = 10):
    """データベースの内容を表示"""
    conn = sqlite3.connect(db_path)
    
    try:
        # テーブル構造を確認
        print("=" * 80)
        print("テーブル構造:")
        print("=" * 80)
        cursor = conn.execute("PRAGMA table_info(messages);")
        columns = cursor.fetchall()
        for col in columns:
            print(f"  {col[1]} ({col[2]})")
        
        # レコード数を確認
        print("\n" + "=" * 80)
        print("統計情報:")
        print("=" * 80)
        cursor = conn.execute("SELECT COUNT(*) FROM messages;")
        count = cursor.fetchone()[0]
        print(f"  総レコード数: {count}")
        
        # サンプルデータを表示
        print("\n" + "=" * 80)
        print(f"サンプルデータ（最初の{limit}件）:")
        print("=" * 80)
        cursor = conn.execute("""
            SELECT id, message, regex_rule 
            FROM messages 
            ORDER BY id 
            LIMIT ?
        """, (limit,))
        
        for row in cursor.fetchall():
            print(f"\n[ID: {row[0]}]")
            print(f"元のメッセージ:")
            print(f"  {row[1][:100]}{'...' if len(row[1]) > 100 else ''}")
            print(f"正規表現ルール:")
            print(f"  {row[2][:100]}{'...' if len(row[2]) > 100 else ''}")
            print("-" * 80)
        
        # ユニークな正規表現ルールの数を確認
        print("\n" + "=" * 80)
        print("ユニークな正規表現ルール数:")
        print("=" * 80)
        cursor = conn.execute("SELECT COUNT(DISTINCT regex_rule) FROM messages;")
        unique_count = cursor.fetchone()[0]
        print(f"  ユニークな正規表現ルール: {unique_count}")
        
    finally:
        conn.close()


if __name__ == "__main__":
    db_path = "regex.sqlite3"
    view_database(db_path, limit=10)

