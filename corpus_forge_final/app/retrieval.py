import math
import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from typing import Any

STOPWORDS = {
    "the", "a", "an", "and", "or", "of", "to", "in", "is", "are", "for", "with", "on",
    "this", "that", "it", "as", "by", "from", "be", "was", "were", "at", "which", "into",
    "about", "what", "how", "why", "when", "where", "who", "does", "do", "did", "can", "could",
    "should", "would", "i", "you", "we", "they", "their", "our", "your", "not", "no", "yes"
}

DEFAULT_CHUNK_SIZE = 170
DEFAULT_OVERLAP = 45
GENERIC_OVERVIEW_TERMS = {
    "summarize", "summary", "overview", "explain", "describe", "purpose", "main", "idea",
    "ideas", "file", "document", "code", "does", "do", "about", "work", "works"
}


@dataclass(frozen=True)
class RetrievalCandidate:
    document: str
    chunk: str
    score: float
    strategy: str
    chunk_index: int
    start_word: int
    end_word: int
    matched_terms: tuple[str, ...]
    confidence: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "document": self.document,
            "chunk": self.chunk,
            "score": round(self.score, 3),
            "strategy": self.strategy,
            "chunk_index": self.chunk_index,
            "start_word": self.start_word,
            "end_word": self.end_word,
            "matched_terms": list(self.matched_terms),
            "confidence": self.confidence,
        }


def tokenize(text: str) -> list[str]:
    tokens = re.findall(r"[A-Za-z0-9_]+", text.lower())
    return [token for token in tokens if token not in STOPWORDS and len(token) > 1]


def estimate_tokens(text: str) -> int:
    return max(1, math.ceil(len(text.split()) * 1.3))


def chunk_text(text: str, size: int = DEFAULT_CHUNK_SIZE, overlap: int = DEFAULT_OVERLAP) -> list[str]:
    return [chunk["text"] for chunk in chunk_with_offsets(text, size=size, overlap=overlap)]


def chunk_with_offsets(text: str, size: int = DEFAULT_CHUNK_SIZE, overlap: int = DEFAULT_OVERLAP) -> list[dict[str, Any]]:
    words = text.split()
    if not words:
        return []
    chunks = []
    start = 0
    while start < len(words):
        end = min(start + size, len(words))
        chunks.append({
            "text": " ".join(words[start:end]),
            "start_word": start + 1,
            "end_word": end,
        })
        if end >= len(words):
            break
        start += max(1, size - overlap)
    return chunks


def _idf(corpus_tokens: list[list[str]]) -> dict[str, float]:
    document_count = max(1, len(corpus_tokens))
    containing_docs = defaultdict(int)
    for tokens in corpus_tokens:
        for token in set(tokens):
            containing_docs[token] += 1
    return {
        token: math.log((document_count + 1) / (count + 0.5)) + 1
        for token, count in containing_docs.items()
    }


def _confidence(score: float, best_score: float) -> str:
    if best_score <= 0 or score <= 0:
        return "none"
    ratio = score / best_score
    if ratio >= 0.78:
        return "high"
    if ratio >= 0.45:
        return "medium"
    return "low"


def _score(query_terms: Counter, candidate_terms: Counter, idf: dict[str, float], candidate_length: int, avg_length: float) -> tuple[float, tuple[str, ...]]:
    # BM25-style scoring keeps the project local and explainable while improving over raw keyword counts.
    k1 = 1.4
    b = 0.72
    matched = []
    score = 0.0
    length_norm = (1 - b) + b * (candidate_length / max(avg_length, 1))
    for term, query_count in query_terms.items():
        tf = candidate_terms.get(term, 0)
        if tf == 0:
            continue
        matched.append(term)
        numerator = tf * (k1 + 1)
        denominator = tf + k1 * length_norm
        score += query_count * idf.get(term, 1.0) * (numerator / max(denominator, 0.001))
    return score, tuple(sorted(matched))


