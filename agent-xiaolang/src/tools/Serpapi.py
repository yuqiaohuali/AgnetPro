import os
import requests

from langchain_core.tools import tool
from dotenv import load_dotenv

load_dotenv()

# 外网实时查询工具（这里使用google查询）
@tool
def serpapi_search(query: str) -> str:
    """
    搜索互联网信息。
    只有需要了解实时信息或不知道的事情的时候才会使用这个工具
    """

    api_key = os.getenv("SERPAPI_API_KEY")
    base_url: str = os.getenv("SERPAPI_BASE_URL") or ""

    if not api_key:
        return "SerpAPI API Key 未配置"

    try:
        response = requests.get(
            base_url,
            params={
                "engine": "google",
                "q": query,
                "api_key": api_key,
                "num": 5,
                "hl": "zh-cn",
            },
            timeout=15,
        )

        print(f"serpapi搜索，GET：{base_url}")

        response.raise_for_status()

        data = response.json()

        if data.get("error"):
            return f"搜索失败：{data['error']}"

        # 提取自然搜索结果
        results = data.get("organic_results", [])

        if not results:
            return "未搜索到相关结果"

        # print(f"serpapi结果：{results}")

        # 格式化结果
        content = []

        for item in results:
            content.append(
                f"标题：{item.get('title', '')}\n"
                f"链接：{item.get('link', '')}\n"
                f"摘要：{item.get('snippet', '')}"
            )

        return "\n\n".join(content)

    except requests.RequestException as e:
        return f"SerpAPI 请求失败：{e}"