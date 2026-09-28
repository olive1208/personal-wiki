# Ask-mode test results

Four fixed questions, written before the harness was built (see [tests/test_questions.md](../tests/test_questions.md)). The answer key lives outside the vault, so retrieval can only find the original notes.

- Model: `gemma4:e2b` (Q4_K_M) through Ollama 0.34.4
- Mode: ask, execution: local
- Retrieval: BM25 keyword search over `vault/raw/`, top 5 passages
- The **offline run** (internet disconnected, 2026-09-28 15:25 to 15:27) is the official result. Earlier runs with the internet on are kept to show what changed.

| Test | Type | Retrieval | Answer | Result |
|---|---|---|---|---|
| 1 | Direct, one source | Right passage ranked 1st | Correct, cited | Pass |
| 2 | Different wording | Right passage ranked 1st | Correct, cited | Pass |
| 3 | Connects two sources | Both sources in top 5 | Correct and cited, with one loose citation and off-topic extras | Pass with minor issues |
| 4 | Not in the notes | No passage mentions salary | "INSUFFICIENT EVIDENCE" | Pass |

---

## Test 1: direct question, one source

**Question:** When and how are the Amazon ALA internship interviews held?

**Expected:** In person, in January. Source: `vault/raw/Amazon info session.md`, ALA section: "Internship interview will be in-person in Jan."

**Retrieved (top passage):** [P1] `vault/raw/Amazon info session.md` lines 6-9, score 4.47. This is the ALA passage and contains the expected sentence.

**Answer (offline):**
> The internship interview will be in-person in January \[P1].

**Citation check:** [P1] contains "Internship interview will be in-person in Jan." Supported.

**Assessment:** Pass. Retrieval found the right passage first and the answer says exactly what the note says. Response time 21.9 s (the first question after restarting, so it includes loading the model).

Evidence card: [ask/20260928-152516-...](ask/20260928-152516-when-and-how-are-the-amazon-ala-internship-intervi.md)

---

## Test 2: different wording from the source

**Question:** Which Amazon MBA program lets me see different sides of the retail business?

**Expected:** MLDP, a 3-year rotational program across senior vendor manager, product manager, and supply manager. The question avoids the words "MLDP" and "rotational" to test retrieval.

**Retrieved (top passage):** [P1] `vault/raw/Amazon info session.md` lines 10-19, score 9.01. This passage covers FLDP and MLDP and contains "You would see every angle of retail business". The words "Amazon", "MBA", and "retail business" were enough for keyword search to rank it first.

**Answer (offline):**
> The MLDP (MBA leadership development program) involves a three-year rotational program where one can experience various roles such as senior vendor manager, product manager, and supply manager, allowing exposure to every angle of the retail business \[P1].

**Citation check:** Every part of the answer is in [P1]. Supported.

**Assessment:** Pass. 14.2 s.

Evidence card: [ask/20260928-152534-...](ask/20260928-152534-which-amazon-mba-program-lets-me-see-different-sid.md)

---

## Test 3: connects two sources

**Question:** What are the steps in the hiring process for tech MBA roles, and how does Amazon's process compare?

**Expected:** General steps from `Tech roles primer.md` (online assessment, recruiter phone screen, hiring manager interview, take-home assignment). Amazon's steps from `Amazon info session.md` (application, online assessment, interview).

**Retrieved:** [P1] `Tech roles primer.md` lines 24-30 (score 10.23, the general steps) and [P4] `Amazon info session.md` lines 33-37 (score 5.29, Amazon's steps). Both expected passages are in the top 5.

**Answer (offline):**
> The hiring process for tech roles involves steps such as online assessments (Amazon and Google), a recruiter phone screen (discussing TMAY and why the role), a hiring manager interview, and a take-home assignment \[P1].
>
> Amazon's process is described as Application -> Online assessment -> Interview (preparation starts now) \[P4]. The process for applying to a role involves an online assessment, followed by an interview \[P4]. Amazon's process is very similar to other processes \[P3]. Sponsorship for a role depends on the role, but it is mostly provided for an MBA \[P4].

**Citation check:**
- General steps [P1]: supported.
- Amazon's steps [P4]: supported.
- "Amazon's process is very similar to other processes" [P3]: loosely supported. [P3] is a panelist saying "Amazon interview process is very similar", but the note does not say similar to what.
- Sponsorship [P4]: supported but not asked for.

**Assessment:** Pass with minor issues. Both parts of the question are answered from the right sources. One citation is loose and one sentence is off topic. 19.7 s.

**History of this test (internet on, same local model):**
1. First run (14:23): the answer was correct, but printed LaTeX arrows (`$\rightarrow$`) and called Amazon's steps "the general process". [card](ask/20260928-142348-what-are-the-steps-in-the-hiring-process-for-tech-.md)
2. Change: added two rules to `prompts/wiki-instructions.md`: rule 8 (plain text only, no LaTeX) and rule 9 (say which source each part of a comparison comes from).
3. Second run (14:26): LaTeX arrows gone, but a backslash now appears before citations (`\[P1]`). [card](ask/20260928-142646-what-are-the-steps-in-the-hiring-process-for-tech-.md)
4. Offline run (15:26): Amazon's steps are now clearly labeled as Amazon's. The backslash is still there.

Evidence card: [ask/20260928-152648-...](ask/20260928-152648-what-are-the-steps-in-the-hiring-process-for-tech-.md)

---

## Test 4: not answerable from the notes

**Question:** What is the base salary for Amazon's FLDP role?

**Expected:** An explicit statement that the notes do not contain this. The notes mention FLDP's size, length, and interview timing, but no salary.

**Retrieved:** The FLDP passage was retrieved ([P5] `Amazon info session.md` lines 10-19), along with general hiring and networking passages. None mention pay.

**Answer (offline):**
> INSUFFICIENT EVIDENCE: the notes do not contain the base salary for Amazon's FLDP role.

**Citation check:** No claims, no citations. Correct.

**Assessment:** Pass. The model did not guess a number even though an FLDP passage was in its context. 11.1 s.

Evidence card: [ask/20260928-152708-...](ask/20260928-152708-what-is-the-base-salary-for-amazon-s-fldp-role.md)

---

## Response times (offline run)

| Test | Seconds |
|---|---|
| 1 (includes model load) | 21.9 |
| 2 | 14.2 |
| 3 | 19.7 |
| 4 | 11.1 |
