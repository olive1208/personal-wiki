"""Ask mode: a standalone factual answer built only from retrieved passages (RAG).

Flow: question -> retrieve passages -> build prompt with research rules
-> call local Gemma -> check citations -> show answer and save an evidence card.
Ask mode never uses chat history or the assistant personality.
"""
import re
from datetime import datetime

from wiki_cli import llm, retrieval
from wiki_cli.config import EVIDENCE_DIR, MODEL, PROMPTS_DIR

INSUFFICIENT = "INSUFFICIENT EVIDENCE"


def format_passages(passages):
    """Give each passage a short label like [P1] plus its source, for the prompt."""
    blocks = []
    for p in passages:
        blocks.append(
            f"[{p['label']}] (source: {p['source']}, lines {p['start_line']}-{p['end_line']})\n{p['text']}"
        )
    return "\n\n".join(blocks)


def check_citations(answer, passages):
    """Find which labels the answer cites, and flag any problems."""
    labels = {p["label"] for p in passages}
    cited = sorted(set(re.findall(r"\[?(P\d+)\]?", answer)), key=lambda x: int(x[1:]))
    problems = []
    unknown = [c for c in cited if c not in labels]
    if unknown:
        problems.append(f"Cites passages that were not retrieved: {', '.join(unknown)}")
    if INSUFFICIENT not in answer.upper() and not cited:
        problems.append("Answer makes claims without any citation.")
    return [c for c in cited if c in labels], problems


def ask(question, k=5):
    """Answer one question from the notes. Returns a dictionary with everything that happened."""
    passages = retrieval.search(question, k=k)
    for n, p in enumerate(passages, start=1):
        p["label"] = f"P{n}"

    if not passages:
        answer = f"{INSUFFICIENT}: no passage in the notes matched this question."
        seconds = 0.0
    else:
        rules = (PROMPTS_DIR / "wiki-instructions.md").read_text(encoding="utf-8")
        messages = [
            {"role": "system", "content": rules},
            {
                "role": "user",
                "content": f"Passages from my notes:\n\n{format_passages(passages)}\n\nQuestion: {question}",
            },
        ]
        answer, seconds = llm.chat(messages, temperature=0)

    cited, problems = check_citations(answer, passages)
    result = {
        "question": question,
        "mode": "ask",
        "execution": "local",
        "model": MODEL,
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "seconds": seconds,
        "passages": passages,
        "answer": answer,
        "cited": cited,
        "problems": problems,
    }
    result["saved_to"] = save_evidence_card(result)
    return result


def save_evidence_card(r):
    """Write the full record of this question to evidence/ask/ as a Markdown file."""
    folder = EVIDENCE_DIR / "ask"
    folder.mkdir(parents=True, exist_ok=True)
    slug = re.sub(r"[^a-z0-9]+", "-", r["question"].lower()).strip("-")[:50]
    path = folder / f"{datetime.now().strftime('%Y%m%d-%H%M%S')}-{slug}.md"

    lines = [
        f"# Ask: {r['question']}",
        "",
        f"- Mode: {r['mode']}",
        f"- Execution: {r['execution']}",
        f"- Model: {r['model']} (Ollama)",
        f"- Time: {r['time']}",
        f"- Response time: {r['seconds']:.1f} seconds",
        "",
        "## Retrieved passages",
        "",
    ]
    for p in r["passages"]:
        lines += [
            f"### [{p['label']}] {p['source']} lines {p['start_line']}-{p['end_line']} (score {p['score']:.2f})",
            "",
            "```",
            p["text"],
            "```",
            "",
        ]
    if not r["passages"]:
        lines += ["(none)", ""]
    lines += ["## Answer", "", r["answer"], "", "## Citations", ""]
    by_label = {p["label"]: p for p in r["passages"]}
    for c in r["cited"]:
        p = by_label[c]
        lines.append(f"- [{c}] {p['source']} lines {p['start_line']}-{p['end_line']}")
    if not r["cited"]:
        lines.append("- (none)")
    lines += ["", "## Automatic citation check", ""]
    lines += [f"- {x}" for x in r["problems"]] or ["- No problems found."]
    lines += ["", "## My assessment", "", "(Fill in: did retrieval find the right passage? Is each claim supported by its citation?)", ""]
    path.write_text("\n".join(lines), encoding="utf-8")
    return path
