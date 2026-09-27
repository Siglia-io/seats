---
name: seats-new
description: Use when the user wants to set up a new group of chat seats (a Log chat, author chats, a research chat, blind checkers, a Skills chat) to interrogate, research or build something in a project. Also use for a second group in the same project at a different scope, intensity or complexity. It interviews the user and writes the group's rules, briefs, folders and a one-paste launcher that opens the Log first.
---

# seats-new — set up a chat group

You are setting up a group of chat seats. Every seat has one job, one knowledge base and one priority, so that no single chat can talk itself into a conclusion. The Log opens first and runs the group.

## 1. Interview (ask these five, one message, then proceed on defaults for anything unanswered)
1. **Where:** the project root, and the name of the context folder (default `context/`).
2. **What is examined:** the documents or questions, with paths.
3. **Goal and intensity:** examine documents, research, or build. Tier: light, standard (default) or full (see `docs/SPEC.md` §3.5).
4. **Who decides:** the owner's name, and any second approver. Their words are always quoted verbatim.
5. **How terminals open:** one launcher paste (default) or tmux.

## 2. Write the group (deterministic; no judgment needed)
- `<root>/seats/PIPELINE.md`, from `templates/rules/PIPELINE.example.md`. Replace the roles, the knowledge-base rows and the documents with the interview's answers. Keep §3's shared rules (evidence, item blocks, independence, no pandering) unchanged.
- `<root>/seats/LEARNING-LOOP.md` and `LESSONS.md`, from `templates/rules/` (`LESSONS.pilot-run-1.md` is a worked example of filled entries, not a file to copy).
- `<root>/seats/skills/`, the group's skill store (INDEX, REQUESTS, REVIEWS). It starts empty: the Skills seat builds this project's skills there, each with a test from a recorded instance.
- `<root>/<context>/chats/<seat>/` for every seat, plus `<context>/log/`, `<context>/relay/` and `<context>/_sealed/`.
- The Log's brief, from `templates/roles/log.md`, and one brief per seat.
- `<root>/seats/launch.sh`, from `templates/launch/launch_all.example.sh`. It exports `SEATS_ROOT`, `SEATS_CONTEXT`, `SEATS_OWNER` and `SEATS_APPROVER` (the names used after `Route:`), opens the Log first with its brief, then each seat in its own terminal: `--permission-mode bypassPermissions` only if the owner has chosen it, and `CLAUDE_CODE_DISABLE_AUTO_MEMORY=1` so project memory cannot cross between seats.

## 3. Hand over
Give the owner the full, numbered steps: which app to open, what to paste, and what they will see when it worked. Every command goes in its own copy-paste block. From there the Log runs the group. The Log starts `scripts/capture.py` in the background and follows its brief.

## Honest scope of this version (v0.1)
Included: the interview (this skill), the templates, and the Log's tooling (capture, coalesce, setup check, the narrative workflow). Project-specific skills (row guards, quote-at-page, clock, pre-FINAL gate, attack-before-filing) are not shipped: they are generated per project, in the store this skill sets up, by the Skills seat. **Not built yet:** the enforcement hooks (session-start role injection, the before-every-tool guard) and the MCP spine described in `docs/SPEC.md`. Until they are built, the rules are instructions, not enforcement.
