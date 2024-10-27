import ftplib
import logging
import os
import time
from typing import Callable, Any

from config import Config


class FtpSync:
    config: Config
    ftpClient: ftplib.FTP
    fileCount: int
    downloadCount: int
    directoryCount: int
    totalBlocks: int

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
        number_of_files = 0
        number_of_directories = 0
        number_of_downloads = 0
        total_blocks = 0

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
                    self.directoryCount += 1
                    number_of_directories += 1
                    self.recursive_copy(os.path.join(working_dir, filename))
                elif details['type'] == 'file':
                    target_file = os.path.join(target_dir, filename)
                    self.fileCount += 1
                    number_of_files += 1

                    ftp_file_size = -1

                    if 'size' in details:
                        ftp_file_size = int(details['size'])
                        blocks = (
                                             ftp_file_size + self.config.ftpServer.blockSize - 1) // self.config.ftpServer.blockSize
                        total_blocks += blocks
                        self.totalBlocks += blocks

                    should_i_download = True

                    if os.path.isfile(target_file):
                        if ftp_file_size >= 0:
                            file_size = os.path.getsize(target_file)
                            if file_size == ftp_file_size:
                                should_i_download = False
                                # print(f'file exists {details["type"]}: {filename} ({working_dir})')

                    if should_i_download:
                        print(f'download {details["type"]}: {filename} ({working_dir})')
                        self.download_file(os.path.join(ftp_dir, filename), target_file)
                        self.downloadCount += 1
                        number_of_downloads += 1
        print(
            f'{working_dir}: {number_of_directories} directories, {number_of_files} files ({self.mb(total_blocks): .0f} MB ), {number_of_downloads} downloads')

    def mb(self, blocks: int) -> float:
        return blocks * self.config.ftpServer.blockSize / 1024.0 / 1024.0

    def sync(self):
        self.fileCount = 0
        self.downloadCount = 0
        self.directoryCount = 0
        self.totalBlocks = 0

        start_time = time.time()

        self.connect_to_ftp_tls()
        self.recursive_copy('')
        self.ftpClient.quit()

        end_time = time.time()
        elapsed_time = end_time - start_time

        hours = elapsed_time // 3600
        minutes = (elapsed_time % 3600) // 60
        seconds = elapsed_time % 60

        print()
        print(f"{self.directoryCount} directories")
        print(f"{self.fileCount} files, {self.mb(self.totalBlocks): .0f} MBytes")
        print(f"{self.downloadCount} files downloaded")
        print(f"Elapsed time: {hours:.0f} hours {minutes:.0f} minutes {seconds:.0f} seconds")
