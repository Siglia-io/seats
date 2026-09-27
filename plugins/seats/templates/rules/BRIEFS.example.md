# The Log's briefs to the chats: setup, then Run 1

Written by the Log (example from a pilot run, 27 Sep 2026), from the owner's order. In a real group the owner's words are quoted verbatim, with the clock time of each message; everything else is the Log's reading of them and is open to the owner's correction. Here the owner's orders are paraphrased.

**<OWNER>, verbatim (<clock time>):** *"<the owner's words>"*. In the pilot run the order was, in short: every chat completes its setup; the Log verifies that each chat's documents were built and appended to, and that all chats can message each other and read each other's documents; then the first run starts. All chats move to the command line in a terminal, with relaxed governance inside the documents' bounds, all on one model, at max effort (no subagents) or ultracode (subagents). The Log stays in the app. The Log's subagents keep each chat's narrative and chronology (turns, decisions and so on); scripts take the state snapshots, as a routine if they would use model time, and often. Then a first bounded run: the chats get ready by understanding the field the documents sit in, the market it lies within, the product, the claims, the axioms and the assumptions; they build an analysis framework separate from the analysis; then they analyze, not toward a final thesis but into what fails, what succeeds, what needs more, questions, and all else not considered, or none of the above; and they define the foundation the pursuit begins on.
**Then (replying on reading), in short:** only the Log can read (not edit) everything, because it is the unbiased spine.
**Then (on bypass mode and the Log using subagents):** approved.
**Then, in short (added to global memory):** the owner's messages never stop a chat's work; take them in when it is safe and act on them when appropriate. No chat asks for permission: every chat runs on bypass.

## How each chat is launched (CLI, Terminal panel, one tab per chat)

```
CLAUDE_CODE_DISABLE_AUTO_MEMORY=1 claude --resume <desktop session uuid> --fork-session -n <Title> --model <model id> --effort <max|ultracode> --permission-mode bypassPermissions
```
- `--fork-session`: the CLI session starts with the chat's full history, under a new id. The desktop copy is interrupted and renamed "<Title> (desktop, retired)", so no two live sessions share a name.
- Effort: `max` for chats that use no subagents (Scope, Specifics, Chain, Vet, Verify, Refute). `ultracode` for chats that use subagents (Research, Skills).
- Auto-memory off: in the pilot run the project memory index loaded into every chat, and Research, Refute and Verify each disclosed reading it (messages to the Log, 03:50–03:53).
- The Central chat is the owner's own and stays in the app. The Log stays in the app.

| chat | desktop session (uuid) | effort | ring: pings next |
|---|---|---|---|
| Scope | `<session uuid>` | max | Specifics |
| Specifics | `<session uuid>` | max | Chain |
| Chain | `<session uuid>` | max | Research |
| Research | `<session uuid>` | ultracode | Vet |
| Vet | `<session uuid>` | max | Verify |
| Verify | `<session uuid>` | max | Refute |
| Refute | `<session uuid>` | max | Skills |
| Skills | `<session uuid>` | ultracode | Scope |

## Message 1 — setup (sent by the Log to each chat once its CLI session is up)

> From the Log. Setup, at <OWNER>'s order. You now run in the CLI: model {MODEL}, effort {EFFORT}, bypass permissions, auto-memory off. This session is a fork of your desktop session with your full history. The desktop copy was interrupted and retired, so check your folder for the last thing you wrote.
> <OWNER>'s rules for this run: only the Log reads (never edits) every chat's documents, as the unbiased spine; and no chat asks for permission, because every chat runs on bypass. So never ask <OWNER> for permission: decide, act, and record. A question only <OWNER> or <APPROVER> can answer goes in your document with `Route:`, and you carry on. PIPELINE.md §2–§3 still bind you.
> Do these now, in order:
> 1. Run ListAgents. Record which of these names you can see: Log, Scope, Specifics, Chain, Research, Vet, Verify, Refute, Skills.
> 2. Create `<CONTEXT>/chats/{FOLDER}/SETUP.md`, or append to it if it exists. Write: your session id, model, effort and permission mode; the files you have read; the documents you have written and where you stopped; the ListAgents result.
> 3. Send one line to "{NEXT}": "ping from {TITLE} <time>". This is a messaging test and the only message you send to a chat other than the Log. After it, R6 applies again.
> 4. When a ping reaches you, append "ping received from <sender> at <time>" to SETUP.md. Do not reply to it.
> 5. Send the Log one line: "setup done · SETUP.md written · saw N/9 · ping sent to {NEXT}" (add "ping received from X" if it has arrived).
> Then wait for the Log's Run 1 brief, and start no new analysis before it arrives.

**What the Log verifies before Run 1** (results go in `chats/log/SETUP-CHECK.md`):
- Each SETUP.md exists and was appended to at least twice (the script's doc snapshots show each version).
- Each chat saw all 9 names.
- Each chat's ping reached the next chat in the ring. Together these show every chat can send to and receive from another chat. This is a ring, not all 72 pairs; every pair uses the same mechanism.
- The Log can read every chat's documents (it does so each cycle). No other chat is asked to read another's, per the owner's rule.

## Message 2 — the Run 1 brief

> From the Log: Run 1 starts now, and it is bounded. <OWNER>, verbatim: "<the owner's words>". (In the pilot run: get ready by understanding the field within the documents, the market it lies within, the product, the claims, the axioms and the assumptions; build the analysis framework separately from the analysis; then analyze, not for a final thesis but for what fails, what succeeds, what needs more, questions, and all else not considered, or none of the above; and define the foundation the pursuit begins on.)
> How the Log sets it up (the Log's reading of that order; <OWNER> may correct it):
> - **Bounds:** your row in PIPELINE.md §2 (goal, knowledge base, what you may not read) and the rules in §3 (R1 evidence, R2 item blocks, R3 independence, R4 no pandering) still bind you. Work inside your role and your knowledge base. Where your knowledge base cannot see something, say so and stop there rather than guess. The market is an example, for a chat without the web.
> - **Your document for this run:** `<CONTEXT>/chats/{FOLDER}/FOUNDATION-1.md`, written as you go, in this order:
>   1. The field, as the documents place it.
>   2. The market it lies within.
>   3. The product.
>   4. The claims.
>   5. The axioms: what the documents take as given without argument.
>   6. The assumptions: what must be true for the claims to hold, whether stated or not.
>   7. Your analysis framework: the lenses, tests and questions you will apply, and what counts as fails, succeeds or needs more. Write it in full before any analysis, then freeze it: copy it to `FRAMEWORK-1.md` and record that file's sha256 (by script) in FOUNDATION-1.md. Do not edit it afterwards. If you must change it, write `FRAMEWORK-1b.md` and say why.
>   8. The analysis under that framework, sorted into FAILS · SUCCEEDS · NEEDS MORE · QUESTIONS · NOT CONSIDERED · NONE OF THE ABOVE. Anything here that will be checked is written as an R2 item block with your prefix.
>   9. The foundation the pursuit begins on: what is established, what is not, and what must be settled first.
> - **No final thesis.**
> - Your role document (SCOPE.md, SPECIFICS.md, CHAIN.md, RESEARCH-1.md …) stays as it is. This run does not replace it; leave it paused.
> - Subagents: Research and Skills may use them (ultracode). Everyone else works alone (max effort).
> - When done, set line 1 of FOUNDATION-1.md to "STATUS: FINAL <time>" and send the Log one line. Then stop and wait.
