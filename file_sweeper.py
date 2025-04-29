import argparse
import os
from datetime import datetime, timedelta


class FileSweeper:
    def __init__(self, target_dir, extensions=None, days_old=90, dry_run=False):
        self.target_dir = target_dir
        self.extensions = [ext.lower() for ext in (extensions or [])]
        self.threshold = datetime.now() - timedelta(days=days_old)
        self.dry_run = dry_run

    def should_delete(self, file_path):
        if not os.path.isfile(file_path):
            return False

        _, ext = os.path.splitext(file_path)
        if self.extensions and ext.lower() not in self.extensions:
            return False

        created_time = datetime.fromtimestamp(os.path.getctime(file_path))
        return created_time < self.threshold

    def delete_file(self, file_path):
        if self.dry_run:
            print(f"[DRY-RUN] Would send to trash: {file_path}")
        else:
            print(f"Sending to trash: {file_path}")
            os.remove(file_path)

    def sweep(self):
        for filename in os.listdir(self.target_dir):
            file_path = os.path.join(self.target_dir, filename)

            if self.should_delete(file_path):
                self.delete_file(file_path)


def parse_args():
    # ヘルプ画面での説明文を設定しながらargparseのインスタンスを生成
    parser = argparse.ArgumentParser(description="Sweep old files safely.")

    # (1) target_dir引数の設定
    parser.add_argument("--target_dir", type=str, required=True, help="Target directory to clean.")

    # (2) extension（削除するファイルの拡張子）引数の設定 
    parser.add_argument(
        "--extensions", type=str, nargs="*", default=[], help="File extensions to target (e.g., .log .txt)."
    )

    # (3) days_old（削除するファイルの作成日。デフォルトは90日以前）
    parser.add_argument(
        "--days_old", type=int, default=90, help="Delete files older than this number of days (default: 90)."
    )

    # (4) dry_run（テスト用引数）
    parser.add_argument(
        "--dry_run",
        action="store_true",
        help="If set, do not actually delete files, just show what would be deleted.",
    )
    return parser.parse_args()


def main():
    # コマンドライン引数の読み込み・解析
    args = parse_args()

    # FileSweeperクラスのインスタンス生成
    sweeper = FileSweeper(
        target_dir=args.target_dir, extensions=args.extensions, days_old=args.days_old, dry_run=args.dry_run
    )
    sweeper.sweep()


if __name__ == "__main__":
    main()
