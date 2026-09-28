# Personal Wiki with Local Gemma

A command-line personal wiki for my MBA tech recruiting notes. A local Gemma model, running on my laptop through Ollama, turns my raw notes into linked Obsidian pages, answers factual questions with citations, and acts as a chat assistant. Everything runs offline after setup.

**Quick links**

- Code: [wiki_cli/](wiki_cli/)
- Wiki (open `vault/` in Obsidian): [vault/index.md](vault/index.md)
- Ask-mode test results (4 tests): [evidence/ask-test-results.md](evidence/ask-test-results.md)
- Chat and search mode checks: [evidence/mode-checks.md](evidence/mode-checks.md)
- Wiki review log: [evidence/wiki-review-log.md](evidence/wiki-review-log.md)
- Offline demonstration: [evidence/screenshots/offline-demo.mp4](evidence/screenshots/offline-demo.mp4) and [evidence/offline-run.txt](evidence/offline-run.txt)

---

## 1. Purpose and sources

The wiki holds what I learned at MBA tech recruiting events, so I can look up facts ("when are Amazon ALA interviews?") and get help preparing (for example, drafting an interview prep plan).

| Original note (`vault/raw/`) | What it is |
|---|---|
| [Amazon info session.md](vault/raw/Amazon%20info%20session.md) | Amazon MBA recruiting session: ALA, FLDP, MLDP and other programs, interview style, process |
| [Tech internship panel.md](vault/raw/Tech%20internship%20panel.md) | Second-year MBA students on how they got tech internships |
| [Tech roles primer.md](vault/raw/Tech%20roles%20primer.md) | Career workshop on MBA roles in tech and the hiring process |
| [Rewrite tech resume.md](vault/raw/Rewrite%20tech%20resume.md) | Workshop on writing resume bullets for tech roles |

These are my own class notes. Before adding them I removed private Google Docs links and broken image and PDF embeds. After they were placed in `raw/`, they were not changed.

