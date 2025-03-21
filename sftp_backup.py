import argparse
import configparser
import os
import sys
from datetime import datetime
from pathlib import Path

import paramiko


def createDir(remotepath, localpath, dirs_list):
    for dir_path in dirs_list:
        dir_name = dir_path.replace(remotepath, "")
        local_dir = localpath + dir_name
        os.makedirs(local_dir, exist_ok=True)


class SftpBackup:
    """ssh接続でファイルをuploadするクラス
    http://docs.paramiko.org/en/3.2/api/sftp.html
    https://medium.com/@thapa.parmeshwor/sftp-upload-and-download-using-python-paramiko-a594e81cbcd8
    """

    sftp_connect = None
    ssh_connect = None
    files = []
    dirs = []

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
            print("Can't Download " + e)

    def close(self):
        self.sftp_connect.close()


if __name__ == "__main__":
    """バックアップ処理
    usage
    $ python sftp_backup.py configファイル名
    - config_file
    [DEFAULT]
    HOST = example.com
    PORT = port_number
    USER = user_name
    KEY_FILE = id_rsa
    PASSPHRASE = passphrase（自動バックアップするなら、パスフレーズ無しで秘密鍵を作成する）
    REMOTE_PATH = remote_filename（バックアップ側のフルパスファイル名）
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
    # コマンドライン引数で指定された設定ファイル（INIファイル）を読み込み
    # DEFAULTセクションの設定値を変数に設定する
    auth_data = {}
    config_ini = configparser.ConfigParser()
    config_ini.read(args.config_file, encoding="utf-8")
    host = config_ini["DEFAULT"]["HOST"].strip()
    port = int(config_ini["DEFAULT"]["PORT"])
    user = config_ini["DEFAULT"]["USER"].strip()
    remotepath = config_ini["DEFAULT"]["REMOTE_PATH"].strip()
    localpath = config_ini["DEFAULT"]["LOCAL_PATH"].strip()
    auth_data["key_file"] = config_ini["DEFAULT"]["KEY_FILE"].strip()
    auth_data["passphrase"] = config_ini["DEFAULT"]["PASSPHRASE"].replace('"', "").strip()

    with SftpBackup(host, port, user, auth_data) as sftp_backup:
        # ----------------------------------------------------------
        # ファイルアップロード処理
        # ----------------------------------------------------------
        if os.path.exists(localpath):
            """バックアップファイル名（remotepath）に日時を付加して拡張子zipで保存する"""
            date_str = datetime.now().strftime("%Y%m%d_%H%M%S")
            remotepath = str(Path(remotepath).with_suffix(""))
            remotepath = f"{remotepath}_{date_str}.zip"
            # バックアップ処理
            sftp_backup.upload_file(remotepath, localpath)
        else:
            print(f"{localpath}が存在しません")
