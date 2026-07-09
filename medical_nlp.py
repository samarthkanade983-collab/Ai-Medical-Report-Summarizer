"""
Medical-oriented extractive summarization: sentence-level TF-IDF + clinical keyword weighting.
"""
import re
from sklearn.feature_extraction.text import TfidfVectorizer

# Boost sentences that contain clinically salient terms (case-insensitive)
_CLINICAL_TERMS = re.compile(
    r"\b("
    r"glucose|hemoglobin|hba1c|a1c|cholesterol|ldl|hdl|triglyceride|tsh|t3|t4|"
    r"vitamin\s*d|wbc|rbc|platelet|creatinine|bun|gfr|egfr|"
    r"blood\s*pressure|bp\b|systolic|diastolic|heart\s*rate|hr\b|bpm|"
    r"impression|diagnosis|finding|abnormal|normal|elevated|reduced|"
    r"recommend|follow[- ]?up|refer|mri|ct\b|x-?ray|ultrasound|"
    r"infarct|ischemia|fracture|tumor|lesion|edema|atrophy"
    r")\b",
    re.IGNORECASE,
)


def _sentences(text: str) -> list:
    t = (text or "").strip()
    if not t:
        return []
    parts = re.split(r"(?<=[.!?])\s+|\n+", t)
    return [s.strip() for s in parts if len(s.strip()) > 15]


def medical_extractive_summarize(text: str, max_sentences: int = 5) -> str:
    """
    Rank sentences by TF-IDF term importance plus clinical-keyword and position bonuses.
    """
    sents = _sentences(text)
    if not sents:
        return (text or "").strip() or "No text to summarize."
    if len(sents) <= max_sentences:
        return " ".join(sents)

    try:
        vec = TfidfVectorizer(
            max_features=min(4096, max(64, len(sents) * 8)),
            stop_words="english",
            ngram_range=(1, 2),
            sublinear_tf=True,
        )
        mat = vec.fit_transform(sents)
        importance = mat.max(axis=1).A.ravel()
    except Exception:
        importance = [1.0] * len(sents)

    n = len(sents)
    scores = []
    for i, sent in enumerate(sents):
        kw = len(_CLINICAL_TERMS.findall(sent))
        pos = 1.0
        if i == 0 or i == n - 1:
            pos = 1.12
        elif i < n * 0.15 or i > n * 0.85:
            pos = 1.06
        score = float(importance[i]) * (1.0 + 0.18 * min(kw, 6)) * pos
        scores.append((score, i))

    scores.sort(key=lambda x: (-x[0], x[1]))
    picked = sorted({i for _, i in scores[:max_sentences]})
    return " ".join(sents[i] for i in picked)


def structured_value_lines(extracted_params: dict) -> str:
    if not extracted_params:
        return ""
    lines = [f"- {k}: {v}" for k, v in extracted_params.items()]
    return "KEY LAB VALUES (from parser):\n" + "\n".join(lines)
