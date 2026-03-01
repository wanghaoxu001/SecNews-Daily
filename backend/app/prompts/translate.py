def translate_prompt(text: str, target_lang: str = "中文") -> list[dict]:
    return [
        {
            "role": "system",
            "content": f"你是一个专业翻译，请将以下文本翻译成{target_lang}。只输出翻译结果，不要添加任何解释。",
        },
        {"role": "user", "content": text},
    ]
