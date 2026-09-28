"""Chat mode: a personal assistant with a personality and memory of this session.

Unlike ask mode, chat keeps the conversation, and it only searches the notes
when a message seems to need them. Casual messages ("what can you help me with?")
and follow-ups ("make that shorter") are answered from the conversation alone.
"""
import re
from datetime import datetime

from wiki_cli import llm, retrieval
from wiki_cli.config import EVIDENCE_DIR, MODEL, PROMPTS_DIR

# Only the most recent messages are sent to the model, to fit its context window
HISTORY_LIMIT = 8

# A search score at or above this means the notes clearly match the message
RETRIEVE_THRESHOLD = 6.0

# Words that show the message is about something in the notes
NOTE_CUES = re.compile(
    r"\b(my notes?|notes|panel|panelists?|info session|workshop|speakers?|according to"
    r"|what did|who said|remind me|amazon|ala|fldp|mldp|hrldp)\b",
    re.IGNORECASE,
)

# Messages about the assistant itself, or edits to the last reply, never need a notes search
CONVERSATIONAL = re.compile(
    r"^(hi|hello|hey|thanks|thank you|ok|okay)\b"
    r"|what can (you|we) do|what can you help|who are you|how do you work"
    r"|\b(shorter|longer|rewrite|rephrase|simplify|make (it|that|this))\b",
    re.IGNORECASE,
)


# Messages that ask the assistant to save or remember something
SAVE_REQUEST = re.compile(
    r"\b(note for later|remember|save (this|that|it)|take note|write (this|that) down|add (this|that|it) to my notes)\b",
    re.IGNORECASE,
)

SAVE_NOTICE = (
    "(Notice from the harness: chat cannot save anything. This message stays in this "
    "chat session only. It is not added to your notes and ask mode will not see it.)"
)


def decide_retrieval(message):
    """Return (passages, reason). An empty list means no notes lookup this turn."""
    if message.startswith("/notes"):
        query = message[len("/notes"):].strip()
        return retrieval.search(query, k=5), "user asked for a notes lookup (/notes)"
    if SAVE_REQUEST.search(message):
        return [], "save or remember request, answered from the chat"
    if CONVERSATIONAL.search(message):
        return [], "conversational or follow-up message, answered from the chat"
    results = retrieval.search(message, k=5)
    if not results:
        return [], "no match in the notes, answered from the chat"
    if NOTE_CUES.search(message):
        return results, "message refers to something in the notes"
    if results[0]["score"] >= RETRIEVE_THRESHOLD:
        return results, f"notes clearly match (top score {results[0]['score']:.1f})"
    return [], "no strong match in the notes, answered from the chat"


def build_user_turn(message, passages):
    """Attach note passages to the user's message when retrieval was used."""
    if not passages:
        return message
    blocks = [
        f"[{p['label']}] (source: {p['source']}, lines {p['start_line']}-{p['end_line']})\n{p['text']}"
        for p in passages
    ]
    return (
        "Note passages that may help (cite them like [P1] if you use them):\n\n"
        + "\n\n".join(blocks)
        + f"\n\nMy message: {message}"
    )


def run_chat():
    persona = (PROMPTS_DIR / "persona.md").read_text(encoding="utf-8")
    history = []
    log = []
    started = datetime.now()

    print(f"[chat | execution: local | model: {MODEL}]")
    print("Scout is ready. Type /exit to quit, /reset to clear, /notes <question> to search notes.\n")

    while True:
        try:
            message = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if not message:
            continue
        if message == "/exit":
            break
        if message == "/reset":
            history = []
            print("(conversation cleared)\n")
            log.append({"you": "/reset", "scout": "(conversation cleared)", "reason": "", "passages": [], "seconds": 0})
            continue

        passages, reason = decide_retrieval(message)
        for n, p in enumerate(passages, start=1):
            p["label"] = f"P{n}"

        history.append({"role": "user", "content": build_user_turn(message, passages)})
        messages = [{"role": "system", "content": persona}] + history[-HISTORY_LIMIT:]
        try:
            reply, seconds = llm.chat(messages, temperature=0.6)
        except llm.ModelUnavailable as error:
            history.pop()
            print(f"ERROR: {error}\n")
            continue
        history.append({"role": "assistant", "content": reply})

        print(f"\nScout: {reply}")
        if SAVE_REQUEST.search(message):
            print(f"\n{SAVE_NOTICE}")
            reply = f"{reply}\n\n{SAVE_NOTICE}"
        if passages:
            print("\nNotes searched:")
            for p in passages:
                print(f"  [{p['label']}] {p['source']}  lines {p['start_line']}-{p['end_line']}")
        print(f"({reason}; {seconds:.1f} s)\n")
        log.append({"you": message, "scout": reply, "reason": reason, "passages": passages, "seconds": seconds})

    if log:
        path = save_transcript(log, started)
        print(f"Transcript saved to: {path}")


def save_transcript(log, started):
    """Save the chat session to evidence/chat/ so it can be checked later."""
    folder = EVIDENCE_DIR / "chat"
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f"{started.strftime('%Y%m%d-%H%M%S')}-chat.md"
    lines = [
        f"# Chat transcript {started.strftime('%Y-%m-%d %H:%M')}",
        "",
        f"- Mode: chat",
        f"- Execution: local",
        f"- Model: {MODEL} (Ollama)",
        "",
    ]
    for n, turn in enumerate(log, start=1):
        lines += [f"## Turn {n}", "", f"**You:** {turn['you']}", "", f"**Scout:** {turn['scout']}", ""]
        if turn["reason"]:
            lines.append(f"- Retrieval decision: {turn['reason']}")
        for p in turn["passages"]:
            lines.append(f"- [{p['label']}] {p['source']} lines {p['start_line']}-{p['end_line']}")
        if turn["seconds"]:
            lines.append(f"- Response time: {turn['seconds']:.1f} s")
        lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")
    return path
