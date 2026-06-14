import os

from dotenv import load_dotenv

from common.path_utils import get_file_path


load_dotenv(get_file_path(".env"))

class Config:
    def __init__(self):
        self.MODEL_BASE_URL = os.getenv("MODEL_BASE_URL")
        self.MODEL_NAME = os.getenv("MODEL_NAME")

        self.BAILIAN_API_KEY = os.getenv("BAILIAN_API_KEY")

        # 配图来源：ai（百炼生图）| baidu（百度图片下载）
        self.IMAGE_SOURCE = os.getenv("IMAGE_SOURCE", "ai").strip().lower()

if __name__ == "__main__":
    config = Config()
    print(config.MODEL_BASE_URL)
    print(config.MODEL_NAME)