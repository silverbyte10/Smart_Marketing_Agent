"""
工作流节点：百度图片下载

【节点流程】
    读取 state（标题、地点）
        ↓
    构造搜索词 + 本地保存路径
        ↓
    调用 baidu_image_utils 搜索并下载
        ↓
    写回 state["toutiao_image_path_list"]
"""

import datetime

from __001__workflow.agent_state import WorkflowAgentState
from common.baidu_image_utils import build_baidu_travel_keyword, download_baidu_images
from common.path_utils import get_file_path

# 每次最多下载 4 张配图
BAIDU_MAX_IMAGES = 4


def _make_save_path(title: str, index: int) -> str:
    """生成保存路径：picture/时间戳+标题前5字_序号.png"""
    time_str = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    filename = f"{time_str}{title[:5]}_{index}.png"
    return get_file_path(f"picture/{filename}")


def toutiao_baidu_image_downloader(toutiao_title: str, toutiao_site: str) -> list[str]:
    """
    业务入口：根据头条标题和地点，从百度下载配图。

    1. 搜索词 = 地点 + 「旅行」
    2. 预生成 4 个本地路径
    3. 搜索并下载，返回成功的路径列表
    """
    # 获取搜索关键词，fallback，备选关键词
    keyword = build_baidu_travel_keyword(toutiao_site, fallback=toutiao_title)
    # 生成保存路径
    save_paths = [_make_save_path(toutiao_title, i + 1) for i in range(BAIDU_MAX_IMAGES)]
    # 下载百度图片
    saved = download_baidu_images(keyword, save_paths, max_count=BAIDU_MAX_IMAGES)
    print(f"百度图片搜索关键词: {keyword}，成功下载 {len(saved)} 张")
    return saved


def baidu_image_download_node(state: WorkflowAgentState):
    """LangGraph 节点：从 state 取参数，下载图片后写回 state。"""
    toutiao_title = state.get("toutiao_title", "")
    toutiao_site = state.get("toutiao_site", "")

    image_path_list = toutiao_baidu_image_downloader(toutiao_title, toutiao_site)
    state["toutiao_image_path_list"] = image_path_list

    if image_path_list:
        print(f"百度图片下载成功: {image_path_list}")
    else:
        print("百度图片下载失败，路径列表为空")
    return state


if __name__ == "__main__":
    # 本地测试：直接运行此文件即可
    print(
        baidu_image_download_node(
            {
                "toutiao_title": "湖北荆州",
                "toutiao_site": "湖北荆州",
            }
        )
    )
