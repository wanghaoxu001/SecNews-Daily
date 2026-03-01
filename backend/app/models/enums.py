import enum


class ProcessStatus(str, enum.Enum):
    pending = "pending"
    processing = "processing"
    processed = "processed"
    similarity_checked = "similarity_checked"
    completed = "completed"
    failed = "failed"


class NewsCategory(str, enum.Enum):
    financial_cyber = "金融业网络安全事件"
    major_cyber = "重大网络安全事件"
    data_breach = "重大数据泄露事件"
    vulnerability = "重大漏洞风险提示"
    other = "其他"


class BriefingStatus(str, enum.Enum):
    draft = "draft"
    published = "published"


class LlmTaskType(str, enum.Enum):
    default = "default"
    translate = "translate"
    summarize = "summarize"
    classify = "classify"
    similarity = "similarity"
    importance = "importance"
    embedding = "embedding"
