CATEGORIES = [
    "金融业网络安全事件",
    "重大网络安全事件",
    "重大数据泄露事件",
    "重大漏洞风险提示",
    "其他",
]


def classify_prompt(title: str, summary: str) -> list[dict]:
    cats = "\n".join(f"- {c}" for c in CATEGORIES)
    return [
        {
            "role": "system",
            "content": (
                "你是一位网络安全新闻分类专家。请根据新闻标题和摘要，将其归入以下五个分类之一。\n"
                f"分类列表：\n{cats}\n\n"
                "只输出分类名称，不要添加任何解释。"
            ),
        },
        {"role": "user", "content": f"标题：{title}\n摘要：{summary}"},
    ]
