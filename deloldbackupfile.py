import os
from datetime import datetime, timedelta

# 対象ディレクトリ
target_dir = "./backup_sophiag"

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
        print(filename)

        # 拡張子を小文字化して比較してファイルの作成時刻を取得
        if ext.lower() in target_extensions:
            created_time = datetime.fromtimestamp(os.path.getctime(file_path))

        # しきい値よりも古ければ削除
        if created_time < threshold:
            print(f"Deleting {file_path} (created: {created_time})")
#            os.remove(file_path)
