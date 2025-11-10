import sqlite3
import re
import argparse
from pathlib import Path


def abstract_message(message: str) -> str:
    """regex.pyのabstract_message関数と同じ処理"""
    # 16進数を先に処理して、エスケープ対象から除外
    parts = []
    last_end = 0
    
    for match in re.finditer(r'0x[0-9A-Fa-f]+', message):
        # マッチ前の部分を処理
        if match.start() > last_end:
            part = message[last_end:match.start()]
            # 空白を処理
            part = re.sub(r'\s+', '___WS___', part)
            # 数字を処理
            part = re.sub(r'\d+', '___NUM___', part)
            # エスケープ
            part = re.escape(part)
            # プレースホルダーを正規表現パターンに戻す
            part = part.replace('___WS___', r'\s+').replace('___NUM___', r'\d+')
            # エスケープされたパターンを正規表現パターンに戻す
            part = part.replace(r'\\d\\+', r'\d+').replace(r'\\s\\+', r'\s+')
            parts.append(part)
        
        # 16進数部分はそのまま正規表現パターンとして追加
        parts.append(r'0x[0-9A-Fa-f]+')
        last_end = match.end()
    
    # 残りの部分を処理
    if last_end < len(message):
        part = message[last_end:]
        part = re.sub(r'\s+', '___WS___', part)
        part = re.sub(r'\d+', '___NUM___', part)
        part = re.escape(part)
        part = part.replace('___WS___', r'\s+').replace('___NUM___', r'\d+')
        part = part.replace(r'\\d\\+', r'\d+').replace(r'\\s\\+', r'\s+')
        parts.append(part)
    
    return ''.join(parts)


def create_schema(conn: sqlite3.Connection):
    """データベーススキーマを作成"""
    with conn:
        conn.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            message TEXT NOT NULL,
            regex_rule TEXT NOT NULL
        );
        """)
        # インデックスを作成（検索性能向上のため）
        conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_regex_rule ON messages(regex_rule);
        """)


def process_line_by_line(conn: sqlite3.Connection, input_file: str, max_lines: int = None):
    """
    テキストファイルからデータを1行ずつ読み込み、正規化してデータベースに格納
    各行について、正規表現変換→格納→検証を実行
    """
    input_path = Path(input_file)
    
    if not input_path.exists():
        raise FileNotFoundError(f"ファイルが見つかりません: {input_file}")
    
    processed_count = 0
    error_count = 0
    
    with open(input_path, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            # 最大行数に達したら終了
            if max_lines is not None and processed_count >= max_lines:
                print(f"\n指定された行数（{max_lines}行）に達したため処理を終了しました")
                break
            
            message = line.rstrip('\n\r')
            if not message:  # 空行をスキップ
                continue
            
            try:
                # 1. 正規表現に変換
                regex_rule = abstract_message(message)
                
                # 2. データベースに格納
                with conn:
                    cursor = conn.execute(
                        "INSERT INTO messages (message, regex_rule) VALUES (?, ?)",
                        (message, regex_rule)
                    )
                    inserted_id = cursor.lastrowid
                
                # 3. 格納した正規表現と元のrawデータをmatchして検証
                try:
                    pattern = re.compile(regex_rule)
                    if not pattern.fullmatch(message):
                        error_msg = (
                            f"エラー: 行 {line_num} (ID: {inserted_id}) でマッチしませんでした\n"
                            f"  元のメッセージ: {message[:100]}{'...' if len(message) > 100 else ''}\n"
                            f"  正規表現ルール: {regex_rule[:100]}{'...' if len(regex_rule) > 100 else ''}"
                        )
                        print(error_msg)
                        error_count += 1
                        # エラーが発生した行をデータベースから削除（オプション）
                        # with conn:
                        #     conn.execute("DELETE FROM messages WHERE id = ?", (inserted_id,))
                        raise ValueError(f"行 {line_num} でマッチ検証に失敗しました")
                    
                    # 正常に処理完了
                    processed_count += 1
                    if processed_count % 100 == 0:
                        print(f"処理済み: {processed_count} 行（エラー: {error_count} 件）")
                
                except re.error as e:
                    error_msg = (
                        f"エラー: 行 {line_num} (ID: {inserted_id}) で正規表現のコンパイルに失敗しました\n"
                        f"  エラー内容: {str(e)}\n"
                        f"  元のメッセージ: {message[:100]}{'...' if len(message) > 100 else ''}\n"
                        f"  正規表現ルール: {regex_rule[:100]}{'...' if len(regex_rule) > 100 else ''}"
                    )
                    print(error_msg)
                    error_count += 1
                    raise ValueError(f"行 {line_num} で正規表現コンパイルに失敗しました: {str(e)}")
            
            except Exception as e:
                error_count += 1
                print(f"行 {line_num} でエラーが発生しました: {str(e)}")
                # エラーが発生した場合は処理を停止
                raise
    
    return processed_count, error_count


def main():
    parser = argparse.ArgumentParser(description='ログメッセージを正規表現に変換してデータベースに格納')
    parser.add_argument(
        '-n', '--num-lines',
        type=int,
        default=None,
        help='処理する行数（指定しない場合は全行処理）'
    )
    args = parser.parse_args()
    
    db_path = "regex.sqlite3"
    input_file = "/Users/user/home/test/regex_preprocess/sqlite_test/gpu001.log-20250714_messages.txt"
    
    print(f"データベース作成: {db_path}")
    conn = sqlite3.connect(db_path)
    
    try:
        print("スキーマを作成中...")
        create_schema(conn)
        
        if args.num_lines:
            print(f"データを読み込み中: {input_file}（{args.num_lines}行まで処理）")
        else:
            print(f"データを読み込み中: {input_file}（全行処理）")
        
        processed_count, error_count = process_line_by_line(conn, input_file, max_lines=args.num_lines)
        
        # 統計情報を表示
        with conn:
            cursor = conn.execute("SELECT COUNT(*) FROM messages;")
            total_count = cursor.fetchone()[0]
        
        print(f"\n" + "=" * 80)
        print(f"処理完了:")
        print(f"  処理した行数: {processed_count}")
        print(f"  エラー件数: {error_count}")
        print(f"  データベース内の総レコード数: {total_count}")
        print("=" * 80)
        
        if error_count == 0:
            print("✓ 全てのログに対してエラーは発生しませんでした")
        else:
            print(f"⚠ {error_count} 件のエラーが発生しました")
            
    finally:
        conn.close()
        print(f"\nデータベースを閉じました: {db_path}")


if __name__ == "__main__":
    main()

