# Lessons — the system's memory between runs (worked example: a pilot run)

Append-only. One entry per adopted or rejected lesson (see `LEARNING-LOOP.md` §3). Each entry: id, run, the lesson in one sentence, the recorded instances it rests on (pointers), the change it made (amendment / skill / test / memory / restructure, with the file), its test and result, and — later — whether it moved its measure.

This file shows two lessons from a pilot run of the method, stripped of that run's project. In a real group, quote the owner's words verbatim, with the clock time of the message; here they are paraphrased.

Run 1 (27 Sep 2026) is the first orientation and tuning; its measures are the baseline. No lessons adopted yet.

## L-001 · Run 1 · When the owner must act, give them every step and every command, ready to paste
- **The owner's order (paraphrased):** keep this in memory and in the documents so it is never forgotten: whenever you instruct the owner or advise a terminal command, give the full step-by-step. After they open a terminal, give every command to copy and paste. And stop triggering a request to allow each command.
- **What happened:** the Log told the owner to "press Enter on 'Yes, I accept' in the Vet tab" three times, without saying where the tab was or how to reach it. It also opened Terminal-panel tabs, each of which asked the owner to allow the command.
- **Change (adopted on the owner's decision):** rule: any instruction to the owner is a full numbered sequence (which app, how to open it, what to press, each command in its own paste block, what they will see when it worked). Tooling: routines run as background processes that need no approval; work the owner must run is bundled into one script and one paste (`<context>/chats/log/launch_cli_chats.sh`).
- **Where it lives:** the owner's global instructions file (writing and communication conventions) and a global memory note on paste-ready owner steps.
- **Measure:** the count of owner instructions per run that lack a paste-ready step, and of allow prompts the Log causes. Baseline in Run 1: 3 incomplete instructions and 5 terminal tabs opened.

## L-002 · Run 1 · The Log never decides, and its subagents never verify
- **The owner's order (paraphrased):** stop; this betrays the system. Subagents are for collection and scanning, not verification. The Log does not decide. The seats go back and forth until a decision is made, or until they admit it cannot be made yet and say why. The Log's job is to ledger, coalesce and present the findings as one: connected where they meet, disjoint where they do not. Then: commit the error to memory and to the documents, and relay it to Skills, which is to build whatever skills, knowledge bases, hooks or suites prevent it.
- **What happened:** asked for a final report, the Log launched a synthesis in which its own subagents were to sort every seat's findings into affirmed, refuted, unsupported, contested and so on, and to re-check quotes as verification. The owner stopped it before any output was written. This repeated, larger, an error the owner had corrected an hour earlier (the Log is not to judge what a finding means), and the Log's 04:34 ruling on Scope's question, recorded in INTEGRITY.md.
- **Change (adopted on the owner's decision):**
  - The Log ledgers, coalesces, routes and presents the seats' findings as one: connected where the seats' findings meet on a source passage, disjoint where they don't, each finding attributed with the seat's own label.
  - Subagents collect and scan only.
  - Verdicts come from the seats' back-and-forth, or a seat's admission that it can't decide yet and why.
  - Built at once: `<context>/chats/log/coalesce.py` (shipped as `scripts/coalesce.py`), a script that decides nothing.
  - Skills is asked to build prevention: skills, knowledge, hooks or any suite.
- **Where it lives:** a global memory note (the orchestrator never decides), this file, INTEGRITY.md, the seats plugin's Log role template.
- **Measure:** count of Log outputs (reports, notes, subagent prompts) that carry a truth label as the Log's own. Baseline for Run 1: 2 (the 04:34 ruling, the 05:12 synthesis).