def fixed_chunk_retrieval(documents: list[dict[str, Any]], query: str, limit: int = 5) -> list[dict[str, Any]]:
    query_terms = Counter(tokenize(query))
    if not documents or not query_terms:
        return []

    raw_chunks = []
    for document in documents:
        for index, chunk in enumerate(chunk_with_offsets(document.get("text", "")), start=1):
            tokens = tokenize(chunk["text"])
            if tokens:
                raw_chunks.append((document, index, chunk, tokens))

    if not raw_chunks:
        return []

    idf = _idf([tokens for _, _, _, tokens in raw_chunks])
    avg_length = sum(len(tokens) for _, _, _, tokens in raw_chunks) / len(raw_chunks)
    candidates = []

    for document, index, chunk, tokens in raw_chunks:
        score, matched = _score(query_terms, Counter(tokens), idf, len(tokens), avg_length)
        if score <= 0:
            continue
        candidates.append(RetrievalCandidate(
            document=document["filename"],
            chunk=chunk["text"],
            score=score,
            strategy="bm25 chunk",
            chunk_index=index,
            start_word=chunk["start_word"],
            end_word=chunk["end_word"],
            matched_terms=matched,
            confidence="pending",
        ))

    candidates = sorted(candidates, key=lambda item: item.score, reverse=True)[:limit]
    best = candidates[0].score if candidates else 0
    return [candidate.__class__(**{**candidate.__dict__, "confidence": _confidence(candidate.score, best)}).to_dict() for candidate in candidates]


def file_level_retrieval(documents: list[dict[str, Any]], query: str, limit: int = 3) -> list[dict[str, Any]]:
    query_terms = Counter(tokenize(query))
    if not documents or not query_terms:
        return []

    doc_tokens = [(document, tokenize(document.get("text", ""))) for document in documents]
    doc_tokens = [(document, tokens) for document, tokens in doc_tokens if tokens]
    if not doc_tokens:
        return []

    idf = _idf([tokens for _, tokens in doc_tokens])
    avg_length = sum(len(tokens) for _, tokens in doc_tokens) / len(doc_tokens)
    candidates = []

    for document, tokens in doc_tokens:
        score, matched = _score(query_terms, Counter(tokens), idf, len(tokens), avg_length)
        if score <= 0:
            continue
        preview = " ".join(document.get("text", "").split()[:220])
        candidates.append(RetrievalCandidate(
            document=document["filename"],
            chunk=preview,
            score=score,
            strategy="bm25 file",
            chunk_index=1,
            start_word=1,
            end_word=min(220, len(document.get("text", "").split())),
            matched_terms=matched,
            confidence="pending",
        ))

    candidates = sorted(candidates, key=lambda item: item.score, reverse=True)[:limit]
    best = candidates[0].score if candidates else 0
    return [candidate.__class__(**{**candidate.__dict__, "confidence": _confidence(candidate.score, best)}).to_dict() for candidate in candidates]


def retrieve(documents: list[dict[str, Any]], query: str, strategy: str = "fixed") -> list[dict[str, Any]]:
    if strategy == "file":
        results = file_level_retrieval(documents, query)
        if results:
            return results
        # try simple substring fallback before overview
        substr = _substring_fallback(documents, query)
        return substr or overview_fallback_retrieval(documents, query)
    if strategy == "compare":
        seen = set()
        combined = fixed_chunk_retrieval(documents, query) + file_level_retrieval(documents, query)
        unique = []
        for item in sorted(combined, key=lambda row: row["score"], reverse=True):
            key = (item["document"], item["strategy"], item["chunk_index"])
            if key not in seen:
                unique.append(item)
                seen.add(key)
        if unique:
            return unique[:8]
        substr = _substring_fallback(documents, query)
        return substr or overview_fallback_retrieval(documents, query)
    results = fixed_chunk_retrieval(documents, query)
    if results:
        return results
    substr = _substring_fallback(documents, query)
    if substr:
        return substr
    # try fuzzy match fallback next
    fuzzy = _fuzzy_fallback(documents, query)
    return fuzzy or overview_fallback_retrieval(documents, query)


