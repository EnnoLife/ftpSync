import sys

from loguru import logger

from config import Config
from ftp_sync import FtpSync

if __name__ == '__main__':
    # main()
    cfg = Config.from_yaml('config.yaml')

    logger.configure(
        handlers=[{"sink": sys.stderr, "level": 'DEBUG'}],  # Change 'WARNING' to your desired level
    )
    # logger.add(cfg.logging.log_file, level=cfg.logging.level, format=cfg.logging.format)

    ftp_sync = FtpSync(cfg)
    ftp_sync.sync()
