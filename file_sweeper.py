import argparse
import os
from datetime import datetime, timedelta

"""
# 対象ディレクトリ
target_dir = "/home/ngoto/backup_sophiag"

# 対象とする拡張子（小文字で指定、複数指定もOK！）
target_extensions = [
    ".zip",
]

# しきい値（ここでは3ヶ月前）
threshold = datetime.now() - timedelta(days=90)

# ディレクトリ内のファイルをすべて見る
for filename in os.listdir(target_dir):
    file_path = os.path.join(target_dir, filename)

    if os.path.isfile(file_path):
        # ファイルの拡張子を取得
        _, ext = os.path.splitext(filename)

        # 拡張子を小文字化して比較してファイルの作成時刻を取得
        if ext.lower() in target_extensions:
            created_time = datetime.fromtimestamp(os.path.getctime(file_path))

        # しきい値よりも古ければ削除
        if created_time < threshold:
            print(f"Deleting {file_path} (created: {created_time})")
            os.remove(file_path)
"""


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
    parser = argparse.ArgumentParser(description="Sweep old files safely.")
    parser.add_argument("--target_dir", type=str, required=True, help="Target directory to clean.")
    parser.add_argument(
        "--extensions", type=str, nargs="*", default=[], help="File extensions to target (e.g., .log .txt)."
    )
    parser.add_argument(
        "--days_old", type=int, default=90, help="Delete files older than this number of days (default: 90)."
    )
    parser.add_argument(
        "--dry_run",
        action="store_true",
        help="If set, do not actually delete files, just show what would be deleted.",
    )
    return parser.parse_args()


def main():
    args = parse_args()

    sweeper = FileSweeper(
        target_dir=args.target_dir, extensions=args.extensions, days_old=args.days_old, dry_run=args.dry_run
    )
    sweeper.sweep()


if __name__ == "__main__":
    main()
