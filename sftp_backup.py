"""
localサーバのデータをremoteサーバにアップロード処理を行う。
Programming by N.Goto 2025-03-22
使用条件
    1. localサーバからremoteサーバに秘密鍵でssh接続できること。
    2. remoteサーバにはバックアップファイル用のディレクトリが存在すること。
    3. ファイル名はremote側もlocal側もFullpathで指定すること。
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

    sftp_connect = None

    def __init__(self, host, port, user, auth_data):
        """クラスが生成された時に最初に呼ばれる
        - サーバ接続のためパスフレーズ無し
        """
        # 接続情報
        self.host = host
        self.port = port
        self.user = user
        self.key_file = auth_data["key_file"]
        self.passphrase = auth_data["passphrase"]
        # 自動バックアップ用にパスフレーズ無しに対応
        if self.passphrase == "":
            self.passphrase = None
        paramiko.util.log_to_file("/tmp/paramiko.log")
        # 秘密鍵による接続
        cc = self.create_connection(self.host, self.port, self.user, self.key_file, self.passphrase)
        if not cc:
            sys.exit(1)

    def __enter__(self):
        print("upload start")
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """修了した時に呼ばれる"""
        self.close()
        print("upload end")
        return True

    def create_connection(self, host, port, user, key_file, passphrase):
        """接続処理"""
        # パスフレーズで秘密鍵を読み込む
        rsa_key = paramiko.RSAKey.from_private_key_file(key_file, passphrase)
        try:
            transport = paramiko.Transport((host, port))
            transport.connect(username=user, pkey=rsa_key)
            self.sftp_connect = paramiko.SFTPClient.from_transport(transport)
            return True
        except paramiko.ssh_exception.SSHException as e:
            print(f"SSHエラーが発生しました: {e}")
            return False
        except paramiko.ssh_exception.AuthenticationException:
            print("認証エラー！秘密鍵が正しいか確認してください。")
            return False

    def is_file_exists(self, localpath):
        try:
            self.sftp_connect.stat(localpath)
            return True
        except IOError as e:
            print(e)
            return False

    def upload_file(self, remotepath, localpath):
        """アップロード処理"""
        try:
            self.sftp_connect.put(localpath, remotepath, callback=None)
        except IOError as e:
            print("Can't Upload " + e)

    def close(self):
        self.sftp_connect.close()


if __name__ == "__main__":
    """バックアップ処理
    usage
    $ python sftp_backup.py configファイル名
    自動バックアップするために、秘密鍵はパスフレーズ無しで作成しておく）

    config_file
    [DEFAULT]
    HOST = example.com
    PORT = port_number
    USER = user_name
    KEY_FILE = id_rsa
    PASSPHRASE = passphrase（「""」を設定で、パスフレーズ無しの秘密鍵に対応）
    REMOTE_PATH = remote_filename（LOCAL_PATHに日時を追加して、拡張子をzipに置き換えてアップロードする）
    LOCAL_PATH = local_filename（バックアップするファイル名）
    """
    # config_fileを読み込むためにargparseを設定する
    try:
        parser = argparse.ArgumentParser()
        parser.add_argument("config_file", help="設定ファイルのパスを指定してください。")
        args = parser.parse_args()
    except SystemExit:
        print("config fileが指定されていません!!")
        exit(-1)
    # configparserでコマンドライン引数で指定された設定ファイル（INIファイル）を読み込み
    # 【DEFAULT】セクションの設定値を変数に設定する
    auth_data = {}
    config_ini = configparser.ConfigParser()
    config_ini.read(args.config_file, encoding="utf-8")
    host = config_ini["DEFAULT"]["HOST"].strip()
    port = int(config_ini["DEFAULT"]["PORT"])
    user = config_ini["DEFAULT"]["USER"].strip()
    auth_data["key_file"] = config_ini["DEFAULT"]["KEY_FILE"].strip()
    auth_data["passphrase"] = config_ini["DEFAULT"]["PASSPHRASE"].replace('"', "").strip()

    # セクションごとのconfigデータを辞書に変換し、リストに格納（Listの内包表記）
    data_list = [
        {
            "section": section,  # セクション名（AUDIT, WAREHOUSE, FACILITY など）
            "REMOTE_PATH": config_ini.get(section, "REMOTE_PATH"),
            "LOCAL_PATH": config_ini.get(section, "LOCAL_PATH"),
        }
        for section in config_ini.sections()
    ]

    with SftpBackup(host, port, user, auth_data) as sftp_backup:
        for data_dict in data_list:
            # ファイルアップロード処理
            if os.path.exists(data_dict["LOCAL_PATH"]):
                """バックアップファイル名（remotepath）に日時を付加して拡張子zipで保存する"""
                date_str = datetime.now().strftime("%Y%m%d_%H%M%S")
                remotepath = str(Path(data_dict["REMOTE_PATH"]).with_suffix(""))
                remotepath = f"{remotepath}_{date_str}.zip"
                print(f"{data_dict['LOCAL_PATH']} -> {remotepath}")
                # バックアップ処理
                sftp_backup.upload_file(remotepath, data_dict["LOCAL_PATH"])
            else:
                print(f"バックアップする「{data_dict['LOCAL_PATH']}」が存在しません！")
