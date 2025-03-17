import argparse
import configparser
import os
import sys

import paramiko


def createDir(remotepath, localpath, dirs_list):
    for dir_path in dirs_list:
        dir_name = dir_path.replace(remotepath, "")
        local_dir = localpath + dir_name
        os.makedirs(local_dir, exist_ok=True)


class SftpBackup:
    """ssh接続してバックアップするクラス
    http://docs.paramiko.org/en/3.2/api/sftp.html
    https://medium.com/@thapa.parmeshwor/sftp-upload-and-download-using-python-paramiko-a594e81cbcd8
    """

    sftp_connect = None
    ssh_connect = None
    files = []
    dirs = []

    def __init__(self, host, port, user, auth_data):
        """クラスが生成された時に最初に呼ばれる"""
        # 接続情報
        self.host = host
        self.port = port
        self.user = user
        self.key_file = auth_data["key_file"]
        self.passphrase = auth_data["passphrase"]
        paramiko.util.log_to_file("/tmp/paramiko.log")
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
            print(f"❌ SSHエラーが発生しました: {e}")
            return False
        except paramiko.ssh_exception.AuthenticationException:
            print("❌ 認証エラー！秘密鍵が正しいか確認してください。")
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
    """ config_file
    [DEFAULT]
    HOST = example.com
    PORT = port_number
    USER = user_name
    KEY_FILE = id_rsa
    PASSPHRASE = passphrase
    REMOTE_PATH = remote_filename
    LOCAL_PATH = local_filename
    """
    # argparser
    parser = argparse.ArgumentParser()
    parser.add_argument("config_file")
    args = parser.parse_args()
    # read config_file
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

    # create sftpclient object.
    with SftpBackup(host, port, user, auth_data) as sftp_backup:
        # ----------------------------------------------------------
        # ファイルアップロード
        # ----------------------------------------------------------
        if os.path.exists(localpath):
            sftp_backup.upload_file(remotepath, localpath)
