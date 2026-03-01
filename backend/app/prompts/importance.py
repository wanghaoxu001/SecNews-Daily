def importance_prompt(title: str, summary: str, category: str, examples: list[dict]) -> list[dict]:
    examples_text = ""
    for ex in examples:
        label = "重要" if ex["is_important"] else "不重要"
        examples_text += f"- 标题：{ex['title']}\n  摘要：{ex.get('summary', '')}\n  判定：{label}\n  理由：{ex.get('reason', '')}\n\n"

    return [
        {
            "role": "system",
            "content": (
                f"你是一位网络安全情报分析师，负责判断新闻对于「{category}」类别的重要性。\n\n"
                f"以下是该分类的典型样本供参考：\n{examples_text}\n"
                "请根据以上参考样本的标准，判断新的新闻是否重要。\n"
                "回答格式：\n"
                "重要: 是/否\n"
                "理由: 简短说明"
            ),
        },
        {
            "role": "user",
            "content": f"标题：{title}\n摘要：{summary}",
        },
    ]
