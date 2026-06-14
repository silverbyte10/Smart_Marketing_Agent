"""
百度图片爬虫工具

【整体流程】（老师可按此顺序讲解）
    1. build_baidu_travel_keyword  → 拼搜索词，如「湖北荆州旅行」
    2. search_baidu_image_urls     → 请求百度接口，拿到图片 URL 列表
    3. download_remote_image       → 把单张图片保存到本地
    4. download_baidu_images       → 组合 2 + 3，批量下载

【百度图片搜索接口】
    地址: https://image.baidu.com/search/acjson
    方式: GET，浏览器 F12 网络面板可看到同样请求
    返回: JSON，data 字段里是图片信息列表
"""

import json
import os
import re

import requests

# ---------- 常量配置 ----------
BAIDU_IMAGE_SEARCH_URL = "https://image.baidu.com/search/acjson"
DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Referer": "https://image.baidu.com/",
    "Accept": "application/json, text/javascript, */*; q=0.01",
}
# 百度接口里常见的图片地址字段，按优先级依次尝试
IMAGE_URL_KEYS = ("middleURL", "thumbURL", "hoverURL", "objURL")


def build_baidu_travel_keyword(site: str, fallback: str = "") -> str:
    """
    Step 1：构造搜索关键词。

    规则：取地点名称，末尾补上「旅行」。
    例：site="湖北荆州" → "湖北荆州旅行"
    """
    address = (site or fallback or "").strip()
    if not address:
        return "旅行"
    if address.endswith("旅行"):
        return address
    return f"{address}旅行"


def search_baidu_image_urls(keyword: str, max_count: int = 4) -> list[str]:
    """
    Step 2：按关键词搜索，返回图片 URL 列表。

    分页说明：pn=起始序号，rn=每页条数；不够就翻页继续取。
    """
    if not keyword or max_count <= 0:
        return []

    urls: list[str] = []
    page_start = 0      # 从第几张开始（分页偏移）
    page_size = 30      # 每页请求数量

    # 循环翻页，直到凑够 max_count 或没有更多结果
    while len(urls) < max_count and page_start < 90:
        # 构造请求参数（核心：word/queryWord 是搜索词，pn/rn 是分页）
        params = {
            "tn": "resultjson_com",
            "word": keyword,
            "queryWord": keyword,
            "pn": page_start,
            "rn": page_size,
            "ie": "utf-8",
            "oe": "utf-8",
        }
        # 构建并发起请求
        resp = requests.get(
            BAIDU_IMAGE_SEARCH_URL,
            params=params,
            headers=DEFAULT_HEADERS,
            timeout=30,
        )
        # 根据返回码抛出异常
        resp.raise_for_status()

        # 解析 JSON，从每条记录里提取图片 URL
        items = _parse_search_response(resp.text)
        if not items:
            break

        for item in items:
            url = _extract_image_url(item)
            if url and url not in urls:
                urls.append(url)
                if len(urls) >= max_count:
                    break

        if len(items) < page_size:
            break
        page_start += page_size

    return urls[:max_count]


def download_remote_image(url: str, save_path: str) -> bool:
    """
    Step 3：下载单张图片到本地。

    :return: 成功 True，失败 False（网络异常、非图片等）
    """
    try:
        os.makedirs(os.path.dirname(os.path.abspath(save_path)), exist_ok=True)
        resp = requests.get(url, headers=DEFAULT_HEADERS, timeout=60)
        resp.raise_for_status()
        with open(save_path, "wb") as f:
            f.write(resp.content)
        return True
    except (OSError, requests.RequestException):
        return False


def download_baidu_images(
    keyword: str,
    save_paths: list[str],
    *,
    max_count: int | None = None,
) -> list[str]:
    """
    Step 4：搜索并批量下载（组合 Step 2 + Step 3）。

    :param keyword: 搜索关键词
    :param save_paths: 本地保存路径列表，与下载数量一一对应
    :return: 成功下载的路径列表
    """
    limit = min(max_count or len(save_paths), len(save_paths), 4)
    if limit <= 0:
        return []
    # 获取图片图片链接
    urls = search_baidu_image_urls(keyword, max_count=limit)
    saved: list[str] = []
    for url, path in zip(urls, save_paths[:limit]):
        if download_remote_image(url, path):
            saved.append(path)
    return saved


# ---------- 内部辅助函数（学生了解即可） ----------


def _parse_search_response(text: str) -> list[dict]:
    """解析百度 acjson 返回文本为图片信息列表。"""
    text = text.replace("\\'", "'")
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        # 百度偶尔返回不规范 JSON，用正则兜底提取 data 数组
        match = re.search(r'"data"\s*:\s*(\[.*\])\s*[,}]', text, re.S)
        if not match:
            return []
        payload = {"data": json.loads(match.group(1))}
    return [item for item in (payload.get("data") or []) if isinstance(item, dict)]


def _extract_image_url(item: dict) -> str | None:
    """从单条搜索结果里取出可用的 http(s) 图片地址。"""
    for key in IMAGE_URL_KEYS:
        url = item.get(key)
        if url and isinstance(url, str) and url.startswith(("http://", "https://")):
            return url
    return None