def overview_fallback_retrieval(documents: list[dict[str, Any]], query: str, limit: int = 3) -> list[dict[str, Any]]:
    query_terms = set(tokenize(query))
    raw_terms = set(re.findall(r"[A-Za-z0-9_]+", query.lower()))
    overview_terms = query_terms | raw_terms
    if not documents or not overview_terms or not _looks_like_overview_question(overview_terms):
        return []

    candidates = []
    for document in documents[:limit]:
        words = document.get("text", "").split()
        if not words:
            continue
        preview = " ".join(words[:220])
        candidates.append(RetrievalCandidate(
            document=document["filename"],
            chunk=preview,
            score=0.1,
            strategy="selected document overview",
            chunk_index=1,
            start_word=1,
            end_word=min(220, len(words)),
            matched_terms=tuple(sorted(overview_terms & GENERIC_OVERVIEW_TERMS)),
            confidence="low",
        ).to_dict())
    return candidates


def _looks_like_overview_question(query_terms: set[str]) -> bool:
    return bool(query_terms & GENERIC_OVERVIEW_TERMS)


def retrieval_diagnostics(documents: list[dict[str, Any]], query: str, results: list[dict[str, Any]]) -> dict[str, Any]:
    query_terms = tokenize(query)
    indexed_words = sum(len(document.get("text", "").split()) for document in documents)
    return {
        "selected_documents": len(documents),
        "indexed_words": indexed_words,
        "query_terms": query_terms,
        "results_returned": len(results),
        "top_score": results[0]["score"] if results else 0,
        "failure_reason": _failure_reason(documents, query_terms, results),
    }


def _failure_reason(documents: list[dict[str, Any]], query_terms: list[str], results: list[dict[str, Any]]) -> str:
    if results:
        return ""
    if not documents:
        return "No active documents were selected."
    if not query_terms:
        return "The question did not contain searchable terms."
    return "No lexical overlap was found with the selected documents. Try using terms that appear in the file."


def _substring_fallback(documents: list[dict[str, Any]], query: str, limit: int = 3) -> list[dict[str, Any]]:
    # Simple, fast fallback: look for raw query tokens as substrings in the document text.
    raw_terms = [t for t in re.findall(r"[A-Za-z0-9_]+", query.lower()) if len(t) > 1]
    if not documents or not raw_terms:
        return []

    candidates = []
    for document in documents:
        text = document.get("text", "")
        lower = text.lower()
        matches = [t for t in raw_terms if t in lower]
        if not matches:
            continue
        # Create a readable preview around first match
        first = matches[0]
        idx = lower.find(first)
        words = text.split()
        # find word index for preview; fallback to start
        preview_start = 0
        if idx != -1:
            # approximate by character count
            prefix = text[:idx]
            preview_start = max(0, len(prefix.split()) - 10)
        preview = " ".join(words[preview_start:preview_start + 220]) if words else ""
        candidates.append(RetrievalCandidate(
            document=document["filename"],
            chunk=preview,
            score=0.05,
            strategy="substring match",
            chunk_index=1,
            start_word=preview_start + 1,
            end_word=min(preview_start + 220, len(words)),
            matched_terms=tuple(sorted(set(matches))),
            confidence="low",
        ).to_dict())
        if len(candidates) >= limit:
            break
    return candidates


def _fuzzy_fallback(documents: list[dict[str, Any]], query: str, limit: int = 3) -> list[dict[str, Any]]:
    from difflib import SequenceMatcher

    q = " ".join(tokenize(query))
    if not documents or not q:
        return []

    candidates = []
    for document in documents:
        text = document.get("text", "")
        preview = " ".join(text.split()[:220]).lower()
        if not preview:
            continue
        ratio = SequenceMatcher(None, q, preview).ratio()
        # minimal threshold to avoid many false positives
        if ratio < 0.35:
            continue
        confidence = "low"
        if ratio >= 0.78:
            confidence = "high"
        elif ratio >= 0.55:
            confidence = "medium"
        candidates.append(RetrievalCandidate(
            document=document["filename"],
            chunk=preview,
            score=round(ratio, 3),
            strategy="fuzzy match",
            chunk_index=1,
            start_word=1,
            end_word=min(220, len(text.split())),
            matched_terms=tuple(),
            confidence=confidence,
        ).to_dict())
        if len(candidates) >= limit:
            break
    return sorted(candidates, key=lambda r: r["score"], reverse=True)[:limit]


def top_terms(documents: list[dict[str, Any]], limit: int = 30) -> list[tuple[str, int]]:
    counter = Counter()
    for document in documents:
        counter.update(tokenize(document.get("text", "")))
    return counter.most_common(limit)
