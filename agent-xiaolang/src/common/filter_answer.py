
def filterAnswer(content: str | dict) -> str:

  """过滤答案"""

  if isinstance(content, str):
    # 模型直接返回字符串
    answer = content
  else:
    # 模型返回内容块列表，只提取文本内容
    answer = "\n".join(
        block["text"]
        for block in content
        if isinstance(block, dict)
        and block.get("type") == "text"
        and isinstance(block.get("text"), str)
    )
  return answer