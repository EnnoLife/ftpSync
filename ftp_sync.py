import ftplib
import logging
import os
from typing import Callable, Any

from config import Config


class FtpSync:
    config: Config
    ftpClient: ftplib.FTP

    def __init__(self, config: Config):
        self.config = config

    def connect_to_ftp(self):
        self.ftpClient = ftplib.FTP(self.config.ftpServer.host)
        self.ftpClient.login(self.config.ftpServer.username, self.config.ftpServer.password)
        self.ftpClient.set_pasv(True)  # Enable passive mode

    def connect_to_ftp_tls(self):
        logging.info(f'Connecting to FTP server: {self.config.ftpServer.host}')
        client = ftplib.FTP_TLS(self.config.ftpServer.host)
        client.login(self.config.ftpServer.username, self.config.ftpServer.password)
        client.prot_p()  # Switch to protected mode
        client.set_pasv(True)  # Enable passive mode
        self.ftpClient = client

    def download_file(self, remote_file, local_file):
        with open(local_file, 'wb') as f:
            self.ftpClient.retrbinary('RETR ' + remote_file, f.write)

    def upload_file(self, local_file, remote_file):
        with open(local_file, 'rb') as f:
            self.ftpClient.storbinary('STOR ' + remote_file, f)

    def list_directory_details(self, directory='/', callback: Callable[[str, dict[str, Any]], str] | None = None):
        file_list = self.ftpClient.mlsd(directory)
        for file_info in file_list:
            filename, details = file_info
            if callback is not None:
                callback(filename, details)
            else:
                print(filename)
                for key, value in details.items():
                    print(f"  {key}: {value}")

    def list_directory(self, directory='/'):
        file_list = self.ftpClient.nlst(directory)
        leading = len(directory) + 1
        for file in file_list:
            print(file[leading:])

    def recursive_copy(self, working_dir: str):
        if working_dir == '':
            ftp_dir = self.config.ftpServer.basedir
            target_dir = self.config.targetDir
        else:
            ftp_dir = os.path.join(self.config.ftpServer.basedir, working_dir)
            target_dir = os.path.join(self.config.targetDir, working_dir)

        file_list = self.ftpClient.mlsd(ftp_dir)
        for file_info in file_list:
            filename, details = file_info

            if 'type' in details:
                if details['type'] == 'dir':
                    stored_dir = os.path.join(target_dir, filename)

                    os.makedirs(stored_dir, 0o755, exist_ok=True)
                    self.recursive_copy(os.path.join(working_dir, filename))
                elif details['type'] == 'file':
                    target_file = os.path.join(target_dir, filename)

                    if os.path.isfile(target_file):
                        print(f'file exists {details["type"]}: {filename} ({working_dir})')
                    else:
                        print(f'download {details["type"]}: {filename} ({working_dir})')
                        self.download_file(os.path.join(ftp_dir, filename), target_file)




    def handler(self, filename: str, details: dict[str, Any]):
        if 'type' in details:
            if details['type'] == 'dir':
                print(filename)

    def sync(self):
        self.connect_to_ftp_tls()
        self.recursive_copy('')
        self.ftpClient.quit()