**How originals connect to generated pages.** `wiki_plan.json` lists each wiki page, its folder, and which raw notes it is built from. Every wiki page lists its sources in its properties and links back to them under "Sources". The [source catalog](#source-catalog) below shows the full mapping.

## 2. Setup and device

### Device

| Item | Value |
|---|---|
| OS | Windows 11, 64-bit |
| CPU | AMD Ryzen 5 7530U (2.0 GHz) |
| RAM | 16 GB (13.9 GB usable) |
| GPU | AMD Radeon integrated graphics, 2 GB shared memory, no dedicated GPU |
| Free disk | about 300 GB of 477 GB |

### Model and runtime

| Item | Value |
|---|---|
| Model | `gemma4:e2b` (Gemma 4 E2B), Ollama model ID `7fbdbf8f5e45` |
| Parameters | 5.1B total (about 2B effective; the rest are per-layer embedding tables) |
| Quantization | Q4_K_M (4-bit) |
| Download size | 7.2 GB |
| Runtime | Ollama 0.34.4, local server at `http://localhost:11434` |
| Runs on | 100% CPU |
| Context window | 4096 tokens for ask and chat, 8192 for ingest |
| Official source | [ollama.com/library/gemma4](https://ollama.com/library/gemma4), [Gemma docs](https://ai.google.dev/gemma/docs/integrations/ollama) |

### Why this model

My laptop has no dedicated GPU, so the model runs on the CPU and shares the 16 GB of system RAM with everything else. E2B is the smallest Gemma 4 size, so it loads fastest and answers fastest on CPU. E4B would need more memory and be slower, and E2B already answers all four test questions correctly. I did not test larger sizes.

### Measured memory and speed

| Measurement | Result |
|---|---|
| Model memory when loaded (`ollama ps`) | 6.7 GB |
| Ask answer, first question (includes loading the model) | 21.6 to 21.9 s |
| Ask answer, model already loaded | 11.1 to 19.7 s |
| Chat reply | 6.7 to 26.7 s |
| Ingest, all 7 pages | 270.1 s (25.0 to 46.5 s per page) |
| Ingest offline, 1 source (2 pages) | 88.7 s (40.3 and 48.4 s) |
| Search | under 1 s, no model |

**Expected vs measured memory.** The assignment's estimate for E2B at Q4_0 is about 2.9 GB. Ollama reported 6.7 GB. The Ollama package also includes the vision and audio parts and the large embedding tables, and loads them all. With Slack, WhatsApp, and Word open, total system memory reached 95%, so I closed those apps before the offline run.

### Dependencies

- Python 3.14.5
- `requests` (talks to Ollama), `rank-bm25` (keyword search), `numpy` (used by rank-bm25). Exact versions are in [requirements.txt](requirements.txt).

### Setup (while online)

```powershell
# 1. Install Ollama for Windows from https://ollama.com and download the model
ollama pull gemma4:e2b
ollama list                      # should show gemma4:e2b

# 2. Get the code and install packages
git clone <this repository>
cd personal-wiki
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

After this, no internet is needed. The model weights stay on the laptop and are not in this repository.

### Commands

Run from the project folder with the virtual environment active. Ollama must be running (it starts with Windows; otherwise open the Ollama app).

| Command | What it does |
|---|---|
| `python -m wiki_cli --help` | List commands, the model, and where settings live |
| `python -m wiki_cli ingest` | Build or update all wiki pages from `vault/raw/`, then rebuild `index.md` and the search index |
| `python -m wiki_cli ingest "vault/raw/Amazon info session.md"` | Update only the pages built from one note |
| `python -m wiki_cli ingest --force` | Rewrite pages even if their sources did not change |
| `python -m wiki_cli search "Amazon interview STAR method"` | Show matching original passages. No model is used. |
| `python -m wiki_cli ask "When are Amazon ALA interviews held?"` | Standalone factual answer with citations, or "INSUFFICIENT EVIDENCE" |
| `python -m wiki_cli chat` | Talk with Scout, the assistant. Type `/exit` to quit, `/reset` to clear, `/notes <question>` to force a notes search. |

`--mode local` is the default for ask. There is no online mode.

**Errors.** If Ollama is not running: `ERROR: Cannot reach Ollama at http://localhost:11434. Open the Ollama app and try again.` If the model is missing: `ERROR: Model 'gemma4:e2b' is not downloaded. Run: ollama pull gemma4:e2b`. If an ingest path does not exist: `ERROR: Not found: <path>`.

## 3. Architecture

```
personal-wiki/
  wiki_cli/            my harness code
    __main__.py        CLI: reads the command and picks the mode
    config.py          paths and model name
    retrieval.py       retrieval tool: split notes into passages, BM25 search
    llm.py             calls local Gemma through Ollama
    ask.py             ask mode (RAG workflow) and evidence cards
    chat.py            chat mode: conversation, retrieval decision, transcripts
    ingest.py          builds wiki pages, index.md, and the search index
  prompts/
    wiki-instructions.md   research rules (ask)
    persona.md             assistant personality and capabilities (chat)
    ingest-instructions.md wiki writing rules (ingest)
  wiki_plan.json       page names, folders, sources, and links
  vault/               the Obsidian vault
    raw/               original notes, unchanged
    wiki/Sessions/     one page per event
    wiki/Topics/       pages that combine several events
    index.md           landing page
  data/chunks.json     search passages (machine file, not in git)
  tests/               test questions and expected answers
  evidence/            saved results, transcripts, screenshots
```

**The five parts, and how they differ**

- **Model:** Gemma 4 E2B. It only turns text into text. It does not read my files, remember past sessions, or search anything by itself.
- **Retrieval tool:** `retrieval.py`. Splits the notes into passages and finds the best matches for a query. Search mode shows its output directly.
- **RAG workflow:** ask mode. Retrieve passages, put them in the prompt with the research rules, and have Gemma answer only from them. This adds context at answer time; it does not train the model.
- **CLI:** `__main__.py`. The terminal commands a user types.
- **Harness:** all of `wiki_cli/`. It picks the mode, loads the right instructions, keeps or drops conversation history, decides when to retrieve, builds prompts, calls Gemma, checks citations, handles errors, and saves outputs.

### One path from command to result: `ask`

1. `__main__.py` reads `ask "<question>"` and calls `ask()` in `ask.py`.
2. `ask.py` calls `retrieval.search(question, k=5)`. If any note in `raw/` is newer than `data/chunks.json`, the index is rebuilt first. BM25 scores every passage and returns the top 5 with file path and line numbers.
3. `ask.py` labels them [P1] to [P5] and builds two messages: a system message with `prompts/wiki-instructions.md`, and a user message with the labeled passages and the question. No chat history and no personality are included.
4. `llm.py` sends this to Ollama (`/api/chat`, temperature 0, thinking off) and times the reply.
5. `ask.py` checks citations: every [P#] in the answer must be one of the retrieved passages, and an answer with claims but no citation is flagged.
6. The answer, sources, and response time are printed, and an evidence card is saved to `evidence/ask/` with the question, model, passages, answer, and citation check.

### How each mode is kept separate

| | ask | chat | search |
|---|---|---|---|
| Instructions | `wiki-instructions.md` | `persona.md` | none |
| Conversation history | none, each question stands alone | last 8 messages of this session | none |
| Retrieval | always, top 5 | only when needed (below) | always |
| Model call | yes, temperature 0 | yes, temperature 0.6 | no |
| Output | answer + citations + evidence card | reply + notes searched + transcript | passages + paths |

**When chat retrieves notes.** In order:
1. `/notes <question>`: always search.
2. Asking to save or remember something: never search, and the harness adds a notice that chat cannot save.
3. Small talk or edits to the last reply ("what can you help me with?", "make that shorter", "thanks"): never search.
4. The message names something in the notes (Amazon, ALA, FLDP, panel, workshop, "my notes"...): search.
5. Otherwise, search only if the best BM25 score is 6.0 or higher.

Chat history is never passed to ask, so something said only in chat cannot become evidence ([check](evidence/mode-checks.md#4-a-claim-made-only-in-chat-is-not-used-by-ask)).

## 4. Design choices

**Passages.** Each note is split at headings, short label lines ending in a colon (like `ALA:` or `Interview:`), and blank lines, with at most about 80 words per passage. My notes are organized by these labels, so a passage usually covers one program or one topic. Each passage keeps its file path and line numbers, which become the citation. The 4 notes give 33 passages.

**Retrieval method.** BM25 keyword search (`rank-bm25`) with a short stopword list. I chose it over embeddings because the corpus is small, it needs no extra model or memory, it runs fully offline, and I can see why a passage ranked where it did. Test 2 checks that it still works when the question uses different words.

**What ask retrieves from.** Ask and search use only the original notes in `raw/`. The wiki pages are model-written summaries, so they are kept for browsing and never used as evidence. This keeps generated text separate from original evidence.

**How much text goes to Gemma.** Ask sends the rules plus 5 passages (about 400 words) and the question. Chat sends the persona, up to 8 recent messages, and 5 passages only when it retrieves. Ingest sends the full text of 1 or 2 notes (at most about 1,000 words) per page.

**Research rules** ([wiki-instructions.md](prompts/wiki-instructions.md)): use only the given passages; cite every claim; start with "INSUFFICIENT EVIDENCE" when the passages do not answer; neutral voice; plain text. Rules 8 and 9 were added after test 3 (see [results](evidence/ask-test-results.md#test-3-connects-two-sources)).

**Assistant personality** ([persona.md](prompts/persona.md)): Scout, a friendly and practical MBA classmate. The file lists what Scout can and cannot do, so "what can you help me with?" gets an accurate answer. Suggestions must be labeled as suggestions, and personal facts must not be invented.

**Model settings.** Thinking mode is turned off (`"think": false`). With it on, Gemma writes a long reasoning section first, which was much slower on CPU. Temperature is 0 for ask (repeatable answers), 0.2 for ingest, and 0.6 for chat.

### Wiki naming, folders, and re-ingestion

- **Names come from `wiki_plan.json`, never from the model.** Filenames are short subject names like `Tech Hiring Process.md`, and the first heading matches the filename.
- **Folders:** `Sessions/` has one page per event; `Topics/` has pages that combine what several events said about one subject.
- **Links:** each page has a "Related notes" section where every link says why it is relevant, and a "Sources" section linking to the original notes. `index.md` groups all pages by folder with a one-line description.
- **Machine details** (source paths, a source fingerprint, model name, generation time, review status) are kept in the page properties, not in the filename.
- **No duplicates on re-ingest.** Each page stores a fingerprint of its source notes. On ingest, a page whose sources have not changed is skipped ("up to date"). A page marked `reviewed: true` is not overwritten even if its sources change, unless `--force` is used. Ingesting again updates the same file; it never creates a new one.

### Source catalog

| Wiki page | Folder | Built from |
|---|---|---|
| [Amazon MBA Info Session](vault/wiki/Sessions/Amazon%20MBA%20Info%20Session.md) | Sessions | Amazon info session |
| [Tech Internship Panel](vault/wiki/Sessions/Tech%20Internship%20Panel.md) | Sessions | Tech internship panel |
| [Tech Roles Workshop](vault/wiki/Sessions/Tech%20Roles%20Workshop.md) | Sessions | Tech roles primer |
| [Tech Resume Workshop](vault/wiki/Sessions/Tech%20Resume%20Workshop.md) | Sessions | Rewrite tech resume |
| [Tech Hiring Process](vault/wiki/Topics/Tech%20Hiring%20Process.md) | Topics | Tech roles primer, Amazon info session |
| [Tech Networking](vault/wiki/Topics/Tech%20Networking.md) | Topics | Tech internship panel, Tech roles primer |
| [Behavioral Interview Prep](vault/wiki/Topics/Behavioral%20Interview%20Prep.md) | Topics | Amazon info session, Rewrite tech resume |

### Reviewing the generated pages

I checked every generated page against the original notes and corrected wrong or misleading statements in the wiki pages. The raw notes were not changed. The unedited model output is in [evidence/wiki-before-review/](evidence/wiki-before-review/) and each correction is listed in the [review log](evidence/wiki-review-log.md). The four single-source Sessions pages were mostly accurate. The three Topics pages, which combine two notes, needed the most fixing.

## 5. Evidence

### Obsidian screenshots

Vault opened at `vault/`. Graph filter: `path:wiki/`, Attachments off, groups colored by `path:wiki/Sessions` (red) and `path:wiki/Topics` (yellow).

| Screenshot | Shows |
|---|---|
| [obsidian-note-top.png](evidence/screenshots/obsidian-note-top.png), [obsidian-note-bottom.png](evidence/screenshots/obsidian-note-bottom.png) | "Tech Hiring Process": readable filename, matching heading, properties with sources, related notes, and source links |
| [obsidian-index-top.png](evidence/screenshots/obsidian-index-top.png), [obsidian-index-bottom.png](evidence/screenshots/obsidian-index-bottom.png) | `index.md` grouped by topic, and the page list |
| [obsidian-graph.png](evidence/screenshots/obsidian-graph.png) | Graph of the 7 wiki pages with readable labels |

**Trace check in Obsidian:** `index.md` → Tech Hiring Process → (Related notes) Amazon MBA Info Session → (Sources) the original `raw/Amazon info session.md`. All links opened the right page.

**Re-ingest check:** running `python -m wiki_cli ingest` a second time printed "up to date" for all 7 pages and "Pages written: 0, unchanged: 7". No duplicate or renamed pages were created.

### Ask-mode tests

Full records, retrieved passages, answers, citation checks, and my assessment: [evidence/ask-test-results.md](evidence/ask-test-results.md). Questions and expected answers were written before building retrieval: [tests/test_questions.md](tests/test_questions.md).

| Test | Question | Offline answer | Result |
|---|---|---|---|
| 1 | When and how are the Amazon ALA internship interviews held? | In person in January [P1] | Pass |
| 2 | Which Amazon MBA program lets me see different sides of the retail business? | MLDP, 3-year rotation, every angle of retail [P1] | Pass |
| 3 | Hiring steps for tech MBA roles, and how Amazon compares | General 4 steps [P1]; Amazon: application, online assessment, interview [P4] | Pass, minor issues |
| 4 | What is the base salary for Amazon's FLDP role? | INSUFFICIENT EVIDENCE | Pass |

### Chat and search checks

[evidence/mode-checks.md](evidence/mode-checks.md): capabilities question, draft and "make that shorter" follow-up, raw search output, and a check that a claim made only in chat is not treated as evidence in ask.

### Offline demonstration

On 2026-09-28 at 15:22 I turned off Wi-Fi, opened a new PowerShell window, and ran help, ingest, search, all four ask tests, and the chat checks.

- Screen recording: [evidence/screenshots/offline-demo.mp4](evidence/screenshots/offline-demo.mp4)
- PowerShell transcript: [evidence/offline-run.txt](evidence/offline-run.txt). It shows `ping ollama.com` failing ("could not find host") and `ollama list` showing the local model. Windows PowerShell 5.1's `Start-Transcript` does not capture output from external programs like Python, so the command results are in the recording and in the saved files below.
- Files written during the offline run (15:22 to 15:28): ask evidence cards `evidence/ask/20260928-1525*` to `1527*`, chat transcript [evidence/chat/20260928-152713-chat.md](evidence/chat/20260928-152713-chat.md), and the wiki as it was right after the offline ingest in [evidence/offline-ingest-output/](evidence/offline-ingest-output/). In that folder, Tech Resume Workshop and Behavioral Interview Prep were regenerated offline (`generated_at: 2026-09-28 15:23`); the other five are the reviewed pages. After the demo I restored the reviewed versions of the two regenerated pages.

## 6. Reflection

### Main limitation: mixing up sources when combining two notes

When a question or page combines two notes, the model sometimes attaches a fact to the wrong source.

- In ask test 3, the first run called Amazon's 3-step process "the general process", which conflicted with the 4-step general process it had just listed.
- In ingest, the "Tech Hiring Process" page said Amazon's process was the general 4-step process, which comes from the roles workshop. It also merged three Amazon programs (ALA, FLDP, MLDP) into one sentence and added "further steps" that no note mentions.

**Cause.** Retrieval was not the problem: both correct passages were retrieved every time. The passages reach the model only as [P1] to [P5] with a file path, and the small E2B model does not reliably keep track of which passage said what. A prompt rule asking it to name the source of each part of a comparison helped a little, but did not fix it.

**Improvement I would try.** Put the source name inside each label, for example `[P4 - Amazon info session]`, so the model sees "Amazon" right next to Amazon's facts. For comparison questions, the harness could also retrieve and answer each part separately, then combine the answers. After that I would test E4B on the same questions to see whether a larger model tracks sources better.

### Other problems found and how they were handled

- **Chat claimed it saved a note.** Adding a rule to the persona did not stop it. Fixed in the harness with a fixed notice ([details](evidence/mode-checks.md#5-failure-found-and-fixed-chat-claimed-it-saved-a-note)).
- **Formatting.** Gemma printed LaTeX arrows, and after a rule fixed that, it added a backslash before citations (`\[P1]`). This is still present; the harness's citation check still reads these correctly.
- **Source tags in wiki pages.** Gemma often tagged facts with a section heading or speaker name instead of the note name. Fixed by hand in review.
- **Memory.** The model used 6.7 GB, more than twice the official estimate, which matters on a 16 GB laptop shared with other apps.

## Online mode

Not implemented. All results in this repository come from the local model.
