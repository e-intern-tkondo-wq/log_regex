#!/usr/bin/env python3
"""
既存のregex.sqlite3からユニークなメッセージのみを抽出して
新しいデータベース（regex_unique.sqlite3）を作成するスクリプト
"""
import sqlite3
from pathlib import Path


def create_unique_database(source_db: str, target_db: str):
    """
    既存のデータベースからユニークなメッセージのみを抽出して新しいデータベースを作成
    
    Args:
        source_db: 元のデータベースファイルパス
        target_db: 作成する新しいデータベースファイルパス
    """
    source_path = Path(source_db)
    target_path = Path(target_db)
    
    if not source_path.exists():
        raise FileNotFoundError(f"元のデータベースが見つかりません: {source_db}")
    
    # 既存のターゲットデータベースを削除（存在する場合）
    if target_path.exists():
        print(f"既存の {target_db} を削除します...")
        target_path.unlink()
    
    print(f"元のデータベース: {source_db}")
    print(f"新しいデータベース: {target_db}")
    print("=" * 80)
    
    # 元のデータベースに接続
    source_conn = sqlite3.connect(source_db)
    source_conn.row_factory = sqlite3.Row
    
    # 新しいデータベースに接続
    target_conn = sqlite3.connect(target_db)
    
    try:
        # 新しいデータベースのスキーマを作成
        print("スキーマを作成中...")
        with target_conn:
            target_conn.execute("""
            CREATE TABLE messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                message TEXT NOT NULL,
                regex_rule TEXT NOT NULL
            );
            """)
            # インデックスを作成
            target_conn.execute("""
            CREATE INDEX idx_regex_rule ON messages(regex_rule);
            """)
        
        # 元のデータベースからユニークなメッセージを取得
        print("ユニークなメッセージを抽出中...")
        cursor = source_conn.execute("""
            SELECT DISTINCT message, regex_rule
            FROM messages
            ORDER BY message
        """)
        
        unique_records = cursor.fetchall()
        total_count = len(unique_records)
        
        print(f"抽出されたユニークなレコード数: {total_count}")
        print("新しいデータベースに格納中...")
        
        # ユニークなレコードを新しいデータベースに挿入
        inserted_count = 0
        with target_conn:
            for record in unique_records:
                target_conn.execute(
                    "INSERT INTO messages (message, regex_rule) VALUES (?, ?)",
                    (record['message'], record['regex_rule'])
                )
                inserted_count += 1
                
                if inserted_count % 500 == 0:
                    print(f"  処理済み: {inserted_count} / {total_count} 件")
        
        print(f"完了: {inserted_count} 件のレコードを格納しました")
        
        # 統計情報を表示
        print("\n" + "=" * 80)
        print("統計情報:")
        print("=" * 80)
        
        # 元のデータベースの統計
        cursor = source_conn.execute("SELECT COUNT(*) FROM messages")
        original_count = cursor.fetchone()[0]
        
        cursor = source_conn.execute("SELECT COUNT(DISTINCT message) FROM messages")
        original_unique = cursor.fetchone()[0]
        
        # 新しいデータベースの統計
        cursor = target_conn.execute("SELECT COUNT(*) FROM messages")
        new_count = cursor.fetchone()[0]
        
        cursor = target_conn.execute("SELECT COUNT(DISTINCT message) FROM messages")
        new_unique = cursor.fetchone()[0]
        
        cursor = target_conn.execute("SELECT COUNT(DISTINCT regex_rule) FROM messages")
        new_unique_regex = cursor.fetchone()[0]
        
        print(f"元のデータベース:")
        print(f"  総レコード数: {original_count}")
        print(f"  ユニークなメッセージ数: {original_unique}")
        print(f"\n新しいデータベース:")
        print(f"  総レコード数: {new_count}")
        print(f"  ユニークなメッセージ数: {new_unique}")
        print(f"  ユニークな正規表現ルール数: {new_unique_regex}")
        print("=" * 80)
        
        if new_count == new_unique:
            print("✓ 新しいデータベースには重複がありません")
        else:
            print(f"⚠ 警告: 新しいデータベースに {new_count - new_unique} 件の重複が存在します")
        
    finally:
        source_conn.close()
        target_conn.close()
        print(f"\nデータベースを閉じました")


def main():
    """メイン処理"""
    source_db = "regex.sqlite3"
    target_db = "regex_unique.sqlite3"
    
    # カレントディレクトリを確認
    current_dir = Path(__file__).parent
    source_path = current_dir / source_db
    target_path = current_dir / target_db
    
    if not source_path.exists():
        print(f"エラー: {source_db} が見つかりません")
        print(f"現在のディレクトリ: {current_dir}")
        return
    
    print("=" * 80)
    print("ユニークなデータベース作成")
    print("=" * 80)
    
    try:
        create_unique_database(str(source_path), str(target_path))
        print(f"\n✓ 新しいデータベース {target_db} が正常に作成されました")
    except Exception as e:
        print(f"\n✗ エラーが発生しました: {str(e)}")
        raise


if __name__ == "__main__":
    main()

