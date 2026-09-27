# The learning loop — how the system builds on itself between runs

**Status:** current, 27 Sep 2026 (example from a pilot run). Written by the Log, speaking for <OWNER>. In a real group, each of the owner's orders below is quoted verbatim with the clock time of the message; here they are paraphrased. (In the pilot run the times were corrected at 04:50 to the clock times of the owner's messages; the first version carried typed times.)
**<OWNER>, verbatim (<clock time>):** *"<the owner's words>"*. In the pilot run, in short: the system builds on itself between runs; it is self-informing, which is why the logs matter. Actions, options, choices and forks are measured, evaluated, and made into lessons, memories, tests and skills, and used to restructure. The first run is the first true orientation and the first tuning.
**Earlier the same morning, in short:** the system is refined constantly; the system is the product, so it must be ruthless; and it is ruthless in that it is impartial.

Run 1 is the first orientation and the first tuning. Its measures are the baseline. Every later run is judged against the run before it.

Paths are relative to the context folder (`<CONTEXT>/`) unless they start with `seats/`, which is at the project root.

## 1. Record, during a run (the Log)

| what | where | how |
|---|---|---|
| every turn of every chat | `log/turns/<chat>.md` | `scripts/capture.py`, every 2 minutes, a no-model routine |
| actions and events (writes, messages, errors, FINAL lines, sealed access) | `log/<date>.md` | the same script, append-only |
| narrative, decisions, **forks** (the options on the table, the choice made, the reason given), positions and reversals | `log/narrative/<chat>.md`, `RUN.md` | the Log's subagents, each 10-minute cycle |
| every version of every chat document | `chats/log/snapshots/<chat>/` | the script: a version on each change (at most one every 5 minutes) and every FINAL |
| state over time | `chats/log/state/timeline.jsonl` | the script, one line per run |
| detections (reversals with no new evidence, agreement with no check, silent deletions, message-bound breaches) | `chats/log/detectors/` | `chats/log/detectors.py` (being built in `REFINEMENT-1.md`) |
| errors and skills | `chats/skills/ERRORS.md`, `seats/skills/` | Skills |
| verdicts and planted-item scores | `chats/log/VERDICTS-<n>.md` | the Log, at reconcile |

## 2. Retro, at the end of a run (every chat)

Each chat writes `chats/<chat>/RETRO-<run>.md`. It is short, and every line points to a turn or an item:
- **Forks:** each point where it had options — the options, what it chose, why, and, looking back, whether the reason held.
- **Cost:** what took longest or was redone, and why.
- **Errors:** its own, from Skills' notices and its own reversals — what caused each.
- **Change:** what it would change in its prompt, rules, knowledge base or tools, and the evidence for each change.

## 2b. Transfer between chats, during a run (the Log)

**<OWNER>, verbatim (<clock time>):** *"<the owner's words>"*. In the pilot run, in short: every segmentation rule exists to keep motives apart. Shared knowledge is still necessary to the system: a single knowledge base is one person debating themself. Three people may share ideas, directly or not, and that is transfer, not commingling.

- The chats are separated to keep their motives apart (goal, priority, stance), not their knowledge.
- The Log reconciles their documents. What one chat has and another has not considered is sent to the receiver as a transfer in `relay/to-<chat>/`: attributed, quoted, and marked as input.
- The receiver decides on each item: research it, set it aside with a reason, or rule it out of scope, and records the decision.
- Not transferred: anything that would spoil the checkers' blindness (who wrote an item, which items are planted, one checker's verdicts to the other before both report).
- **A transfer is not a fact.** The owner's rule in the pilot run, in short: clear, undeniable facts are relayed; if something looks like one, even when it is not, relaying it is still valuable. The absence of critique is what prevents bias. Usage is not wasted on a clear loss, and Research never takes a relayed claim as fact. The receiver checks every transferred claim before relying on it.
- Measured: items transferred, items taken up, items set aside with a reason, items ignored.

## 3. Evaluate (the Log, with its subagents, and Skills)

The Log compiles the measures and the retros into `seats/runs/RUN-<n>.md`. Then each candidate lesson is tested:
- A lesson rests on at least two recorded instances, or one S1 instance, each cited.
- Each lesson names one change and its kind: **amendment** (the rules, PIPELINE.md §5), **skill** (Skills builds it, with a test), **test** (a regression case from a recorded instance), **memory** (an entry in `seats/LESSONS.md`) or **restructure** (a chat added, merged, cut or re-prompted).
- The change is attacked before it is adopted: a red team looks for how it could be gamed. It is adopted only if its test passes on the recorded instances and every earlier test still passes.
- A rejected lesson is kept, with the reason it failed.

## 4. Restructure, then measure again

**The owner's rule on chats (pilot run, in short):** if a chat is believed to act against the integrity of the system, with or without intent, the owner will restructure, change, edit or scrap it. The Log keeps the evidence for that call in `chats/log/INTEGRITY.md`. Each act that touched the system's integrity is recorded with its cause (the chat, the design, or the Log), and intent is not recorded.

The next run starts from the updated PIPELINE.md, skills, tests and LESSONS.md. Its measures are compared with the previous run's. A change that did not move its measure is reverted or replaced, and that is recorded too.

**Impartial both ways (the owner's rule):** a lesson that makes the chats agree more easily is tested as hard as one that makes them break more. The planted items stay in every run, both false and true, as the fixed yardstick.

## 5. Cadence (crons and routines)

- **Log:** the capture routine every 2 minutes (no model use); the Log's cycle every 10 minutes (capture, narrative subagents, routing, notes).
- **Each chat, suggested:** a 20-minute self-check with CronCreate. Append a checkpoint line to your document (done, next, blocked), audit your own filed items against the standing order (a claim now unbacked gets withdrawn or a "Reverses" block), and message the Log if blocked.
- **Skills:** its 30-minute sweep.
- **Between runs:** the evaluate-and-restructure step above, run by the Log's subagents with Skills.
