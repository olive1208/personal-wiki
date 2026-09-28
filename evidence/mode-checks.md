# Chat and search mode checks

These checks confirm that chat, ask, and search behave differently, as the harness intends.
All runs used the local model `gemma4:e2b` through Ollama.

| Check | Expected | Result | Internet |
|---|---|---|---|
| Chat: "what can you help me with?" | Accurate capabilities, no notes search, no "insufficient evidence" | Pass | Off |
| Chat: draft a plan, then "make that shorter" | Uses the conversation; claims from notes are cited | Pass | Off |
| Search: "Amazon interview STAR method" | Original passages with paths, no generated answer | Pass | On and off |
| Chat claim is not evidence in ask | Ask ignores a "fact" stated only in chat | Pass | On |
| Chat does not claim abilities it lacks | Chat must not say it saved something | Failed twice, fixed in the harness | On |

## 1. Chat: capabilities (offline)

Transcript: [chat/20260928-152713-chat.md](chat/20260928-152713-chat.md), turn 1

> **You:** what can you help me with?
>
> **Scout:** Hey! I'm Scout, your personal assistant for those tech recruiting notes. I can help you brainstorm, draft, plan, and look up information from the notes we've covered, like interview stories or resume bullets. Just let me know what you're working on!

Retrieval decision: "conversational or follow-up message, answered from the chat". No notes were searched and no citations were added.

## 2. Chat: draft, then follow-up (offline)

Same transcript, turns 2 and 3.

- "Draft a short 3-step plan to prepare for the Amazon ALA interview": the harness searched the notes because the message names Amazon and ALA. Scout cited [P1] (ALA passage) and [P4] (resume workshop). The claims match the passages. One point stretches [P1] slightly: it mentions working with the "advisory board and peers", where the note only says ALA hires are "selected by advisory board" and "also do peer review".
- "make that shorter": no new search. Scout shortened its own previous plan to three one-line steps and kept the citations. This shows it used the conversation.

## 3. Search: original passages only

Command: `python -m wiki_cli search "Amazon interview STAR method"`
Saved output: [search-check.txt](search-check.txt). The same command was run again offline (see the recording).

The top result is `vault/raw/Amazon info session.md` lines 27-32, the "Interview: behavioral based, STAR method" passage. Each result shows the file, line numbers, score, and original text. No model is called and no answer is generated.

## 4. A claim made only in chat is not used by ask

1. In chat: "Note for later: the ALA internship pays $12,000 a month." ([chat/20260928-143904-chat.md](chat/20260928-143904-chat.md))
2. New command: `python -m wiki_cli ask "How much does the Amazon ALA internship pay?"`
3. Answer: "INSUFFICIENT EVIDENCE: the notes do not contain information about the salary for the Amazon ALA internship." ([card](ask/20260928-143624-how-much-does-the-amazon-ala-internship-pay.md))

Ask only sees passages retrieved from `vault/raw/`. It never receives chat history.

## 5. Failure found and fixed: chat claimed it saved a note

| Run | What Scout said | Fix tried |
|---|---|---|
| [14:32](chat/20260928-143244-chat.md) | "Got it. I've saved your notes." | none yet |
| [14:35](chat/20260928-143542-chat.md) | "Got it. I've noted that the ALA internship pays $12,000 a month." | Added a rule to `prompts/persona.md`: "You cannot save anything..." The model ignored it. |
| [14:39](chat/20260928-143904-chat.md) | Same reply, followed by a notice from the harness | Changed `wiki_cli/chat.py`: when a message asks to note, remember, or save something, the harness prints a fixed notice that chat cannot save and ask will not see it. |

The fix does not depend on the model following instructions. The small model's reply is unchanged, but the user always sees the correct statement.
