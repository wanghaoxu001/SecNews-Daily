import logging
import jieba

logger = logging.getLogger(__name__)


def tokenize(text: str) -> list[str]:
    """Tokenize text using jieba for Chinese, simple split for others."""
    words = jieba.lcut(text)
    return [w.strip().lower() for w in words if len(w.strip()) > 1]


def tfidf_cosine_similarity(text_a: str, text_b: str) -> float:
    """Calculate TF-IDF based cosine similarity between two texts."""
    tokens_a = tokenize(text_a)
    tokens_b = tokenize(text_b)

    if not tokens_a or not tokens_b:
        return 0.0

    # Build vocabulary
    vocab = set(tokens_a) | set(tokens_b)

    # Term frequency
    tf_a = {w: tokens_a.count(w) / len(tokens_a) for w in vocab}
    tf_b = {w: tokens_b.count(w) / len(tokens_b) for w in vocab}

    # Cosine similarity
    dot = sum(tf_a.get(w, 0) * tf_b.get(w, 0) for w in vocab)
    norm_a = sum(v ** 2 for v in tf_a.values()) ** 0.5
    norm_b = sum(v ** 2 for v in tf_b.values()) ** 0.5

    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)
