"""
localサーバのデータをremoteサーバにアップロード処理を行う。
Programming by N.Goto 2025-03-22
使用条件
    1. localサーバからremoteサーバに秘密鍵でssh接続できること。
    2. remoteサーバにはバックアップファイル用のディレクトリが存在すること。
    3. ファイル名はremote側もlocal側もFullpathで指定すること。
    4. バックアップファイルが貯まる一方なので、整理を忘れないこと。
"""

import argparse
import configparser
import os
import sys
from datetime import datetime
from pathlib import Path

import paramiko


class SftpBackup:
    """ssh接続でファイルをuploadするクラス
    http://docs.paramiko.org/en/3.2/api/sftp.html
    https://medium.com/@thapa.parmeshwor/sftp-upload-and-download-using-python-paramiko-a594e81cbcd8
    """

    def __init__(self, host, port, user, auth_data):
        """クラスが生成された時に最初に呼ばれる
        - ここで、remoteサーバへ秘密鍵によるssh接続させる.
        - サーバ接続のためパスフレーズ無し.
        """
        self.host = host
        self.port = port
        self.user = user
        self.key_file = auth_data["key_file"]
        self.passphrase = auth_data.get("passphrase") or None  # None対応簡略化
        self.sftp_connect = None

        paramiko.util.log_to_file("/tmp/paramiko.log")
        if not self.create_connection():
            sys.exit(1)

    def __enter__(self):
        print("Upload start")
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()
        print("Upload finished.")
        return False  # エラーを伝搬する（Trueにすると例外を握りつぶすので注意）

    def create_connection(self):
        """SFTP接続を確立する"""
        try:
            rsa_key = paramiko.RSAKey.from_private_key_file(self.key_file, self.passphrase)
            transport = paramiko.Transport((self.host, self.port))
            transport.connect(username=self.user, pkey=rsa_key)
            self.sftp_connect = paramiko.SFTPClient.from_transport(transport)
            return True
        except paramiko.AuthenticationException:
            print("認証エラー: 秘密鍵やユーザー情報を確認してください。")
        except paramiko.SSHException as e:
            print(f"SSHエラーが発生しました: {e}")
        except Exception as e:
            print(f"予期しないエラー: {e}")
        return False

    def upload_file(self, remotepath, localpath):
        """ファイルをアップロードする"""
        try:
            self.sftp_connect.put(localpath, remotepath)
            print(f"Uploaded {localpath} to {remotepath}")
        except IOError as e:
            print(f"アップロード失敗: {e}")

    def close(self):
        if self.sftp_connect:
            self.sftp_connect.close()


def parse_config(config_path):
    """設定ファイルを読み込み、接続情報とアップロード対象リストを返す
    usage
    $ python sftp_backup.py configファイル名
    自動バックアップするために、秘密鍵はパスフレーズ無しで作成しておく）
    ---------------------------
    config_file
    [DEFAULT]
    HOST = example.com
    PORT = port_number
    USER = user_name
    KEY_FILE = id_rsa
    PASSPHRASE = ""（パスフレーズ無しの秘密鍵に対応）
    REMOTE_PATH = remote_filename（LOCAL_PATHに日時を追加して、拡張子をzipに置き換えてアップロードする）
    LOCAL_PATH = local_filename（バックアップするfullpathのファイル名）
    """
    config = configparser.ConfigParser()
    config.read(config_path, encoding="utf-8")

    auth_data = {
        "key_file": config["DEFAULT"]["KEY_FILE"].strip(),
        "passphrase": config["DEFAULT"]["PASSPHRASE"].replace('"', "").strip(),
    }

    host = config["DEFAULT"]["HOST"].strip()
    port = int(config["DEFAULT"]["PORT"])
    user = config["DEFAULT"]["USER"].strip()

    backup_targets = [
        {
            "section": section,
            "REMOTE_PATH": config.get(section, "REMOTE_PATH"),
            "LOCAL_PATH": config.get(section, "LOCAL_PATH"),
        }
        for section in config.sections()
    ]

    return host, port, user, auth_data, backup_targets


def main():
    parser = argparse.ArgumentParser(description="SFTP自動バックアップツール")
    parser.add_argument("config_file", help="設定ファイル(.ini)のパスを指定してください。")
    args = parser.parse_args()

    if not os.path.exists(args.config_file):
        print(f"設定ファイルが見つかりません: {args.config_file}")
        sys.exit(1)

    host, port, user, auth_data, backup_targets = parse_config(args.config_file)

    with SftpBackup(host, port, user, auth_data) as sftp_backup:
        for target in backup_targets:
            local_path = target["LOCAL_PATH"]
            if os.path.exists(local_path):
                date_str = datetime.now().strftime("%Y%m%d_%H%M%S")
                base_remote = str(Path(target["REMOTE_PATH"]).with_suffix(""))
                remote_path = f"{base_remote}_{date_str}.zip"
                print(f"{local_path} -> {remote_path}")
                sftp_backup.upload_file(remote_path, local_path)
            else:
                print(f"バックアップ対象ファイルが存在しません: {local_path}")


if __name__ == "__main__":
    main()
