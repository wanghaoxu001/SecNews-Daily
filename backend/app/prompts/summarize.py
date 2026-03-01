def summarize_prompt(content: str) -> list[dict]:
    return [
        {
            "role": "system",
            "content": (
                "你是一位网络安全领域的新闻编辑。请根据以下新闻正文，生成一段简洁的中文摘要（100-200字）。"
                "摘要应包含：事件核心内容、涉及的组织/产品、影响范围。只输出摘要，不要添加标题或多余说明。"
            ),
        },
        {"role": "user", "content": content},
    ]
