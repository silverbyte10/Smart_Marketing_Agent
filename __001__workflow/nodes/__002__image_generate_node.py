import datetime
import os

import dashscope
import requests
from dashscope import MultiModalConversation

from __001__workflow.agent_state import WorkflowAgentState
from common.config import Config
from common.path_utils import get_file_path

conf = Config()

dashscope.base_http_api_url = "https://dashscope.aliyuncs.com/api/v1"

DEFAULT_NEGATIVE_PROMPT = (
    "低分辨率，低画质，肢体畸形，手指畸形，画面过饱和，蜡像感，人脸无细节，"
    "过度光滑，画面具有AI感。构图混乱。文字模糊，扭曲。"
)


def _extract_image_url(response) -> str | None:
    """从百炼多模态返回中解析图片 URL。"""
    try:
        output = response.output
        if not output:
            return None
        choices = output.get("choices") or []
        if not choices:
            return None
        content = choices[0].get("message", {}).get("content") or []
        for item in content:
            if isinstance(item, dict) and item.get("image"):
                return item["image"]
        return None
    except (AttributeError, IndexError, KeyError, TypeError):
        return None


def _download_image(url: str, save_path: str) -> bool:
    """将远程图片下载到本地路径。"""
    try:
        dir_name = os.path.dirname(os.path.abspath(save_path))
        if dir_name:
            os.makedirs(dir_name, exist_ok=True)
        resp = requests.get(url, timeout=120)
        # 等待响应完成
        resp.raise_for_status()
        with open(save_path, "wb") as f:
            f.write(resp.content)
        return True
    except (OSError, requests.RequestException):
        return False


def generate_and_download_image(
    prompt: str,
    save_path: str,
    *,
    api_key: str | None = None,
    model: str = "qwen-image-2.0-pro",
    size: str = "2048*2048",
    negative_prompt: str = DEFAULT_NEGATIVE_PROMPT,
) -> bool:
    """
    根据提示词调用百炼生图，并将结果下载到 save_path。

    :param prompt: 生图提示词
    :param save_path: 图片保存的本地路径（含文件名）
    :return: 生图且下载均成功返回 True，否则 False
    """
    messages = [
        {
            "role": "user",
            "content": [{"text": prompt}],
        }
    ]

    response = MultiModalConversation.call(
        api_key=api_key or conf.BAILIAN_API_KEY,
        model=model,
        messages=messages,
        result_format="message",
        stream=False,
        watermark=False,
        prompt_extend=True,
        negative_prompt=negative_prompt,
        size=size,
    )

    if response.status_code != 200:
        return False

    image_url = _extract_image_url(response)
    if not image_url:
        return False

    return _download_image(image_url, save_path)


def generate_prompt(title: str, content: str, site: str) -> str:
    return (
        f"一幅围绕旅行探索主题创作的高质量图像，"
        f"画面展现与标题内容相关的旅行场景，如自然风光、城市街景、异国风情或户外探险，"
        f"构图中可以包含人物、交通工具、建筑或自然景观，"
        f"整体氛围充满冒险、自由与美好假期的感觉，色调明亮或富有层次，"
        f"背景可以是山川、海滩、森林、古城、夜景等，"
        f"表达放松、探索、享受生活的情绪。"
        f"图片描述地址为:{site}。"
        f"图片中不能有任何文字。"
        f"允许写实艺术风格，但需保证画面和谐美观、细节丰富。"
    )

def sanitize_title_for_filename(title: str) -> str:
    now = datetime.datetime.now()
    time_str = now.strftime("%Y%m%d%H%M%S")
    return time_str + title[:5] + ".png"


def toutiao_image_generator(toutiao_title, toutiao_content, toutiao_site):
    prompt = generate_prompt(toutiao_title, toutiao_content, toutiao_site)
    # 通过get_file_path 从相对路径获取绝对路径
    ouputpath = get_file_path(f"picture/{sanitize_title_for_filename(title=toutiao_title)}")
    # 生成并下载图片
    generate_and_download_image(prompt, ouputpath)
    return ouputpath



def image_generate_node(state: WorkflowAgentState):
    toutiao_title = state.get("toutiao_title", "")
    toutiao_content = state.get("toutiao_content", "")
    toutiao_site = state.get("toutiao_site", "")
    image_path = toutiao_image_generator(toutiao_title, toutiao_content, toutiao_site)

    state['toutiao_image_path_list'] = [image_path]
    print(f"图片生成成功: {image_path}")
    return state

if __name__ == "__main__":
    print(image_generate_node({"toutiao_title": "新疆天山", "toutiao_content": "新疆天山", "toutiao_site": "新疆天山"}))