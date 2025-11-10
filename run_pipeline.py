#!/usr/bin/env python3
"""
パイプラインスクリプト: 複数の-n値を順次実行
エラーが発生した場合は処理を停止
"""
import subprocess
import sys
from pathlib import Path


def run_command(num_lines: int) -> bool:
    """
    指定された行数でcreate_regex_db.pyを実行
    戻り値: 成功した場合はTrue、エラーが発生した場合はFalse
    """
    script_path = Path(__file__).parent / "create_regex_db.py"
    
    print(f"\n{'=' * 80}")
    print(f"実行中: python create_regex_db.py -n {num_lines}")
    print(f"{'=' * 80}\n")
    
    try:
        result = subprocess.run(
            [sys.executable, str(script_path), "-n", str(num_lines)],
            check=True,
            capture_output=False,
            text=True
        )
        print(f"\n✓ -n {num_lines} の処理が正常に完了しました")
        return True
    except subprocess.CalledProcessError as e:
        print(f"\n✗ -n {num_lines} の処理でエラーが発生しました (終了コード: {e.returncode})")
        return False
    except Exception as e:
        print(f"\n✗ -n {num_lines} の処理で予期しないエラーが発生しました: {str(e)}")
        return False


def main():
    """メイン処理: 10, 50, 100, 1000を順次実行"""
    num_lines_list = [10, 50, 100, 1000]
    
    print("=" * 80)
    print("パイプライン実行開始")
    print(f"実行する-n値: {', '.join(map(str, num_lines_list))}")
    print("=" * 80)
    
    for num_lines in num_lines_list:
        success = run_command(num_lines)
        
        if not success:
            print(f"\n{'=' * 80}")
            print(f"エラー: -n {num_lines} の処理でエラーが発生したため、パイプラインを停止します")
            print(f"{'=' * 80}")
            sys.exit(1)
    
    print(f"\n{'=' * 80}")
    print("✓ パイプライン処理が全て正常に完了しました")
    print(f"  実行した-n値: {', '.join(map(str, num_lines_list))}")
    print(f"{'=' * 80}")


if __name__ == "__main__":
    main()

