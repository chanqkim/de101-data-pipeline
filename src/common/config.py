import os

# logging configuration
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
LOG_DIR = os.path.join(BASE_DIR, "logs")
LOG_FILE_NAME = "data_pipeline.log"
LOG_FORMATER = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
LOG_LEVEL = "INFO"
LOG_MAX_BYTES = 10 * 1024 * 1024  # 10MB
LOG_FILE_BACKUP_COUNT = 30  # keep 30 backup log files (1 month)

# crawling related configuration
DEFAULT_HEADER = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}

# lol_champ_perf related configuration
LOL_CHAMP_PERF_FILE_DIR = os.path.join(BASE_DIR, "file_export/lol_champ_perf")
