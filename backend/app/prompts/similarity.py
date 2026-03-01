def similarity_prompt(news_title: str, news_summary: str, candidate_title: str, candidate_summary: str) -> list[dict]:
    return [
        {
            "role": "system",
            "content": (
                "你是一位网络安全新闻去重专家。请判断以下两条新闻是否报道了同一事件或高度相似的内容。\n"
                "回答格式：\n"
                "相似: 是/否\n"
                "理由: 简短说明"
            ),
        },
        {
            "role": "user",
            "content": (
                f"新闻A：\n标题：{news_title}\n摘要：{news_summary}\n\n"
                f"新闻B：\n标题：{candidate_title}\n摘要：{candidate_summary}"
            ),
        },
    ]
