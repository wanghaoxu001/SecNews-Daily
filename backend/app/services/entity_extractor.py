import re
import logging

logger = logging.getLogger(__name__)

CVE_PATTERN = re.compile(r"CVE-\d{4}-\d{4,7}", re.IGNORECASE)
# Common org/product patterns
ORG_KEYWORDS = re.compile(
    r"(?:Microsoft|Google|Apple|Amazon|Meta|Cisco|Fortinet|Palo Alto|VMware|Adobe|"
    r"Oracle|SAP|IBM|Huawei|Alibaba|Tencent|Baidu|Samsung|Intel|AMD|NVIDIA|"
    r"Apache|Linux|Windows|Android|iOS|Chrome|Firefox|WordPress|Jenkins|"
    r"SolarWinds|CrowdStrike|Mandiant|Kaspersky|Sophos|McAfee|Symantec)",
    re.IGNORECASE,
)


def extract_entities(text: str) -> set[str]:
    """Extract CVEs, organization names, and product names from text."""
    entities = set()
    # CVEs
    entities.update(CVE_PATTERN.findall(text))
    # Orgs/Products
    entities.update(m.group() for m in ORG_KEYWORDS.finditer(text))
    return {e.lower() for e in entities}


def entity_overlap_score(entities_a: set[str], entities_b: set[str]) -> float:
    """Calculate Jaccard similarity between two entity sets."""
    if not entities_a or not entities_b:
        return 0.0
    intersection = entities_a & entities_b
    union = entities_a | entities_b
    return len(intersection) / len(union)
