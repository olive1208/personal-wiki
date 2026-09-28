"""Retrieval tool.

Splits the original notes in vault/raw into short passages and finds the
passages that best match a question, using BM25 keyword search.
Everything runs locally. No language model is used here.
"""
import json
import re

from rank_bm25 import BM25Okapi

from wiki_cli.config import CHUNKS_FILE, DATA_DIR, PROJECT_ROOT, RAW_DIR

# A passage holds at most about this many words
MAX_WORDS = 80

# Common words that do not help find the right passage
STOPWORDS = {
    "a", "an", "the", "and", "or", "of", "to", "in", "on", "for", "at", "by",
    "is", "are", "was", "were", "be", "it", "this", "that", "with", "as",
    "what", "which", "who", "how", "when", "where", "why", "do", "does", "did",
    "i", "me", "my", "you", "your", "we", "our", "they", "their", "can", "s",
}


def tokenize(text):
    """Turn text into a list of lowercase search words."""
    words = re.findall(r"[a-z0-9]+", text.lower())
    return [w for w in words if w not in STOPWORDS]


def is_section_start(line):
    """True for a heading ("# Roles") or a short label line ("ALA:", "Interview:")."""
    if line.startswith("#"):
        return True
    words = line.split()
    return (
        line.endswith(":")
        and len(words) <= 6
        and not line[0].isdigit()
        and not line.startswith("-")
    )


def split_into_passages(path):
    """Split one note into passages, keeping the line numbers of each."""
    lines = path.read_text(encoding="utf-8-sig").splitlines()
    source = path.relative_to(PROJECT_ROOT).as_posix()
    passages = []
    current, start, end, word_count = [], 0, 0, 0

    def save_current():
        if current:
            passages.append({
                "id": f"{path.stem} L{start}-{end}",
                "source": source,
                "start_line": start,
                "end_line": end,
                "text": "\n".join(current),
            })

    for number, line in enumerate(lines, start=1):
        stripped = line.strip()
        # A new section always starts a new passage.
        # A blank line also does, once the current passage has some content.
        # A tiny passage (just a label like "MBA roles:") stays with the next line.
        if current and word_count >= 5 and (is_section_start(stripped) or (not stripped and word_count >= 30)):
            save_current()
            current, word_count = [], 0
        if not stripped:
            continue
        words = len(stripped.split())
        # Start a new passage if this line would make the current one too long.
        # Very short passages (like a heading "ALA:") stay attached to the next line.
        if current and word_count >= 30 and word_count + words > MAX_WORDS:
            save_current()
            current, word_count = [], 0
        if not current:
            start = number
        current.append(line.rstrip())
        word_count += words
        end = number

    save_current()
    return passages


def build_index():
    """Read every note in vault/raw and save all passages to data/chunks.json."""
    files = sorted(list(RAW_DIR.glob("*.md")) + list(RAW_DIR.glob("*.txt")))
    passages = []
    for path in files:
        passages.extend(split_into_passages(path))
    DATA_DIR.mkdir(exist_ok=True)
    CHUNKS_FILE.write_text(json.dumps(passages, indent=2, ensure_ascii=False), encoding="utf-8")
    return passages


def index_is_stale():
    """True if the index is missing or any note in vault/raw is newer than it."""
    if not CHUNKS_FILE.exists():
        return True
    built = CHUNKS_FILE.stat().st_mtime
    return any(f.stat().st_mtime > built for f in RAW_DIR.iterdir() if f.is_file())


def load_passages():
    """Load saved passages, rebuilding the index first if it is missing or out of date."""
    if index_is_stale():
        return build_index()
    return json.loads(CHUNKS_FILE.read_text(encoding="utf-8"))


def search(query, k=5):
    """Return the k passages that best match the query, best first."""
    passages = load_passages()
    if not passages:
        return []
    bm25 = BM25Okapi([tokenize(p["text"]) for p in passages])
    scores = bm25.get_scores(tokenize(query))
    ranked = sorted(zip(scores, passages), key=lambda pair: pair[0], reverse=True)
    return [dict(p, score=float(s)) for s, p in ranked[:k] if s > 0]
