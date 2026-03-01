def similarity_prompt(news_title: str, news_summary: str, candidate_title: str, candidate_summary: str) -> list[dict]:
    return [
        {
            "role": "system",
            "content": (
                "你是一位网络安全新闻去重专家。请判断以下两条新闻是否报道了同一事件或高度相似的内容。\n"
                "你必须仅返回一个 JSON 对象，不要返回 Markdown 代码块，不要输出额外解释。\n"
                'JSON 格式如下：{"is_similar": true/false, "reason": "简短说明"}'
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
