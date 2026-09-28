"""Command-line interface: reads the command you type and runs the right mode."""
import argparse
import sys

from wiki_cli import retrieval
from wiki_cli.config import MODEL
from wiki_cli.llm import ModelUnavailable


def cmd_search(args):
    """Search mode: show matching original passages. No model, no answer."""
    results = retrieval.search(args.query, k=args.k)
    if not results:
        print("No matching passages found.")
        return
    print(f'Search results for: "{args.query}"\n')
    for n, r in enumerate(results, start=1):
        print(f"[{n}] {r['source']}  lines {r['start_line']}-{r['end_line']}  (score {r['score']:.2f})")
        print(r["text"])
        print("-" * 60)


def cmd_ask(args):
    """Ask mode: standalone factual answer with citations, or insufficient evidence."""
    if args.mode != "local":
        print("Online mode is not set up. Use --mode local (the default).")
        sys.exit(1)
    from wiki_cli.ask import ask

    print(f"[ask | execution: local | model: {MODEL}]")
    print("Retrieving passages and asking Gemma...\n")
    r = ask(args.question, k=args.k)

    print(r["answer"])
    print("\nSources:")
    by_label = {p["label"]: p for p in r["passages"]}
    for c in r["cited"]:
        p = by_label[c]
        print(f"  [{c}] {p['source']}  lines {p['start_line']}-{p['end_line']}")
    if not r["cited"]:
        print("  (none cited)")
    for problem in r["problems"]:
        print(f"WARNING: {problem}")
    print(f"\nResponse time: {r['seconds']:.1f} s")
    print(f"Evidence card saved to: {r['saved_to']}")


def cmd_ingest(args):
    """Ingest: build or update wiki pages from the original notes, then rebuild the indexes."""
    from wiki_cli.ingest import ingest

    print(f"[ingest | execution: local | model: {MODEL}]")
    try:
        result = ingest(args.path, force=args.force)
    except FileNotFoundError as error:
        print(f"ERROR: {error}")
        sys.exit(1)
    print(
        f"\nPages written: {len(result['written'])}, unchanged: {len(result['skipped'])}, "
        f"model time: {result['seconds']:.1f} s"
    )


def cmd_chat(args):
    """Chat mode: personal assistant that uses the conversation and searches notes only when needed."""
    from wiki_cli.chat import run_chat

    run_chat()


def main():
    parser = argparse.ArgumentParser(
        prog="wiki",
        description="Personal wiki with a local Gemma model. Notes are read from vault/raw.",
        epilog=(
            f"Model: {MODEL} through Ollama at http://localhost:11434 (local, default). "
            "Settings are in wiki_cli/config.py; page names and links in wiki_plan.json; "
            "model instructions in prompts/. Run 'python -m wiki_cli <command> --help' for details."
        ),
    )
    commands = parser.add_subparsers(dest="command", required=True)

    p = commands.add_parser("ingest", help="build or update wiki pages from notes in vault/raw")
    p.add_argument("path", nargs="?", default=None, help="vault/raw (all notes, default) or one note in it")
    p.add_argument("--force", action="store_true", help="rewrite pages even if their sources did not change")
    p.set_defaults(func=cmd_ingest)

    p = commands.add_parser("search", help="show original passages that match a query (no model used)")
    p.add_argument("query", help="words to search for")
    p.add_argument("-k", type=int, default=5, help="number of passages to show (default 5)")
    p.set_defaults(func=cmd_search)

    p = commands.add_parser("ask", help="factual answer from your notes, with citations")
    p.add_argument("question", help="the question to answer")
    p.add_argument("--mode", choices=["local", "online"], default="local", help="where the model runs (default local)")
    p.add_argument("-k", type=int, default=5, help="number of passages given to the model (default 5)")
    p.set_defaults(func=cmd_ask)

    p = commands.add_parser("chat", help="talk with Scout, your assistant (keeps the conversation)")
    p.set_defaults(func=cmd_chat)

    args = parser.parse_args()
    try:
        args.func(args)
    except ModelUnavailable as error:
        print(f"ERROR: {error}")
        sys.exit(1)


if __name__ == "__main__":
    main()
